#! /usr/bin/bash

ENV_FILE=$(dirname "${BASH_SOURCE[0]}")/../.env

set -a
source $ENV_FILE
set +a

uv run manage.py loaddata ohmg/core/fixtures/sanborn-region-categories.json
uv run manage.py loaddata ohmg/core/fixtures/sanborn-layerset-categories.json

uv run manage.py loaddata tests/data/fixtures/places/new-iberia-la-and-parents.json
uv run manage.py loaddata tests/data/fixtures/core/new-iberia-1885-map.json
uv run manage.py loaddata tests/data/fixtures/core/new-iberia-1885-docs.json

uv run manage.py loaddata tests/data/fixtures/core/new-iberia-1885-main-content-layerset.json

mkdir -p ./uploaded/documents
mkdir -p ./uploaded/thumbnails

cp ./tests/data/files/source_images/new_iberia_la_1885_p1.jpg ./uploaded/documents/new_iberia_la_1885_p1.jpg
cp ./tests/data/files/source_images/new_iberia_la_1885_p2.jpg ./uploaded/documents/new_iberia_la_1885_p2.jpg
cp ./tests/data/files/source_images/new_iberia_la_1885_p3.jpg ./uploaded/documents/new_iberia_la_1885_p3.jpg

cp ./tests/data/files/thumbnails/new_iberia_la_1885_p1-doc-thumb.jpg ./uploaded/thumbnails/new_iberia_la_1885_p1-doc-thumb.jpg
cp ./tests/data/files/thumbnails/new_iberia_la_1885_p2-doc-thumb.jpg ./uploaded/thumbnails/new_iberia_la_1885_p2-doc-thumb.jpg
cp ./tests/data/files/thumbnails/new_iberia_la_1885_p3-doc-thumb.jpg ./uploaded/thumbnails/new_iberia_la_1885_p3-doc-thumb.jpg

# small hack to resave and trigger signals on the test Document objects.
uv run manage.py shell -c "from ohmg.core.models import Document; [i.save() for i in Document.objects.all()]"
