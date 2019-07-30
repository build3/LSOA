# Prerequisites

* `docker` `>= 17.09`
* `docker-compose` (for development environment)

# Production image

To build production image run:

```bash
$ docker build -t <docker_image_name> -f docker/Dockerfile-prod .
```

The resulting image will run gunicorn server and expose port 80 to the
host.

To run the image on the host please run:

```bash
$ docker run -d -p 80:80 --env-file=.env <docker_image_name>
```

This will spawn new docker container which will serve the application on
the host's port 80. Also, the static file collection and database
migrations will be run on it's startup.

The `.env` file should contain all environment variables neede to
configure the application, especially the database connection string:

```
DATABASE_URL=postgres://user:password@db-host:5432/lsoa
```

# Development environment

To run development image with `docker-compose` you need to provide
initial database dump. Place it in the main code directory in
`kidviz.sql` file. To run development environment use:

```base
$ docker-compose up --build
```

The development server will be available at
[http://localhost:8000](http://localhost:8000) and the code will be
watched for changes.

> NOTE: the current setup does not provide all environment options that
> are referenced in the `settings.py`. To add other please edit
> `docker-compose.yml` and add them in section
> `services.backend.environment`.
