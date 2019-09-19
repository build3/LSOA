#!/bin/sh

set -e

NAME="kidviz"
NUM_WORKERS=5

#/tools/wait-for db:5432 -- echo Database ready

DJANGO_SETTINGS_MODULE=settings
DJANGO_WSGI_MODULE=wsgi

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

pipenv run ./manage.py collectstatic
pipenv run ./manage.py migrate

exec pipenv run gunicorn ${DJANGO_WSGI_MODULE}:application \
    --name $NAME \
    --workers $NUM_WORKERS \
    --bind=0.0.0.0:80 \
    --log-file=-
