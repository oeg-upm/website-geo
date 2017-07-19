# Declare base image, because this software needs
# the latest redis docker built image with all
# the necessary to run properly.

FROM redis:alpine
MAINTAINER Alejandro F. Carrera

COPY redis.conf /usr/local/etc/redis/redis.conf
CMD [ "redis-server", "/usr/local/etc/redis/redis.conf" ]
