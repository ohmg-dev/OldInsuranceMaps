#! /usr/bin/bash

docker run --name titiler \
  -p 8008:8000 \
  -e PORT=8000 \
  -e MOSAIC_SCRIPT_ZOOM=False \
  -e WORKERS_PER_CORE=1 \
  --rm \
  -it \
  ghcr.io/mradamcox/titiler:0.11.6-ohmg
