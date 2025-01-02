#! /usr/bin/bash

ENV_FILE=$(dirname "${BASH_SOURCE[0]}")/../.env

set -a
source $ENV_FILE
set +a

psql -U postgres -c "CREATE USER "$DATABASE_USER" WITH ENCRYPTED PASSWORD '$DATABASE_PASSWORD'"
psql -U postgres -c "CREATE DATABASE "$DATABASE_NAME" WITH OWNER "$DATABASE_USER";"
psql -U postgres -d $DATABASE_NAME -c "CREATE EXTENSION PostGIS;"

python manage.py migrate

python manage.py loaddata default-layerset-categories
