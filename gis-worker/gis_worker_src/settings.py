#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Ontology Engineering Group
        http://www.oeg-upm.net/
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Copyright (C) 2017 Ontology Engineering Group.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  GeoLinkeddata Open Data Portal is licensed under a
  Creative Commons Attribution-NC 4.0 International License.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
"""

import os
import sys
import json

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


kind_logs = ['info', 'warn', 'error']


##########################################################################


def dump_messages(logger, messages):
    """ This function allows to print messages to the logger or
        stdout with print function.

    Args:
        logger (Logger): logger class to write messages
        messages (dict): information from outputs

    """

    # Set prefix for all messages
    __prefix = '\n * '

    # Save messages to logger
    __logger_msg = {
        'info': '',
        'warn': '',
        'error': ''
    }

    # Iterate kind of messages
    for __k in kind_logs:
        if len(messages[__k]):

            # Print jump if there is any message
            __logger_msg[__k] += '\n'

            # Save messages to structure
            for __m in messages[__k]:
                __logger_msg[__k] += \
                    __prefix + __m

    for __k in kind_logs:
        if len(__logger_msg[__k]):

            # Print messages
            getattr(logger, __k)(__logger_msg[__k] + '\n')


def generate_error_java_exception(message):
    """ This function returns a message when
        java from GeoKettle raise an exception.

    Args:
        message (string): Java backtrace message

    Returns:
        dict: Information structure with error

    """

    return {
        'error': [
            'Java Exception was raised from GeoKettle.',
            'Check the file on GeoKettle standalone version.',
            message
        ],
        'warn': [],
        'info': []
    }


def generate_error_duplicated_transformation():
    """ This function returns a message when
        transformation is already at the same folder
        of the current transformation

    Returns:
        dict: Information structure with error

    """

    return {
        'error': [
            'Delete the previous transformation before proceed.'
        ],
        'warn': [],
        'info': []
    }


def generate_error_file_not_found():
    """ This function returns a message when file is
        not found.

    Returns:
        dict: Information structure with error

    """

    return {
        'error': [
            'File is not found. Please, check the file path.'
        ],
        'warn': [],
        'info': []
    }


def generate_error_identifier_not_found():
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


def generate_error_extension_not_valid():
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


def generate_error_xml_node_not_found(tag):
    """ This function returns a message when there is
        no nodes on XML GeoKettle file.

    Args:
        tag (string): kind of node

    Returns:
        dict: Information structure with error

    """

    return {
        'error': [
            'There was an error at checking file path. Please, '
            'review it because no ' + tag + ' were found.'
        ],
        'warn': [],
        'info': []
    }


def generate_error_xml_node_srs_error():
    """ This function returns a message when there is
        no SRS transformation on XML GeoKettle file.

    Returns:
        dict: Information structure with error

    """

    return {
        'error': [
            'EPSG:4326 transformation is not found. Please, '
            'check the file path.'
        ],
        'warn': [],
        'info': []
    }


def generate_error_xml_nodes_invalid(nodes, tag):
    """ This function returns a message when a node
        or nodes are not valid at a XML GeoKettle file.

    Args:
        nodes (list): nodes not allowed
        tag (string): kind of node


    Returns:
        dict: Information structure with error


    """

    # Create error structure
    __error = []

    # Iterate over steps list
    for __node in nodes:

        # Append message
        __error.append('The ' + __node + ' ' + tag + ' is not allowed.')

    # Append last message
    __error.append('Please, review configuration or XML file.')

    return {
        'error': __error,
        'warn': [],
        'info': []
    }


def generate_error_xml_path_invalid(paths):
    """ This function returns a message when a path
        or paths are not valid at a XML GeoKettle file.

    Returns:
        dict: Information structure with error

    """

    # Create error structure
    __error = []

    # Iterate over steps list
    for __path in paths:

        # Append message
        __error.append(__path + ' is not allowed for GeoKettle.')

    # Append last message
    __error.append('Please, review configuration or filesystem permissions.')

    return {
        'error': __error,
        'warn': [],
        'info': []
    }


def generate_error_xml_vulnerabilities():
    """ This function returns a message when XML file
        has or might have vulnerabilities or exploits.

    Returns:
        dict: Information structure with error

    """

    return {
        'error': [
            'Might be vulnerabilities or errors on this XML file.',
            'Check this website: https://docs.python.org/2/'
            'library/xml.html#xml-vulnerabilities'
        ],
        'warn': [],
        'info': []
    }


class WorkerLogger(object):

    def info(self, message):
        print(' * [INFO] ' + message)

    def warn(self, message):
        print(' * [WARN] ' + message)

    def error(self, message):
        print(' * [ERROR] ' + message)


class Config(object):

    def __init__(self):

        def check_resources_folder(path):
            """ This function allows you to check if the
                path is accessible. If it is False, it will
                create the folder for the application.

            Args:
                path (string): path of the folder

            """

            try:

                # Create directory directly
                os.makedirs(path)
                return True
            except OSError:

                # If the directory does not exist
                if not os.path.isdir(path):
                    raise Exception(
                        'Check the resources folder: ' + path
                    )
                return True

        def get_configuration_file():
            """ This function allows you to load a configuration from file.

            Returns:
                 dict: configuration fields and values.

            """

            # Configuration folder
            __config_path = os.path.dirname(os.path.realpath(__file__)) + \
                os.sep + 'configuration.json'

            # Open file to load configuration
            with open(__config_path) as __file_data:

                # Return dictionary as configuration
                __dict = dict(json.load(__file_data))
                return __dict

        # Get configuration for the current instance
        settings = get_configuration_file()
        self.debug = settings['debug']

        # UPLOAD CONFIGURATION
        if check_resources_folder(settings['upload']['folder']):
            self.upload_folder = settings['upload']['folder']
        self.upload_mime = settings['upload']['types']
        self.upload_drivers = settings['upload']['drivers']

        # CELERY CONFIGURATION
        self.celery_port = settings['celery']['port']
        self.celery_host = settings['celery']['url'] if self.celery_port == 80 or \
            self.celery_port == 443 else settings['celery']['url'] + \
            ':' + str(self.celery_port)
        self.celery_user = settings['celery']['username']
        self.celery_pwd = settings['celery']['password']

        # XML CONFIGURATION
        self.xml_allowed_steps = settings['xml']['steps']
        self.xml_allowed_entries = settings['xml']['entries']
        self.xml_allowed_paths = settings['xml']['folders']
        self.xml_special_paths = [
            '${Internal.Transformation.Filename.Directory}',
            '${Internal.Job.Filename.Directory}'
        ]

        # DATABASE CONFIGURATION
        self.redis_worker = settings['redis_worker']
