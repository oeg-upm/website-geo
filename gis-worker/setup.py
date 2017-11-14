#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Ontology Engineering Group
        http://www.oeg-upm.net/
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Copyright (C) 2017 Ontology Engineering Group.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Geographic Information System Worker is licensed under a
  Creative Commons Attribution-NC 4.0 International License.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
"""

import os
from setuptools import setup, find_packages

__author__ = "Alejandro F. Carrera"
__copyright__ = "Copyright 2017 © GeoLinkeddata Platform"
__credits__ = ["Alejandro F. Carrera", "Oscar Corcho"]
__license__ = "Creative Commons Attribution-Noncommercial license"
__maintainer__ = "Alejandro F. Carrera"
__email__ = "alejfcarrera@mail.ru"


##########################################################################


def read(name):
    return open(os.path.join(os.path.dirname(__file__), name)).read()


setup(
    name="gis-worker",
    version="1.0.0",
    author=__author__,
    author_email=__email__,
    description="This software allows you execute jobs and \
        transformations from asynchronous way with Celery and \
        messaging protocol as AMQP (RabbitMQ)",
    license=__license__,
    keywords="geolinkeddata celery worker geokettle gis",
    url="https://github.com/oeg-upm/website-geo.git",
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    install_requires=[
        'celery', 'hiredis', 'redis',
        'defusedxml', 'python-dateutil'
    ],
    classifiers=[],
    scripts=['gis_worker.py']
)