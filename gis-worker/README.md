## Geographic Information System Worker Image

This Docker Image includes:

 * [GeoKettle Docker Image](https://github.com/oeg-upm/docker-geokettle)
 * [GDAL 2.2.1](http://trac.osgeo.org/gdal/wiki/DownloadingGdalBinaries)
 * [GDAL Python 2.2.1](http://gdal.org/python/)
 * [Google LIBKML](https://github.com/google/libkml)
 * GIS Worker for receiving tasks from RabbitMQ and save them on Redis

---

Configuration for the Docker Container (edit [docker.sh](./gis_worker_run/docker.sh) file)

|Name|Default value|
|----------|--------------|
|OEG_DEBUG_FLAG|1 ~ True|
|OEG_RESOURCES_FOLDER|/opt/resources|

Build the Docker Image

```bash
docker build -t oegupm/geolinkeddata-worker .
```

Run container

1. First, you need to configure | run a specific [Redis](../redis-docker) instance

```bash
cd ../redis-docker && ./launch.sh
```

2. Second, you need to configure | run a specific [RabbitMQ](../rabbitmq-docker) instance

```bash
cd ../rabbitmq-docker && ./launch.sh
```

3. Execute docker script

```bash
cd gis_worker_run && ./docker.sh
```

---

Options for Command Line Interface

```bash
python gis_worker.py -h
usage: gis_worker.py [-h] [ -t | -a | -f | -gj | -gt path ]

This software allows you execute jobs and transformations from asynchronous
way with Celery and messaging protocol as AMQP (RabbitMQ) plus Redis DB to
save the generated information or from CLI.

optional arguments:
  -h, --help            show this help message and exit
  -t path, --transform path
                        transform the geometries of the specific path to
                        Shapefile, also its SRS will be converted to WGS84.
  -a path, --analyse path
                        print information from Shapefile's geometries, this
                        option will raise an exception if geometry was not
                        transformed to Shapefile before.
  -f path, --fields path
                        print information from Shapefile's fields, this option
                        will raise an exception if geometry was not
                        transformed to Shapefile before.
  -gj path, --geo-job path
                        execute a GeoKettle job.
  -gt path, --geo-transform path
                        execute a GeoKettle transformation.
```

---

Ontology Engineering Group © Copyright 2017.

Licensed under [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/).

Maintainer, [Alejandro F. Carrera](https://www.github.com/alejandrofcarrera)
