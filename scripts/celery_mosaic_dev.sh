#! /usr/bin/bash

uv run celery -A ohmg.conf.celery:app worker \
	-Q mosaic \
	--without-gossip \
	--without-mingle \
	-Ofair -B -E \
	--statedb=worker.state \
	-s celerybeat-schedule \
	--loglevel=DEBUG \
	--concurrency=1 \
	-n worker2@%h
