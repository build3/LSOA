FROM python:3.7-slim

RUN apt update && apt install -y gcc libpq-dev netcat
COPY tools/wait-for /tools/wait-for
COPY tools/run-development.sh /tools/run.sh

RUN pip install -U pip
RUN pip install pipenv
RUN cp /usr/local/bin/pipenv /usr/bin/pipenv

WORKDIR /app

EXPOSE 8000
