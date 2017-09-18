#!/bin/sh

# Docker script to launch Redis instance
# Edit this file to configure some properties of the
# GeoLinkeddata Redis instance

# Configuration
GEO_REDIS_PORT=6379

# Stop previous Redis container
./stop.sh

# Download new Docker image
docker pull redis:alpine

# Build image
docker build -t oegupm/geolinkeddata-redis .

# Launch docker container
docker run -d --name geolinkeddata.redis \
    --restart always \
    -v $(pwd)/redis.conf:/usr/local/etc/redis/redis.conf \
    -p $GEO_REDIS_PORT:6379 \
    oegupm/geolinkeddata-redis
