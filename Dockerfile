FROM python:3.8-slim-buster
WORKDIR /app
COPY requirements.txt requirements.txt
RUN apt-get update && apt-get install ffmpeg -y
RUN pip3 install -r requirements.txt
COPY ["run.py", "config.py", "streamer", "common", "static", "./"]
ENTRYPOINT ["python", "run.py"]