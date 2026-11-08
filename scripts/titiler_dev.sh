#! /usr/bin/bash

# -p 8008:8008 will expose it at the local host port,
# but it seems better to use --network=host
# instead because then it can access the local network
# only use --network=host in local dev.

docker run --name titiler \
  --network=host \
  -e PORT=8008 \
  -e MOSAIC_STRICT_ZOOM=False \
  -e WORKERS_PER_CORE=1 \
  --rm \
  -it \
  ghcr.io/developmentseed/titiler:2.4.0
