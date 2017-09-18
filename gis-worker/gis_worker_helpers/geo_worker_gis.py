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
from os.path import splitext
from subprocess import Popen, PIPE
from geo_worker_xml import WorkerXML


__author__ = "Alejandro F. Carrera"
__copyright__ = "Copyright 2017 © GeoLinkeddata Platform"
__credits__ = ["Alejandro F. Carrera", "Oscar Corcho"]
__license__ = "Apache"
__maintainer__ = "Alejandro F. Carrera"
__email__ = "alejfcarrera@mail.ru"


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


def cmd_geo(arguments):
    """ This function executes a GeoKettle command.

    Returns:
        Triple: Return parsed output, errors and exit code.

    """

    # Extend arguments with GeoKettle CLI options
    __arguments = [
        arguments[0], '-file=' + arguments[1],
        '-level=Detailed', '-norep'
    ]

    # Execute GeoKettle command
    __g_out, __g_err = exec_command(__arguments)

    return parse_geo_return(__g_out, __g_err)


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
    __g_out, __g_err = exec_command(__arguments)

    return parse_ogr_return(__g_out, __g_err)


def cmd_ogrinfo(arguments):
    """ This function executes an ogrinfo command.

    Returns:
        Triple: Return parsed output, errors and exit code.

    """

    # Extend arguments with ogr executable
    __arguments = ['ogrinfo', '-al', '-so'] + arguments

    # Execute GDAL commands
    __g_out, __g_err = exec_command(__arguments)
    
    return parse_ogr_return(__g_out, __g_err)


def exec_command(arguments):
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
    elif extension == '.kml':
        return 'LIBKML'
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
        ],

        # KML -> kml
        ['.kml'],

    ]

    # Find extensions group
    for __ext in __extensions:
        if extension in __ext:
            return __ext

    # Return empty list if there is no found
    return []


def get_projection(path):
    """ This function gets gis projections
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

    # Get Spatial reference
    __file_spatial = __file_layer.GetSpatialRef()

    # Detect GIS kind of data
    __f_cs = 'GEOGCS' if __file_spatial.IsGeographic() == 1 else 'PROJCS'
    __f_an = __file_spatial.GetAuthorityName(__f_cs)
    __f_ac = __file_spatial.GetAuthorityCode(__f_cs)

    # Detect if name and code are valid
    __file_spatial = str(__f_an) + ':' + str(__f_ac) \
        if __f_an is not None and __f_ac is not None else None

    # Close file
    __file_src = None

    return __file_spatial


def validate_ogr_fields(path, fields):
    """ This function checks the fields of specific Geospatial file.

    Returns:
        Tuple: Return the removed or valid fields.

    """

    # Get extension from path
    __ext_src = '.'.join(path.split('.')[-2:]) \
        if len(path.split('.')) > 2 \
        else splitext(path)[1]

    # Get kind of file depending on final extension
    __driver = get_ogr_driver(__ext_src)

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
        for __f_index in range(len(fields)):

            # Check if field is True (has value)
            if fields[__f_index] in __fields_null:
                if __fields_null[fields[__f_index]]:
                    continue

            # Get if the feature has value
            __fields_null[fields[__f_index]] = \
                __file_feat.IsFieldSetAndNotNull(fields[__f_index])

        # Next feature
        __file_feat = __file_layer.GetNextFeature()

    __f_pad = 0
    __rem_fields = []
    for __field in fields:

        # Index of the field
        __file_field_i = fields.index(__field) - __f_pad

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

    # Close file
    __file_src = None

    return __rem_fields


def generate_centroids(path):
    """ This function calculates the centroid for geometries
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
    """ This function calculates the area for geometries
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


def parse_geo_return(outputs, errors):

    # Create temporal output log
    __output = outputs.split('\n')

    # Check Java exception is present
    if 'Exception in thread' in errors:

        return print_error_java_exception(errors)

    # Create index structure to improve performance
    # of looking for characters in specific log string
    __index_dash = {}
    __index_dash_keys = ['INFO', 'WARN', 'ERROR']

    # Create structure of return
    __return = {'info': [], 'warn': [], 'error': []}

    # Iterate over output
    for __message in __output:

        # Remove kind of log and date
        for __key in __index_dash_keys:

            # Check kind of log
            if __key in __message:

                # Save index to structure
                # + 2 -> character + space
                if __key not in __index_dash:
                    __index_dash[__key] = find_occurrence(
                        __message, '-', 2
                    ) + 2

                # Get message
                __m = __message[__index_dash[__key]:]

                # Save message
                __return[__key.lower()].append(__m)

    return __return


##########################################################################


def find_occurrence(s, x, n=0):
    """ This function returns an index where
        occurrence is found.

        Return:
            Integer: index
    """
    i = -1
    for c in xrange(n):
        i = s.find(x, i + 1)
        if i < 0:
            break
    return i


def print_error_information():
    """ This function returns a message when file
        has not valid information or steps.

        Return:
            Dict: Information structure with error
    """

    return {
        'error': [
            'Information is not valid. Please, check the file path '
            'and metadata about steps and GeoKettle transformation '
            'or job.'
        ],
        'warn': [],
        'info': []
    }


def print_error_extension():
    """ This function returns a message when file
        has not valid extension.

        Return:
            Dict: Information structure with error
    """

    return {
        'error': [
            'Extension is not valid. Please, check the file path.'
        ],
        'warn': [],
        'info': []
    }


def print_error_java_exception(java_message):
    """ This function returns a message when java
        from GeoKettle raise an exception.

        Return:
            Dict: Information structure with error
    """

    return {
        'error': [
            'Java Exception was raised from GeoKettle.',
            'Check the file on GeoKettle standalone version.',
            java_message
        ],
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

    def transform(self, path, extension):

        # Get kind of file depending on final extension
        __driver = get_ogr_driver(extension)

        # Check driver (extension)
        if __driver is None:
            return print_error_extension()

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

        # Detect if there were any errors
        if len(__g_info['error']):
            return __g_info

        # Detect if extensions are the same
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

        # Generate centroid and Area if Geometry
        # is kind of Polygon
        if 'polygon' in [
            __o for __o in __gi_info['info']
            if 'Geometry:' in __o
        ][0].lower():

            # Execute centroids generation
            generate_centroids(__path_dst)

            # Execute area generation
            generate_areas(__path_dst)

        # Join error messages
        __g_info['error'] += __gi_info['error']

        # Validate all fields and join log messages
        __g_info['warn'] += self.validate_fields(__path_dst)

        # Get information about new and old fields
        __g_fields = self.get_fields(__path_dst, True)
        __g_info['info'] += __g_fields['info']

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

        # Add projection to info
        __info_proj = get_projection(path)
        if __info_proj is not None:
            __info['info'].append('CRS: ' + __info_proj)

        return __info

    def validate_fields(self, path):

        # Get information when executes
        __info = self.get_fields(path)

        # Validate fields from received information
        __rem_fields = validate_ogr_fields(path, __info['info'])

        # Set empty return structure
        __log_messages = []

        # Check if new fields is the same previous fields
        if len(__rem_fields):

            # Add new possible warning messages
            __log_messages += [
                'Removed field ' + __f +
                ' because is empty' for __f in __rem_fields
            ]

        return __log_messages

    def get_fields(self, path, extend=False):

        # Get information when executes
        __info = cmd_ogrinfo([path])

        # Remove unnecessary information
        __info['info'] = [
            __o for __o in __info['info'] 
            if 'Geometry:' not in __o and 'Feature Count:' not in __o
            and 'Extent: (' not in __o and 'Layer name:' not in __o
        ]

        if not extend:

            # Only show name of fields
            __info['info'] = [
                __f[:__f.index(':')]
                for __f in __info['info']
            ]

        return __info

    def execute_geo_transform(self, path):

        # Get extension from path
        __ext_src = '.'.join(path.split('.')[-2:]) \
            if len(path.split('.')) > 2 \
            else splitext(path)[1]

        # Check if extension is valid
        if __ext_src != '.ktr':
            return print_error_extension()

        # Create XML instance
        __xml_instance = WorkerXML()

        # Get XML information
        __x_info = __xml_instance.get_steps(
            __xml_instance.check_issues(path)
        )

        # Check information
        if __x_info is None:
            return print_error_information()

        # Execute GeoKettle
        __g_info = cmd_geo(['pan.sh', path])

        # Create new structure
        __gr_info = {
            'info': [],
            'warn': __g_info['warn'],
            'error': __g_info['error']
        }

        # Parse information messages
        if len(__g_info['info']):

            # Iterate over messages
            for __message in __g_info['info']:

                # Iterate over steps
                for __step in __x_info:

                    # Check message template
                    if __step in __message and 'I=' in __message:
                        __message_copy = str(__message)
                        __message_copy = 'Performance by ' + \
                            __message_copy.replace('Finished processing (', '')[:-1]
                        __gr_info['info'].append(__message_copy)

        return __gr_info
