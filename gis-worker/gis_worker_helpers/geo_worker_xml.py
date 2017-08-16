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
import json
import xml.etree.ElementTree
import defusedxml.ElementTree

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


def print_error_vulnerabilities():
    """ This function returns a message when XML file has
        or might have vulnerabilities or exploits.

        Return:
            Dict: Information structure with error
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


def print_error_not_found():
    """ This function returns a message when file is not found.

        Return:
            Dict: Information structure with error
    """

    return {
        'error': [
            'File is not found. Please, check the file path.'
        ],
        'warn': [],
        'info': []
    }


def print_error_steps(steps):
    """ This function returns a message when a step or steps
        are not valid at a XML GeoKettle file.

        Return:
            Dict: Information structure with error
    """

    # Create error structure
    __error = []

    # Iterate over steps list
    for __step in steps:

        # Append message
        __error.append('The ' + __step + ' step is not allowed.')

    # Append last message
    __error.append('Please, review configuration or XML file.')

    return {
        'error': __error,
        'warn': [],
        'info': []
    }


def print_error_paths(paths):
    """ This function returns a message when a path or paths
        are not valid at a XML GeoKettle file.

        Return:
            Dict: Information structure with error
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


class WorkerXML(object):
    """ This constructor creates only an instance of a Object with
        some features and methods for XML files. These files are
        important because are the format for GeoKettle jobs and
        transformations.

    """

    # Create singleton instance
    __metaclass__ = Singleton

    def __init__(self):

        self.config = get_configuration_file()

    def check_issues(self, path):

        try:

            # defusedxml will only be used for check XML problems
            # because this library is slower than python library
            # https://docs.python.org/2/library/xml.html#xml-vulnerabilities
            return defusedxml.ElementTree.parse(path) is not None

        except Exception:
            return False

    def check_steps(self, xml_tree):

        # Get allowed types for XML files
        __allowed_types = self.config['xml']['steps']

        # Check if there is config
        if not len(__allowed_types):

            # Empty list ~ all allowed
            return []

        # Get step from XML file
        __steps = xml_tree.findall('step')

        # Structure to save non valid steps
        __no_steps = []

        # Iterate over steps
        for __step in __steps:

            # Check if step is allowed
            if __step not in __allowed_types:
                __no_steps.append(__step)

        return __no_steps

    def check_paths(self, xml_tree):

        # Get allowed folders for XML files
        __allowed_folders = self.config['xml']['folders']

        # Check if there is config
        if not len(__allowed_folders):

            # Empty list ~ all allowed
            return []

        # Get step from XML file
        __steps = xml_tree.findall('step')

        # Structure to save non valid steps
        __no_folders = []

        # Iterate over steps
        for __step in __steps:

            # Get filename if it exists
            __folder_node = __step.find('filename')

            # Get value of node
            if __folder_node is not None:

                # Value of node
                __folder = __folder_node.text

                # Get folder without file
                __folder = os.path.dirname(__folder)

                # Check folder is valid
                if __folder not in __allowed_folders:

                    # Add folder to structure
                    __no_folders.append(__folder)

            return __no_folders

    def check(self, path):

        # Check if path is a correct file and exists
        if not os.path.exists(path) or not os.path.isfile(path):

            return print_error_not_found()

        # Check vulnerabilities
        if not self.check_issues(path):

            return print_error_vulnerabilities()

        # Parse XML object
        __xml_tree = xml.etree.ElementTree.parse(path)

        # Check if steps are valid
        __no_steps = self.check_steps(__xml_tree)
        if len(__no_steps):

            return print_error_steps(__no_steps)

        # Check if there is any folder and they are valid
        __no_folders = self.check_paths(__xml_tree)
        if len(__no_folders):

            return print_error_paths(__no_folders)

        return None
