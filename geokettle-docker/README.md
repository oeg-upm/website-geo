## GeoKettle Docker Image

This Docker Image includes:

 * Java 8 - OpenJDK
 * Apache Ant 1.10.1
 * GeoKettle 2.5

Build the Docker Image

```bash
docker build -t geokettle:2.5 .
```

Run container to see if Docker Image is working

```bash
docker run geokettle:2.5 kitchen.sh
```

Not available GeoKettle CLI:

* spoon.sh: not supported because is a GUI
* carte.sh: not supported because is for remote execution

Available GeoKettle CLI:

* pan.sh: running transformations
* kitchen.sh: running jobs

---

GeoLinkeddata © Copyright 2017.

Alejandro F. Carrera

