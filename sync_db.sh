#!/bin/bash

dropdb lsoa
dropuser lsoa
createuser lsoa -S
createdb lsoa
echo "GRANT ALL ON DATABASE lsoa TO lsoa;" | psql -d lsoa

export PGPASSWORD="a9c40c18fb6acb178ad14770cd995fc7df6cd277494c681b69f8221b03d7e204"
pg_dump -h ec2-54-235-86-244.compute-1.amazonaws.com -p 5432 -Fc --no-acl --no-owner -o -U cjkjixfzqxvufd d3q8rv0h6cuhp4  | gzip > dumpfile.gz

unset PGPASSWORD
gunzip -c dumpfile.gz | pg_restore --verbose --clean --no-acl --no-owner -d lsoa -U lsoa && rm -f dumpfile.gz
