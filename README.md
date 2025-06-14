# Online Historical Map Georeferencer (OHMG)

OHMG is a web application that facilitates public participation in the process of georeferencing and mosaicking historical maps. Currently, a single implementation of this software exists, at OldInsuranceMaps.net, a platform based around the Sanborn Map Collection at the Library of Congress ([loc.gov/collections/sanborn-maps](https://loc.gov/collections/sanborn-maps)). More generic deployments are in the works.

- **Home page:** [ohmg.dev](https://ohmg.dev)
- **Implementation:** [oldinsurancemaps.net](https://oldinsurancemaps.net)
- **Documentation:** [about.oldinsurancemaps.net](https://about.oldinsurancemaps.net)

---

Please don't hesitate to [open a ticket](https://github.com/ohmg-dev/OldInsuranceMaps/issues/new/choose) if you have trouble with the site, find a bug, or have suggestions otherwise.

---

## Software Details

OHMG uses the [Django](https://www.djangoproject.com/) web framework for URL routing, auth, and the ORM, and [Django Ninja](https://django-ninja.dev) to create an API. A newsletter is implemented with [Django Newsletter](https://github.com/jazzband/django-newsletter).

The frontend is built (mostly) with [Svelte](https://svelte.dev), using [OpenLayers](https://openlayers.org) for all map interfaces. [OpenStreetMap](https://openstreetmap.org) and [Mapbox](https://www.mapbox.com) are the basemap sources.

Other components include:

- [Postgres + PostGIS](https://postgis.net/)
  - Database
- [GDAL (3.5+ release)](https://gdal.org/en/stable/)
  - A dependency of PostGIS, and also used directly for all warping/mosaicking operations.
- [Celery + RabbitMQ](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/rabbitmq.html)
  - Background task management (a handful of loading/splitting/warping processes run in the background)
  - Presumably, Redis could be used for the broker instead of RabbitMQ.
- [TiTiler](https://developmentseed.org/titiler)
  - Tileserver for georeferencing COGs (Cloud Optimized GeoTIFFs)

## Development Installation

Running the application requires a number of components to be installed and configured properly. The following commands assume a Debian-based Linux distribution.

### Install system dependencies

You will need the following packages (at least... I still need to figure out the exact list of these dependencies):

```bash
sudo apt install build-essential gdal-bin python3.8-dev libgdal-dev libgeos-dev
```

### Get the source code and set up Python environment

Clone the repo and enter the local directory

```bash
git clone https://github.com/ohmg-dev/OldInsuranceMaps && cd OldInsuranceMaps
```

Make virtual env & upgrade pip

```bash
python3 -m venv env
source env/bin/activate
python -m pip install pip --upgrade
```

Install GDAL Python bindings. These must match exactly the version of GDAL you have on your system, so use this command:

```bash
pip install gdal=="`gdal-config --version`.*"
```

Install the `ohmg` package into your virtual environment

```bash
pip install -e .[dev]
```

Install pre-commit hook (if you will be writing code)

```bash
pre-commit install
```

Use the `.env.example` to create your `.env` file

```bash
cp .env.example .env
```

See [environment variables](#environment-variables) for more information.

### Initialize database

In your running Postgres instance, create a database like this

```bash
psql -U postgres -c "CREATE USER ohmg WITH ENCRYPTED PASSWORD '$DB_PASSWORD'"
psql -U postgres -c "CREATE DATABASE oldinsurancemaps WITH OWNER ohmg;"
psql -U postgres -d oldinsurancemaps -c "CREATE EXTENSION PostGIS;"
```

Alternatively, if you have set all of the  `DATABASE_*` variables in `.env`, you can use the included script to complete the database setup:

```bash
source ./scripts/setup_database.sh
```

Run migrations and create admin user to access the Django admin panel (and login to the site once it's running)

```bash
python manage.py migrate
python manage.py createsuperuser
```

Load all the place objects to create geography scaffolding (this will take a minute or two)

```bash
python manage.py place import-all
```

Download plugin assets

```bash
python manage.py configure get-plugins
```

Load test data into database (optional)

```bash
source ./scripts/load_dev_data.sh
```

### Build frontend

The frontend uses a suite of independently built svelte components. During development use the following command to auto-build these components and reload your browser.

```bash
cd ohmg/frontend/svelte
pnpm install
pnpm run dev
```

<!--
In production, use the `build` command instead, and then Django's `collectstatic` to consolidate all static assets.

```bash
cd ohmg/frontend/svelte
pnpm install
pnpm run build 
cd ../../..
python manage.py collectstatic --noinput
```

See

```bash
source ./scripts/deploy_frontend.sh
```

for more context.
-->

### Run Django dev server

You can now run

```bash
python manage.py runserver
```

and view the site at `http://localhost:8000`.

However, a few more pieces need to be set up independently before the app will be fully functional. Complete the following sections and then restart the dev server so that any new `.env` values will be properly acquired.

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

Make sure you have `TITILER_HOST=http://localhost:8008` in `.env` (see [environment variables](#environment-variables)).

### Static file server

During development, a separate HTTP server must be used to supply TiTiler with COG endpoints, because the Django dev server does not serve HTTP range requests (more on this [here](https://code.djangoproject.com/ticket/22479) and [here](https://github.com/python/cpython/issues/86809)). The easiest workaround is to use node's [http-server](https://www.npmjs.com/package/http-server).

From within the repository root (alongside the `uploaded` directory) run:

```bash
npx http-server .
```

All COGs will now be accessible at `http://localhost:8080/uploaded/`.

---

Make sure you have `MEDIA_HOST=http://localhost:8080` in `.env`. `MEDIA_HOST` is a prefix that will be prepended to any uploaded media paths that are passed to TiTiler.

In production, you will already be using a webserver for static files so you will not need to use `http-server`. In this case, remove `MEDIA_HOST` from `.env` or set it to `''`.

## Running tests

All tests are stored in `ohmg/tests`. Make sure you have installed dev requirements, then run:

```bash
python manage.py test
```

To skip the tests that make external calls to the LOC API, use the following command. Keep in mind that coverage numbers will be lower when you skip tests.

```bash
python manage.py test --exclude-tag=loc
```

## Environment variables

_section in progress_

<!--
These are the essential environment variables that must be present in your `.env` file to make the application work. In some cases, certain variables are only required during development, others only in production. Sensible defaults are provided to get things up and running as quickly as possible.

|name|default|description|used in|
|---|---|---|---|
|`DATABASE_NAME`|`oldinsurancemaps`|name of the postgres database|dev+prod|
|`DATABASE_USER`|`ohmg`|postgres user with write access to database|dev+prod|
|`DATABASE_PASSWORD`|`ohmg_password`|password for user|dev+prod|
|`DATABASE_HOST`|`localhost`|postgres host|dev+prod|
|`DATABASE_PORT`|`5432`|postgres port|dev+prod|
|`TITILER_HOST`|`http://localhost:8008`|address for running TiTiler instance|dev+prod|

-->