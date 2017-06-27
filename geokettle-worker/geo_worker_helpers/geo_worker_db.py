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
import json
import time
import redis
from celery.utils.log import get_task_logger
from redis import TimeoutError, ConnectionError

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
    __config_base_path = '../geo_worker_config'

    # Check if application is on Debug mode
    if int(os.environ.get('OEG_DEBUG_MODE', 1)) == 1:

        # Get development configuration
        __config_path = os.environ.get(
            'OEG_CONFIG_DEBUG_FILE', __config_base_path + '/config_debug.json'
        )
    else:

        # Get production configuration
        __config_path = os.environ.get(
            'OEG_CONFIG_FILE', __config_base_path + '/config_production.json'
        )

    # Load current directory of geo_worker.py
    cwd = os.path.dirname(os.path.realpath(__file__)) + '/'

    # Open file to load configuration
    with open(cwd + __config_path) as __file_data:

        # Return dictionary as configuration
        return dict(json.load(__file_data))


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


def configure_redis():
    """ This function allows to configure a Redis database.
    """

    __number_redis = 0
    __redis_connections = {}
    __redis_pools = {}
    __configuration = get_configuration_file()

    # Generate connection pools to Redis Database
    for __redis_name in __configuration['redis']['db_ids']:

        # Create new connection pool
        __redis_pool = create_redis_pool(
            __configuration['redis']['db']['host'],
            __configuration['redis']['db']['port'],
            __configuration['redis']['db']['pass'],
            __number_redis
        )

        # Test connection pool
        if __redis_pool is None:

            # Disconnect other connection pools
            for __redis_pool_name in __redis_pools.keys():
                __redis_pools[__redis_pool_name].disconnect()

            return None

        else:

            # Save connection to structure
            __redis_connections[__redis_name] = redis.Redis(
                connection_pool=__redis_pool
            )

        # Add new number for next connection pool
        __number_redis += 1

    return __redis_connections


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


class WorkerRedis(object):
    """ This constructor creates only an instance of a Database
        class for saving data on Redis following the singleton
        pattern (software design pattern).

    """

    # Create singleton instance
    __metaclass__ = Singleton

    def __init__(self):
        
        # Create configuration for Redis
        self.redis = configure_redis()

        # Set status of Redis configuration
        self.status = self.redis is not None

        if self.status:

            # Create logger for this Python script
            self.logger = get_task_logger(__name__)

    def check_existence(self, identifier, database):
        """ This function allows to check if key exists.
        """

        # Check Redis configuration
        if not self.status:
            return False

        # Return status
        return self.redis[database].exists(identifier)   

    def unlock(self, identifier, forced=False):
        """ This function allows to remove a Redis lock.

        Returns:
            Bool: Return True if unlock, False otherwise.

        """

        # Check Redis configuration
        if not self.status:
            return False

        # Check if lock exists
        if self.redis['tasks'].exists(identifier):
        
            # Check the time of expiration
            # This behaviour is to be sure that the
            # worker with the lock is not crashed
            if (int(self.redis['tasks'].get(identifier)) <
                    int(time.time())) or forced:

                self.logger.warn(' -> UNLOCKED %s', identifier)

                # Release the identifier of the task
                self.redis['tasks'].delete(identifier)

                # Unlock was successful
                return True

        # Unlock was unsuccessful
        return False

    def lock(self, identifier, database, seconds=21):
        """ This function allows to create a Redis lock.

        Returns:
            int: Return
                0 = lock is created.
                1 = lock is not created by redis.
                2 = lock is not created by worker.
                3 = lock is not created by status.

        """

        # Check Redis configuration
        if not self.status:
            return 1

        # Create pseudo-identifier
        __identifier = identifier + ':' + database

        # Check if lock does not exist
        if not self.redis['tasks'].exists(__identifier):
            
            # Save database to lock
            self.redis['tasks'].setnx(
                __identifier, str(int(time.time()) + seconds)
            )

            self.logger.warn(' -> LOCKED %s', __identifier)

            # Lock was successful
            return 0

        else:

            # Try to unlock
            if self.unlock(__identifier):
                
                # Try to lock again
                if self.lock(identifier, database) == 0:

                    # Lock was successful
                    return 0

        # Check if for any reason the task is finished
        if self.check_existence(identifier, database):

            # If task is finished, unlock the resource
            self.unlock(__identifier, True)

            # Lock must be removed for always
            return 3

        # Lock was unsuccessful
        return 2
