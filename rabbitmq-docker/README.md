## RabbitMQ Docker Image Scripts

This Docker Image includes:

 * RabbitMQ - Alpine Version (shared volumes)

Configuration for the Docker Container (edit [launch.sh](./launch.sh) file)

|Name|Default value|
|----------|--------------|
|GEO_RABBIT_USER|rabbitmq|
|GEO_RABBIT_PWD|password|
|GEO_RABBIT_PORT|5672|
|GEO_RABBIT_MEM|512M ~ 512 MB|
|GEO_RABBIT_ADMIN_PORT|15672|

Run instance of GeoLinkeddata RabbitMQ

```bash
./launch.sh
```

Stop instance of GeoLinkeddata RabbitMQ

```bash
./stop.sh
```

**Note**: this version has two shared volumes, one for logging and other for data. If you want to persist one of them, add to [launch.sh](launch.sh) this parameters.

```bash
...
-p $GEO_RABBIT_ADMIN_PORT:15672 \
-v HOST_FOLDER_FOR_LOGGING:/data/log \
-v HOST_FOLDER_FOR_DATA:/data/mnesia \
-e RABBITMQ_DEFAULT_USER=$GEO_RABBIT_USER \
...

```

---

Ontology Engineering Group © Copyright 2017.

Licensed under [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/).

Maintainer, [Alejandro F. Carrera](https://www.github.com/alejandrofcarrera)
