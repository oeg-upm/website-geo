#!/bin/sh

# Docker script to stop Redis instance

# Get current active containers named geolinkeddata.redis
containers=$(docker ps -aqf "name=geolinkeddata.redis")

# Get length of active containers
ncontainers=${#containers[@]}

# Detect if active containers is 0
if [ "$ncontainers" -eq "1" ]
then
    if [ "${containers[0]}" == "" ]
    then
        echo "[WARN] No active Redis containers were found."
        exit 0
    fi
fi

# Iterate over containers
for container in $containers
do
    
    # Stop and Remove container
    docker stop $container >/dev/null 2>&1 && docker rm $container >/dev/null 2>&1

done
echo "[SUCCESS] Redis container was stopped."
