## Redis Docker Image Scripts

This Docker Image includes:

 * Redis

Configuration for the Docker Container (edit [launch.sh](./launch.sh) file)

|Name|Default value|
|----------|--------------|
|GEO_REDIS_PORT|6379|

Run instance of GeoLinkeddata Redis

```bash
./launch.sh
```

Stop instance of GeoLinkeddata Redis

```bash
./stop.sh
```

**Note**: this version has one shared volume (data). If you want to persist it, add to [launch.sh](launch.sh) this parameter.

```bash
...
-v ./redis.conf:/usr/local/etc/redis/redis.conf \
-v HOST_FOLDER_FOR_DATA:/data \
-p $GEO_REDIS_PORT:6379 \
...

```

---

Ontology Engineering Group © Copyright 2017.

Licensed under [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/).

Maintainer, [Alejandro F. Carrera](https://www.github.com/alejandrofcarrera)
