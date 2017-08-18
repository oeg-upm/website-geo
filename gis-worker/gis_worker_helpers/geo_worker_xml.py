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


def print_error_srs():
    """ This function returns a message when there is no
        SRS transformation on XML GeoKettle file.

        Return:
            Dict: Information structure with error
    """

    return {
        'error': [
            'EPSG:4326 transformation is not found. Please, '
            'check the file path.'
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

        # Get step from XML file
        __steps = xml_tree.findall('step')

        # Structure to save non valid steps
        __no_steps = []
        __valid_steps = []

        # Get allowed types for XML files
        __allowed_types = self.config['xml']['steps']

        # Iterate over steps
        for __step in __steps:

            # Get type if it exists
            __type_node = __step.find('type')

            # Get value of node
            if __type_node is not None:

                # Value of node
                __type = __type_node.text

                # Check if there is config
                # All allowed
                if not len(__allowed_types):
                    __valid_steps.append(__type)

                else:

                    # Check type is good
                    if __type not in __allowed_types:
                        __no_steps.append(__type)
                    else:
                        __valid_steps.append(__type)

        return __no_steps, __valid_steps

    def check_paths(self, xml_tree):

        # Structure to save non valid steps
        __no_steps = []
        __no_folders = []
        __valid_folders = []

        # Get allowed folders for XML files
        __allowed_folders = self.config['xml']['folders']

        # Iterate over steps
        for __step in xml_tree.findall('step'):

            # Check kind of step and children nodes
            __step_f = __step.find('filename')
            if __step_f is None:
                __step_f = __step.find('file')
            if __step_f is None:
                continue

            # Get filename node
            if __step_f.tag == 'filename':

                # Check node is valid
                if __step_f.text == '':
                    __no_steps.append(__step.find('type').text)
                    continue

                # Get folder without file
                __folder = os.path.dirname(__step_f.text)

                # Check if there is config
                if not len(__allowed_folders):
                    __valid_folders.append(__step_f.text)

                else:

                    # Check folder is good
                    if __folder not in __allowed_folders:
                        __no_folders.append(__step_f.text)

                    else:
                        __valid_folders.append(__step_f.text)

            # Get file node
            if __step_f.tag == 'file':

                # Get name node from node's children
                __step_n = __step_f.find('name')

                # Get extension node from node's children
                __step_e = __step_f.find('extention')

                print __step_n, __step_e

                # Check node is valid
                if __step_n is None or __step_e is None:
                    __no_steps.append(__step.find('type').text)
                    continue

                # Check node is valid
                if __step_n.text == '' or __step_e.text == '':
                    __no_steps.append(__step.find('type').text)
                    continue

                # Create path from values
                __step_f = __step_n.text + '.' + __step_e.text

                # Get folder without file
                __folder = os.path.dirname(__step_f)

                # Check if there is config
                if not len(__allowed_folders):
                    __valid_folders.append(__step_f)

                else:

                    # Check folder is good
                    if __folder not in __allowed_folders:
                        __no_folders.append(__step_f)

                    else:
                        __valid_folders.append(__step_f)

        return __no_steps, __no_folders, __valid_folders

    def check_srs(self, xml_tree):

        # Get step from XML file
        __steps = xml_tree.findall('step')

        # Create variable for transformation
        __step_t = None

        # Iterate over steps
        for __step in __steps:

            # Get type if it exists
            __step_type = __step.find('type')

            # Check if type is transformation
            if __step_type.text == 'SRSTransformation':
                __step_t = __step
                break

        # Check if type was found
        if __step_t is None:
            return False

        # Create variable for SRS
        __step_s = None

        # Iterate over transformation's children
        for __step in __step_t:

            # Get target if it exists
            if __step.tag == 'target_srs':
                __step_s = __step
                break

        # Check if target was found
        if __step_s is None:
            return False

        # Create flags for result
        __step_a = False
        __step_r = False

        # Iterate over SRS's children
        for __step in __step_s:

            # Check SRS's authority
            if __step.tag == 'authority' and \
               __step.text == 'EPSG':
                __step_a = True

            # Check SRS's code
            if __step.tag == 'srid' and \
               __step.text == '4326':
                __step_r = True

        return __step_a and __step_r

    def check_transform(self, path):

        # Check if path is a correct file and exists
        if not os.path.exists(path) or not os.path.isfile(path):

            return print_error_not_found()

        # Check vulnerabilities
        if not self.check_issues(path):

            return print_error_vulnerabilities()

        # Parse XML object
        __xml_tree = xml.etree.ElementTree.parse(path)

        # Check if steps are valid
        __no_steps, __valid_steps = self.check_steps(__xml_tree)
        if len(__no_steps):

            return print_error_steps(__no_steps)

        # Check if there is any folder and they are valid
        __no_steps, __no_folders, __valid_folders = \
            self.check_paths(__xml_tree)

        if len(__no_steps):

            return print_error_steps(__no_steps)

        if len(__no_folders):

            return print_error_paths(__no_folders)

        # Check if there is a mandatory target SRS
        if not self.check_srs(__xml_tree):

            return print_error_srs()

        # Create return structure
        __return = {
            'info': [], 'warn': [], 'error': []
        }

        if len(__valid_steps):

            # Add header message
            __return['info'].append(
                '* ------------ Steps --------------\n'
            )

            for __step in __valid_steps:

                # Append message
                __return['info'].append(
                    'The ' + __step + ' execution was allowed.'
                )

        if len(__valid_folders):

            # Add header message
            __return['info'][-1] += '\n'
            __return['info'].append(
                '* ------------ Folders ------------\n'
            )

            for __folder in __valid_folders:

                # Append message
                __return['info'].append(
                    'Access to ' + __folder + ' was allowed.'
                )

        return __return
