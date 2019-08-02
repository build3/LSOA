# Prerequisites

* `docker` `>= 17.09`
* `docker-compose` (for development environment)

# Environments

The setup procedure for both environments (`development` and
`production`) is exactly the same. The only difference is the directory
in which the commands should be run.

# Running images

At first navigate to the directory specific to the variant you want to
run:

```bash
$ cd docker/<environment>
```

where `<environment>` is either `production` or `development`. Then
create directory which will store database files:

```bash
$ mkdir data
```

Copy the initial SQL dump to `kidviz.sql` file:

```bash
$ cp path/to/dump.sql kidviz.sql
```

This dump is necessary since the Django migrations will fail on empty
database.

Create the `env` file:

```bash
$ touch env
```

Fill it with all necessary environment variables (like AWS keys) that
should be passed to the application in runtime. Each variable should be
placed on separate line in th following format:

```
VARIABLE_NAME=variable_value
```

Build images:

```bash
$ docker-compose build
```

Run the application:

```bash
$ docker-compsoe up
```

The development version will be available at [http://localhost:8000](http://localhost:8000),
and the production version will be bound to [http://localhost](http://localhost).
