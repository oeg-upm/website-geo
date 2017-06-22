#!/bin/bash

function pkill() {
    for X in `ps ax | grep $1 | grep -v grep | awk {'print $1'}`; do
        kill -9 $X;
    done
}

pkill celery

# Suppress Warnings
export PYTHONWARNINGS="ignore"

# Save directory
cwd=$(pwd)
cd ..

# Init GeoLinkeddata Worker
celery worker --app geo_worker.app --loglevel=info &

# Came back to directory
cd $cwd
