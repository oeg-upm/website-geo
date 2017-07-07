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

import sys
import time
from celery.task import task
from celery.utils.log import get_task_logger
from gis_worker_helpers.geo_worker_gis import WorkerGIS
from gis_worker_helpers.geo_worker_db import WorkerRedis

reload(sys)
sys.setdefaultencoding('utf8')

__author__ = "Alejandro F. Carrera"
__copyright__ = "Copyright 2017 © GeoLinkeddata Platform"
__credits__ = ["Alejandro F. Carrera", "Oscar Corcho"]
__license__ = "Apache"
__maintainer__ = "Alejandro F. Carrera"
__email__ = "alejfcarrera@mail.ru"


##########################################################################


def get_libraries():
    """ This function allows to configure the database and the GDAL
        libraries to use them from the Celery workers of this project.

    Returns:
        Tuple: Redis and GDAL object or Raise an exception.

    """

    # Create instance of Redis database
    __redis_db = WorkerRedis()

    # Check if redis configuration is good
    if not __redis_db.status:
        raise Exception(
            'Redis configuration is not valid or Redis '
            'is not running'
        )

    # Create instance of GDAL methods
    __gdal_lib = WorkerGIS()

    # Check if libraries are good imported
    if not __gdal_lib.status:
        raise Exception(
            'GIS tools are not available at PATH. Please, '
            'check your Geokettle configuration and be sure '
            'that GDAL libraries are installed correctly and '
            'the version is greater than 2.1.0'
        )

    return __redis_db, __gdal_lib


##########################################################################


def print_worker_status(logger, status):
    """ This function allows to print a specific message depending on
        returned Celery worker's status.

    """

    if status == 1:

        # Log when the configuration is wrong
        logger.warn('\n * Skipped task (redis is not running)')

    elif status == 2:

        # Log when the task is locked
        logger.warn('\n * Skipped task (locked by other worker)')

    else:

        # Log when the task is finished
        logger.warn('\n * Skipped task (finished by other worker)')


def print_worker_errors(logger, messages):
    """ This function allows print messages to Celery logger.

    """

    # Count messages
    __messages_count = len(messages)

    # Show number of messages and messages
    __log_message = '\n * ' + str(__messages_count) + ' issues were found:'

    for __message in messages:
        __log_message += '\n * ' + __message

    # Show messages
    logger.error(__log_message)


def save_worker_messages(worker_db, logger, identifier, database, messages, kind):
    """ This function allows save the messages on the database and
        print the important messages (errors) through Celery logger.

    Return:
        Tuple: Flags boolean values (True if there is any message)

    """

    __flag_error = False
    __flag_warn = False

    # Check if there is any warning
    if len(messages['warn']):

        # Save on database the messages
        worker_db.save_record_warning(
            identifier + ':' + str(kind), database, messages['warn']
        )

        # Set new flag
        __flag_warn = True

    # Check if there is any error
    if len(messages['error']):

        # Save on database the messages
        worker_db.save_record_error(
            identifier + ':' + str(kind), database, messages['error']
        )

        # Print important messages
        print_worker_errors(logger, messages['error'])

        # Set new flag
        __flag_error = True

    return __flag_error, __flag_warn


def create_initial_mapping(identifier, logger, redis, gdal):
    """ This function allows create or update an initial mapping
        on the database for a specific identifier.

    """

    # Lock the execution for this task. In this case we will use
    # the Redis SETNX to ensure that other remote machines won't do
    # the same task.
    __lock_status = redis.lock(identifier, 'mapping-i')

    # Check status of the lock
    if __lock_status == 0:

        # Check if file was uploaded successfully
        if redis.check_existence(identifier, 'files'):

            # Get information about the specific identifier
            __file = redis.redis['files'].hgetall(identifier)

            # Status 1 | Transform to Shapefile
            __status = 1

            # Transform resource to Shapefile
            __ogr_info = gdal.transform(
                identifier, __file['name'],
                __file['extension'], 'shp'
            )

            # Set flags from generated information
            __flag_error, __flag_warn = save_worker_messages(
                redis, logger, identifier, 'mapping-i',
                __ogr_info, __status
            )

            if __flag_error:

                # Save status for tracking errors
                redis.save_record_status(
                    identifier, 'mapping-i', __status
                )

            # Check any previous error
            if not __flag_error:

                # Status 2 | Get parameters
                __status = 2

                # Get parameters through GDAL tools
                __ogr_info = gdal.get_info(
                    identifier, __file['name'], 'shp'
                )

                # Set flags from generated information
                __flag_error, __flag_warn = save_worker_messages(
                    redis, logger, identifier, 'mapping-i',
                    __ogr_info, __status
                )

                if __flag_error:

                    # Save status for tracking errors
                    redis.save_record_status(
                        identifier, 'mapping-i', __status
                    )

                else:

                    # Save new parameters on database
                    redis.save_record_properties(
                        identifier, __ogr_info['info']
                    )

            # Check any previous error
            if not __flag_error:

                # Status 3 | Get fields properties
                __status = 3

                # Get fields through GDAL tools
                __ogr_info = gdal.get_fields(
                    identifier, __file['name'], 'shp'
                )

                # Set flags from generated information
                __flag_error, __flag_warn = save_worker_messages(
                    redis, logger, identifier, 'mapping-i',
                    __ogr_info, __status
                )

                if __flag_error:

                    # Save status for tracking errors
                    redis.save_record_status(
                        identifier, 'mapping-i', __status
                    )

                else:

                    # Save initial mapping on database
                    redis.save_initial_mapping(
                        identifier, __ogr_info['info']
                    )

                    # Save status for tracking success
                    redis.save_record_status(
                        identifier, 'mapping-i', 0
                    )

            # if there was an error, delete all files
            if __flag_error:
                gdal.delete(identifier, __file['name'], 'shp')

        else:

            logger.error(
                '\n * Record was not found, the task was received, but '
                'there is no saved record for this identifier'
            )

        # Release lock
        redis.unlock(identifier + ':mapping-i', True)

    else:

        # Log status
        print_worker_status(logger, __lock_status)


##########################################################################


@task(bind=True, name='gis_worker_tasks.initial_mapping')
def initial_mapping(self):

    # Create logger to log messages to specific log file
    logger = get_task_logger(__name__)

    try:
        
        # Get instance of Redis and GDAL instance of Redis Database
        __redis_db, __gdal_lib = get_libraries()

    except Exception as e:

        # Set none to avoid warnings
        __redis_db = None
        __gdal_lib = None

        # Print message
        __message = e.message if e.message != '' else e
        logger.error('\n * ' + str(__message))

        # Retry task (max 10) to wait for loading libraries
        if self.request.retries < 10:
            raise self.retry(
                exc='', countdown=(self.request.retries + 1) * 20
            )

    # Create identifier from task_id
    __identifier = self.request.id

    # Execute new initial mapping generation
    create_initial_mapping(
        __identifier, logger, __redis_db, __gdal_lib
    )


@task(bind=True, name='gis_worker_tasks.update_mapping')
def update_mapping(self):

    # Create logger to log messages to specific log file
    logger = get_task_logger(__name__)

    try:
        
        # Get instance of Redis and GDAL instance of Redis Database
        __redis_db, __gdal_lib = get_libraries()

    except Exception as e:

        # Set none to avoid warnings
        __redis_db = None
        __gdal_lib = None

        # Print message
        __message = e.message if e.message != '' else e
        logger.error('\n * ' + str(__message))

        # Retry task (max 10) to wait for loading libraries
        if self.request.retries < 10:
            raise self.retry(
                exc='', countdown=(self.request.retries + 1) * 20
            )

    # Create identifier from task_id
    __identifier = self.request.id

    # Delete previous mapping
    __redis_db.del_initial_mapping(__identifier)

    # Execute new initial mapping generation
    create_initial_mapping(
        __identifier, logger, __redis_db, __gdal_lib
    )


@task(bind=True, name='gis_worker_tasks.extended_mapping')
def extended_mapping(self):

    # Create logger to log messages to specific log file
    logger = get_task_logger(__name__)

    try:
        
        # Get instance of Redis and GDAL instance of Redis Database
        __redis_db, __gdal_lib = get_libraries()

    except Exception as e:

        # Set none to avoid warnings
        __redis_db = None

        # Print message
        __message = e.message if e.message != '' else e
        logger.error('\n * ' + str(__message))

        # Retry task (max 10) to wait for loading libraries
        if self.request.retries < 10:
            raise self.retry(
                exc='', countdown=(self.request.retries + 1) * 20
            )

    # Get identifier of the task -> file
    __identifier = self.request.id

    # Lock the execution for this task. In this case we will use
    # the Redis SETNX to ensure that other remote machines won't do
    # the same task.
    __lock_status = __redis_db.lock(__identifier, 'mapping-e')

    # Check status of the lock
    if __lock_status == 0:

        # Do task
        time.sleep(5)
        
        # Release lock
        __redis_db.unlock(__identifier + ':mapping-e', True)

    else:

        # Log status
        print_worker_status(logger, __lock_status)


@task(bind=True, name='gis_worker_tasks.default', max_retries=5)
def default(self):
    
    # Create logger to log messages to specific log file
    logger = get_task_logger(__name__)

    # Print message
    logger.warn('\n * Received task from default queue')

