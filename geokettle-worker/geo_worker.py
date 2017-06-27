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

import os
import sys
import json
from celery import Celery
from kombu import Exchange, Queue
from geo_worker_helpers.geo_worker_gis import WorkerGIS
from geo_worker_helpers.geo_worker_db import WorkerRedis
from geo_worker_helpers.geo_worker_log import WorkerLogger

__author__ = "Alejandro F. Carrera"
__copyright__ = "Copyright 2017 © GeoLinkeddata Platform"
__credits__ = ["Alejandro F. Carrera", "Oscar Corcho"]
__license__ = "Apache"
__maintainer__ = "Alejandro F. Carrera"
__email__ = "alejfcarrera@mail.ru"


##########################################################################


def get_configuration_file():
    """ This function allows you to load a configuration from file.

    Returns:
        Dict: Return configuration constraints.

    """

    # Configuration folder
    base_path = './geo_worker_config'

    # Check if application is on Debug mode
    if int(os.environ.get('OEG_DEBUG_MODE', 1)) == 1:

        # Get development configuration
        config_file_path = os.environ.get(
            'OEG_CONFIG_DEBUG_FILE', base_path + '/config_debug.json'
        )
    else:

        # Get production configuration
        config_file_path = os.environ.get(
            'OEG_CONFIG_FILE', base_path + '/config_production.json'
        )

    # Load current directory of geo_worker.py
    cwd = os.path.dirname(os.path.realpath(__file__)) + '/'

    # Open file to load configuration
    with open(cwd + config_file_path) as data_file:

        # Return dictionary as configuration
        return dict(json.load(data_file))


##########################################################################


class Singleton(type):
    """ This constructor creates only an instance of a specific type
        following the singleton pattern (software design pattern).

    """
    
    def __call__(cls, *args, **kwargs):
        try:
            return cls.__instance
        except AttributeError:
            return super(Singleton, cls).__call__(*args, **kwargs)


class Worker(object):
    """ This constructor creates only an instance of a Worker
        following the singleton pattern (software design pattern).

    """

    # Create singleton instance
    __metaclass__ = Singleton

    def configure_celery(self):
        """ This function allows to configure a Celery instance.
        """

        # Create new Celery instance
        celery_app = Celery('geo_worker')

        # Configure exchanges of RabbitMQ
        default_exchange = Exchange('default', type='direct')
        mapping_exchange = Exchange('mapping', type='direct')

        # Get RabbitMQ URL
        celery_app.conf.broker_url = 'pyamqp://' + \
            str(self.config['celery']['broker_user']) + ':' + \
            str(self.config['celery']['broker_pass']) + '@' + \
            str(self.config['celery']['broker_host']) + ':' + \
            str(self.config['celery']['broker_port']) + '//'

        # Compatibility with previous AMQP protocols
        celery_app.conf.task_protocol = 1

        # Import registered tasks
        celery_app.conf.imports = ('geo_worker_tasks',)

        # Configure queues of RabbitMQ
        celery_app.conf.task_queues = (
            Queue(
                'mapping-initial', mapping_exchange,
                routing_key='mapping.initial'
            ),
            Queue(
                'mapping-partial', mapping_exchange,
                routing_key='mapping.partial'
            ),
            Queue(
                'mapping-complete', mapping_exchange,
                routing_key='mapping.complete'
            ),
            Queue(
                'default', default_exchange,
                routing_key='default'
            )
        )

        # Configure default queue of RabbitMQ
        celery_app.conf.task_default_queue = 'default'
        celery_app.conf.task_default_exchange_type = 'direct'
        celery_app.conf.task_default_routing_key = 'default'

        # Configure tasks of Celery - RabbitMQ
        celery_app.conf.task_routes = {
            'geo_worker_tasks.initial_mapping': {
                'queue': 'mapping-initial',
                'exchange': mapping_exchange,
                'routing_key': 'mapping.initial'
            },
            'geo_worker_tasks.partial_mapping': {
                'queue': 'mapping-partial',
                'exchange': mapping_exchange,
                'routing_key': 'mapping.partial'
            },
            'geo_worker_tasks.complete_mapping': {
                'queue': 'mapping-complete',
                'exchange': mapping_exchange,
                'routing_key': 'mapping.complete'
            },
            'geo_worker_tasks.default': {
                'queue': 'default',
                'exchange': default_exchange,
                'routing_key': 'default'
            }
        }

        return celery_app

    def __init__(self):

        # Create logger for this Python script
        self.logger = WorkerLogger()

        # Init Database connections
        self.db = WorkerRedis()

        # Check Database connections
        if not self.db.status:

            # Log error to log file
            self.logger.log.error(
                'Redis configuration is not valid or Redis '
                'is not running'
            )

            # Exit worker
            sys.exit(1)

        # Init GIS helpers
        self.gis = WorkerGIS()

        # Check GIS helpers
        if not self.gis.status:

            # Log error to log file
            self.logger.log.error(
                'GIS tools are not available at PATH. Please, '
                'check your Geokettle configuration and be sure '
                'that GDAL libraries are installed correctly'
            )

            # Exit worker
            sys.exit(1)

        # Get configuration of worker
        self.config = get_configuration_file()

        # Init Celery worker
        self.celery = self.configure_celery()


# Create Celery Worker and export Celery app
worker = Worker()
app = worker.celery
