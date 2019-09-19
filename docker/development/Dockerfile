FROM python:3.7-slim

RUN apt update && apt install -y gcc libpq-dev netcat pipenv
COPY tools/wait-for /tools/wait-for
COPY tools/run-development.sh /tools/run.sh

WORKDIR /app

EXPOSE 8000
