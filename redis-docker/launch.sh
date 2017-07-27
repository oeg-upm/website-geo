#!/bin/sh

# Docker script to launch Redis instance
# Edit this file to configure some properties of the
# GeoLinkeddata Redis instance

# Configuration
GEO_REDIS_PORT=6379

# Stop previous Redis container
./stop.sh

# Build image if it is necessary
docker inspect oegupm/geolinkeddata-redis >/dev/null 2>&1 && ibs=1 || ibs=0
if [ "$ibs" -eq "0" ]; then
    docker build -t oegupm/geolinkeddata-redis .
fi

# Launch docker container
docker run -d --name geolinkeddata.redis \
    --restart always \
    -v $(pwd)/redis.conf:/usr/local/etc/redis/redis.conf \
    -p $GEO_REDIS_PORT:6379 \
    oegupm/geolinkeddata-redis
