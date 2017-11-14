#!/bin/bash

# Configuration by default
export PYTHONWARNINGS="ignore"

# Kill previous processes
function pkill() {
    for X in `ps ax | grep $1 | grep -v grep | awk {'print $1'}`; do
        kill -9 $X;
    done
}
pkill celery

# Save directory
cwd=$(pwd)
cd "$cwd/.."

# Init GIS Worker
celery worker --app gis_worker.app -l info -Ofair &

# Came back to directory
cd "$cwd"
