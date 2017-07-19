#!/bin/sh

# Docker script to launch RabbitMQ instance
# Edit this file to configure some properties of the
# GeoLinkeddata RabbitMQ instance

# Configuration
GEO_RABBIT_MEM=512M
GEO_RABBIT_USER=rabbitmq
GEO_RABBIT_PWD=password
GEO_RABBIT_PORT=5672
GEO_RABBIT_ADMIN_PORT=15672
GEO_RABBIT_ADMIN=0

# Stop previous RabbitMQ container
./stop.sh

# Build image if it is necessary
docker image inspect oegupm/geolinkeddata-rabbitmq >/dev/null 2>&1 && ibs=1 || ibs=0
if [ "$ibs" -eq "0" ]; then
    docker build -t oegupm/geolinkeddata-rabbitmq .
fi

# Launch docker container
docker run -d --name geolinkeddata.rabbitmq \
    --restart always \
    -p $GEO_RABBIT_PORT:5672 \
    -p $GEO_RABBIT_ADMIN_PORT:15672 \
    -e RABBITMQ_DEFAULT_USER=$GEO_RABBIT_USER \
    -e RABBITMQ_DEFAULT_PASS=$GEO_RABBIT_PWD \
    -e RABBITMQ_ENABLE_MANAGEMENT_PLUGIN=$GEO_RABBIT_ADMIN \
    oegupm/geolinkeddata-rabbitmq
