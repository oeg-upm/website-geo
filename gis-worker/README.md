## Geographic Information System Worker Image

This Docker Image includes:

 * [GeoKettle Docker Image](https://github.com/oeg-upm/docker-geokettle)
 * [GDAL 2.2.1](http://trac.osgeo.org/gdal/wiki/DownloadingGdalBinaries)
 * [GDAL Python 2.2.1](http://gdal.org/python/)
 * [Google LIBKML](https://github.com/google/libkml)
 * GIS Worker for receiving tasks from RabbitMQ and save them on Redis

Configuration for the Docker Container (edit [docker.sh](./gis_worker_run/docker.sh) file)

|Name|Default value|
|----------|--------------|
|OEG_DEBUG_FLAG|1 ~ True|
|OEG_RESOURCES_FOLDER|/opt/geo-resources|

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

Ontology Engineering Group © Copyright 2017.

Licensed under [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/).

Maintainer, [Alejandro F. Carrera](https://www.github.com/alejandrofcarrera)
