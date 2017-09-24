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
import argparse
from celery import Celery
from kombu import Exchange, Queue

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')

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
         dict: configuration fields and values.

    """

    # Configuration folder
    __config_base_path = './gis_worker_config'
    __debug = False

    # Check if application is on Debug mode
    if int(os.environ.get('OEG_DEBUG_MODE', 1)) == 1:

        # Get development configuration
        __config_path = os.environ.get(
            'OEG_CONFIG_DEBUG_FILE', __config_base_path + '/config_debug.json'
        )

        # Set debug flag
        __debug = True

    else:

        # Get production configuration
        __config_path = os.environ.get(
            'OEG_CONFIG_FILE', __config_base_path + '/config_production.json'
        )

    # Load current directory of geo_worker.py
    cwd = os.path.dirname(os.path.realpath(__file__)) + os.sep

    # Open file to load configuration
    with open(cwd + __config_path) as __file_data:

        # Return dictionary as configuration
        __dict = dict(json.load(__file_data))
        __dict['debug'] = __debug
        
        return __dict


##########################################################################


class Singleton(type):
    """ This constructor creates only an instance of a specific type
        following the singleton pattern (software design pattern).

    Returns:
        class: Super class of specific instance

    """
    
    def __call__(cls, *args, **kwargs):
        try:
            return cls.__instance
        except AttributeError:
            return super(Singleton, cls).__call__(*args, **kwargs)


class Worker(object):
    """ This constructor creates only an instance of a Worker
        following the singleton pattern (software design pattern).

    Returns:
        class: Worker

    """

    # Create singleton instance
    __metaclass__ = Singleton

    def configure_celery(self):
        """ This function allows to configure a Celery instance.
        """

        # Create new Celery instance
        celery_app = Celery('gis_worker')

        # Configure exchanges of RabbitMQ
        default_exchange = Exchange('geo.default', type='direct')
        mapping_exchange = Exchange('geo.mapping', type='direct')

        # Get RabbitMQ URL
        celery_app.conf.broker_url = 'pyamqp://' + \
            str(self.config['celery']['broker_user']) + ':' + \
            str(self.config['celery']['broker_pass']) + '@' + \
            str(self.config['celery']['broker_host']) + ':' + \
            str(self.config['celery']['broker_port']) + '//'

        # Compatibility with previous AMQP protocols
        celery_app.conf.task_protocol = 1

        # Import registered tasks
        celery_app.conf.imports = ('gis_worker_tasks',)

        # Configure queues of RabbitMQ
        celery_app.conf.task_queues = (
            Queue(
                'geo-mapping-initial', mapping_exchange,
                routing_key='geo.mapping.initial'
            ),
            Queue(
                'geo-mapping-update', mapping_exchange,
                routing_key='geo.mapping.update'
            ),
            Queue(
                'geo-mapping-extended', mapping_exchange,
                routing_key='geo.mapping.extended'
            ),
            Queue(
                'geo-default', default_exchange,
                routing_key='geo.default'
            )
        )

        # Configure default queue of RabbitMQ
        celery_app.conf.task_default_queue = 'geo-default'
        celery_app.conf.task_default_exchange_type = 'direct'
        celery_app.conf.task_default_routing_key = 'geo.default'

        # Configure tasks of Celery - RabbitMQ
        celery_app.conf.task_routes = {
            'gis_worker_tasks.initial_mapping': {
                'queue': 'geo-mapping-initial',
                'exchange': mapping_exchange,
                'routing_key': 'geo.mapping.initial'
            },
            'gis_worker_tasks.update_mapping': {
                'queue': 'geo-mapping-update',
                'exchange': mapping_exchange,
                'routing_key': 'geo.mapping.update'
            },
            'gis_worker_tasks.extended_mapping': {
                'queue': 'geo-mapping-extended',
                'exchange': mapping_exchange,
                'routing_key': 'geo.mapping.extended'
            },
            'gis_worker_tasks.default': {
                'queue': 'geo-default',
                'exchange': default_exchange,
                'routing_key': 'geo.default'
            }
        }

        return celery_app

    def __init__(self):

        # Get configuration of worker
        self.config = get_configuration_file()

        # Init Celery worker
        self.celery = self.configure_celery()


# Create Celery Worker and export Celery app
worker = Worker()
app = worker.celery


##########################################################################


def main_script():
    """ This function allows you to run the python script from command
        line. It accepts arguments and options as you can see below these
        comments.

    """

    # Create configuration for command line
    parser = argparse.ArgumentParser(
        description='This software allows you execute jobs and \
            transformations from asynchronous way with Celery and \
            messaging protocol as AMQP (RabbitMQ) plus Redis DB \
            to save the generated information or from CLI.',
        usage='gis_worker.py [-h] [ -t | -i | -f | -gj | -gt path ]'
    )
    parser.add_argument(
        '-t', '--transform', nargs=1, default=None, metavar='path',
        help='transform the geometries of the specific path to\n'
             'Shapefile, also its SRS will be converted to WGS84.'
    )
    parser.add_argument(
        '-i', '--info', nargs=1, default=None, metavar='path',
        help='print information from geometries file.'
    )
    parser.add_argument(
        '-f', '--fields', nargs=1, default=None, metavar='path',
        help='print information from Shapefile\'s fields, this\n'
             'option will raise an exception if geometry was not\n'
             'transformed to Shapefile before.'
    )
    parser.add_argument(
        '-gj', '--geo-job', nargs=1, default=None, metavar='path',
        help='execute a GeoKettle job.'
    )
    parser.add_argument(
        '-gt', '--geo-transform', nargs=1, default=None, metavar='path',
        help='execute a GeoKettle transformation.'
    )

    # Check parameters from CLI
    __args = parser.parse_args()

    # Import python script with real methods
    import gis_worker_tasks

    # Option: convert + id
    if __args.transform is not None:

        sys.exit(gis_worker_tasks.transform_with_path(
            __args.transform[0], '.shp', None
        )['status'])

    # Option: info + id
    elif __args.info is not None:

        sys.exit(gis_worker_tasks.info_with_path(
            __args.info[0], None
        )['status'])

    # Option: fields + id
    elif __args.fields is not None:

        sys.exit(gis_worker_tasks.fields_with_path(
            __args.fields[0], None
        )['status'])

    # Option: job + file
    elif __args.geo_job is not None:

        sys.exit(gis_worker_tasks.execute_geo_job_with_path(
            __args.geo_job[0], None, True
        )['status'])

    # Option: transform + file
    else:

        sys.exit(gis_worker_tasks.execute_geo_transform_with_path(
            __args.geo_transform[0], None, True
        )['status'])

if __name__ == "__main__":
    main_script()
