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


import os
import sys
import json
import shutil
from os.path import splitext
from celery.task import task
from celery.utils.log import get_task_logger
from gis_worker_helpers.geo_worker_gis import WorkerGIS
from gis_worker_helpers.geo_worker_xml import WorkerXML
from gis_worker_helpers.geo_worker_db import WorkerRedis

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


print_styles = ['info', 'warn', 'error']


def get_configuration_file():
    """ This function allows you to load a configuration from file.

    Returns:
         dict: configuration fields and values.

    """

    # Configuration folder
    __config_base_path = './gis_worker_config'
    __debug = False

    # Check if application is on Debug mode
    if int(os.environ.get('GEO_WORKER_DEBUG', 1)) == 1:

        # Get development configuration
        __config_path = os.environ.get(
            'GEO_WORKER_CFG_DEV', __config_base_path + '/config_debug.json'
        )

        # Set debug flag
        __debug = True

    else:

        # Get production configuration
        __config_path = os.environ.get(
            'GEO_WORKER_CFG_PROD', __config_base_path + '/config_production.json'
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


def get_redis_instance():
    """ This function allows to configure the database to use
        it from the Celery workers of this project or from CLI.

    Returns:
        class: Redis Worker

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
        it from the Celery workers of this project or from CLI.

    Returns:
        class: GIS Worker

    """

    # Create instance of GDAL methods
    __gdal_lib = WorkerGIS()

    # Check if libraries are good imported
    if not __gdal_lib.status:
        raise Exception(
            'GIS tools are not available at PATH.\n * Please, '
            'check your Geokettle configuration\n * and be sure '
            'that GDAL libraries are\n * installed correctly and '
            'the version is\n * greater than 2.2.0'
        )

    return __gdal_lib


def get_libraries():
    """ This function allows to configure the database and the GDAL
        libraries to use them from the Celery workers of this project.

    Returns:
        tuple: Redis Worker and GIS Worker classes

    """

    return get_redis_instance(), get_gdal_instance()


##########################################################################


def print_to_logger(messages, logger=None):
    """ This function allows to print messages to the logger or
        stdout with print function.

    Args:
        messages (dict): information from outputs
        logger (Logger): logger class to write messages

    """

    # Set prefix for all messages
    __prefix = '\n * '
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
    for __k in print_styles:

        # Detect if there are any messages
        if len(messages[__k]):

            # Print jump depending on logger
            if logger is None:
                print('')
            else:
                __logger_msg[__k] += '\n'

            # Log messages
            for __m in messages[__k]:

                # Print / save messages depending on logger
                if logger is None:
                    print(' * [' + __prefix_kind[__k] + '] ' + __m)
                else:
                    __logger_msg[__k] += __prefix + __m

    # Print jump / messages depending on logger
    if logger is not None:

        # Iterate kind of messages
        for __k in print_styles:

            # Detect if there are any messages
            if len(__logger_msg[__k]):

                # Print messages
                getattr(logger, __k)(__logger_msg[__k] + '\n')


def print_not_found_message():
    """ This function returns a message when identifier
        is not found on the database.

    Returns:
        dict: Information structure with error

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


def print_error_extension():
    """ This function returns a message when
        file has not valid extension.

    Returns:
        dict: Information structure with error

    """

    return {
        'error': [
            'Extension is not valid. Please, check the file path.'
        ],
        'warn': [],
        'info': []
    }


def print_worker_status(status, logger=None):
    """ This function allows to print a specific message depending on
        returned Celery worker's status.

    Args:
        status (int): kind of task's status
        logger (Logger): logger class to write messages

    Returns:
        dict: Information structure with error

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
    """ This function allows print errors to logger.

    Args:
        messages (dict): information from outputs
        logger (Logger): logger class to write messages

    Returns:
        dict: Information structure with error

    """

    # Print messages
    print_to_logger({
        'error': messages,
        'warn': [],
        'info': []
    }, logger)


##########################################################################


def transform_with_path(path, ext_dst, logger):
    """ This function transforms a gis or geometries path to
        other kind of geometry through GDAL libraries.

    Args:
        path (string): file's path
        ext_dst (string): extension of transformation
        logger (Logger): logger class to write messages

    Return:
        dict: information about the outputs and status code

    """

    # Transform resource and return result
    __t_info, __ln_info, __lmd5_info, __li_info, __fn_info = \
        get_gdal_instance().transform(path, ext_dst)

    # Detect if external logger was activated
    if logger is None:
        if len(__t_info['error']):
            __t_info['error'] = [
                '* ------------ Errors -------------\n'
            ] + __t_info['error']
        if len(__t_info['warn']):
            __t_info['warn'] = [
                '* ----------- Warnings ------------\n'
            ] + __t_info['warn']
        if __fn_info is not None and len(__fn_info['raw']):
            __t_info['info'] = [
               '* ------------ Fields -------------\n'
            ]
            for __fn in __fn_info['raw']:
                __t_info['info'] += __fn

        # Log messages to stdout
        print_to_logger(__t_info, logger)

    # Return status code and messages
    return {
        'status': 2,
        'messages': __t_info
    } if len(__t_info['error']) else {
        'status': 0,
        'messages': __t_info,
        'information': {
            'names': __ln_info,
            'names_md5': __lmd5_info,
            'properties': __li_info['info'],
            'fields': __fn_info['info']
        }
    }


def transform_with_id(identifier, ext_dst, rd, logger):
    """ This function transforms a gis or geometries path to
        other kind of geometry through GDAL libraries.

    Args:
        identifier (string): task internal id
        ext_dst (string): extension of transformation
        rd (WorkerRedis): instance of WorkerRedis
        logger (Logger): logger class to write messages

    Return:
        dict: information about the outputs and status code

    """

    # Check if database has metadata for this identifier
    if rd.check_existence(identifier, 'files'):

        # Get extension about the specific identifier
        __f_ext = rd.redis['files'].hget(
            identifier, 'extension'
        )

        # Generate path
        __config = get_configuration_file()
        __path = __config['folder'] + os.sep + \
            identifier + os.sep + identifier + \
            '.' + __f_ext

        # Transform resource and get result
        return transform_with_path(__path, ext_dst, logger)

    else:

        # Return not found message
        return {'status': 1, 'messages': print_not_found_message()}


def transform_revert_with_id(identifier):
    """ This function deletes generated files from
        a custom transformation for specific identifier.

    Args:
        identifier (string): task internal id

    """

    # Generate path
    __config = get_configuration_file()
    __path = __config['folder'] + os.sep + \
        identifier + os.sep
    __path_shp = __path + 'shp' + os.sep
    __path_trs = __path + 'trs' + os.sep

    # Check Shapefile path exists
    if os.path.isdir(__path_shp):

        # Remove directory
        shutil.rmtree(__path_shp)

    # Check transformation path exists
    if os.path.isdir(__path_trs):

        # Remove directory
        shutil.rmtree(__path_trs)

    # Remove any GeoJSON VRT file:
    for __f in os.listdir(__path):

        # Get extension from path
        __file_ext = '.'.join(__f.split('.')[-2:]) \
            if len(__f.split('.')) > 2 \
            else os.path.splitext(__f)[1]

        # Check extension
        if __file_ext == '.vrt':
            os.remove(__path + __f)


def info_with_path(path, logger, inc_layers=False):
    """ This function gets information from metadata
        gis or geometries file through GDAL libraries.

    Args:
        path (string): file's path
        logger (Logger): logger class to write messages
        inc_layers (bool): flag to include layers' name

    Return:
        dict: information about the outputs and status code

    """

    # Get information resource and return result
    __t_info = get_gdal_instance().get_info(path, inc_layers)

    # Detect if external logger was activated
    if logger is None:
        if len(__t_info['error']):
            __t_info['error'] = [
                '* ------------ Errors -------------\n'
            ] + __t_info['error']
        if len(__t_info['warn']):
            __t_info['warn'] = [
                '* ----------- Warnings ------------\n'
            ] + __t_info['warn']
        if len(__t_info['info']):
            __t_info['info'] = [
                '* --------- Information -----------\n'
            ] + __t_info['info']

        # Log messages to stdout
        print_to_logger(__t_info, logger)

    # Return status code and messages
    return {
        'status': 2 if len(__t_info['error']) else 0,
        'messages': __t_info
    }


def fields_with_path(path, logger, inc_layers=False):
    """ This function gets information from metadata
        fields about gis or geometries file through
        GDAL libraries.

    Args:
        path (string): file's path
        logger (Logger): logger class to write messages
        inc_layers (bool): flag to include layers' name

    Return:
        dict: information about the outputs and status code

    """

    # Get information resource and return result
    __t_info = get_gdal_instance().get_fields(path, inc_layers)

    # Detect if external logger was activated
    if logger is None:
        if len(__t_info['error']):
            __t_info['error'] = [
                '* ------------ Errors -------------\n'
            ] + __t_info['error']
        if len(__t_info['warn']):
            __t_info['warn'] = [
                '* ----------- Warnings ------------\n'
            ] + __t_info['warn']
        if len(__t_info['info']):
            __t_info['info'] = [
               '* ------------ Fields -------------\n'
            ] + __t_info['info']

        # Log messages to stdout
        print_to_logger(__t_info, logger)

    # Return status code and messages
    return {
        'status': 2 if len(__t_info['error']) else 0,
        'messages': __t_info
    }


def execute_geo_job_with_path(path, logger, checks):
    """ This function gets information from GeoKettle XML file
        job, executes it and throws any possible issue
        or good information from its execution.

    Args:
        path (string): file's path
        logger (Logger): logger class to write messages
        checks (bool): checking flag

    Return:
        dict: information about the outputs and status code

    """

    # Get extension from path
    __ext_src = '.'.join(path.split('.')[-2:]) \
        if len(path.split('.')) > 2 \
        else splitext(path)[1]

    # Get information about XML file
    __t_info = WorkerXML().check_job(path, checks) \
        if __ext_src == '.kjb' else print_error_extension()

    # Check if there is any error
    if not len(__t_info['error']):

        # Execute job with GeoKettle
        __tj_info = get_gdal_instance()
        __tj_info = __tj_info.execute_geo_job(path)

        # Check if it was some error
        if len(__tj_info['error']):

            __t_info['info'] = []
            __t_info['warn'] = []
            __t_info['error'] = __tj_info['error']

        else:

            __t_info['error'] = []
            __t_info['info_e'][-1] += '\n'
            __t_info['info_s'][-1] += '\n'
            __t_info['info_f'][-1] += '\n'
            __t_info['info'] = [
                '* ----------- Entries -------------\n'
            ] + __t_info['info_e'] + [
                '* ------------ Steps --------------\n'
            ] + __t_info['info_s'] + [
                '* ------------ Folders ------------\n'
            ] + __t_info['info_f']
            if len(__tj_info['info']):
                __t_info['info'] += [
                    '* ------------- Stats -------------\n'
                ] + __tj_info['info']
            __t_info['warn'] += __tj_info['warn']

    # Detect if external logger was activated
    if logger is None:
        if len(__t_info['error']):
            __t_info['error'] = [
                '* ------------ Errors -------------\n'
            ] + __t_info['error']
        if len(__t_info['warn']):
            __t_info['warn'] = [
                '* ----------- Warnings ------------\n'
            ] + __t_info['warn']

        # Log messages to stdout
        print_to_logger(__t_info, logger)

    # Return status code and messages
    return {
        'status': 2 if len(__t_info['error']) else 0,
        'messages': __t_info
    }


def execute_geo_job_with_id(identifier, rd, logger):
    """ This function gets information from task identifier.
        It executes the possible GeoKettle XML job linked to
        this specific task and throws any possible issue
        or good information from its execution.

    Args:
        identifier (string): task internal id
        rd (WorkerRedis): instance of WorkerRedis
        logger (Logger): logger class to write messages

    Return:
        dict: information about the outputs and status code

    """
    # Check if database has metadata for this identifier
    if rd.check_existence(identifier, 'files'):

        # Get information about the specific identifier
        __f_info = rd.redis['files'].hgetall(identifier)

        # Generate path
        __config = get_configuration_file()
        __path = __config['folder'] + os.sep + \
            identifier + os.sep + __f_info['name'] + \
            __f_info['extension']

        # Transform resource and get result
        return execute_geo_transform_with_path(
            __path, logger, False
        )

    else:

        # Return not found message
        return {'status': 1, 'messages': print_not_found_message()}


def execute_geo_transform_with_path(path, logger, checks):
    """ This function gets information from GeoKettle XML file
        transformation, executes it and throws any possible issue
        or good information from its execution.

    Args:
        path (string): file's path
        logger (Logger): logger class to write messages
        checks (bool): checking flag

    Return:
        dict: information about the outputs and status code

    """

    # Get extension from path
    __ext_src = '.'.join(path.split('.')[-2:]) \
        if len(path.split('.')) > 2 \
        else splitext(path)[1]

    # Get information about XML file
    __t_info = WorkerXML().check_transform(path, checks) \
        if __ext_src == '.ktr' else print_error_extension()

    # Check if there is any error
    if not len(__t_info['error']):

        # Execute job with GeoKettle
        __tj_info = get_gdal_instance()
        __tj_info = __tj_info.execute_geo_transform(path)

        # Check if it was some error
        if len(__tj_info['error']):

            __t_info['info'] = []
            __t_info['warn'] = []
            __t_info['error'] = __tj_info['error']

        else:

            __t_info['error'] = []
            __t_info['info_s'][-1] += '\n'
            __t_info['info_f'][-1] += '\n'
            __t_info['info'] = [
                '* ------------ Steps --------------\n'
            ] + __t_info['info_s'] + [
                '* ------------ Folders ------------\n'
            ] + __t_info['info_f'] + [
                '* ------------- Stats -------------\n'
            ] + __tj_info['info']
            __t_info['warn'] += __tj_info['warn']

    # Detect if external logger was activated
    if logger is None:
        if len(__t_info['error']):
            __t_info['error'] = [
                '* ------------ Errors -------------\n'
            ] + __t_info['error']
        if len(__t_info['warn']):
            __t_info['warn'] = [
                '* ----------- Warnings ------------\n'
            ] + __t_info['warn']

        # Log messages to stdout
        print_to_logger(__t_info, logger)

    # Return status code and messages
    return {
        'status': 2 if len(__t_info['error']) else 0,
        'messages': __t_info
    }


def execute_geo_transform_with_id(identifier, rd, logger):
    """ This function gets information from task identifier.
        It executes the possible GeoKettle XML transformation
        linked to this specific task and throws any possible
        issue or good information from its execution.

    Args:
        identifier (string): task internal id
        rd (WorkerRedis): instance of WorkerRedis
        logger (Logger): logger class to write messages

    Return:
        dict: information about the outputs and status code

    """

    # Check if database has metadata for this identifier
    if rd.check_existence(identifier, 'files'):

        # Get information about the specific identifier
        __f_info = rd.redis['files'].hgetall(identifier)

        # Generate path
        __config = get_configuration_file()
        __path = __config['folder'] + os.sep + \
            identifier + os.sep + __f_info['name'] + \
            __f_info['extension']

        # Transform resource and get result
        return execute_geo_transform_with_path(
            __path, logger, False
        )

    else:

        # Return not found message
        return {'status': 1, 'messages': print_not_found_message()}


##########################################################################


def init_mapping(identifier, rd, logger):
    """ This function allows create or update an initial mapping
        on the database for a specific identifier.

    Args:
        identifier (string): task internal id
        rd (WorkerRedis): instance of WorkerRedis
        logger (Logger): logger class to write messages

    """

    # Remove previous files
    transform_revert_with_id(identifier)

    # Lock the execution for this task. In this case we will use
    # the Redis SETNX to ensure that other remote machines won't do
    # the same task.
    __lock_status = rd.lock(identifier, 'mapping-i')

    # Check status of the lock
    if __lock_status == 0:

        # Transform to Shapefile
        __o_info = transform_with_id(
            identifier, '.shp', rd, logger
        )

        # Flags for errors
        __flag_error = __o_info['status'] == 2
        __flag_not_exist = __o_info['status'] == 1

        # Detect flags
        if not __flag_not_exist and not __flag_error:

            # Save messages
            for __k in print_styles:
                if len(__o_info['messages'][__k]):
                    rd.save_record_log(
                        identifier, 'mapping-i', __k,
                        __o_info['messages'][__k]
                    )

            # Delete previous values
            rd.remove_records(identifier)

            # Save information from layers
            rd.save_record_info(
                identifier,
                __o_info['information']['names'],
                __o_info['information']['names_md5'],
                __o_info['information']['properties']
            )

            # Save fields from layers
            rd.save_record_fields(
                identifier,
                __o_info['information']['names'],
                __o_info['information']['fields']
            )

            # Save status for tracking success
            rd.save_record_status(
                identifier,
                'mapping-i', 0
            )

        # Detect error flag
        if __flag_error:

            # Save error messages
            if len(__o_info['messages']['error']):
                rd.save_record_log(
                    identifier, 'mapping-i', 'error',
                    __o_info['messages']['error']
                )

            # Save status for tracking success
            rd.save_record_status(
                identifier, 'mapping-i', 1
            )

            # Remove generated files
            transform_revert_with_id(identifier)

        if __flag_not_exist:

            # Show not found message
            print_to_logger(
                print_not_found_message(), logger
            )

        # Release lock
        rd.unlock(identifier + ':mapping-i', True)

    else:

        # Log status
        print_worker_status(__lock_status, logger)


##########################################################################


@task(bind=True, name='gis_worker_tasks.create_mapping', max_retries=5)
def create_mapping(self):
    """ This function allows create an initial mapping
        from a specific task from AMQP messages.

    """

    # Create logger to log messages to specific log file
    __logger = get_task_logger(__name__)

    try:

        # Get instance of Redis Database instance
        __redis = get_redis_instance()

        # Create identifier from task_id
        __identifier = self.request.id

        # Execute new initial mapping generation
        init_mapping(__identifier, __redis, __logger)

        # Close redis
        __redis.exit()

    except Exception as e:

        __logger.info(e)

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


@task(bind=True, name='gis_worker_tasks.extend_mapping')
def extend_mapping(self):
    return None


@task(bind=True, name='gis_worker_tasks.default', max_retries=5)
def default(self):
    """ This function allows to receive the messages from
        the default queue from AMQP messages.

    """
    
    # Create logger to log messages to specific log file
    logger = get_task_logger(__name__)

    # Print message
    logger.warn('\n * Received task from default queue')
