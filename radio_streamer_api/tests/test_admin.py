from io import BytesIO

import pytest
from flask import url_for

plist = "test"
song = "test_song"

#PLAYLIST TESTS

@pytest.fixture
def create_plist(client, admin_headers):
    playlist_url = url_for('api.playlist')
    data = {
        "playlist": plist,
        "title": "test_song",
        "audio_url": "https://wwww.test.com/music.mp3",
        "thumbnail_image_url": "https://wwww.test.com/music.jpg"
    }
    resp = client.post(playlist_url, headers=admin_headers,
                     json=data)
    return resp.status_code

def test_create_plist(create_plist):
    # Test create playlist
    assert create_plist == 201

def test_play_plist(client, admin_headers, create_plist):
    play_url = url_for('api.play')

    # Test play from playlist
    resp = client.post(play_url, headers=admin_headers,
                     json={"playlist": plist})
    assert resp.status_code == 200 and resp.get_json()[0] == plist

    # Test non existent plist
    resp = client.post(play_url, headers=admin_headers,
                     json={"playlist": plist+"33443333"})
    assert resp.status_code == 404
    

def test_delete_plist(client, admin_headers, create_plist):
    # Test delete playlist
    play_url = url_for('api.playlist', title=song, playlist=plist)

    resp = client.delete(play_url, headers=admin_headers)
    assert resp.status_code == 200

    play_url = url_for('api.playlist', title="er4trg234", playlist="Ddddd")
    resp = client.delete(play_url, headers=admin_headers)
    assert resp.status_code == 404

def test_get_plist(client, admin_headers, create_plist):
    # Test get playlist
    play_url = url_for('api.playlist', playlist=plist, title=song)

    resp = client.get(play_url, headers=admin_headers)
    data = resp.get_json()["results"][0]
    assert resp.status_code == 200 and data["playlist"] == plist \
            and data["title"] == song
    
    # Test get playlists only
    play_url = url_for('api.playlist', playlist=plist, title=song,
                        playlists_only="true")
    
    resp = client.get(play_url, headers=admin_headers)
    data = resp.get_json()["playlists"]
    assert resp.status_code == 200 and plist in data[0]
    
    # Test non existent playlist
    play_url = url_for('api.playlist', playlist="fdtg4r54t4", title=song)
    resp = client.get(play_url, headers=admin_headers)
    assert resp.get_json()["results"] == []
    

# MEDIA RESOURCE TESTS

@pytest.fixture
def create_media(client, admin_headers):
    media_url = url_for('api.media', title=song, playlist=plist)
    data = {
            'audio': (BytesIO(b'audio file content'), 'test.mp3'),
            'thumbnail': (BytesIO(b'test image data'), 'test.jpg'),
            }
    resp = client.post(media_url, headers=admin_headers,
                       data=data,
                       content_type="multipart/form-data",)
    return resp

def test_create_media(create_media):
    # Test create playlist
    assert create_media.status_code == 201

def test_delete_media(client, create_media, admin_headers):
    
    # Test delete media
    media_url = url_for('api.media', title=song, playlist=plist)
    resp = client.delete(media_url, headers=admin_headers)
    assert resp.status_code == 200

    # Test delete nonexistent media
    media_url = url_for('api.media', title=song, playlist=plist)
    resp = client.delete(media_url, headers=admin_headers)
    assert resp.status_code == 404

    # Test delete no title and playlist
    media_url = url_for('api.media')
    resp = client.delete(media_url, headers=admin_headers)
    assert resp.status_code == 400

def test_get_media(client, create_media, admin_headers):
    # Test get one media
    media_url = url_for('api.media', title=song, playlist=plist)
    resp = client.get(media_url, headers=admin_headers)
    data = resp.get_json()[0]
    assert resp.status_code == 200 and data["title"] == song \
            and data["playlist"] == plist
    
    # Test get multiple media
    media_url = url_for('api.media', title='*', playlist=plist)
    resp = client.get(media_url, headers=admin_headers)
    data = resp.get_json()[0]
    assert resp.status_code == 200 and data["title"] == song \
            and data["playlist"] == plist

    # Test get nonexistent media
    media_url = url_for('api.media', title="45354334", playlist="456ess")
    resp = client.get(media_url, headers=admin_headers)
    assert resp.status_code == 404

    # Test get no title and playlist
    media_url = url_for('api.media')
    resp = client.get(media_url, headers=admin_headers)
    assert resp.status_code == 400
