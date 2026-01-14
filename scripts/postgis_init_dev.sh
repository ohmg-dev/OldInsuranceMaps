#! /usr/bin/bash

docker create --name postgis15 \
	-p 5432:5432 \
	-e POSTGRES_PASSWORD=postgres \
	-e POSTGRES_HOST_AUTH_METHOD=trust \
	postgis/postgis:15-3.5-alpine
