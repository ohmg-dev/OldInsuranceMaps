#! /usr/bin/bash

set -a
source ../.env
set +a

psql -U postgres -c "DROP DATABASE "$DATABASE_NAME";"
psql -U postgres -c "DROP USER "$DATABASE_USER";"
