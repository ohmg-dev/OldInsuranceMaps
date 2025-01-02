# Online Historical Map Georeferencer (OHMG)

OHMG is a web application that facilitates public participation in the process of georeferencing and mosaicking historical maps. This is a standalone project that requires an external instance of [Titiler](https://developmentseed.org/titiler) to serve the mosaicked layers. See Dependencies below for more about the tech stack.

At present, the system is structured around the Sanborn Map Collection at the Library of Congress ([loc.gov/collections/sanborn-maps](https://loc.gov/collections/sanborn-maps)). More generic ingestion methods are in the works.

- **Implementation:** [oldinsurancemaps.net](https://oldinsurancemaps.net)
- **Documentation:** [about.oldinsurancemaps.net](https://about.oldinsurancemaps.net)

---

Please don't hesitate to [open a ticket](https://github.com/ohmg-dev/OldInsuranceMaps/issues/new/choose) if you have trouble with the site, find a bug, or have suggestions otherwise.

---

## Software Details

This is a Django project, with a frontend built (mostly) with [Svelte](https://svelte.dev), using [OpenLayers](https://openlayers.org) for all map interfaces. OpenStreetMap and Mapbox are the basemap sources.

### Third-party Django Apps

- [Django Ninja](https://django-ninja.dev) - API
- [Django Newsletter](https://github.com/jazzband/django-newsletter) - Newsletter (optional feature)

### External Dependencies

- Postgres/PostGIS
- Celery + RabbitMQ
- GDAL >= 3.5
- [TiTiler](https://developmentseed.org/titiler)

## Development Installation

Running the application requires a number of components to be installed and configured properly.

### Create database

Install Postgres/PostGIS as you like. Once running, create a database like this

```bash
psql -U postgres -c "CREATE USER ohmg WITH ENCRYPTED PASSWORD '$DB_PASSWORD'"
psql -U postgres -c "CREATE DATABASE oldinsurancemaps WITH OWNER ohmg;"
psql -U postgres -d oldinsurancemaps -c "CREATE EXTENSION PostGIS;"
```

See also `./scripts/create_database.sh`. You can run this script once you have updated the `DATABASE_*` variables in `.env`.

### Install Django project

Make virtual env

```bash
python3 -m venv env
source env/bin/activate
```

Install GDAL bindings. These must match exactly the version of GDAL you have on your system, so use this command:

```bash
pip install gdal=="`gdal-config --version`.*"
```

Clone the repo and enter the local directory

```bash
git clone https://github.com/ohmg-dev/OldInsuranceMaps && cd OldInsuranceMaps
```

Install the package into your virtual environment

```bash
pip install -e .[dev]
```

Install pre-commit hook

```bash
pre-commit install
```

Copy example environment variables file, and update this file as needed (more instruction each )

```bash
cp .env.example .env
```

Initialize database, create admin user

```bash
python manage.py migrate
python manage.py createsuperuser
```

Load all the place objects to create geography scaffolding

```bash
python manage.py place import-all
```

### Build frontend

The frontend uses a suite of independently built svelte components.

```bash
cd ohmg/frontend/svelte
pnpm install
pnpm run dev
```

### Run Django dev server

You can now run

```bash
python manage.py runserver
```

and view the site at `http://localhost:8000`.

However, few more components will need to be set up independently before the app will be fully functional. Complete the following sections and then rerun the dev server so that any new `.env` values will be properly aqcuired.

### Rabbit + Celery

In development, RabbitMQ can be run via Docker like so:

```bash
docker run --name rabbitmq --hostname my-rabbit \
  -p 5672:5672 \
  -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=username \
  -e RABBITMQ_DEFAULT_PASS=password \
  --rm \
  rabbitmq:3-alpine
```

For convenience, this command is in the following script:

```bash
source ./scripts/rabbit_dev.sh
```

Once RabbitMQ is running, update `.env` with the `RABBITMQ_DEFAULT_USER` and `RABBITMQ_DEFAULT_PASS` credentials you used above when creating the container.

Now you are ready to run Celery in development with:

```bash
source ./scripts/celery_dev.sh
```

### TiTiler

TiTiler can also be run via Docker, using a slightly modified version of the official container (it is only modified to include the WMS endpoint extension):

```bash
docker run --name titiler \
  -p 8008:8000 \
  -e PORT=8000 \
  -e MOSAIC_STRICT_ZOOM=False \
  -e WORKERS_PER_CORE=1 \
  --rm \
  -it \
  ghcr.io/mradamcox/titiler:0.11.6-ohmg
```

Or the same command is wrapped in:

```bash
source ./scripts/titiler_dev.sh
```

This will start a container running TiTiler and expose it to `localhost:8008`.

Make sure you have `TITILER_HOST=http://localhost:8008` in `.env`.

### Static file server

During development, a separate HTTP server must be used to supply Titiler with COG endpoints, because the Django dev server does not serve HTTP range requests (more on this [here](https://code.djangoproject.com/ticket/22479) and [here](https://github.com/python/cpython/issues/86809)). The easiest workaround is to use node's [http-server](https://www.npmjs.com/package/http-server).

From within the repository root (alongside the `uploaded` directory) run:

```bash
npx http-server .
```

All COGs will now be accessible at `http://localhost:8080/uploaded/`.

---

Make sure you have `MEDIA_HOST=http://localhost:8080` in `.env`. `MEDIA_HOST` is a prefix that will be prepended to any uploaded media paths that are passed to TiTiler.

In production, you will already be using a webserver for static files so you will not need to use `http-server`. In this case, remove `MEDIA_HOST` from `.env` or set it to `''`.

## Running Tests

All tests are stored in ohmg/tests. Make sure you have installed dev requirements, then run:

```bash
python manage.py test
```

To skip the tests that make external calls to the LOC API, use the following command. Keep in mind that coverage numbers will be lower when you skip tests.

```bash
python manage.py test --exclude-tag=loc
```
