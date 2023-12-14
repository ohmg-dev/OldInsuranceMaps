# Online Historical Map Georeferencer (OHMG)

OHMG is a web application that facilitates public participation in the process of georeferencing and mosaicking historical maps. This is a standalone project that requires an external instance of [Titiler](https://developmentseed.org/titiler) to serve the mosaicked layers. See Dependencies below for more about the tech stack.

At present, the system is structured around the Sanborn Map Collection at the Library of Congress ([loc.gov/collections/sanborn-maps](https://loc.gov/collections/sanborn-maps)). More generic ingestion methods are in the works.

- **Implementation:** [oldinsurancemaps.net](https://oldinsurancemaps.net)
- **Documentation:** [ohmg.dev](https://ohmg.dev)

---

Please don't hesitate to [open a ticket](https://github.com/mradamcox/loc-insurancemaps/issues/new/choose) if you have trouble with the site, find a bug, or have suggestions otherwise.

---

## Site Overview

You can browse content in the platform by map, by place name, or by item name.

![Homepage](./ohmg/frontend/static/img/browse.jpg)

Each volume's summary page has an interactive Map Overview showing all of the sheets that have been georeferenced so far.

![Volume Summary - Map Overview](./ohmg/frontend/static/img/vsummary-031922.jpg)

Each volume's summary page also lists the progress and georeferencing stage of each sheet.

![Volume Summary - Georeferencing Overview](./ohmg/frontend/static/img/vsummary2-031922.jpg)

Finally, each resource itself has it's own page, showing a complete lineage of the work that has been performed on it by various users.

![Alexandria, La, 1900, p1 [2]](./ohmg/frontend/static/img/example-resource-alex-1900.jpg)

## Process Overview

The georeferencing process generally consists of three operations, each with their own browser interface.

Document preparation (sometimes they must be split into multiple pieces):

![Splitting interface](./ohmg/frontend/static/img/example-split-alex-1900.jpg)

Ground control point creation (these are used to warp the document into a geotiff):

![Georeferencing interface](./ohmg/frontend/static/img/example-georef-alex-1900.jpg)

And a "multimask" that allows a volume's sheets to be trimmed *en masse*, a quick way to create a seamless mosaic from overlapping sheets:

![Trimming interface](./ohmg/frontend/static/img/example-multimask-alex-1900.jpg)

Learn much more about each step [in the docs](https://ohmg.dev/docs/category/making-the-mosaics-1).

All user input is tracked through registered accounts, which allows for a comprehensive understanding of user engagement and participation, as well as a complete database of all input georeferencing information, like ground control points, masks, etc.

## Software Details

This is a Django project, with a frontend built (mostly) with [Svelte](https://svelte.dev), using [OpenLayers](https://openlayers.org) for all map interfaces. OpenStreetMap and Mapbox are the basemap sources.

### Third-party Django Apps

- [Django Ninja](https://django-ninja.rest-framework.com) - API
- [Django Newsletter](https://github.com/jazzband/django-newsletter) - Adds a newsletter to the site

### External Dependencies

- Postgres/PostGIS
- Celery + RabbitMQ
- GDAL >= 3.5
- [TiTiler](https://developmentseed.org/titiler)

## Installation

(section still in progress)

### Create database

```bash
psql -U postgres -c "CREATE USER ohmg WITH ENCRYPTED PASSWORD '$DB_PASSWORD'"
psql -U postgres -c "CREATE DATABASE oldinsurancemaps WITH OWNER ohmg;"
psql -U postgres -d oldinsurancemaps -c "CREATE EXTENSION PostGIS;"
```

See also scripts/create_database.sh.

### Install Django project

Make virtual env

```bash
python3 -m venv env
source env/bin/activate
```

Install Python deps

```bash
git clone https://github.com/mradamcox/ohmg && cd ohmg
pip install -r requirements.txt
```

Set environment variables

```bash
cp .env.original .env
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

The frontend uses a series of independently built svelte components.

```bash
cd ohmg/frontend/svelte
pnpm install
pnpm run dev
```
