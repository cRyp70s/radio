import logging
import random
import time
import os
import subprocess as sp

import requests

from conf import RTSP_STREAM, CACHE_FILE_TIME
from ..common.redis import redis_backend

# Command to stream music to rtsp-simple-server instance with ffmpeg
COMMAND = [
    "ffmpeg",
    "-re",
    "-stream_loop",
    "-1",
    "-i",
    "-",
    "-acodec",
    "rawaudio",
    "-c",
    "copy",
    "-vn",
    "-f",
    "rtsp",
    RTSP_STREAM,
]

logging.basicConfig(level=logging.DEBUG)

# Local cache directory
if not os.path.exists("static/"):
    os.mkdir("static/")


def get_from_url(playlist, song, song_url):
    """
    Get song from url or local cache
    and store in opus format.
    """
    filename = f"static/{playlist}-{song}"
    filename2 = f"static/{playlist}-{song}.opus"
    logging.debug(f"Retrieving {filename}")
    # Download if file doesnt exists or is stale
    if (
        not os.path.exists(filename)
        or (time.time() - os.path.getmtime(filename)) > CACHE_FILE_TIME
    ):
        logging.debug(f"Downloading {filename}")
        for _ in range(5):
            # Retry up to five times
            resp = requests.get(song_url)
            if resp.ok:
                data = resp.content
                with open(filename, "wb") as f:
                    f.write(data)
                com = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    filename,
                    "-c:a",
                    "libopus",
                    "-b:a",
                    "40K",
                    filename2,
                ]
                sp.check_output(com)
                break
        else:
            msg = f"Could not download media: {resp.reason}"
            logging.error(msg)
            resp.raise_for_status()
    with open(filename2, "rb") as f:
        return f.read(), filename2


def run():
    """
    Run and execute main server loop.
    """
    PIPE = sp.Popen(COMMAND, stdin=sp.PIPE)
    last_playlist = ""
    promotions = []
    played = 0
    logging.debug("Starting")
    while True:
        try:
            while True:
                # CURRENT_PLAY is a list in the following format
                # [<playlist>, [(name, song_url, thumbnail_url)..]]
                playlist, songs = redis_backend.get("CURRENT_PLAY")

                try:
                    # Get ads
                    promotions = redis_backend.get("CURRENT_PROMOTIONS")
                except Exception as e:
                    logging.exception(e)

                for song_name, url, thumb_url in songs:
                    logging.debug(f"Setting {song_name} as playing.")
                    played += 1
                    song_data = get_from_url(playlist, song_name, url)
                    logging.debug(song_data[0][:10])
                    logging.debug("Setting Thumbnail.")
                    redis_backend.set("CURRENT_THUMB", thumb_url)
                    redis_backend.set("CURRENT_SONG", song_name)
                    PIPE.stdin.write(song_data[0])
                    fp = os.path.abspath(song_data[1])
                    sl = float(
                        sp.Popen(
                            f'ffprobe -i {fp} \
                              -show_entries format=duration\
                                -v quiet -of csv="p=0"',
                            shell=True,
                            stdout=sp.PIPE,
                        ).stdout.read()
                    )
                    sleep = sl * 0.95
                    logging.debug(
                        f"Waiting for {song_name} \
                                  to finish play {sleep}."
                    )
                    playlist, songs = redis_backend.get("CURRENT_PLAY")

                    if playlist != last_playlist:
                        # Playlist changed
                        PIPE.kill()
                        PIPE = sp.Popen(COMMAND, stdin=sp.PIPE)
                        break

                    if (played % 6) == 0:
                        # Play a random ad
                        logging.debug("Playing Promotion")
                        try:
                            name, url, thumb_url = random.choice(promotions)
                            song_data = get_from_url("promotions", name, url)
                            PIPE.stdin.write(song_data[0])
                            redis_backend.set("CURRENT_THUMB", thumb_url)
                            fp = os.path.abspath(song_data[1])
                            sl = float(
                                sp.Popen(
                                    f'ffprobe -i {fp} -show_entries \
                                        format=duration -v quiet -of csv="p=0"',
                                    shell=True,
                                    stdout=sp.PIPE,
                                ).stdout.read()
                            )
                            sleep = sl * 0.95
                            time.sleep(sleep)
                        except Exception as e:
                            logging.exception(e)
                last_playlist = playlist
        except Exception as e:
            logging.exception(e)
