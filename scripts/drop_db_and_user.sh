#! /usr/bin/bash

ENV_FILE=$(dirname "${BASH_SOURCE[0]}")/../.env

set -a
source $ENV_FILE
set +a

psql -U postgres -c "DROP DATABASE "$DATABASE_NAME";"
psql -U postgres -c "DROP USER "$DATABASE_USER";"
