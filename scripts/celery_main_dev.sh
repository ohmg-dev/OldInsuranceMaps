#! /usr/bin/bash

uv run celery -A ohmg.conf.celery:app worker \
	-Q main,background \
	--without-gossip \
	--without-mingle \
	-Ofair -B -E \
	--statedb=worker.state \
	-s celerybeat-schedule \
	--loglevel=DEBUG \
	--concurrency=10 \
	-n worker1@%h
