#! /usr/bin/bash

ENV_FILE=$(dirname "${BASH_SOURCE[0]}")/../.env

set -a
source $ENV_FILE
set +a

read -p "This will drop the database "$DATABASE_NAME" if it exists. Continue? Y/n " -n 1 -r
echo
if ! [[ $REPLY =~ ^[Nn]$ ]]
then
    ## create postgis extension in the default db so it is available later when tests are run.
    ## this makes it possible to run tests without a db user that is a superuser
    psql -U postgres -h $DATABASE_HOST -d "template1" -c "CREATE EXTENSION IF NOT EXISTS PostGIS;"
    psql -U postgres -h $DATABASE_HOST -c "CREATE USER "$DATABASE_USER" WITH ENCRYPTED PASSWORD '$DATABASE_PASSWORD'"
    psql -U postgres -h $DATABASE_HOST -c "ALTER USER "$DATABASE_USER" CREATEDB";
    psql -U postgres -h $DATABASE_HOST -c "DROP DATABASE IF EXISTS "$DATABASE_NAME" WITH (FORCE);"
    psql -U postgres -h $DATABASE_HOST -c "CREATE DATABASE "$DATABASE_NAME" WITH OWNER "$DATABASE_USER";"

    python manage.py migrate

    python manage.py loaddata tests/data/fixtures/auth/admin-user.json
    python manage.py loaddata default-region-categories
    python manage.py loaddata default-layerset-categories
    python manage.py loaddata default-navbar
fi
