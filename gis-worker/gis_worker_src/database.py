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
import time
import redis
import settings
from redis import TimeoutError, ConnectionError

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


config = settings.Config()


def create_redis_pool(redis_host, redis_port, redis_pass, redis_db):
    """ This function creates a connection pool for Redis Database
        with a specific configuration. This is important to create
        connections and execute queries easily.

    Args:
        redis_host (string): host where Redis is available
        redis_port (int): port for Redis connection
        redis_pass (string): password for Redis connection
        redis_db (int): database for Redis client

    Returns:
        class: Redis Pool or None if something went wrong

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
    """ This function creates a connection pool for any of Redis
        configuration saved on configuration parameter.

    Args:
        configuration (dict): settings for Redis

    Returns:
        dict: Redis connection pools

    """

    __number_redis = 0
    __redis_connections = {}
    __redis_pools = {}

    # Generate connection pools to Redis Database
    for __redis_name in configuration['dbs']:

        # Create new connection pool
        __redis_pools[__redis_name] = create_redis_pool(
            configuration['host'], configuration['port'],
            configuration['pass'], __number_redis
        )

        # Test connection pool
        if __redis_pools[__redis_name] is None:

            # Disconnect other connection pools
            for __redis_pool_name in __redis_pools.keys():
                if __redis_pools[__redis_pool_name] is not None:
                    __redis_pools[__redis_pool_name].disconnect()

            return None

        else:

            # Save connection to structure
            __redis_connections[__redis_name] = redis.Redis(
                connection_pool=__redis_pools[__redis_name]
            )

        # Add new number for next connection pool
        __number_redis += 1

    return __redis_connections


##########################################################################


class WorkerRedis(object):
    """ This constructor creates only an instance of a Database
        class for saving data on Redis following the singleton
        pattern (software design pattern).

    Returns:
        class: Redis Worker

    """

    def __init__(self):

        # Execute method to create new instance of Redis - Worker
        # 0) tasks - Control about lock / unlock tasks
        # 1) status - Status about finished tasks
        # 2) messages - Messages with information (backtrace)
        # 3) files - Information about files from tasks
        # 4) mapping-i - Initial mapping
        # 5) mapping-v - Validation mapping
        # 6) mapping-s - Semantic mapping
        # 7) mapping-e - Extended mapping
        self.redis = configure_redis(config.redis_worker)

    def get_information(self, identifier):
        """ This function allows to get all the information
            from a specific key.

        Args:
            identifier (string): key to check

        Returns:
            dict: information or None

        """

        # Get information from database
        __info = self.redis['files'].hgetall(identifier)

        return None if not len(__info) else __info

    def check_existence(self, identifier, database):
        """ This function allows to check if key exists.

        Args:
            identifier (string): key to check
            database (string): identifier of db

        Returns:
            bool: True if exists, False otherwise

        """

        # Return status
        return self.redis[database].exists(identifier)

    def remove_records(self, identifier, mapping, files=False):
        """ This function allows to delete the information
            and all the fields for specific identifier.

        Args:
            identifier (string): key to delete it
            mapping (string): kind of mapping
            files (bool): flag to delete links / layers

        """

        # Remove any other trace
        for __d in [mapping, 'messages']:
            for __k in self.redis[__d].scan_iter(identifier + '*'):
                self.redis[__d].delete(__k)

        # Delete everything if flag is activated
        if files:
            self.redis['files'].delete(identifier)

    def save_record_info(self, identifier, layers, layers_md5, layers_info):
        """ This function allows to save the new parameters.

        Args:
            identifier (string): key where save information
            layers (list): transformed files' names
            layers_md5 (dict): relations between ids and names
            layers_info (list): transformed files' properties
        
        """

        # Save data to database
        for __k in range(0, len(layers)):

            # Get identifier of layer
            __layer = layers[__k]

            # Set layer name
            self.redis['files'].set(
                identifier + ':layer:' +
                __layer + ':name',
                layers_md5[__layer]
            )

            # Set layer information
            self.redis['files'].hmset(
                identifier + ':layer:' +
                __layer + ':info',
                layers_info[__k]
            )

    def save_record_fields(self, identifier, layers, layers_fields):
        """ This function allows to save the new parameters.

        Args:
            identifier (string): key where save information
            layers (list): transformed files' names
            layers_fields (list): transformed files' fields

        """

        # Save data to database
        for __k in range(0, len(layers)):

            # Get identifier of layer
            __layer = layers[__k]

            # Set layer fields
            self.redis['mapping-i'].hmset(
                identifier + ':layer:' +
                __layer + ':fields',
                layers_fields[__k]
            )

    def save_record_status(self, identifier, database, status):
        """ This function allows to save the status of the task.

        Args:
            identifier (string): key where save information
            database (string): identifier of db
            status (int): value returned from task
        
        """

        # Save new status on the database
        self.redis['status'].rpush(
            identifier, database + ':' + str(status)
        )

    def save_record_log(self, identifier, kind, messages):
        """ This function allows to save the status of the task.

        Args:
            identifier (string): key where save information
            kind (string): kind of logger
            messages (list): info messages returned from task

        """

        # Set dash for new identifier
        __kind = '-' + kind

        # Create new structure of messages
        __messages = [
            __message.strip(' \t\n\r')
            for __message in messages
            if __message != '\n'
        ]

        # Save structure
        for __message in __messages:
            self.redis['messages'].rpush(
                identifier + __kind, __message
            )

    def unlock(self, identifier, forced=False):
        """ This function allows to remove a Redis lock.

        Args:
            identifier (string): key to unlock
            forced (bool): flag for unlocking db hardly

        Returns:
            bool: True if unlock, False otherwise.

        """

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

        Args:
            identifier (string): key to lock
            database (string): identifier of db
            seconds (int): time to lock

        Returns:
            int: status returned
                0 = lock is created.
                1 = lock is not created by worker.
                2 = lock is not created by status.

        """

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
            return 2

        # Return status depending previous lock
        return 0 if __lock_status else 1
