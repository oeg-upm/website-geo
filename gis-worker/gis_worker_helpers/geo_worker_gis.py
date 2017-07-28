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
import logging
from os.path import splitext
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
    __arguments = [
        'ogr2ogr', '-t_srs', 'EPSG:4326', '-f'
    ] + arguments + ['-explodecollections']

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
    if extension == '.shp':
        return 'ESRI Shapefile'
    else:
        return ''


def get_ogr_file_extensions(extension):
    """ This function allows to get the possible linked files
        with a specific extension file of geo-spatial data.

    Returns:
        List: Return group of extensions.

    """

    # Define group of extensions files
    # TODO: extend this list of list for other extensions
    __extensions = [

        # Shapefile -> shp
        [
            '.shp', '.shx', '.shx', '.prj', '.sbn', '.sbx',
            '.dbf', '.fbn', '.fbx', '.ain', '.aih', '.shp.xml'
        ]
    ]

    # Find extensions group
    for __ext in __extensions:
        if extension in __ext:
            return __ext

    # Return empty list if there is no found
    return []


def validate_ogr_fields(path, fields):
    """ This function check the fields of specific Geospatial file.

    Returns:
        Dict: Return information about the fields.

    """

    # Get extension from path
    __ext_src = '.'.join(path.split('.')[-2:]) \
        if len(path.split('.')) > 2 \
        else splitext(path)[1]

    # Get kind of file depending on final extension
    __driver = get_ogr_driver(__ext_src)

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
    __file_src = __file.Open(path, 1)
    __file_layer = __file_src.GetLayer()
    __file_layer_def = __file_layer.GetLayerDefn()

    # Iterate over features of the layer
    __file_feat = __file_layer.GetNextFeature()
    while __file_feat is not None:

        # Iterate over fields of the Shapefile
        for __f_index in range(len(__fields)):

            # Check if field is True (has value)
            if __fields[__f_index] in __fields_null:
                if __fields_null[__fields[__f_index]]:
                    continue

            # Get if the feature has value
            __fields_null[__fields[__f_index]] = \
                __file_feat.IsFieldSetAndNotNull(__fields[__f_index])

        # Next feature
        __file_feat = __file_layer.GetNextFeature()

    __f_pad = 0
    __rem_fields = []
    __val_fields = {}
    for __field in __fields:

        # Index of the field
        __file_field_i = __fields.index(__field) - __f_pad

        # Remove empty fields from Shapefile
        if not __fields_null[__field]: 
            __file_layer.DeleteField(__file_field_i)
            __f_pad += 1

            # Save removed field
            __rem_fields.append(__field)

        # Rename to lowercase non-empty fields
        else:

            # Create copy of field and change name
            __file_field = __file_layer_def.GetFieldDefn(
                __file_field_i
            )
            __file_field.SetName(__field.lower())

            # Replace field on the layer
            __file_layer.AlterFieldDefn(
                __file_field_i, __file_field, ogr.ALTER_NAME_FLAG
            )

            # Search kind of field
            __val_field = [
                __f[__f.index(':') + 2:].split(' ')[0]
                for __f in fields if __f[:__f.index(':')] == __field
            ][0]

            # Save renamed field
            __val_fields[__field.lower()] = __val_field

    # Close file
    __file_src = None

    return __val_fields, __rem_fields


def generate_centroids(path):
    """ This function create centroids for geometries
        of specific Geospatial file.

    """

    # Get extension from path
    __ext_src = '.'.join(path.split('.')[-2:]) \
        if len(path.split('.')) > 2 \
        else splitext(path)[1]

    # Get kind of file depending on final extension
    __driver = get_ogr_driver(__ext_src)

    # Get layer from OGR Tools to check if
    # there is any field is null or empty, so
    # must be deleted, this file is opened as
    # DataSource Read-Write (1)
    from osgeo import ogr
    __file = ogr.GetDriverByName(__driver)
    __file_src = __file.Open(path, 1)
    __file_layer = __file_src.GetLayer()

    # Add field to layer
    __file_field = ogr.FieldDefn('centroid', ogr.OFTString)
    __file_layer.CreateField(__file_field)

    # Iterate over features of the layer
    __file_feat = __file_layer.GetNextFeature()
    while __file_feat is not None:

        # Get Geometry
        __file_geom = __file_feat.GetGeometryRef()

        # Get Centroid value as WKT
        __file_cent = __file_geom.Centroid().ExportToWkt()

        # Save value at new field
        __file_feat.SetField('centroid', __file_cent)

        # Save feature at layer
        __file_layer.SetFeature(__file_feat)
        
        # Next feature
        __file_feat = __file_layer.GetNextFeature()

    # Close file
    __file_src = None


def generate_areas(path):
    """ This function create areas for geometries
        of specific Geospatial file.

    """

    # Get extension from path
    __ext_src = '.'.join(path.split('.')[-2:]) \
        if len(path.split('.')) > 2 \
        else splitext(path)[1]

    # Get kind of file depending on final extension
    __driver = get_ogr_driver(__ext_src)

    # Get layer from OGR Tools to check if
    # there is any field is null or empty, so
    # must be deleted, this file is opened as
    # DataSource Read-Write (1)
    from osgeo import ogr
    __file = ogr.GetDriverByName(__driver)
    __file_src = __file.Open(path, 1)
    __file_layer = __file_src.GetLayer()

    # Add field to layer
    __file_field = ogr.FieldDefn('area', ogr.OFTReal)
    __file_layer.SetWidth(32)
    __file_layer.SetPrecision(2)
    __file_layer.CreateField(__file_field)

    # Iterate over features of the layer
    __file_feat = __file_layer.GetNextFeature()
    while __file_feat is not None:

        # Get Geometry
        __file_geom = __file_feat.GetGeometryRef()

        # Get area value
        __file_cent = __file_geom.GetArea() 

        # Save value at new field
        __file_feat.SetField('area', __file_cent)

        # Save feature at layer
        __file_layer.SetFeature(__file_feat)
        
        # Next feature
        __file_feat = __file_layer.GetNextFeature()

    # Close file
    __file_src = None


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

    def transform(self, path, extension):

        # Get kind of file depending on final extension
        __driver = get_ogr_driver(extension)

        # Get extension from path
        __ext_src = '.'.join(path.split('.')[-2:]) \
            if len(path.split('.')) > 2 \
            else splitext(path)[1]

        # Set flag if source extension is shp
        __shp_ext = '_bis' if __ext_src == extension else ''

        # Create arguments for transforming to Shapefile
        __command = [
            __driver, path.replace(__ext_src, '') +
            __shp_ext + extension, path
        ]

        # Execute OGR
        __g_info = cmd_ogr2ogr(__command)

        # # Detect if extensions are the same
        if __ext_src == extension:

            # Get folder from path
            __path_folder = os.path.dirname(path)

            # Get list of extensions from kind of file
            __path_ext = get_ogr_file_extensions(extension)

            # Get all nodes from directory
            __path_files = os.listdir(__path_folder)

            # Get old and new file name from path
            __path_name = path.replace(__path_folder + '/', '').replace(__ext_src, '')

            # Generate files from file name + list of extensions
            __path_list = [__path_name + __l for __l in __path_ext]

            # Get intersection between files and list of possible files
            __path_files = set(__path_files).intersection(set(__path_list))

            for __path_file in __path_files:

                # Delete old files
                os.remove(__path_folder + '/' + __path_file)

                # Rename new files
                os.rename(
                    __path_folder + '/' + __path_file.replace(
                        __path_name, __path_name + '_bis'
                    ),
                    __path_folder + '/' + __path_file
                )

        # Set destination path
        __path_dst = path.replace(__ext_src, '') + extension

        # Get information from GDAL
        __gi_info = self.get_info(__path_dst)

        # Generate centroid and Area if Geometry is
        # Polygon or MultiPolygon
        if 'polygon' in [
            __g_property for __g_property in __gi_info['info']
            if 'Geometry:' in __g_property
        ][0].lower():

            # Execute centroids generation
            generate_centroids(__path_dst)

            # Execute area generation
            generate_areas(__path_dst)

        return __g_info

    def get_info(self, path):

        # Get information when executes
        __info = cmd_ogrinfo([path])

        # Only get fields for output
        __info_fields = []
        for __o in __info['info']:

            # Save Kind of geometry
            if 'Geometry:' in __o:
                __info_fields.append(__o)

            # Save count of features
            elif 'Feature Count:' in __o:
                __info_fields.append(__o)

            # Save bounding                
            elif 'Extent: (' in __o:
                __info_fields.append(__o)

        __info['info'] = __info_fields

        return __info

    def get_fields(self, path):

        # Get information when executes
        __info = cmd_ogrinfo([path])

        # Remove unnecessary information
        __info['info'] = [
            __o for __o in __info['info'] 
            if 'Geometry:' not in __o and 'Feature Count:' not in __o
            and 'Extent: (' not in __o and 'Layer name:' not in __o
        ]

        # Get fields from received information
        __val_fields, __rem_fields = validate_ogr_fields(path, __info['info'])

        # Check if new fields is the same previous fields
        if len(__rem_fields):

            # Add new possible warning messages
            __info['warn'] += [
                'Removed field ' + __f +
                ' because is empty' for __f in __rem_fields
            ]

        # Generate new fields information
        __info['info'] = __val_fields

        # Save Centroid field
        __info['info']['centroid'] = 'String'

        return __info
