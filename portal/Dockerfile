#
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
#  Ontology Engineering Group
#        http://www.oeg-upm.net/
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
#  Copyright (C) 2017 Ontology Engineering Group.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
#  Geographic Information System Worker is licensed under a
#  Creative Commons Attribution-NC 4.0 International License.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
#

# Declare base image, because this software needs
# the latest python-alpine docker built image with all
# the necessary to run properly.
FROM python:2.7-alpine
MAINTAINER Alejandro F. Carrera

# Create environment for bastet
ENV LIBRARY_PATH=/lib:/usr/lib

# Install dependencies
RUN echo "http://dl-4.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories && \
    mkdir -p /tmp/build && \
    mkdir -p /tmp/dependencies && \
    apk --update add --no-cache \
        --virtual=/tmp/dependencies \
        build-base python-dev libstdc++ musl-dev g++ && \
    ln -s /usr/include/locale.h /usr/include/xlocale.h && \
    pip install --upgrade pip && \
    pip install --no-cache-dir --disable-pip-version-check Flask && \
    rm -rf /root/.cache && \
    rm -rf /var/cache/apk/* && \
    rm -rf /tmp/dependencies

# Create directory for worker
ENV HOME /opt/portal
WORKDIR /opt/portal
COPY requirements.txt requirements.txt

# Install dependencies
RUN pip install -r requirements.txt

# Copy files of project
COPY . $HOME

# Expose ports
EXPOSE 8000

# Run business when docker run
ENTRYPOINT ["gunicorn", "portal:app", "-w", "2", "-t", "120", "-k", "gevent", "-b", "0.0.0.0:8000"]
