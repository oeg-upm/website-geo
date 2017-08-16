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
reload(sys)
sys.setdefaultencoding('utf8')

import os
import time
import json
from celery.task import task
from celery.utils.log import get_task_logger
from gis_worker_helpers.geo_worker_gis import WorkerGIS
from gis_worker_helpers.geo_worker_gis import get_ogr_file_extensions
from gis_worker_helpers.geo_worker_xml import WorkerXML
from gis_worker_helpers.geo_worker_db import WorkerRedis

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
    cwd = os.path.dirname(os.path.realpath(__file__)) + '/'

    # Open file to load configuration
    with open(cwd + __config_path) as __file_data:

        # Return dictionary as configuration
        __dict = dict(json.load(__file_data))
        __dict['debug'] = __debug

        return __dict


##########################################################################


def get_redis_instance():
    """ This function allows to configure the database to use
    it from the Celery workers of this project or CLI.

    Returns:
        Redis object or Raise an exception.

    """

    # Create instance of Redis database
    __redis_db = WorkerRedis()

    # Check if redis configuration is good
    if not __redis_db.status:
        raise Exception(
            'Redis configuration is not valid or\n * Redis '
            'is not running'
        )

    return __redis_db


def get_gdal_instance():
    """ This function allows to configure the GDAL library to use
    it from the Celery workers of this project or CLI.

    Returns:
        GDAL object or Raise an exception.

    """

    # Create instance of GDAL methods
    __gdal_lib = WorkerGIS()

    # Check if libraries are good imported
    if not __gdal_lib.status:
        raise Exception(
            'GIS tools are not available at PATH.\n * Please, '
            'check your Geokettle configuration\n * and be sure '
            'that GDAL libraries are\n * installed correctly and '
            'the version is\n * greater than 2.1.0'
        )

    return __gdal_lib


def get_libraries():
    """ This function allows to configure the database and the GDAL
        libraries to use them from the Celery workers of this project.

    Returns:
        Tuple: Redis and GDAL object or Raise an exception.

    """

    return get_redis_instance(), get_gdal_instance()


##########################################################################


def print_to_logger(messages, logger=None):
    """ This function allows to print messages to the logger or
        stdout with print function.

    """

    # Set prefix for all messages
    __prefix = '\n * '
    __prefix_order = ['info', 'warn', 'error']
    __prefix_kind = {
        'info': 'INFO',
        'warn': 'WARN',
        'error': 'ERROR'
    }

    # Save messages to logger
    __logger_msg = {
        'info': '',
        'warn': '',
        'error': ''
    }

    # Iterate kind of messages
    for __k in __prefix_order:

        # Detect if there are any messages
        if len(messages[__k]):

            # Print jump depending on logger
            if logger is None:
                print ''
            else:
                __logger_msg[__k] += '\n'

            # Log messages
            for __m in messages[__k]:

                # Print / save messages depending on logger
                if logger is None:
                    print ' * [' + __prefix_kind[__k] + '] ' + __m
                else:
                    __logger_msg[__k] += __prefix + __m

    # Print jump / messages depending on logger
    if logger is None:
        print ''
    else:

        # Iterate kind of messages
        for __k in __prefix_order:

            # Detect if there are any messages
            if len(__logger_msg[__k]):

                # Print messages
                getattr(logger, __k)(__logger_msg[__k] + '\n')


def print_not_found_message():
    """ This function returns a message when identifier
        is not found on the database.

        Return:
            Dict: Information structure with error
    """

    return {
        'error': [
            '* ------------ Errors -------------\n',
            'Record was not found, the task was received, but '
            'there is no saved record for this identifier.'
        ],
        'warn': [],
        'info': []
    }


def print_worker_status(status, logger=None):
    """ This function allows to print a specific message depending on
        returned Celery worker's status.

    """

    if status == 1:

        # Create message when the configuration is wrong
        __message = ['Skipped task (redis is not running)']

    elif status == 2:

        # Create message when the task is locked
        __message = ['Skipped task (locked by other worker)']

    else:

        # Create message when the task is finished
        __message = ['Skipped task (finished by other worker)']

    # Print messages
    print_to_logger({
        'warn': __message,
        'info': [],
        'error': []
    }, logger)


def print_worker_errors(messages, logger=None):
    """ This function allows print messages to Celery logger.

    """

    # Print messages
    print_to_logger({
        'error': messages,
        'warn': [],
        'info': []
    }, logger)


##########################################################################


def transform_with_path(path, ext_dst, logger=None, ext_logger=True):
    """ This function transforms a gis or geometries path to
        other kind of geometry through GDAL libraries.

    Return:
        Dict, GDAL information and status code

    """

    # Transform resource and return result
    __t_info = get_gdal_instance().transform(path, ext_dst)

    # Add messages to result
    if len(__t_info['error']) and ext_logger:
        __t_info['error'] = [
            '* ------------ Errors -------------\n'
        ] + __t_info['error']
    if len(__t_info['warn']) and ext_logger:
        __t_info['warn'] = [
            '* ----------- Warnings ------------\n'
        ] + __t_info['warn']
    if len(__t_info['info']) and ext_logger:
        __t_info['info'] = [
           '* ---- Fields of the Shapefile ----\n'
        ] + __t_info['info']

    # Log messages from result
    print_to_logger(__t_info, logger)

    # Return status code and messages
    return {
        'status': 2 if len(__t_info['error']) else 0,
        'messages': __t_info
    }


def transform_with_id(identifier, ext_dst, logger, ext_logger):
    """ This function transforms a gis or geometries path to
        other kind of geometry through GDAL libraries.

    Return:
        Dict, GDAL information and status code

    """

    # Check if redis or gdal were input
    __lib = get_libraries()

    # Check if database has metadata for this identifier
    if __lib[0].check_existence(identifier, 'files'):

        # Get information about the specific identifier
        __f_info = __lib[0].redis['files'].hgetall(identifier)

        # Generate path
        __config = get_configuration_file()
        __path = __config['folder'] + '/' + \
            identifier + '/' + __f_info['name'] + \
            __f_info['extension']

        # Close redis
        __lib[0].exit()

        # Transform resource and get result
        return transform_with_path(__path, ext_dst, logger, ext_logger)

    else:

        # Close redis
        __lib[0].exit()

        # Create messages structure from zero
        __t_info = print_not_found_message()

        # Log messages from result
        print_to_logger(__t_info, logger)

        # Return status code and messages
        return {
            'status': 1 if len(__t_info['error']) else 0,
            'messages': __t_info
        }


def info_with_path(path, logger=None, ext_logger=True):
    """ This function gets information from metadata
        gis or geometries file through GDAL libraries.

    Return:
        Dict, GDAL information and status code

    """

    # Get information resource and return result
    __t_info = get_gdal_instance().get_info(path)

    # Add messages to result
    if len(__t_info['error']) and ext_logger:
        __t_info['error'] = [
            '* ------------ Errors -------------\n'
        ] + __t_info['error']
    if len(__t_info['warn']) and ext_logger:
        __t_info['warn'] = [
            '* ----------- Warnings ------------\n'
        ] + __t_info['warn']
    if len(__t_info['info']) and ext_logger:
        __t_info['info'] = [
            '* --------- Information -----------\n'
        ] + __t_info['info']

    # Log messages from result
    print_to_logger(__t_info, logger)

    # Return status code and messages
    return {
        'status': 2 if len(__t_info['error']) else 0,
        'messages': __t_info
    }


def info_with_id(identifier, logger, ext_logger):
    """ This function gets information from metadata
        gis or geometries file through GDAL libraries.

    Return:
        Dict, GDAL information and status code

    """

    # Check if redis or gdal were input
    __lib = get_libraries()

    # Check if database has metadata for this identifier
    if __lib[0].check_existence(identifier, 'files'):

        # Get information about the specific identifier
        __f_info = __lib[0].redis['files'].hgetall(identifier)

        # Generate path
        __config = get_configuration_file()
        __path = __config['folder'] + '/' + \
            identifier + '/' + __f_info['name'] + \
            __f_info['extension']

        # Close redis
        __lib[0].exit()

        # Transform resource and get result
        return info_with_path(__path, logger, ext_logger)

    else:

        # Close redis
        __lib[0].exit()

        # Create messages structure from zero
        __t_info = print_not_found_message()

        # Log messages from result
        print_to_logger(__t_info, logger)

        # Return status code and messages
        return {
            'status': 1 if len(__t_info['error']) else 0,
            'messages': __t_info
        }


def fields_with_path(path, logger=None, ext_logger=True):
    """ This function gets information from metadata
        fields about gis or geometries file through
        GDAL libraries.

    Return:
        Dict, GDAL information and status code

    """

    # Get information resource and return result
    __t_info = get_gdal_instance().get_fields(path, True)

    # Add messages to result
    if len(__t_info['error']) and ext_logger:
        __t_info['error'] = [
            '* ------------ Errors -------------\n'
        ] + __t_info['error']
    if len(__t_info['warn']) and ext_logger:
        __t_info['warn'] = [
            '* ----------- Warnings ------------\n'
        ] + __t_info['warn']
    if len(__t_info['info']) and ext_logger:
        __t_info['info'] = [
            '* ------------ Fields -------------\n'
        ] + __t_info['info']

    # Log messages from result
    print_to_logger(__t_info, logger)

    # Return status code and messages
    return {
        'status': 2 if len(__t_info['error']) else 0,
        'messages': __t_info
    }


def fields_with_id(identifier, logger, ext_logger):
    """ This function gets information from metadata
        fields about gis or geometries file through
        GDAL libraries.

    Return:
        Dict, GDAL information and status code

    """

    # Check if redis or gdal were input
    __lib = get_libraries()

    # Check if database has metadata for this identifier
    if __lib[0].check_existence(identifier, 'files'):

        # Get information about the specific identifier
        __f_info = __lib[0].redis['files'].hgetall(identifier)

        # Generate path
        __config = get_configuration_file()
        __path = __config['folder'] + '/' + \
            identifier + '/' + __f_info['name'] + \
            __f_info['extension']

        # Close redis
        __lib[0].exit()

        # Transform resource and get result
        return fields_with_path(__path, logger, ext_logger)

    else:

        # Close redis
        __lib[0].exit()

        # Create messages structure from zero
        __t_info = print_not_found_message()

        # Log messages from result
        print_to_logger(__t_info, logger)

        # Return status code and messages
        return {
            'status': 1 if len(__t_info['error']) else 0,
            'messages': __t_info
        }


def delete_with_id(identifier, extension):
    """ This function deletes a specific folder with
        extensions inside this folder.

    """

    # Generate path
    __config = get_configuration_file()
    __path = __config['folder'] + '/' + identifier

    # Check path exists
    if os.path.isdir(__path):

        # Get all files from path
        __path_files = os.listdir(__path)

        # Get all extensions from base extension
        __extensions = get_ogr_file_extensions(extension)

        # Iterate over files
        for __file in __path_files:

            # Join path with file
            __f = __path + '/' + __file

            # Get extension from path
            __file_ext = '.'.join(__f.split('.')[-2:]) \
                if len(__f.split('.')) > 2 else os.path.splitext(__f)[1]

            # Check if extension is valid
            if __file_ext in __extensions:

                # Check if path is a correct file and exists
                if os.path.exists(__f) and os.path.isfile(__f):

                    # Remove path
                    os.remove(__f)


def execute_geo_job_with_path(path, logger=None, ext_logger=True):
    return None


def execute_geo_job_with_id(identifier, logger, ext_logger):
    return None


def execute_geo_transform_with_path(path, logger=None, ext_logger=True):
    return None


def execute_geo_transform_with_id(identifier, logger, ext_logger):
    return None


##########################################################################


def create_initial_mapping(identifier, redis, logger):
    """ This function allows create or update an initial mapping
        on the database for a specific identifier.

    """

    # Lock the execution for this task. In this case we will use
    # the Redis SETNX to ensure that other remote machines won't do
    # the same task.
    __lock_status = redis.lock(identifier, 'mapping-i')

    # Check status of the lock
    if __lock_status == 0:

        # Transform to Shapefile
        __o_info = transform_with_id(
            identifier, '.shp', logger, False
        )

        # Flags for errors
        __flag_error = __o_info['status'] == 2
        __flag_not_exist = __o_info['status'] == 1

        # Detect flags
        if not __flag_not_exist and not __flag_error:

            # Save warn messages
            if len(__o_info['messages']['warn']):
                redis.save_record_warning(
                    identifier, 'mapping-i',
                    __o_info['messages']['warn']
                )

            # Save initial mapping on database
            redis.save_initial_mapping(
                identifier, __o_info['messages']['info']
            )

            # Save status for tracking success
            redis.save_record_status(
                identifier, 'mapping-i', 0
            )

        # Detect error flag
        if __flag_error:

            # Save error messages
            if len(__o_info['messages']['error']):
                redis.save_record_error(
                    identifier, 'mapping-i',
                    __o_info['messages']['error']
                )

            # Save status for tracking success
            redis.save_record_status(
                identifier, 'mapping-i', 1
            )

            # Delete generated files
            delete_with_id(identifier, '.shp')

        if __flag_not_exist:

            # Show not found message
            print_to_logger(
                print_not_found_message(), logger
            )

        # Release lock
        redis.unlock(identifier + ':mapping-i', True)

    else:

        # Log status
        print_worker_status(logger, __lock_status)


##########################################################################


@task(bind=True, name='gis_worker_tasks.initial_mapping', max_retries=5)
def initial_mapping(self):

    # Create logger to log messages to specific log file
    __logger = get_task_logger(__name__)

    try:

        # Get instance of Redis Database and GDAL instance
        __lib = get_libraries()

        # Create identifier from task_id
        __identifier = self.request.id

        # Execute new initial mapping generation
        create_initial_mapping(__identifier, __lib[0], __logger)

        # Close redis
        __lib[0].exit()

    except Exception as e:

        # Print error message
        print_to_logger({
            'error': [
                '* ------------ Errors -------------\n',
                str(e.message if e.message != '' else e)
            ],
            'warn': [],
            'info': []
        }, __logger)

        # Retry task (max 5) to wait for loading libraries
        if self.request.retries < 5:
            raise self.retry(
                exc='', countdown=(self.request.retries + 1) * 20
            )


@task(bind=True, name='gis_worker_tasks.update_mapping', max_retries=5)
def update_mapping(self):

    # Create logger to log messages to specific log file
    __logger = get_task_logger(__name__)

    try:

        # Get instance of Redis Database and GDAL instance
        __lib = get_libraries()

        # Create identifier from task_id
        __identifier = self.request.id

        # Remove previous mapping
        __lib[0].del_initial_mapping(__identifier)

        # Execute new initial mapping generation
        create_initial_mapping(__identifier, __lib[0], __logger)

        # Close redis
        __lib[0].exit()

    except Exception as e:

        # Print error message
        print_to_logger({
            'error': [
                '* ------------ Errors -------------\n',
                str(e.message if e.message != '' else e)
            ],
            'warn': [],
            'info': []
        }, __logger)

        # Retry task (max 5) to wait for loading libraries
        if self.request.retries < 5:
            raise self.retry(
                exc='', countdown=(self.request.retries + 1) * 20
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
