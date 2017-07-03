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
from celery.utils.log import get_task_logger

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
    __config_base_path = '../geo_worker_config'
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

        # Get resources folder
        __dict['resources'] = '/opt/geo-resources/'
        
        return __dict


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

            # Check GDAL 2.1.0 version
            from osgeo import gdal
            version_num = int(gdal.VersionInfo('VERSION_NUM'))
            return version_num > 2000000

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
    __g_out, __g_err = exec_ogr_command(__arguments)

    return parse_ogr_return(__g_out, __g_err)


def cmd_ogrinfo(arguments):
    """ This function executes an ogrinfo command.

    Returns:
        Triple: Return parsed output, errors and exit code.

    """

    # Extend arguments with ogr executable
    __arguments = ['ogrinfo', '-al', '-so'] + arguments

    # Execute GDAL commands
    __g_out, __g_err = exec_ogr_command(__arguments)
    
    return parse_ogr_return(__g_out, __g_err)


def exec_ogr_command(arguments):
    """ This function executes an ogr command through subprocess.

    Returns:
        Triple: Return output, errors and exit code of the process.

    """

    # Create process
    __proc = Popen(arguments, stdout=PIPE, stderr=PIPE)

    # Execute process
    __proc_out, __proc_err = __proc.communicate()

    return __proc_out, __proc_err


def get_ogr_driver(extension):
    """ This function allows to get the driver by extension.

    Returns:
        String: Return specific driver.

    """

    # TODO: extend this list for other extensions
    if extension == 'shp':
        return 'ESRI Shapefile'
    else:
        return ''


def check_ogr_fields(file_path, fields, extension):
    """ This function check the fields of specific Geospatial file.

    Returns:
        Dict: Return information about the fields.

    """

    # Get kind of file depending on final extension
    __driver = get_ogr_driver(extension)

    # Create data structure of fields
    __fields = [
        __f[:__f.index(':')] for __f in fields
    ]

    # Create data structure for empty properties
    __fields_null = {}

    # Get layer from OGR Tools to check if
    # there is any field is null or empty, so
    # must be deleted, this file is opened as
    # DataSource Read-Write (1)
    from osgeo import ogr
    __file = ogr.GetDriverByName(__driver)
    __file_src = __file.Open(file_path, 1)
    __file_layer = __file_src.GetLayer()

    # Iterate over features of the layer
    for __file_feat in __file_layer:

        # Set index for fields
        __index = -1

        # Iterate over fields of the Shapefile
        for __f_index in range(len(__fields)):

            # Check if field is True (has value)
            if __fields[__f_index] in __fields_null:
                if __fields_null[__fields[__f_index]]:
                    continue

            # Get if the feature has value
            __fields_null[__fields[__f_index]] = \
                __file_feat.IsFieldSetAndNotNull(__fields[__f_index])

    # Remove empty fields from Shapefile
    __f_pad = 0
    for __field in __fields:
        if not __fields_null[__field]: 
            __file_layer.DeleteField(
                __fields.index(__field) - __f_pad
            )
            __f_pad += 1

    # Return only not empty fields
    return [
        __field for __field in __fields_null
        if __fields_null[__field]
    ]


def parse_ogr_return(outputs, errors):
    """ This function parses the both outputs from ogr execution.

    Returns:
        Dict: Return information about the outputs.

    """

    # Create temporal output log
    __output = outputs.split('\n')

    # Create temporal error log
    __errors = errors.split('\n')

    # Search failures at output or errors
    __error = []
    for __o in range(len(__output)):
        if 'FAILURE' in __output[__o]:
            __error.append(__output[__o + 1])
    for __o in range(len(__errors)):
        if 'FAILURE' in __errors[__o]:
            __error.append(__errors[__o + 1])

    # Remove empty lines and search only properties
    # from ogrinfo output
    __output = [
        __o for __o in __output
        if __o != '' and ':' in __o and __o[-1] != ':'
        and 'INFO' not in __o
    ]

    # Remove empty lines and save only warnings
    __warning = [
        __e[__e.index(':') + 2:] for __e in __errors
        if 'Warning' in __e and __e != ''
    ]

    # Remove empty lines and save only errors
    __error += [
        __e[__e.index(':') + 2:] for __e in __errors
        if 'ERROR' in __e and __e != ''
    ]

    # Remove duplicates
    __error = list(set(__error))

    return {
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

        # Get current configuration
        self.config = get_configuration_file() 

        # Set status of GIS configuration
        self.status = check_geokettle_path() and check_gdal_path()

        if self.status:

            # Create logger for this Python script
            self.logger = get_task_logger(__name__)

    def transform(self, identifier, file_name, extension_src, extension_dst):

        # Get kind of file depending on final extension
        __driver = get_ogr_driver(extension_dst)

        # Create full path
        __file_path = self.config['resources'] + identifier + '/'

        if self.config['debug']:
            self.logger.warn(
                '\n * TRANSFORM ' + __file_path + file_name + ' ' + 
                '[' + extension_src + '] to [' + extension_dst + ']'
            )

        # Create arguments for transforming to Shapefile
        __command = [
            '-t_srs', 'EPSG:4326', '-f', __driver,
            __file_path + file_name + '.' + extension_dst, 
            __file_path + file_name + '.' + extension_src,
            '-explodecollections'
        ]

        return cmd_ogr2ogr(__command)

    def delete(self, identifier, file_name, extension):

        # Get list of extensions from kind of file
        # TODO: extend this list for other extensions
        if extension == 'shp':
            __list = [
                '.shp', '.shx', '.shx', '.prj', '.sbn', '.sbx',
                '.dbf', '.fbn', '.fbx', '.ain', '.aih', '.shp.xml'
            ]
        else:
            __list = []

        # Join extensions with file name
        __list = [file_name + __l for __l in __list]

        # Get all nodes from directory
        __path_files = os.listdir(self.config['resources'] + identifier)

        # Get intersection between files and list of possible files
        __path_files = set(__path_files).intersection(set(__list))

        # Remove found files
        __debug_log = ''
        for __path_file in __path_files:
            os.remove(
                self.config['resources'] + identifier + '/' + __path_file
            )

            if self.config['debug']:
                __debug_log += '\n * DELETED ' + self.config['resources'] + \
                    identifier + '/' + __path_file

        # Print log if debug flag
        if self.config['debug'] and len(__path_files):
            self.logger.warn(__debug_log)

    def get_info(self, identifier, file_name, extension):

        # Generate full path of the file
        __file_path = self.config['resources'] + \
            identifier + '/' + file_name + '.' + extension

        # Create arguments for getting information about file
        __command = [__file_path]

        # Get information when executes
        __info = cmd_ogrinfo(__command)

        # Only get fields for output
        __info['info'] = [
            __o for __o in __info['info'] 
            if 'Geometry:' in __o or 'Feature Count:' in __o
            or 'Extent: (' in __o
        ]

        return __info

    def get_fields(self, identifier, file_name, extension):

        # Generate full path of the file
        __file_path = self.config['resources'] + \
            identifier + '/' + file_name + '.' + extension

        # Create arguments for getting information about file
        __command = [__file_path]

        # Get information when executes
        __info = cmd_ogrinfo(__command)

        # Remove unnecessary information
        __info['info'] = [
            __o for __o in __info['info'] 
            if 'Geometry:' not in __o and 'Feature Count:' not in __o
            and 'Extent: (' not in __o and 'Layer name:' not in __o
        ]

        # Get fields from received information
        __old_fields = [
            __f[:__f.index(':')] for __f in __info['info']
        ]

        # Get information about fields
        __new_fields = check_ogr_fields(
            __file_path, __info['info'], extension
        )

        # Check if new fields is the same previous fields
        __diff = set(__old_fields).difference(set(__new_fields))
        if len(__diff):

            # Generate new fields information
            __info['info'] = {
                __f[:__f.index(':')]: __f[__f.index(':') + 2:].split(' ')[0]
                for __f in __info['info'] if __f[:__f.index(':')] in __new_fields
            }

            # Add new possible warning messages
            __info['warn'] += ['Removed field ' + __f +
                ' because is empty' for __f in __diff]

        else:

            # Generate new fields information
            __info['info'] = {
                __f[:__f.index(':')]: __f[__f.index(':') + 2:].split(' ')[0]
                for __f in __info['info'] if __f[:__f.index(':')] in __old_fields
            }

        return __info
