#!/bin/sh

# Docker script to launch RabbitMQ instance
# Edit this file to configure some properties of the
# GeoLinkeddata RabbitMQ instance

# Default configuration

GEO_RABBIT_MEM=512M
GEO_RABBIT_USER=rabbitmq
GEO_RABBIT_PWD=password
GEO_RABBIT_PORT=5672

# Launch docker container

docker run -d --name geolinkeddata.rabbitmq \
    --restart always \
    -p $GEO_RABBIT_PORT:5672 \
    -e RABBITMQ_DEFAULT_USER=$GEO_RABBIT_USER \
    -e RABBITMQ_DEFAULT_PASS=$GEO_RABBIT_PWD \
    rabbitmq:alpine
