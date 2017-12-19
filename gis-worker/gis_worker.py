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

import sys
import argparse
from celery.utils.log import get_task_logger
from celery import Celery
from kombu import Exchange, Queue
from gis_worker_src import settings

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')

__author__ = "Alejandro F. Carrera"
__copyright__ = "Copyright 2017 © GeoLinkeddata Platform"
__credits__ = ["Alejandro F. Carrera", "Oscar Corcho"]
__license__ = "Creative Commons Attribution-Noncommercial license"
__maintainer__ = "Alejandro F. Carrera"
__email__ = "alejfcarrera@mail.ru"


##########################################################################


class Worker(object):
    """ This constructor creates only an instance of a Worker
        following the singleton pattern (software design pattern).

    Returns:
        class: Worker

    """

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
            self.config.celery_user + ':' + self.config.celery_pwd + '@' + \
            self.config.celery_host + '//'

        # Compatibility with previous AMQP protocols
        celery_app.conf.task_protocol = 1

        # Import registered tasks
        celery_app.conf.imports = ('gis_worker_tasks',)

        # Configure queues of RabbitMQ
        celery_app.conf.task_queues = (
            Queue(
                'geo-mapping-create', mapping_exchange,
                routing_key='geo.mapping.create'
            ),
            Queue(
                'geo-mapping-extend', mapping_exchange,
                routing_key='geo.mapping.extend'
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
            'gis_worker_tasks.create_mapping': {
                'queue': 'geo-mapping-create',
                'exchange': mapping_exchange,
                'routing_key': 'geo.mapping.create'
            },
            'gis_worker_tasks.extend_mapping': {
                'queue': 'geo-mapping-extend',
                'exchange': mapping_exchange,
                'routing_key': 'geo.mapping.extend'
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
        self.config = settings.Config()

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

    # Check there at least one parameter
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    # Get parameters from CLI
    __args = parser.parse_args()

    # Import python script with real methods
    import gis_worker_tasks

    # Create Logger from settings
    __logger = settings.WorkerLogger()

    # Option: convert + id
    if __args.transform is not None:

        sys.exit(gis_worker_tasks.transform_with_path(
            __args.transform[0], '.shp', __logger
        )['status'])

    # Option: info + id
    elif __args.info is not None:

        sys.exit(gis_worker_tasks.info_with_path(
            __args.info[0], __logger, True
        )['status'])

    # Option: fields + id
    elif __args.fields is not None:

        sys.exit(gis_worker_tasks.fields_with_path(
            __args.fields[0], __logger, True
        )['status'])

    # Option: job + file
    elif __args.geo_job is not None:

        sys.exit(gis_worker_tasks.execute_geo_job_with_path(
            __args.geo_job[0], __logger, True
        )['status'])

    # Option: transform + file
    elif __args.geo_transform is not None:

        sys.exit(gis_worker_tasks.execute_geo_transform_with_path(
            __args.geo_transform[0], __logger, True
        )['status'])

    else:
        sys.exit(1)


if __name__ == "__main__":
    main_script()
