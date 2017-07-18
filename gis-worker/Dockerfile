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
    GDAL_PATH=/opt/gdal-2.2.1 \
    LIBKML_URL=https://github.com/google/libkml/trunk \
    LIBKML_PATH=/opt/libkml \
    HOME=/opt/worker

# Install machine dependencies
RUN mkdir -p /opt/worker && \
    apt-get update && \
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
        postgresql-client-common libpq-dev python-setuptools python-dev && \
    apt-get clean -y && \
    apt-get autoclean -y && \
    apt-get autoremove -y && \
    easy_install pip && \
    rm -rf /var/lib/apt/lists/* /tmp/* && \
    rm -rf /usr/share/locale/* && \
    rm -rf /var/cache/debconf/*-old && \
    rm -rf /var/lib/apt/lists/*

# Copy worker files
COPY . $HOME

# Install GDAL plus KML library
RUN cd /opt && \
    svn co $LIBKML_URL $LIBKML_PATH && \
    cd $LIBKML_PATH && \
    ./autogen.sh && \
    ./configure && \
    make && \
    make install && \
    cd /opt/ && \
    curl $GDAL_URL/$GDAL_VERSION/gdal-$GDAL_VERSION.tar.gz -o gdal-$GDAL_VERSION.tar.gz && \
    tar -xvzf gdal-$GDAL_VERSION.tar.gz && \
    cd $GDAL_PATH && \
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
    cd /opt && \
    pip download GDAL==$GDAL_VERSION && \
    tar -xvzf GDAL-$GDAL_VERSION.tar.gz && \
    cd /opt/GDAL-$GDAL_VERSION && \
    python setup.py build_ext --include-dirs=/usr/include/gdal/ && \
    python setup.py install && \
    cd $HOME && \
    python setup.py install && \
    rm -rf /usr/share/locale/* && \
    rm -rf /usr/share/doc/* && \
    rm -rf /opt/gdal* && \
    rm -rf /opt/GDAL* && \
    rm -rf $LIBKML_PATH && \
    rm -rf /tmp/* && \
    chown -R geo:geo /opt

# Change working directory
WORKDIR $HOME

# Use non-root user
USER geo

# Run celery when docker run
ENTRYPOINT ["celery", "worker", "-A", "gis_worker.app", "-l", "info", "-Ofair"]
