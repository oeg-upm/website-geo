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
import shutil
from os.path import splitext
from celery.task import task
from gis_worker_src import settings
from celery.utils.log import get_task_logger
from gis_worker_src.gis import WorkerGIS
from gis_worker_src.xml import WorkerXML
from gis_worker_src.database import WorkerRedis

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
    if __redis_db.redis is None:
        raise Exception('Bad redis configuration or not running')

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


def transform_with_path(path, extension, logger):
    """ This function transforms a gis or geometries path to
        other kind of geometry through GDAL libraries.

    Args:
        path (string): file's path
        extension (string): extension of transformation
        logger (Logger): logger class to write messages

    Return:
        dict: information about the outputs and status code

    """

    # Transform resource and return result
    __t_info, __ln_info, __lmd5_info, __li_info, __fn_info = \
        get_gdal_instance().transform(path, extension)

    # Detect if logger is not Celery logger
    if isinstance(logger, settings.WorkerLogger):
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

        # Log messages
        settings.dump_messages(logger, __t_info)

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


def transform_with_id(identifier, information, logger):
    """ This function transforms a gis or geometries path to
        other kind of geometry through GDAL libraries.

    Args:
        identifier (string): task internal id
        information (dict): information about task
        logger (Logger): logger class to write messages

    Return:
        dict: information about the outputs and status code

    """

    # Generate path from configuration
    __path = config.upload_folder + os.sep + \
        identifier + os.sep + information['filename'] + \
        information['extension']

    # Transform resource and get result
    return transform_with_path(__path, '.shp', logger)


def transform_revert_with_id(identifier):
    """ This function deletes generated files from
        a custom transformation for specific identifier.

    Args:
        identifier (string): task internal id

    """

    # Generate path
    __path = config.upload_folder + os.sep + \
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

        # Check extension
        if os.path.splitext(__f)[1] == '.vrt':
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

    # Detect if logger is not Celery logger
    if isinstance(logger, settings.WorkerLogger):
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

        # Log messages
        settings.dump_messages(logger, __t_info)

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

    # Detect if logger is not Celery logger
    if isinstance(logger, settings.WorkerLogger):
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

        # Log messages
        settings.dump_messages(logger, __t_info)

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

    # Get information about XML file
    __t_info = WorkerXML().check_job(path, checks) \
        if splitext(path)[1] == '.kjb' else \
        settings.generate_error_extension_not_valid()

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

    # Detect if logger is not Celery logger
    if isinstance(logger, settings.WorkerLogger):
        if len(__t_info['error']):
            __t_info['error'] = [
                '* ------------ Errors -------------\n'
            ] + __t_info['error']
        if len(__t_info['warn']):
            __t_info['warn'] = [
                '* ----------- Warnings ------------\n'
            ] + __t_info['warn']

        # Log messages
        settings.dump_messages(logger, __t_info)

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

    return


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

    # Get information about XML file
    __t_info = WorkerXML().check_transform(path, checks) \
        if splitext(path)[1] == '.ktr' else \
        settings.generate_error_extension_not_valid()

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

    # Detect if logger is not Celery logger
    if isinstance(logger, settings.WorkerLogger):
        if len(__t_info['error']):
            __t_info['error'] = [
                '* ------------ Errors -------------\n'
            ] + __t_info['error']
        if len(__t_info['warn']):
            __t_info['warn'] = [
                '* ----------- Warnings ------------\n'
            ] + __t_info['warn']

        # Log messages to stdout
        settings.dump_messages(logger, __t_info)

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

    return


##########################################################################


def init_mapping(identifier, logger):
    """ This function allows create or update an initial mapping
        on the database for a specific identifier.

    Args:
        identifier (string): task internal id
        logger (Logger): logger class to write messages

    """

    # Remove previous files
    transform_revert_with_id(identifier)

    # Get instance of Redis Database
    __redis = get_redis_instance()

    # Lock the execution for this task. In this case we will use
    # the Redis SETNX to ensure that other remote machines won't do
    # the same task.
    __lock_status = __redis.lock(identifier, 'mapping-i')

    # Check status of the lock
    if __lock_status == 0:

        # Get information about identifier
        __file_info = __redis.get_information(identifier)

        # Transform to Shapefile depending if
        # information is good or not
        __o_info = {
            'status': 1,
            'messages': settings.generate_error_identifier_not_found()
        } if __file_info is None else transform_with_id(
            identifier, __file_info, logger
        )

        # Flags for errors
        __flag_error = __o_info['status'] == 2
        __flag_not_exist = __o_info['status'] == 1

        # Detect flags
        if not __flag_not_exist and not __flag_error:

            # Save messages on database
            for __k in settings.kind_logs:
                if len(__o_info['messages'][__k]):
                    __redis.save_record_log(
                        identifier, 'mapping-i', __k,
                        __o_info['messages'][__k]
                    )

            # Delete previous values
            __redis.remove_records(identifier)

            # Save information from layers
            __redis.save_record_info(
                identifier,
                __o_info['information']['names'],
                __o_info['information']['names_md5'],
                __o_info['information']['properties']
            )

            # Save fields from layers
            __redis.save_record_fields(
                identifier,
                __o_info['information']['names'],
                __o_info['information']['fields']
            )

            # Save status for tracking success
            __redis.save_record_status(
                identifier,
                'mapping-i', 0
            )

        # Detect error flag
        if __flag_error:

            # Save error messages
            if len(__o_info['messages']['error']):
                __redis.save_record_log(
                    identifier, 'mapping-i', 'error',
                    __o_info['messages']['error']
                )

            # Save status for tracking success
            __redis.save_record_status(
                identifier, 'mapping-i', 1
            )

            # Remove generated files
            transform_revert_with_id(identifier)

        if __flag_not_exist:

            # Show not found message
            settings.dump_messages(
                logger, settings.generate_error_identifier_not_found()
            )

        # Release lock
        __redis.unlock(identifier + ':mapping-i', True)

    else:

        # Show lock status error
        __message = 'Skipped task ('
        __message += 'locked by other worker' if \
            __lock_status == 1 else 'finished by other worker'
        __message += ')'

        # Show lock status error
        settings.dump_messages(
            logger, {
                'info': [],
                'warn': [__message],
                'error': []
            }
        )


##########################################################################


@task(bind=True, name='gis_worker_tasks.create_mapping', max_retries=5)
def create_mapping(self, identifier):
    """ This function allows create an initial mapping
        from a specific task from AMQP messages.

    Args:
        self (Task): internal pointer to Celery task
        identifier (string): task internal id

    """

    # Create logger to log messages to specific log file
    __logger = get_task_logger(__name__)

    try:

        # Execute new initial mapping generation
        init_mapping(identifier, __logger)

    except Exception as e:

        # Dump messages to logger
        settings.dump_messages(__logger, {
            'error': [
                '* ------------ Errors -------------\n',
                str(e.message if e.message != '' else e)
            ],
            'warn': [],
            'info': []
        })

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

    Args:
        self (Task): internal pointer to Celery task

    """
    
    # Create logger to log messages to specific log file
    __logger = get_task_logger(__name__)

    # Dump messages to logger
    settings.dump_messages(__logger, {
        'error': [],
        'warn': [
            '* ----------- Warnings ------------\n',
            'Received task from default queue'
        ],
        'info': []
    })
