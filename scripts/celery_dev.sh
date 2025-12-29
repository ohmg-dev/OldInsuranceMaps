#! /usr/bin/bash

celery -A ohmg.conf.celery:app worker --without-gossip --without-mingle -Ofair -B -E --statedb=worker.state -s celerybeat-schedule --loglevel=DEBUG --concurrency=10 -n worker1@%h
