#!/bin/bash

echo "dropdb lsoa"
dropdb lsoa

echo "dropuser lsoa"
dropuser lsoa

echo "createuser lsoa -S"
createuser lsoa -S

echo "createdb lsoa"
createdb lsoa

echo "GRANT ALL ON DATABASE lsoa TO lsoa;"
echo "GRANT ALL ON DATABASE lsoa TO lsoa;" | psql -d lsoa

echo "heroku pg:backups:capture" && heroku pg:backups:capture && echo "heroku pg:backups:download" && heroku pg:backups:download && \
gunzip -c dumpfile.gz | pg_restore --verbose --clean --no-acl --no-owner -d lsoa -U lsoa && rm -f dumpfile.gz
rm -f latest.dump
