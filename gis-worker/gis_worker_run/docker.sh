#!/bin/bash

# Docker script to launch GIS Worker instance
# Edit this file to configure some properties of the
# GIS Worker instance

# Configuration
GEO_WORKER_RESOURCES=

# Stop and Remove container
docker stop geolinkeddata.worker >/dev/null 2>&1
docker rm geolinkeddata.worker >/dev/null 2>&1

# Save directory
cwd=$(pwd)
cd "$cwd/.."

# Suppress Warnings
export PYTHONWARNINGS="ignore"

# Remove all python temp files
rm -rf *.egg-info

# Detect if RabbitMQ is running
rabbit_cont=$(docker ps -aqf "name=geolinkeddata.rabbitmq")

# Get length of active containers
rabbit_ncont=${#rabbit_cont[@]}

# Detect if active containers is 0
if [ "$rabbit_ncont" -eq "1" ]
then
    if [ "${rabbit_cont[0]}" == "" ]
    then
        echo "[ERROR] No active RabbitMQ containers were found."
        exit 1
    fi
fi

# Detect if Redis is running
redis_cont=$(docker ps -aqf "name=geolinkeddata.redis")

# Get length of active containers
redis_ncont=${#redis_cont[@]}

# Detect if active containers is 0
if [ "$redis_ncont" -eq "1" ]
then
    if [ "${redis_cont[0]}" == "" ]
    then
        echo "[ERROR] No active Redis containers were found."
        exit 1
    fi
fi

# Build image if it is necessary
docker inspect oegupm/geolinkeddata-worker >/dev/null 2>&1 && ibs=1 || ibs=0
if [ "$ibs" -eq "0" ]; then
    docker build -t oegupm/geolinkeddata-worker .
fi

# Launch docker container
if [[ -z "$GEO_WORKER_RESOURCES" && "$GEO_WORKER_RESOURCES" = '' ]]
then
    docker run -d --name geolinkeddata.worker \
        --restart=always \
        -e OEG_DEBUG_MODE=0 \
        --link geolinkeddata.redis:redishost \
        --link geolinkeddata.rabbitmq:rabbithost \
        oegupm/geolinkeddata-worker
else
    docker run -d --name geolinkeddata.worker \
        --restart=always \
        -v $GEO_WORKER_RESOURCES:/opt/resources \
        -e OEG_DEBUG_MODE=0 \
        --link geolinkeddata.redis:redishost \
        --link geolinkeddata.rabbitmq:rabbithost \
        oegupm/geolinkeddata-worker
fi

# Came back to directory
cd "$cwd"
