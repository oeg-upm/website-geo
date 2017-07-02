#!/bin/bash

# Stop and Remove Docker Container
docker stop geolinkeddata.worker >/dev/null 2>&1 && cbs=1 || cbs=0
if [ "$cbs" -eq "1" ]; then
    docker rm geolinkeddata.worker >/dev/null 2>&1
fi

# Suppress Warnings
export PYTHONWARNINGS="ignore"

# Save directory
cwd=$(pwd)
cd ..

# Remove all python temp files
rm -rf *.egg-info

# Rebuild Container Image
docker image inspect geolinkeddata/worker >/dev/null 2>&1 && ibs=1 || ibs=0
if [ "$ibs" -eq "1" ]; then
    docker rmi geolinkeddata/worker >/dev/null 2>&1
fi
docker build -t geolinkeddata/worker .

# Get Debug flag
if [[ -z "${OEG_DEBUG_MODE}" ]]; then
    BDV=0
else
    BDV="${OEG_DEBUG_MODE}"
fi

# Run docker container
docker run -d --restart=always -e OEG_DEBUG_MODE=$BDV -v $(pwd):/opt/worker --name geolinkeddata.worker geolinkeddata/worker

# Came back to directory
cd $cwd
