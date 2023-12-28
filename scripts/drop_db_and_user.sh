#! /usr/bin/bash

psql -U postgres -c "DROP DATABASE oldinsurancemaps;"
psql -U postgres -c "DROP USER ohmg;"
