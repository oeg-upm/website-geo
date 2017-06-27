#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Ontology Engineering Group
        http://www.oeg-upm.net/
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Copyright (C) 2017 Ontology Engineering Group.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at
            http://www.apache.org/licenses/LICENSE-2.0
  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
"""

from celery.task import task
from geo_worker_helpers.geo_worker_log import WorkerLogger

__author__ = "Alejandro F. Carrera"
__copyright__ = "Copyright 2017 © GeoLinkeddata Platform"
__credits__ = ["Alejandro F. Carrera", "Oscar Corcho"]
__license__ = "Apache"
__maintainer__ = "Alejandro F. Carrera"
__email__ = "alejfcarrera@mail.ru"


##########################################################################


@task(bind=True, name='geo_worker_tasks.initial_mapping', max_retries=5)
def initial_mapping(self):

    # Create logger to log messages to specific log file
    logger = WorkerLogger()

    # Log kind of task received
    logger.log.info("[Worker - Initial] Task received")


@task(bind=True, name='geo_worker_tasks.partial_mapping', max_retries=5)
def partial_mapping(self):

    # Create logger to log messages to specific log file
    logger = WorkerLogger()

    # Log kind of task received
    logger.log.info("[Worker - Partial] Task received")


@task(bind=True, name='geo_worker_tasks.complete_mapping', max_retries=5)
def complete_mapping(self):

    # Create logger to log messages to specific log file
    logger = WorkerLogger()

    # Log kind of task received
    logger.log.info("[Worker - Complete] Task received")


@task(bind=True, name='geo_worker_tasks.default', max_retries=5)
def default(self):

    # Create logger to log messages to specific log file
    logger = WorkerLogger()

    # Log kind of task received
    logger.log.info("[Worker - Default] Task received")
