#! /usr/bin/bash

set -a
source ../.env
set +a

psql -U postgres -c "CREATE USER "$DATABASE_USER" WITH ENCRYPTED PASSWORD '$DATABASE_PASSWORD'"
psql -U postgres -c "CREATE DATABASE "$DATABASE_NAME" WITH OWNER "$DATABASE_USER";"
psql -U postgres -d $DATABASE_NAME -c "CREATE EXTENSION PostGIS;"
