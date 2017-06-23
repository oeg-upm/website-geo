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
import redis
from celery import Celery
from kombu import Exchange, Queue
from redis import TimeoutError, ConnectionError

__author__ = "Alejandro F. Carrera"
__copyright__ = "Copyright 2017 © GeoLinkeddata Platform"
__credits__ = ["Alejandro F. Carrera", "Oscar Corcho"]
__license__ = "Apache"
__version__ = "2.0"
__maintainer__ = "Alejandro F. Carrera"
__email__ = "alejfcarrera@mail.ru"


##########################################################################


def create_redis_pool(redis_host, redis_port, redis_pass, redis_db):
    """ This function creates a connection pool for Redis Database
        with a specific configuration. This is important to save and get
        information and status of the jobs and transformations for
        Geokettle.

    Returns:
        Redis Instance or None if configuration fails

    """

    __redis_pool = redis.ConnectionPool(
        socket_connect_timeout=5,
        host=redis_host,
        port=redis_port,
        password=redis_pass,
        db=redis_db
    )
    try:

        # Detect if Redis is running
        __connection = __redis_pool.get_connection('ping')
        __connection.send_command('ping')
        return __redis_pool

    except (ConnectionError, TimeoutError):
        
        # Disconnect connection pool
        __redis_pool.disconnect()

        return None


def check_geokettle_path():
    """ This function detects if Geokettle executables are included
        on the current environment (PATH variable). This is important
        to avoid full path directories and to be compatible with Docker
        Geokettle Image.

    Returns:
        bool: Return True if "kitchen" and "pan" exist, False otherwise.

    """

    # Create split character depeding on operative system
    path_split = ';' if 'win32' in sys.platform else ':'

    # Get folders from PATH variable
    path_dirs = os.environ.get('PATH').split(path_split)

    # Iterate over folders
    for path_dir in path_dirs:

        # Get all nodes from directory
        path_files = os.listdir(path_dir)

        # Return if kitchen and pan exists at the same folder
        if 'kitchen.sh' in path_files and 'pan.sh' in path_files:
            return True

    # executables were not found
    return False


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

        # Get RabbitMQ URL
        celery_url = 'pyamqp://' + \
            str(self.config['celery']['broker_user']) + ':' + \
            str(self.config['celery']['broker_pass']) + '@' + \
            str(self.config['celery']['broker_host']) + ':' + \
            str(self.config['celery']['broker_port']) + '//'

        # Create new Celery instance
        celery_app = Celery('geo_worker', broker_url=celery_url)

        # Configure exchanges of RabbitMQ
        default_exchange = Exchange('default', type='direct')
        mapping_exchange = Exchange('mapping', type='direct')

        # Configure queues of RabbitMQ
        celery_app.conf.task_queues = (
            Queue(
                'default', default_exchange,
                routing_key='default'
            ),
            Queue(
                'mapping-partial', mapping_exchange,
                routing_key='mapping.create.partial'
            ),
            Queue(
                'mapping-entire', mapping_exchange,
                routing_key='mapping.create.entire'
            )
        )

        # Configure default queue of RabbitMQ
        celery_app.conf.task_default_queue = 'default'
        celery_app.conf.task_default_exchange_type = 'direct'
        celery_app.conf.task_default_routing_key = 'default'

        return celery_app

    def configure_redis(self):
        """ This function allows to configure a Redis database.
        """

        number_redis_db = 0
        redis_connections = {}
        redis_pools = {}

        # Generate connection pools to Redis Database
        for redis_config_name in self.config['redis']['db_ids']:

            # Create new connection pool
            __redis_pool = create_redis_pool(
                self.config['redis']['db']['host'],
                self.config['redis']['db']['port'],
                self.config['redis']['db']['pass'],
                number_redis_db
            )

            # Test connection pool
            if __redis_pool is None:

                # Disconnect other connection pools
                for redis_pool_name in redis_pools.keys():
                    redis_pools[redis_pool_name].disconnect()

                # Raise exception to caller method
                raise Exception('Redis is not running or configured')

            else:

                # Save connection to structure
                redis_connections[redis_config_name] = redis.Redis(
                    connection_pool=__redis_pool
                )

            # Add new number for next connection pool
            number_redis_db += 1

        return redis_connections

    def __init__(self):

        # Check if geokettle is available
        if check_geokettle_path():

            # Get configuration of worker
            self.config = get_configuration_file()

            # Generate links
            self.celery = self.configure_celery()
            self.redis = self.configure_redis()

        else:
            raise Exception('Geokettle binaries are not available [PATH]')
        

# Create Celery Worker and export Celery app
worker = Worker()
app = worker.celery
