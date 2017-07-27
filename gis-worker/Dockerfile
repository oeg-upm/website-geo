# Declare base image, because this software needs
# the latest geokettle docker built image with all
# the necessary to run properly.

FROM oegupm/geokettle-x3geo
MAINTAINER Alejandro F. Carrera

# Use root user
USER root

# Set environment to download GDAL
ENV GDAL_VERSION=2.2.1 \
    GDAL_URL=http://download.osgeo.org/gdal \
    LIBKML_URL=https://github.com/google/libkml/trunk

# Install machine dependencies
RUN apt-get update && \
    apt-get upgrade -qq -y && \
    apt-get install -qq -y libtool build-essential cmake make curl \
        ca-certificates g++ autoconf bison flex doxygen libpq-dev \
        libpng12-dev libjpeg-dev libgif-dev liblzma-dev libgeos-dev \
        libcurl4-gnutls-dev libproj-dev libxml2-dev libexpat-dev \
        libxerces-c-dev libnetcdf-dev libpq-dev libpng12-dev \
        libjpeg-dev libgif-dev liblzma-dev libgeos-dev \
        libcurl4-gnutls-dev libproj-dev libxml2-dev libexpat-dev \
        libxerces-c-dev libnetcdf-dev libepsilon-dev liblcms2-2 \
        libproj0 proj-data libpcre3-dev libjasper-dev libarmadillo-dev \
        subversion libgeos-3.4.2 libgeos-c1 shapelib proj-data \
        postgresql-client-common libpq-dev && \
    cd /opt && \
    svn co $LIBKML_URL libkml && \
    cd libkml && \
    ./autogen.sh && \
    ./configure && \
    make && \
    make install && \
    curl $GDAL_URL/$GDAL_VERSION/gdal-$GDAL_VERSION.tar.gz | tar zxv -C /tmp > /dev/null 2>&1 && \
    cd /tmp/gdal-$GDAL_VERSION && \
    ./configure --prefix=/usr --with-threads \
        --with-hide-internal-symbols=yes \
        --with-rename-internal-libtiff-symbols=yes \
        --with-rename-internal-libgeotiff-symbols=yes \
        --with-spatialite --with-pg --with-epsilon --with-gta \
        --with-liblzma --with-webp --with-libkml --with-armadillo \
        --with-libtiff=internal --with-geotiff=internal --with-geos \
        --with-curl --with-static-proj4=yes && \
    make && \
    make install && \
    apt-get update && \
    apt-get upgrade -qq -y && \
    apt-get install -qq -y python-setuptools python-dev && \
    easy_install pip && \
    apt-get clean -y && \
    apt-get autoclean -y && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* /tmp/* && \
    rm -rf /usr/share/locale/* && \
    rm -rf /var/cache/debconf/*-old && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /usr/share/doc/* && \
    mkdir -p /opt/worker

# Install Python GDAL specific version
# for compatibility with last GDAL
# installation and python dependencies
RUN cd /opt && \
    pip download GDAL==$GDAL_VERSION && \
    tar -xvzf GDAL-$GDAL_VERSION.tar.gz > /dev/null 2>&1 && \
    cd /opt/GDAL-$GDAL_VERSION && \
    python setup.py build_ext --include-dirs=/usr/include/gdal/ > /dev/null 2>&1 && \
    python setup.py install && \
    rm -rf /opt/GDAL-$GDAL_VERSION.tar.gz && \
    rm -rf /opt/GDAL-$GDAL_VERSION && \
    rm -rf /opt/libkml && \
    rm -rf /tmp/*

# Create directory for worker
ENV HOME /opt/worker
WORKDIR /opt/worker
COPY . /opt/worker

# Install worker and fix permissions
RUN python setup.py install && \
    chown -R geo:geo /opt

# Use non-root user
USER geo

# Run celery when docker run
ENTRYPOINT ["celery", "worker", "-A", "gis_worker.app", "-l", "info", "-Ofair"]