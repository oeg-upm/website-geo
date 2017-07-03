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

# Get Debug flag
if [[ -z "${OEG_DEBUG_MODE}" ]]; then
    BDV=0
else
    BDV="${OEG_DEBUG_MODE}"
fi

# Get Geo Resources folder path
if [[ -z "${OEG_RESOURCES_FOLDER}" ]]; then
    ORFD="/opt/geo-resources/"
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

# Run docker container
docker run -d --restart=always -v $ORFD:/opt/geo-resources/ --link geolinkeddata.redis:redishost --link geolinkeddata.rabbitmq:rabbithost -e OEG_DEBUG_MODE=$BDV --name geolinkeddata.worker geolinkeddata/worker

# Came back to directory
cd $cwd
