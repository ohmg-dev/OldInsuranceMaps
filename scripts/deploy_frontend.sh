#! /usr/bin/bash

# activating the virtual environment should set $VIRTUAL_ENV
# to /path/to/env, use this to find the python executable
PYTHON=$VIRTUAL_ENV/bin/python
# full path to this script. anticipate app paths from here
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_ROOT=$SCRIPT_DIR/..

echo "building frontend"
CURRENT_DIR=$PWD
cd $PROJECT_ROOT/ohmg/frontend/svelte_components
pnpm install
rm -rf ./public/build
pnpm run build
cd $CURRENT_DIR

echo "getting static plugin assets"
$VIRTUAL_ENV/bin/python $PROJECT_ROOT/manage.py get-plugins

echo "running collectstatic"
$VIRTUAL_ENV/bin/python $PROJECT_ROOT/manage.py collectstatic --noinput

echo "update build number"
$VIRTUAL_ENV/bin/python $PROJECT_ROOT/manage.py update_build
