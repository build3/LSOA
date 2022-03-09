FROM python:3.7-slim

RUN apt-get clean && apt-get update && apt-get install -y gcc libpq-dev netcat pipenv curl
COPY tools/wait-for /tools/wait-for
COPY tools/run-production.sh /tools/run.sh

COPY Pipfile Pipfile.lock /app/

WORKDIR /app
RUN pipenv install

COPY . /app

EXPOSE 80

CMD ["/tools/run.sh"]
