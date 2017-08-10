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
import time
import redis
from redis import TimeoutError, ConnectionError

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
        Dict: Return configuration constraints.

    """

    # Configuration folder
    __config_base_path = '../gis_worker_config'
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
    cwd = os.path.dirname(os.path.realpath(__file__)) + '/'

    # Open file to load configuration
    with open(cwd + __config_path) as __file_data:

        # Return dictionary as configuration
        __dict = dict(json.load(__file_data))
        __dict['debug'] = __debug
        
        return __dict


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


def configure_redis(configuration):
    """ This function allows to configure a Redis database.

    """

    __number_redis = 0
    __redis_connections = {}
    __redis_pools = {}

    # Generate connection pools to Redis Database
    for __redis_name in configuration['redis']['db_ids']:

        # Create new connection pool
        __redis_pools[__redis_name] = create_redis_pool(
            configuration['redis']['db']['host'],
            configuration['redis']['db']['port'],
            configuration['redis']['db']['pass'],
            __number_redis
        )

        # Test connection pool
        if __redis_pools[__redis_name] is None:

            # Disconnect other connection pools
            for __redis_pool_name in __redis_pools.keys():
                __redis_pools[__redis_pool_name].disconnect()

            return None

        else:

            # Save connection to structure
            __redis_connections[__redis_name] = redis.Redis(
                connection_pool=__redis_pools[__redis_name]
            )

        # Add new number for next connection pool
        __number_redis += 1

    return __redis_connections, __redis_pools


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
        
        # Get current configuration
        self.config = get_configuration_file()

        # Create configuration for Redis
        self.redis, self.redis_pools = configure_redis(self.config)

        # Set status of Redis configuration
        self.status = self.redis is not None

    def check_existence(self, identifier, database):
        """ This function allows to check if key exists.

        Returns:
            Return True if exists, False otherwise

        """

        # Check Redis configuration
        if not self.status:
            return False

        # Return status
        return self.redis[database].exists(identifier)

    def save_initial_mapping(self, identifier, fields):
        """ This function allows to save the mapping for
            specific identifier. This mapping is the generated
            mapping from GDAL tools, identifying the fields from
            the source or raw data.
        
        """

        # Create data structure
        __mapping = {}

        # Iterate over the fields
        for __f in fields:

            # Get position of : on field
            __field_double_point = __f.index(':')

            # Get name of field
            __field_name = __f[:__field_double_point]

            # Get kind of field
            __field_value = str(
                __f[__field_double_point + 2:].split(' ')[0]
            ).lower()

            # Save field on dict
            __mapping[__field_name] = __field_value

        # Save mapping fields on database
        self.redis['mapping-i'].hmset(identifier, __mapping)

    def del_initial_mapping(self, identifier):
        """ This function allows to delete the mapping for
            specific identifier.
        
        """

        # Delete mapping fields on database
        self.redis['mapping-i'].delete(identifier)

    def save_record_properties(self, identifier, fields):
        """ This function allows to save the new parameters.
        
        """

        # Create dictionary from fields
        __fields = {
            __f[:__f.index(':')].lower(): __f[__f.index(':') + 2:]
            for __f in fields
        }

        # Get previous values
        __values = self.redis['files'].hgetall(identifier)

        # Join dictionaries
        __values.update(__fields)

        # Rename fields
        if 'extent' in __values:
            __values['bounding'] = __values['extent']
            del __values['extent']
        if 'feature count' in __values:
            __values['features'] = __values['feature count']
            del __values['feature count']

        # Save new dictionary with information
        self.redis['files'].hmset(identifier, __values)

    def save_record_status(self, identifier, database, status):
        """ This function allows to save the status of the task.
        
        """

        # Create new value with join of parameters
        __value = database + ':' + str(status)

        # Get current timestamp
        __time = str(int(time.time()))

        # Save new status on the database
        self.redis['status'].zadd(identifier, __value, __time)

    def save_record_warning(self, identifier, database, messages):
        """ This function allows to save log messages on the database.
        
        """

        # Remove previous messages
        self.redis[database + '-w'].delete(identifier)

        # Save new messages
        self.redis[database + '-w'].sadd(identifier, *messages)

    def save_record_error(self, identifier, database, messages):
        """ This function allows to save log messages on the database.
        
        """

        # Remove previous messages
        self.redis[database + '-e'].delete(identifier)

        # Save new messages
        self.redis[database + '-e'].sadd(identifier, *messages)

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

        # Create lock flag
        __lock_status = False

        # Create pseudo-identifier
        __identifier = identifier + ':' + database

        # Check if lock does not exist
        if not self.redis['tasks'].exists(__identifier):
            
            # Save database to lock
            self.redis['tasks'].setnx(
                __identifier, str(int(time.time()) + seconds)
            )

            # Set new value to flag
            __lock_status = True

        else:

            # Try to unlock
            if self.unlock(__identifier):
                
                # Try to lock again
                if self.lock(identifier, database) == 0:

                    # Set new value to flag
                    __lock_status = True

        # Check if for any reason the task is finished
        if self.check_existence(identifier, database):

            # If task is finished, unlock the resource
            self.unlock(__identifier, True)

            # Lock must be removed for always
            return 3

        # Return status depending previous lock
        return 0 if __lock_status else 2

    def exit(self):

        # Iterate over Connection Pools
        for __redis_name in self.redis_pools.keys():

            # Disconnect all clients
            self.redis_pools[__redis_name].disconnect()

        # Clear memory
        self.redis_pools = None
        self.redis = None
