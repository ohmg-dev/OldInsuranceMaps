set -a
. ./.env
set +a

celery -A loc_insurancemaps.celeryapp:app worker --without-gossip --without-mingle -Ofair -B -E --statedb=worker.state -s celerybeat-schedule --loglevel=DEBUG --concurrency=10 -n worker1@%h
