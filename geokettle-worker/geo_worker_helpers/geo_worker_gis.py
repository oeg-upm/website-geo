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
from subprocess import Popen, PIPE

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


def check_geokettle_path():
    """ This function detects if Geokettle executables are included
        on the current environment (PATH variable). This is important
        to avoid full path directories and to be compatible with Docker
        Geokettle Image.

    Returns:
        bool: Return True if "kitchen" and "pan" exist, False otherwise.

    """

    # Create split character depending on operative system
    path_split = ';' if 'win32' in sys.platform else ':'

    # Get folders from PATH variable
    path_dirs = os.environ.get('PATH').split(path_split)

    # Iterate over folders
    for path_dir in path_dirs:

        # Get all nodes from directory
        path_files = os.listdir(path_dir)

        # Return if kitchen and pan exists at the same folder
        if 'kitchen.sh' in path_files and 'pan.sh' in path_files:
            return True

    # executables were not found
    return False


def check_gdal_path():
    """ This function detects if GDAL executables are included
        on the current environment (PATH variable). This is important
        to avoid full path directories and to be sure that GDAL tools
        are available to execute them.

    Returns:
        bool: Return True if GDAL tools exist, False otherwise.

    """

    # Create split character depending on operative system
    path_split = ';' if 'win32' in sys.platform else ':'

    # Get folders from PATH variable
    path_dirs = os.environ.get('PATH').split(path_split)

    # Iterate over folders
    for path_dir in path_dirs:

        # Get all nodes from directory
        path_files = os.listdir(path_dir)

        # Return if kitchen and pan exists at the same folder
        if 'ogr2ogr' in path_files and 'ogrinfo' in path_files:
            return True

    # executables were not found
    return False


##########################################################################


def cmd_ogr2ogr(arguments):
    """ This function executes an ogr2ogr command.

    Returns:
        Triple: Return parsed output, errors and exit code.

    """

    # Extend arguments with ogr executable
    __arguments = ['ogr2ogr'] + arguments

    # Execute GDAL commands
    __g_out, __g_err, __g_exit = exec_ogr_command(__arguments)
    
    return parse_ogr_return(__g_out, __g_err, __g_exit)


def cmd_ogrinfo(arguments):
    """ This function executes an ogrinfo command.

    Returns:
        Triple: Return parsed output, errors and exit code.

    """

    # Extend arguments with ogr executable
    __arguments = ['ogrinfo', '-al', '-so'] + arguments

    # Execute GDAL commands
    __g_out, __g_err, __g_exit = exec_ogr_command(__arguments)
    
    return parse_ogr_return(__g_out, __g_err, __g_exit)


def exec_ogr_command(arguments):
    """ This function executes an ogr command through subprocess.

    Returns:
        Triple: Return output, errors and exit code of the process.

    """

    # Create process
    __proc = Popen(arguments, stdout=PIPE, stderr=PIPE)

    # Execute process
    __proc_out, __proc_err = __proc.communicate()

    # Get exit status
    __proc_exit = __proc.returncode

    return __proc_out, __proc_err, __proc_exit


def parse_ogr_return(outputs, errors, code):
    """ This function parses the both outputs from ogr execution.

    Returns:
        Dict: Return information about the outputs.

    """

    # Create temporal output log
    __output = outputs.split('\n')

    # Search failures at ogrinfo output
    __error = []
    for __o in range(len(__output)):
        if 'FAILURE' in __output[__o]:
            __error.append(__output[__o + 1])

    # Remove empty lines and search only properties
    # from ogrinfo output
    __output = [
        __o for __o in __output
        if __o != '' and ':' in __o and __o[-1] != ':'
        and 'INFO' not in __o
    ]

    # Create temporal error log
    __errors = errors.split('\n')

    # Remove empty lines and save only warnings
    __warning = [
        __e[__e.index(':') + 2:] for __e in __error
        if 'Warning' in __e and __e != ''
    ]

    # Remove empty lines and save only errors
    __error += [
        __e[__e.index(':') + 2:] for __e in __errors
        if 'ERROR' in __e and __e != ''
    ]

    return {
        'status': code,
        'info': __output,
        'warn': __warning,
        'error': __error
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


class WorkerGIS(object):
    """ This constructor creates only an instance of a GIS library
        for doing transformations or getting information from data
        following the singleton pattern (software design pattern).

    """

    # Create singleton instance
    __metaclass__ = Singleton

    def __init__(self):

        # Set status of GIS configuration
        self.status = check_geokettle_path() and check_gdal_path()      

    def transform_to_shp(self, identifier, extension):

        # Create arguments for transforming to Shapefile
        __command = [
            '-t_srs', 'EPSG:4326', '-f', 'ESRI Shapefile',
            identifier + '.shp', identifier + '.' + extension,
            '-explodecollections'
        ]

        return cmd_ogr2ogr(__command)

    def get_info(self, identifier, extension):

        # Create arguments for getting information about file
        __command = [identifier + '.' + extension]

        return cmd_ogrinfo(__command)

    def get_fields(self, identifier, extension):

        # Create arguments for getting information about file
        __command = [identifier + '.' + extension]

        # Get information when executes
        __info = cmd_ogrinfo(__command)

        # Only get fields for output
        __info['info'] = [
            __o for __o in __info['info'] 
            if 'Geometry:' not in __o and 'Feature Count:' not in __o
            and 'Extent: (' not in __o and 'Layer name:' not in __o
        ]

        return __info
