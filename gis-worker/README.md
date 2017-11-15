## Geographic Information System Worker Image

### Use of Docker Image that includes:

 * [GeoKettle Docker Image](https://github.com/oeg-upm/docker-geokettle)
 * [GDAL 2.2.2](http://trac.osgeo.org/gdal/wiki/DownloadingGdalBinaries)
 * [GDAL Python 2.2.2](http://gdal.org/python/)
 * [Google LIBKML](https://github.com/google/libkml)
 * GIS Worker for receiving tasks from RabbitMQ and save them on Redis

#### Configuration:

To set the configuration for ```GeoKettle```, please edit the ```xml``` key at [configuration](./gis_worker_helpers/configuration.json) file.

Also, you can set the shared volumes at Docker launch script (in this case, you do not need to set any environment key). The keys to set the shared volumes are ```GEO_WORKER_RESOURCES``` & ```GEO_WORKER_CFG``` at [docker.sh](./gis_worker_run/docker.sh). By default, these keys are Null to be avoided.

#### Build & Running:

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

### Use of GIS Worker as CLI:

#### Configuration:

To set the configuration for ```GeoKettle```, please edit the ```xml``` key at [configuration](./gis_worker_helpers/configuration.json) file. The other key that can be changed is ```debug``` to set the verbose mode.

#### Help:

```bash
python gis_worker.py -h
usage: gis_worker.py [-h] [ -t | -i | -f | -gj | -gt path ]

This software allows you execute jobs and transformations from asynchronous
way with Celery and messaging protocol as AMQP (RabbitMQ) plus Redis DB to
save the generated information or from CLI.

optional arguments:
  -h, --help            show this help message and exit
  -t path, --transform path
                        transform the geometries of the specific path to
                        Shapefile, also its SRS will be converted to WGS84.
  -i path, --info path  print information from geometries file.
  -f path, --fields path print fields from geometries file.
  -gj path, --geo-job path
                        execute a GeoKettle job.
  -gt path, --geo-transform path
                        execute a GeoKettle transformation.
```

---

Geographic Information System Worker (c) by Ontology Engineering Group

Geographic Information System Worker is licensed under a CC BY-NC 4.0.

Maintainer, [Alejandro F. Carrera](https://www.github.com/alejandrofcarrera)

You should have received a copy of the license along with this
work. If not, [see](http://creativecommons.org/licenses/by-nc/4.0/).
