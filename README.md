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
- [GDAL](https://gdal.org/en/stable/)
  - A dependency of PostGIS, and also used directly for all warping/mosaicking operations.
- [Celery + RabbitMQ](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/rabbitmq.html)
  - Background task management (a handful of loading/splitting/warping processes run in the background)
- [TiTiler](https://developmentseed.org/titiler)
  - Tileserver for COGs (Cloud Optimized GeoTIFFs)

## Installation

Running the application requires a number of components to be installed and configured properly. The following commands assume a Debian-based Linux distribution.

### Install system dependencies

You will need a few system packages.

```bash
sudo apt install build-essential gdal-bin python3-gdal libgeos-dev libgdal-dev
```

Extra dependencies helpful during development:

```bash
sudo apt install graphviz graphviz-dev pre-commit
```

> [!NOTE]
> 3.5 is the minimum GDAL version that the app requires, so the system gdal installation must be >= or higher than that, however, the version of the Python bindings must be <= to the system version. While pinning a specific Python version is easy, anticipating the exact system gdal across distros is trickier (Debian 13: 3.10.3, Debian 12: 3.6.2, Ubuntu 24: 3.8.4, [etc.](https://pkgs.org/download/gdal)). The solution here is to install whatever GDAL comes with the distro, and pin the Python bindings in `pyproject.toml` very low (between 3.5 and 3.6), to ensure maximum liklihood of a smooth installation.

### Get the source code

Clone the repo and enter the local directory

```bash
git clone https://github.com/ohmg-dev/OldInsuranceMaps && cd OldInsuranceMaps
```

### Install with `uv`

First, [install `uv`](https://docs.astral.sh/uv/getting-started/installation/), an all-in-one Python version and package manager.

With `uv` installed, run this command inside the cloned repo:

```bash
uv sync --extra dev
```

This will:

1. Install the proper version of Python
2. Create a new virtual environment in `.venv`
3. Install all Python dependencies into that environment.

Next, install pre-commit hook (if you will be writing code)

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

Run migrations and create admin user to access the Django admin panel (and login to the site once it's running)

```bash
python manage.py migrate
python manage.py createsuperuser
```

Load a few other fixtures with some default objects:

```bash
python manage.py loaddata default-region-categories
python manage.py loaddata default-layerset-categories
python manage.py loaddata default-navbar
```

Alternatively, if you have set all of the  `DATABASE_*` variables in `.env`, you can use the included script to perform all of the actions described above:

```bash
source ./scripts/setup_database.sh
```

The superuser created by this script is username: `admin`, password: `admin`.

Load test data into database (optional)

```bash
source ./scripts/load_dev_data.sh
```

### Build frontend

There are a few js and css plugins that must be downloaded to the local static directory:

```bash
python manage.py get-plugins
```

The frontend uses a suite of independently built svelte components. First install `pnpm`: https://pnpm.io/installation. Then:

```bash
cd ohmg/frontend/svelte_components
pnpm install
```

During development use the following command to auto-build the components and reload your browser.

```bash
pnpm run dev
```

In production, use the `build` command instead, and then Django's `collectstatic` to consolidate all static assets.

```bash
pnpm run build 
cd ../../..
python manage.py collectstatic --noinput
```

This bash script combines all steps into one:

```bash
source ./scripts/deploy_frontend.sh
```

### Run Django dev server

You can now activate the virtual environment and then run the django dev server:

```bash
source .venv/bin/activate
python manage.py runserver
```

and view the site at `http://localhost:8000`.

However, a few more pieces need to be set up independently before the app will be fully functional. Complete the following sections and then restart the dev server so that any new `.env` values will be properly acquired.

> [!NOTE]
> You can also skip the virtualenv activation and use uv to run management commands like this:
>
> ```bash
> uv run manage.py runserver
> ```

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
  ghcr.io/mradamcox/titiler:0.26.0-ohmg
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

Make sure you have `LOCAL_MEDIA_HOST=http://localhost:8080` in `.env`. `LOCAL_MEDIA_HOST` is a prefix that will be prepended to any uploaded media paths that are passed to TiTiler.

In production, you will already be using a webserver for static files so you will not need to use `http-server`. In this case, remove `LOCAL_MEDIA_HOST` from `.env` or set it to `''`.

## Running tests

All tests are stored in `ohmg/tests`. Make sure you have installed dev requirements, then run:

```bash
python manage.py test
```

To skip the tests that make external calls to the LOC API, use the following command. Keep in mind that coverage numbers will be lower when you skip tests.

```bash
python manage.py test --exclude-tag=loc
```

## Install the Place scaffolding

Load all the place objects to create geography scaffolding (this will take a minute or two)

```bash
python manage.py place import-all
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
