## RabbitMQ Docker Image Scripts

This Docker Image includes:

 * RabbitMQ - Alpine Version

Configuration for the Docker Container (edit [launch.sh](./launch.sh) file)

|Name|Default value|
|----------|--------------|
|GEO_RABBIT_USER|rabbitmq|
|GEO_RABBIT_PWD|password|
|GEO_RABBIT_PORT|5672|
|GEO_RABBIT_MEM|512 MB|

Run instance of GeoLinkeddata RabbitMQ

```bash
./launch.sh
```

Stop instance of GeoLinkeddata RabbitMQ

```bash
./stop
```

---

GeoLinkeddata © Copyright 2017.

Alejandro F. Carrera


