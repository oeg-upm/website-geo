#!/bin/bash

# Stop previous worker container
docker stop geolinkeddata.worker >/dev/null 2>&1 && cbs=1 || cbs=0
if [ "$cbs" -eq "1" ]; then
    docker rm geolinkeddata.worker >/dev/null 2>&1
fi

# Save directory
cwd=$(pwd)
cd ..

# Suppress Warnings
export PYTHONWARNINGS="ignore"

# Remove all python temp files
rm -rf *.egg-info

# Get Geo Resources folder path
if [[ -z "${OEG_RESOURCES_FOLDER}" ]]; then
    ORFD="/opt/geo-resources"
else
    ORFD="${OEG_RESOURCES_FOLDER}"
fi

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
docker run -d --name geolinkeddata.worker \
    --restart=always \
    -v $ORFD:/opt/resources \
    -e OEG_DEBUG_MODE=0 \
    --link geolinkeddata.redis:redishost \
    --link geolinkeddata.rabbitmq:rabbithost \
    oegupm/geolinkeddata-worker

# Came back to directory
cd $cwd
