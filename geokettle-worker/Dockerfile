# Declare base image, because this software needs
# the latest geokettle docker built image with all
# the necessary to run properly.

FROM geokettle:2.5
MAINTAINER Alejandro F. Carrera

# Set environment to download GDAL
ENV GDAL_VERSION=2.2.1 \
    GDAL_URL=http://download.osgeo.org/gdal

# Install dependencies
RUN apt-get update && apt-get upgrade -qq -y && apt-get install -qq -y \
    build-essential make curl ca-certificates libcurl4-gnutls-dev \
    shapelib libproj-dev libproj0 proj-data libgeos-3.4.2 libgeos-c1 libgeos-dev \
    postgresql-client-common libpq-dev

# Download source code from website
RUN curl $GDAL_URL/$GDAL_VERSION/gdal-$GDAL_VERSION.tar.gz | tar zxv -C /tmp > /dev/null 2>&1

# Configure installation
RUN cd /tmp/gdal-$GDAL_VERSION && ./configure \
    --prefix=/usr \
    --with-threads \
    --with-hide-internal-symbols=yes \
    --with-rename-internal-libtiff-symbols=yes \
    --with-rename-internal-libgeotiff-symbols=yes \
    --with-libtiff=internal \
    --with-geotiff=internal \
    --with-geos \
    --with-pg \
    --with-curl \
    --with-static-proj4=yes \
    --with-ecw=no \
    --with-grass=no \
    --with-hdf5=no \
    --with-java=no \
    --with-mrsid=no \
    --with-perl=no \
    --with-python=no \
    --with-webp=no \
    --with-xerces=no > /dev/null 2>&1

# Install GDAL
RUN cd /tmp/gdal-$GDAL_VERSION && make && make install

# Install pip
RUN apt-get install -qq -y python-setuptools python-dev && \
	easy_install pip

# Clean docker image
RUN apt-get remove --purge libcurl4-gnutls-dev libproj-dev \
	libgeos-dev libpq-dev -y && \
  	apt-get clean -y && \
  	apt-get autoclean -y && \
  	apt-get autoremove -y && \
  	rm -rf /var/lib/apt/lists/* /tmp/* && \
  	rm -rf /usr/share/locale/* && \
  	rm -rf /var/cache/debconf/*-old && \
  	rm -rf /var/lib/apt/lists/* && \
  	rm -rf /usr/share/doc/*

# Create directories & virtual env
RUN mkdir /opt/worker
ENV HOME /opt/worker
VOLUME ["/opt/worker"]
WORKDIR /opt/worker

# Configure init
ADD ./geo_worker_docker/start /opt/start

# Run init when docker run
CMD ["/opt/start"]
