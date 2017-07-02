# Declare base image, because the plugins need to
# be compatible with Jena, Jena has Java 8 as base
# so we need Java 8, OpenJDK for this Docker Image.

FROM openjdk:8
MAINTAINER Alejandro F. Carrera

# Set environment to download and install GeoKettle
ENV GEOKETTLE_VERSION=2.5 \
    GEOKETTLE_SVN=http://dev.spatialytics.com/svn/geokettle-2.0/trunk \
    GEOKETTLE_PATH=/opt/geokettle \
    ANT_URL=http://ftp.cixug.es/apache/ant/binaries/ \
    ANT_PATH=apache-ant-1.10.1 \
    ANT_HOME=/usr/local/ant \
    PATH="${PATH}:/usr/local/ant/bin:/opt/geokettle"

# Download source code from repository
RUN cd /opt && \
    svn checkout $GEOKETTLE_SVN $GEOKETTLE_PATH > /dev/null 2>&1

# Download ant and install to compile source code
RUN curl $ANT_URL/$ANT_PATH-bin.zip -o $ANT_PATH.zip && \
    unzip $ANT_PATH.zip && \
    rm -rf $ANT_PATH.zip && \
    mv $ANT_PATH /usr/local/ant

# Compile Geokettle
RUN cd $GEOKETTLE_PATH && \
    ant > /dev/null 2>&1 && \
    mv $GEOKETTLE_PATH/distrib /tmp/geokettle && \
    rm -rf $GEOKETTLE_PATH && \
    mv /tmp/geokettle $GEOKETTLE_PATH

# Clean docker image
RUN apt-get clean -y && \
  apt-get autoclean -y && \
  apt-get autoremove -y && \
  rm -rf /usr/share/locale/* && \
  rm -rf /var/cache/debconf/*-old && \
  rm -rf /var/lib/apt/lists/* && \
  rm -rf /usr/share/doc/*

# Default terminal
WORKDIR $GEOKETTLE_PATH
ENTRYPOINT ["/bin/bash"]
