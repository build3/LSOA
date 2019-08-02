#!/bin/sh

/tools/wait-for db:5432 -- echo Database ready

pipenv install

pipenv run ./manage.py migrate
exec pipenv run ./manage.py runserver 0.0.0.0:8000 2>&1
