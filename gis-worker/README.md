## Geographic Information System Worker Image

This Docker Image includes:

 * [GeoKettle 2.5](../geokettle-docker)
 * [GDAL 2.2.1](http://trac.osgeo.org/gdal/wiki/DownloadingGdalBinaries)
 * [GDAL Python 2.2.1](http://gdal.org/python/)
 * [Google LIBKML](https://github.com/google/libkml)

Build the Docker Image

```bash
docker build -t geolinkeddata/worker .
```

Run container

1. First, you need to run a Redis instance

```bash
docker run -d --name geolinkeddata.redis redis
```

2. Second, you need to run a specific [RabbitMQ](../rabbitmq-docker) instance

```bash
cd ../rabbitmq-docker && ./launch.sh
```

3. Execute docker script

```bash
cd gis_worker_run && ./docker.sh
```

---

GeoLinkeddata © Copyright 2017.

Alejandro F. Carrera

