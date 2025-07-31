#! /usr/bin/bash

ENV_FILE=$(dirname "${BASH_SOURCE[0]}")/../.env

set -a
source $ENV_FILE
set +a

read -p "This will drop the database "$DATABASE_NAME" if it exists. Continue? y/N " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    sudo -u postgres psql -c "CREATE USER "$DATABASE_USER" WITH ENCRYPTED PASSWORD '$DATABASE_PASSWORD'"
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS "$DATABASE_NAME" WITH (FORCE);"
    sudo -u postgres psql -c "CREATE DATABASE "$DATABASE_NAME" WITH OWNER "$DATABASE_USER";"
    sudo -u postgres psql -d $DATABASE_NAME -c "CREATE EXTENSION PostGIS;"

    python manage.py migrate

    python manage.py loaddata tests/data/fixtures/auth/admin-user.json
    python manage.py loaddata default-region-categories
    python manage.py loaddata default-layerset-categories
    python manage.py loaddata default-navbar
fi
