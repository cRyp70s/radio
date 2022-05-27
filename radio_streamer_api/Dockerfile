# This is a simple Dockerfile to use while developing
# It's not suitable for production
#
# It allows you to run both flask and celery if you enabled it
# for flask: docker run --env-file=.flaskenv image flask run
# for celery: docker run --env-file=.flaskenv image celery worker -A myapi.celery_app:app
#
# note that celery will require a running broker and result backend
FROM python:3.8-alpine


RUN mkdir /code
WORKDIR /code
COPY requirements.txt setup.py tox.ini ./
RUN pip install -U pip
RUN \
 apk add --no-cache postgresql-libs && \
 apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
 python3 -m pip install -r requirements.txt --no-cache-dir && \
 apk --purge del .build-deps
RUN pip install -r requirements.txt
RUN pip install -e .

COPY . .
EXPOSE 8000
EXPOSE 8001
ENTRYPOINT ["gunicorn", "api.wsgi:app", "-b", "0.0.0.0:8000"]
