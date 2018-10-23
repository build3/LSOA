#!/bin/bash

echo "dropdb kidviz"
dropdb kidviz

echo "dropuser kidviz"
dropuser kidviz

echo "createuser kidviz -S"
createuser kidviz -S

echo "createdb kidviz"
createdb kidviz

echo "GRANT ALL ON DATABASE kidviz TO kidviz;"
echo "GRANT ALL ON DATABASE kidviz TO kidviz;" | psql -d kidviz

echo "heroku pg:backups:capture" && heroku pg:backups:capture && echo "heroku pg:backups:download" && heroku pg:backups:download && \
gunzip -c dumpfile.gz | pg_restore --verbose --clean --no-acl --no-owner -d kidviz -U kidviz && rm -f dumpfile.gz
rm -f latest.dump
