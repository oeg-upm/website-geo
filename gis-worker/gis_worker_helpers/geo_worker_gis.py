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

import re
import os
import sys
import hashlib
import unicodedata
from os.path import splitext
from dateutil.parser import parse
from subprocess import Popen, PIPE

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')

__author__ = "Alejandro F. Carrera"
__copyright__ = "Copyright 2017 © GeoLinkeddata Platform"
__credits__ = ["Alejandro F. Carrera", "Oscar Corcho"]
__license__ = "Apache"
__maintainer__ = "Alejandro F. Carrera"
__email__ = "alejfcarrera@mail.ru"


##########################################################################


def parse_path(path):
    """ This function allows you to parse a path.

    Args:
        path (string): file's path

    Returns:
        dict: Information about the path.

    """

    # Get folder from path
    __path_dir = os.path.dirname(path) + os.sep

    # Get extension of the file
    __path_ext = splitext(path)[1]

    # Get file name
    __path_name = path.replace(__path_dir, '')
    __path_name = __path_name.replace(__path_ext, '')

    return {
        'name': __path_name,
        'extension': __path_ext,
        'folder': __path_dir
    }


def md5_string(string):
    try:
        string_encode = string.encode()
    except Exception:
        string_encode = string
    return hashlib.md5(
        string_encode +
        's4lt_g30_l1nk3d_d4t4'
    ).hexdigest()


def clean_string(string):
    """ This function allows you to remove
        latin characters and spaces or from any string.

    Args:
        string (string): value to be parsed

    Returns:
        string: parsed value

    """

    uni_value = string.decode("utf-8")
    form = unicodedata.normalize('NFKD', uni_value)
    return re.sub(r'[^a-zA-Z0-9]', '', u"".join(
        [c for c in form if not unicodedata.combining(c)]
    )).lower()


def find_string(string, piece, n=0):
    """ This function returns an index where
        occurrence is found.

    Args:
        string (string): sentence to check
        piece (string): word or character to check
        n (index): position to start

    Returns:
        int: index

    """

    i = -1
    for c in xrange(n):
        i = string.find(piece, i + 1)
        if i < 0:
            break
    return i


##########################################################################


def check_geokettle_path():
    """ This function detects if Geokettle executables are included
        on the current environment (PATH variable). This is important
        to avoid full path directories and to be compatible with Docker
        Geokettle Image.

    Returns:
        bool: True if "kitchen" and "pan" exist, False otherwise.

    """

    # Create split character depending on operative system
    path_split = ';' if 'win32' in sys.platform else ':'

    # Get folders from PATH variable
    path_dirs = os.environ.get('PATH').split(path_split)

    # Iterate over folders
    for path_dir in path_dirs:

        # Check if folder exists
        if os.path.isdir(path_dir):

            # Get all nodes from directory
            path_files = os.listdir(path_dir)

            # Return if kitchen and pan exists at the same folder
            if 'kitchen.sh' in path_files and 'pan.sh' in path_files:
                return True

    # Executables were not found
    return False


def check_gdal_path():
    """ This function detects if GDAL executables are included
        on the current environment (PATH variable). This is important
        to avoid full path directories and to be sure that GDAL tools
        are available to execute them.

    Returns:
        bool: True if GDAL tools exist, False otherwise.

    """

    # Create split character depending on operative system
    path_split = ';' if 'win32' in sys.platform else ':'

    # Get folders from PATH variable
    path_dirs = os.environ.get('PATH').split(path_split)

    # Iterate over folders
    for path_dir in path_dirs:

        # Check if folder exists
        if os.path.isdir(path_dir):

            # Get all nodes from directory
            path_files = os.listdir(path_dir)

            # Return if kitchen and pan exists at the same folder
            if 'ogr2ogr' in path_files and 'ogrinfo' in path_files:

                # Check GDAL 2.2.0 version
                from osgeo import gdal
                version_num = int(gdal.VersionInfo('VERSION_NUM'))
                return version_num > 2020000

    # Executables were not found
    return False


def check_geo_has_features(information):
    """ This function allows you to check if the
        information has any features

    Args:
        information (list): files' information

    Returns:
        bool: True or False

    """

    return int([
        o for o in information if
        'Feature' in o
    ][0].split(': ')[1]) > 0


def check_geo_has_extent(information):
    """ This function allows you to check if the
        information has good extent

    Args:
        information (list): files' information

    Returns:
        bool: True or False

    """

    # Get Extent value from information
    __value = [
        o for o in information if 'Extent' in o
    ][0].split(': ')[1]

    # Check if Extent is good
    __value = __value.replace('(', '').\
        replace(')', '').replace(' - ', ', ').split(', ')

    # Return check
    return all(float(s) != 0.0 for s in __value)


##########################################################################


def cmd_geo(arguments):
    """ This function executes a GeoKettle command.

    Args:
        arguments (list): parameters to execute

    Returns:
        triple: parsed output, errors and exit code.

    """

    # Extend arguments with GeoKettle CLI options
    __arguments = [
        arguments[0], '-file=' + arguments[1],
        '-level=Detailed', '-norep'
    ]

    # Execute GeoKettle command
    __g_out, __g_err = exec_command(__arguments)

    return parse_geo_return(__g_out, __g_err), __g_out


def cmd_ogr2ogr(arguments):
    """ This function executes an ogr2ogr command.

    Args:
        arguments (list): parameters to execute

    Returns:
        triple: parsed output, errors and exit code.

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

    Args:
        arguments (list): parameters to execute

    Returns:
        triple: parsed output, errors and exit code.

    """

    # Extend arguments with ogr executable
    __arguments = ['ogrinfo', '-al', '-so'] + arguments

    # Execute GDAL commands
    __g_out, __g_err = exec_command(__arguments)
    
    return parse_ogr_return(__g_out, __g_err)


def exec_command(arguments):
    """ This function executes an ogr command through
        subprocess.

    Args:
        arguments (list): parameters to execute

    Returns:
        triple: output, errors and exit code of the process.

    """

    # Create process
    __proc = Popen(arguments, stdout=PIPE, stderr=PIPE)

    # Execute process
    __proc_out, __proc_err = __proc.communicate()

    return __proc_out, __proc_err


def get_ogr_driver(extension):
    """ This function allows to get the driver
        by extension.

    Args:
        extension (string): file extension to look for

    Returns:
        string: GDAL driver.

    Todo:
        * Extend for other drivers ...

    """

    if extension == '.shp':
        return 'ESRI Shapefile'
    elif extension == '.kml':
        return 'LIBKML'
    elif extension == '.geojson':
        return 'GeoJSON'
    else:
        return ''


def get_ogr_file_extensions(extension):
    """ This function allows to get the possible
        linked files with a specific extension
        file of geo-spatial data.

    Args:
        extension (string): file extension to look for

    Returns:
        list: group of extensions.

    Todo:
        * Extend for other extensions ...

    """

    # Define group of extensions files
    __extensions = [

        # Shapefile -> shp
        [
            '.shp', '.shx', '.shx', '.prj', '.sbn', '.sbx',
            '.dbf', '.fbn', '.fbx', '.ain', '.aih', '.shp.xml'
        ],

        # KML -> kml
        ['.kml'],

        # GeoJSON -> geojson
        ['.geojson']

    ]

    # Find extensions group
    for __ext in __extensions:
        if extension in __ext:
            return __ext

    # Return empty list if there is no found
    return []


def get_ogr_value(value):
    """ This function returns the parsed value
        from specific ogr data.

    Args:
        value (string): value to check

    Returns:
        type: Python real data

    """

    # Check if data is String
    if type(value) == str:

        # Deep copy
        try:
            __value = str(value)
        except Exception:
            __value = '' + value

        # Check possible date
        try:
            __value = parse(__value)
            if len(value) >= 8 and __value is not None:
                return __value.strftime('%Y-%m-%d')
        except Exception:
            pass

        # Check possible number
        try:
            return eval(value)
        except Exception:
            return value

    else:
        return value


def validate_ogr_fields(path, fields):
    """ This function checks the fields
        of specific Geo-spatial file.

    Args:
        path (string): file's path
        fields (list): fields' information

    Returns:
        list: removed bad or empty fields.

    """

    # Get information from path
    __path = parse_path(path)

    # Get kind of file depending on final extension
    __driver = get_ogr_driver(__path['extension'])

    # Create data structure for checking fields
    __fields_flags = {}

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
        for __field in fields:

            # Check if field is checking at least once
            if __field not in __fields_flags:
                __fields_flags[__field] = {'b': False}

            # Get real index
            __index = __file_feat.GetFieldIndex(__field)

            # Check if field is String and non empty
            __value = __file_feat.GetField(__index)
            if __file_feat.GetFieldType(__index) == 4 and \
               __value is not None:

                # Determine real value for specific data
                __real_value = get_ogr_value(__value)

                # Change if data is equals to old data
                if __value != __real_value:
                    __file_feat.SetField(
                        __index, __real_value
                    )
                    __file_layer.SetFeature(__file_feat)

            # Check if field is True (has value)
            if __fields_flags[__field]['b']:
                continue

            # Get if the feature has value
            __fields_flags[__field]['b'] = \
                not __file_feat.IsFieldNull(__index) and \
                __file_feat.IsFieldSet(__index)
            __fields_flags[__field]['i'] = __index

        # Go to Next feature
        __file_feat = __file_layer.GetNextFeature()

    # Set structures for removing fields
    __sorted_fields = [
        __f[0] for __f in sorted(
            __fields_flags.items(),
            key=lambda x: x[1]['i']
        )
    ]
    __f_pad = 0
    __f_counter = 0
    __rem_fields = []
    for __field in __sorted_fields:

        # Index of the field
        __index = __f_counter - __f_pad

        # Remove empty fields from Shapefile
        if not __fields_flags[__field]['b']:
            __file_layer.DeleteField(__index)
            __f_pad += 1

            # Save removed field
            __rem_fields.append(__field)

        # Rename to lowercase non-empty fields
        else:

            # Clean name of the field
            __file_field = __file_layer_def.GetFieldDefn(__index)
            __file_name = clean_string(__field).encode('utf-8')

            # Change name if it is necessary
            if __file_name != __field:
                __file_field.SetName(__file_name)
                __file_layer.AlterFieldDefn(
                    __index, __file_field,
                    ogr.ALTER_NAME_FLAG
                )

        # Increase counter
        __f_counter += 1

    # Close file
    __file_src = None

    return __rem_fields


def get_projection(path):
    """ This function gets gis projections
        of specific Geo-spatial file.

    Args:
        path (string): file's path

    Returns:
        string: OGR projection

    """

    # Get information from path
    __path = parse_path(path)

    # Get kind of file depending on final extension
    __driver = get_ogr_driver(__path['extension'])

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


def set_centroids(path):
    """ This function calculates the centroid
        for geometries of specific Geo-spatial
        file and save them on the same file.

    Args:
        path (string): file's path

    """

    # Get information from path
    __path = parse_path(path)

    # Get kind of file depending on final extension
    __driver = get_ogr_driver(__path['extension'])

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


def set_areas(path):
    """ This function calculates the area
        for geometries of specific Geo-spatial
        file and save them on the same file.

    Args:
        path (string): file's path

    """

    # Get information from path
    __path = parse_path(path)

    # Get kind of file depending on final extension
    __driver = get_ogr_driver(__path['extension'])

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
    __file_field.SetWidth(32)
    __file_field.SetPrecision(2)
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


def set_vrt(path, layers, deleted):
    """ This function generates the VRT file
        to create a good conversion for GeoJSON
        geo-spatial file.

    Args:
        path (dict): path's information
        layers (list): list of file's path
        deleted (list): list of index to be deleted

    Returns:
        string: path of vrt path written to disk

    """

    # Start template for VRT
    __vrt_template = '<OGRVRTDataSource>' \
        '<OGRVRTUnionLayer name="GeoLinkedData Features">'

    # Iterate over files
    for __file_i in range(0, len(layers)):

        # Check if index needs to be included
        if __file_i not in deleted:
            __vrt_template += '<OGRVRTLayer name="' + \
                layers[__file_i] + '">'
            __vrt_template += '<SrcDataSource>' + \
                path['folder'] + 'shp/' + \
                layers[__file_i] + '.shp' + \
                '</SrcDataSource>'
            __vrt_template += '</OGRVRTLayer>'

    # End template for VRT
    __vrt_template += '</OGRVRTUnionLayer>' \
        '</OGRVRTDataSource>'

    # Write VRT file to disk
    __vrt_path = path['folder'] + path['name'] + '.vrt'
    with open(__vrt_path, 'w') as __vrt_file:
        __vrt_file.write(__vrt_template)

    return __vrt_path


def parse_ogr_return(outputs, errors):
    """ This function parses the both
        outputs from ogr execution.

    Args:
        outputs (string): stdout information
        errors (string): stderr information

    Returns:
        dict: information about the outputs.

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
    """ This function parses the both outputs
        from GeoKettle execution.

    Args:
        outputs (string): stdout information
        errors (string): stderr information

    Returns:
        dict: information about the outputs.

    """

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
                    __index_dash[__key] = find_string(
                        __message, '-', 2
                    ) + 2

                # Get message
                __m = __message[__index_dash[__key]:]

                # Save message
                __return[__key.lower()].append(__m)

    return __return


##########################################################################


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


def print_error_java_exception(java_message):
    """ This function returns a message when
        java from GeoKettle raise an exception.

    Returns:
        dict: Information structure with error

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
    """ This constructor creates a super class of defined type
        from parameter.

    Returns:
        class: Super class of specific instance

    """
    
    def __call__(cls, *args, **kwargs):
        try:
            return cls.__instance
        except AttributeError:
            return super(Singleton, cls).__call__(*args, **kwargs)


class WorkerGIS(object):
    """ This constructor creates only an instance of a
        GIS library for doing transformations or getting
        information from data following the singleton pattern
        (software design pattern).

    Returns:
        class: GIS Worker

    """

    # Create singleton instance
    __metaclass__ = Singleton

    def __init__(self):

        # Set status of GIS configuration
        self.status = check_geokettle_path() and check_gdal_path()

    def transform(self, path, extension):
        """ This function allows to transform any geo-spatial
            file to specific extension thanks to GDAL tools.

        Args:
            path (string): file's path
            extension (string): extension to be transformed

        Returns:
            dict: information about the outputs

        """

        # Get kind of file depending on final extension
        __driver = get_ogr_driver(extension)

        # Check driver (extension)
        if __driver is None:
            return print_error_extension()

        # Get information from path
        __path = parse_path(path)
        __path_shp = __path['folder'] + 'shp' + os.sep
        __path_trs = __path['folder'] + 'trs' + os.sep

        # Check if transformation paths exist
        if os.path.exists(__path_shp) and \
           os.path.exists(__path_trs):
            return {'info': [], 'warn': [], 'error': [
                'Delete the previous transformation before proceed.'
            ]}, None, None, None, None

        # Create arguments for transforming to Shapefile
        __command = [__driver, __path_shp, path]

        # Execute OGR
        __g_info = cmd_ogr2ogr(__command)

        # Detect if there were any errors
        if len(__g_info['error']):
            return __g_info, None, \
                None, None, None

        # Detect warnings
        if len(__g_info['warn']):
            __g_info['warn'][-1] += '\n'
            __g_info['warn'] = [
                'GDAL transformation\n'
            ] + __g_info['warn']

        # Get all nodes from directory
        __path_files = os.listdir(__path_shp)

        # Rename and generate SHP structure
        __layers_name = []
        __layers_md5 = {}
        for __path_rev in __path_files:

            # Get information from file
            __path_info = parse_path(__path_rev)

            # Check if md5 is saved
            if __path_info['name'] not in __layers_md5:
                __layers_md5[__path_info['name']] = \
                    md5_string(__path_info['name'])
                __layers_name.append(
                    __layers_md5[__path_info['name']]
                )
            __layer_md5 = __layers_md5[__path_info['name']]

            # Execute rename
            os.rename(
                __path_shp + __path_rev,
                __path_shp + __path_rev.replace(
                    __path_info['name'], __layer_md5
                )
            )

        # Convert keys to values
        __layers_md5 = {
            __v: __k for __k, __v in
            __layers_md5.items()
        }

        # Structure for deleted Shapefiles
        __paths_index_delete = []

        # Structure for layers' information
        __layers_info = {'raw': [], 'info': []}

        # Structure for fields'
        __layers_fields_info = {'raw': [], 'info': []}

        for __path_rev_i in range(0, len(__layers_name)):

            # Get completed path
            __path_rev = __path_shp + \
                __layers_name[__path_rev_i] + extension

            # Get information from GDAL
            __gi_info = self.get_info(__path_rev)

            # Check if file has not features, bad
            # extend or any previous issue
            if not check_geo_has_features(__gi_info['info']) or \
               not check_geo_has_extent(__gi_info['info']) or \
               len(__gi_info['error']):

                # Add paths for deletion
                __paths_index_delete.append(__path_rev_i)

                # Delete all possible extensions
                for __path_ext in get_ogr_file_extensions(extension):

                    # Get real path to delete
                    __path_delete = __path_rev.replace(
                        extension, __path_ext
                    )

                    # Delete if exists
                    if os.path.isfile(__path_delete):
                        os.remove(__path_delete)

                # Join error messages if they exist
                if len(__gi_info['error']):
                    if __path_rev_i < len(__layers_name) - 1:
                        __gi_info['error'][-1] += '\n'
                    __g_info['error'] += [
                        'Layer - ' + __layers_name[__path_rev_i] + '\n'
                    ]
                    __g_info['error'] += __gi_info['error']

                # Next file
                continue

            # Generate centroid and Area if Geometry
            # is kind of Polygon
            if 'Geometry: Polygon' == [
                __o for __o in __gi_info['info']
                if 'Geometry:' in __o
            ][0].lower():

                # Execute centroids generation
                set_centroids(__path_rev)

                # Execute area generation
                set_areas(__path_rev)

            # Save layers' information
            __raw_layer_info = __gi_info['info']
            if __path_rev_i < len(__layers_name) - 1:
                __raw_layer_info[-1] += '\n'
            __raw_layer_info = [
                    'Layer - ' + __layers_md5[
                        __layers_name[__path_rev_i]
                    ] + ' - ' + __layers_name[
                        __path_rev_i
                    ] + '\n'
                ] + __raw_layer_info
            __layers_info['raw'].append(__raw_layer_info)
            __layers_info['info'].append(__gi_info['info_values'])

            # Validate and save messages
            __raw_validate_info = self.validate_fields(__path_rev)
            if len(__raw_validate_info):
                if __path_rev_i < len(__layers_name) - 1:
                    __raw_validate_info[-1] += '\n'
                __raw_validate_info = [
                    'Layer - ' + __layers_md5[
                        __layers_name[__path_rev_i]
                    ] + ' - ' + __layers_name[
                        __path_rev_i
                    ] + '\n'
                ] + __raw_validate_info
                __g_info['warn'] += __raw_validate_info

            # Get information about new and old fields
            __raw_fields_info = self.get_fields(__path_rev)
            if len(__raw_fields_info['info']):
                __layers_fields_info['info'].append(
                    __raw_fields_info['info_values']
                )
                __raw_fields_info = __raw_fields_info['info']
                if __path_rev_i < len(__layers_name) - 1:
                    __raw_fields_info[-1] += '\n'
                __raw_fields_info = [
                    'Layer - ' + __layers_md5[
                        __layers_name[__path_rev_i]
                    ] + ' - ' + __layers_name[
                        __path_rev_i
                    ] + '\n'
                ] + __raw_fields_info
                __layers_fields_info['raw'].append(__raw_fields_info)

        # Generate VRT for GeoJSON transformation
        __vrt_path = set_vrt(
            __path, __layers_name,
            __paths_index_delete
        )

        # Get driver for geojson properly
        __driver = get_ogr_driver('.geojson')

        # Check folder of transformations
        if not os.path.exists(__path_trs) or \
           not os.path.isdir(__path_trs):
            os.mkdir(__path_trs)

        # Execute transformation to GeoJSON
        __geo_path = __path_trs + __path['name'] + '.geojson'
        cmd_ogr2ogr([__driver, __geo_path, __vrt_path])

        # Delete bad layers
        __layers_name = [
            __layers_name[__path_rev_i]
            for __path_rev_i in range(0, len(__layers_name))
            if __path_rev_i not in __paths_index_delete
        ]
        __layers_md5 = {
            __path_rev_i: __layers_md5[__path_rev_i]
            for __path_rev_i in __layers_md5.keys()
            if __path_rev_i in __layers_name
        }

        return __g_info, __layers_name, __layers_md5, \
            __layers_info, __layers_fields_info

    def get_info(self, path, inc_layers=False):
        """ This function allows to get information from
            specific file thanks to GDAL tools.

        Args:
            path (string): file's path
            inc_layers (bool): flag to include layers' name

        Returns:
            dict: information about the outputs

        """

        # Get information when executes
        __info = cmd_ogrinfo([path])

        # Check if any error exist
        if len(__info['error']):
            __info['info_values'] = []
            return __info

        # Structures for information
        __values = {}
        __messages = []

        # Information to save
        __names = {
            'Geometry': 'geometry',
            'Feature Count': 'features',
            'Extent': 'bounding'
        }

        # Include layers name
        if inc_layers:
            __names['Layer name'] = 'Layer'

        # Iterate over information
        for __o in __info['info']:

            # Get value and name
            __name = __o[:__o.index(':')]
            __value = __o[__o.index(':') + 2:]

            # Check if name is a counter
            if __name == 'Feature Count':
                __value = int(__value)

            # Check if name is valid
            if __name in __names.keys():

                # Save value info
                __values[__names[__name]] = __value

                # Save raw info
                __messages.append(__o)

        # Add projection to info
        __info_proj = get_projection(path)
        if __info_proj is not None:
            __values['crs'] = __info_proj
            __messages.append('CRS: ' + __info_proj)

        # Save information to structure
        __info['info'] = __messages
        __info['info_values'] = __values

        return __info

    def validate_fields(self, path):
        """ This function allows to validate fields from
            specific file thanks to GDAL tools.

        Args:
            path (string): file's path

        Returns:
            list: information about the outputs

        """

        # Get information when executes
        __info = self.get_fields(path)

        # Check if any error exist
        if len(__info['error']):
            return []

        # Validate fields from received information
        __rem_fields = validate_ogr_fields(
            path, __info['info_values'].keys()
        )

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

    def get_fields(self, path, inc_layers=False):
        """ This function allows to get fields' information
            from specific file thanks to GDAL tools.

        Args:
            path (string): file's path
            inc_layers (bool): flag to include layers' name

        Returns:
            dict: information about the outputs

        """

        # Get information when executes
        __info = cmd_ogrinfo([path])

        # Check if any error exist
        if len(__info['error']):
            __info['info_values'] = []
            return __info

        # Remove unnecessary information
        __info['info'] = [
            __o for __o in __info['info'] 
            if 'Geometry:' not in __o and 'Feature Count:' not in __o
            and 'Extent: (' not in __o
        ]

        # Check if layers name must be included
        if not inc_layers:
            __info['info'] = [
                __o for __o in __info['info']
                if 'Layer name:' not in __o
            ]

            # Structures for fields
            __values = {}

            # Iterate over fields information
            for __f in __info['info']:

                # Get field name
                __field_name = __f[:__f.index(':')]

                # Save field info
                __field_type = __f.replace(__field_name, '')[2:]
                __field_type = __field_type[:__field_type.index('(') - 1]
                __field_type = str(__field_type).lower()

                # Check field info
                if __field_type == 'real' or __field_type == 'float':
                    __field_type = 'double'

                # Save field structure
                __values[__field_name] = __field_type

            # Save structure
            __info['info_values'] = __values

        return __info

    def execute_geo_transform(self, path):
        """ This function allows to execute GeoKettle
            transformation from specific XML file
            thanks to GeoKettle CLI tools.

        Args:
            path (string): file's path

        Returns:
            dict: information about the outputs

        """

        # Execute GeoKettle
        __g_info, __original_info = cmd_geo(['pan.sh', path])

        # Get extension from path
        __ext_src = '.'.join(path.split('.')[-2:]) \
            if len(path.split('.')) > 2 \
            else splitext(path)[1]

        # Get directory path to save on log
        __log_path = path.replace(__ext_src, '')
        with open(__log_path, 'w') as outfile:
            outfile.write(__original_info)

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

                # Check message template
                if 'Finished processing (' in __message:
                    __message_list = str(__message).split(' - ')
                    __gr_info['info'].append(
                        'Performance by ' + __message_list[0] +
                        ': ' + __message_list[1][21:][:-1] + '.'
                    )

        return __gr_info

    def execute_geo_job(self, path):
        """ This function allows to execute GeoKettle
            job from specific XML file thanks to
            GeoKettle CLI tools.

        Args:
            path (string): file's path

        Returns:
            dict: information about the outputs

        """

        # Execute GeoKettle
        __g_info, __original_info = cmd_geo(['kitchen.sh', path])

        # Get extension from path
        __ext_src = '.'.join(path.split('.')[-2:]) \
            if len(path.split('.')) > 2 \
            else splitext(path)[1]

        # Get directory path to save on log
        __log_path = path.replace(__ext_src, '')
        with open(__log_path, 'w') as outfile:
            outfile.write(__original_info)

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

                # Check message template
                if 'Finished processing (' in __message:
                    __message_list = str(__message).split(' - ')
                    __gr_info['info'].append(
                        'Performance by ' + __message_list[0] +
                        ': ' + __message_list[1][21:][:-1] + '.'
                    )

        return __gr_info
