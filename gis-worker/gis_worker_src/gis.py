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
import utils
import settings
from datetime import datetime
from dateutil.parser import parse
from subprocess import Popen, PIPE

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


def check_geo_has_extent(information):
    """ This function allows you to check if the
        information has good extent

    Args:
        information (string): bounding box info

    Returns:
        bool: True or False

    """

    return not all(
        float(s) == 0.0 for s in
        information[1:][:-1].replace(
            ') - (', ', '
        ).split(', ')
    )


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

    """

    return None if extension not in config.upload_drivers else \
        str(config.upload_drivers[extension])


def get_ogr_file_extensions(extension):
    """ This function allows to get the possible
        linked files with a specific extension
        file of geo-spatial data.

    Args:
        extension (string): file extension to look for

    Returns:
        list: group of extensions.

    """
    # Find extensions group
    for __mime_key in config.upload_mime.keys():
        if extension in config.upload_mime[__mime_key]:
            return config.upload_mime[__mime_key]

    # Return empty list if there is no found
    return []


def parse_ogr_value(value, kind):
    """ This function returns the parsed value
        from specific ogr data.

        types => int = 0,
            int64 (long) = 12,
            real (float) = 2,
            str = 4,
            date = 9

    Args:
        value (string): value to check
        kind (OGRType): kind to check

    Returns:
        dict: parsed information

    """

    def parse_ogr_number(number):
        if type(number) == float:
            return {'value': number, 'ogr': 2}
        elif type(number) == long:
            return {'value': number, 'ogr': 12}
        else:
            return {'value': number, 'ogr': 0}

    # Check if data is a String
    if kind == 4:

        # Deep copy
        try:
            __value = str(value)
        except Exception:
            __value = '' + value

        # Check possible date
        try:
            __value = parse(__value)
            if len(value) >= 8 and __value is not None:
                return {
                    'value': __value.strftime('%Y-%m-%d'),
                    'ogr': 9
                }
        except Exception:
            pass

        # Check possible number
        try:
            return parse_ogr_number(eval(value))
        except Exception:
            return {'value': value, 'ogr': 4}

    # Check if data is a Date
    elif kind == 9:
        return {'value': value, 'ogr': 9}

    # data must be a Number
    else:
        return parse_ogr_number(value)


def extend_ogr_fields(path, fields):
    """ This function checks the fields
        of specific Geo-spatial file.

    Args:
        path (string): file's path
        fields (dict): fields' information

    Returns:
        dict: extended info of fields

    """

    # Get information from path
    __path = utils.parse_path(path)

    # Get kind of file depending on final extension
    __driver = get_ogr_driver(__path['extension'])

    # Get names of fields
    __fields = fields.keys()

    # Create structure for values
    __fields_values = {}

    # Get layer from OGR Tools to check if
    # there is any field is null or empty, so
    # must be deleted, this file is opened as
    # DataSource Read-Write (1)
    from osgeo import ogr
    __file = ogr.GetDriverByName(__driver)
    __file_src = __file.Open(path, 1)
    __file_layer = __file_src.GetLayer()

    # Iterate over features of the layer
    __file_feat = __file_layer.GetNextFeature()

    while __file_feat is not None:

        # Iterate over fields
        for __field in __fields:

            # Check if field info is saved (first time)
            if __field not in __fields_values:
                __fields_values[__field] = {
                    'd': False, 'v': []
                }

            # Check if field is marked as duplicate
            if __fields_values[__field]['d']:
                continue

            # Get real index
            __index = __file_feat.GetFieldIndex(__field)

            # Get value from field
            __value = __file_feat.GetField(__index)

            # Check if value is already inserted
            if __value in __fields_values[__field]['v']:
                __fields_values[__field]['d'] = True
                continue
            else:
                __fields_values[__field]['v'].append(__value)

        # Go to Next feature
        __file_feat = __file_layer.GetNextFeature()

    # Close file
    __file_src = None

    # Remove values to clean memory
    # and re-structure dictionary
    for __field in __fields_values.keys():
        del __fields_values[__field]['v']
        __fields_values[__field] = \
            __fields_values[__field]['d']

    return __fields_values


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
    __path = utils.parse_path(path)

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

    # Create structure for remove features
    __file_feat_rem = []
    __file_feat_count = 0

    # Iterate over features of the layer
    __file_feat = __file_layer.GetNextFeature()

    while __file_feat is not None:

        # Set count
        __file_feat_count += 1

        # Get Feature internal ID
        __file_feat_id = __file_feat.GetFID()

        # Check if feature has geometry (valid & non-empty)
        __file_feat_geo = __file_feat.GetGeometryRef()
        if __file_feat_geo is None or __file_feat_geo.IsEmpty() or \
           not __file_feat_geo.IsValid():
            __file_feat_rem.append(__file_feat_id)

            # Go to Next feature
            __file_feat = __file_layer.GetNextFeature()
            continue

        # Iterate over fields of the Shapefile
        for __field in fields:

            # Check if field info is saved (first time)
            if __field not in __fields_flags:
                __fields_flags[__field] = {'v': {}}

            # Get real index
            __index = __file_feat.GetFieldIndex(__field)
            __fields_flags[__field]['i'] = __index

            # Only these types are allowed on Shapefiles
            # int = 0, int64 (double) = 12, real (float) = 2
            # str = 4 and date = 9

            # Get original value from field
            __field_v = __file_feat.GetField(__index)

            # Check if original value is valid
            if __field_v is not None:

                # Get original kind of field
                __field_k = __file_feat.GetFieldType(__index)

                # Parse value and kind to verify them
                __field_info = parse_ogr_value(__field_v, __field_k)

                # Save value to dictionary
                __fields_flags[__field]['v'][__file_feat_id] = \
                    __field_info['value']

                # Check if real and ogr types are different
                if __field_k != __field_info['ogr']:

                    # Check if column has more than one type
                    if 't' in __fields_flags[__field]:
                        if __fields_flags[__field]['t'] == 'invalid':
                            continue
                        elif __fields_flags[__field]['t'] != \
                                __field_info['ogr']:
                            __fields_flags[__field]['t'] = 'invalid'
                            continue
                    else:
                        __fields_flags[__field]['t'] = __field_info['ogr']

        # Go to Next feature
        __file_feat = __file_layer.GetNextFeature()

    # Reset pointer
    __file_layer.ResetReading()

    # Remove features without geometry
    for __file_feat in __file_feat_rem:
        __file_layer.DeleteFeature(__file_feat)

    # Set structures for removing fields
    __sorted_fields = [
        __f[0] for __f in sorted(
            __fields_flags.items(),
            key=lambda x: x[1]['i']
        )
    ]

    # Create structure for empty fields
    __rem_fields = []

    # Iterate and rebuild fields
    for __field in __sorted_fields:

        # Index of the field
        __index = __file_layer.FindFieldIndex(__field, 1)

        # Calculate filled values
        __filled = float(len(__fields_flags[__field]['v'])) / \
            float(__file_feat_count)

        # Remove empty fields or less 1% filled
        if len(__fields_flags[__field]['v']) == 0 or __filled < 0.01:
            __file_layer.DeleteField(__index)
            __rem_fields.append(__field)

        # Rename or change type of column
        else:

            # Generate cleaned field's name
            __field_n = utils.clean_string(__field).encode('utf-8')

            # Check if field needs to be renamed
            if 't' not in __fields_flags[__field] or (
                't' in __fields_flags[__field] and
                __fields_flags[__field]['t'] == 'invalid'
            ):

                # Clean name of the field
                __file_field = __file_layer_def.GetFieldDefn(__index)

                # Change name if it is necessary
                if __field_n != __field:
                    __file_field.SetName(__field_n)
                    __file_layer.AlterFieldDefn(
                        __index, __file_field,
                        ogr.ALTER_NAME_FLAG
                    )

            else:

                # Remove old field
                __file_layer.DeleteField(__index)

                # Create new field
                __file_layer.CreateField(ogr.FieldDefn(
                    __field_n, __fields_flags[__field]['t']
                ))

                # Index of the new field
                __index = __file_layer.FindFieldIndex(__field_n, 1)

                # Iterate over features of the layer
                __file_feat = __file_layer.GetNextFeature()
                while __file_feat is not None:

                    # Get Feature internal ID
                    __file_feat_id = __file_feat.GetFID()

                    # Check if there is a saved value
                    if __file_feat_id in __fields_flags[__field]['v']:

                        # Set value to feature
                        __file_feat.SetField(
                            __index, __fields_flags[__field]['v'][__file_feat_id]
                        )

                    # Go to Next feature
                    __file_layer.SetFeature(__file_feat)
                    __file_feat = __file_layer.GetNextFeature()

                # Reset pointer
                __file_layer.ResetReading()

    # Close file
    __file_layer.SyncToDisk()
    __fields_flags = None
    __file_src = None

    return __rem_fields, len(__file_feat_rem)


def get_projection(path):
    """ This function gets gis projections
        of specific Geo-spatial file.

    Args:
        path (string): file's path

    Returns:
        string: OGR projection

    """

    # Get information from path
    __path = utils.parse_path(path)

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
    __path = utils.parse_path(path)

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
    __file_field = ogr.FieldDefn('geometry_c', ogr.OFTString)
    __file_layer.CreateField(__file_field)

    # Iterate over features of the layer
    __file_feat = __file_layer.GetNextFeature()
    while __file_feat is not None:

        # Get Geometry
        __file_geom = __file_feat.GetGeometryRef()

        # Get Centroid value as WKT
        __file_cent = __file_geom.Centroid().ExportToWkt()

        # Save value at new field
        __file_feat.SetField('geometry_c', __file_cent)
        __file_layer.SetFeature(__file_feat)
        
        # Next feature
        __file_feat = __file_layer.GetNextFeature()

    # Close file
    __file_layer.ResetReading()
    __file_layer.SyncToDisk()
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

    def clean_message(message):
        return str(message).decode('string_escape').\
            replace('  ', ' ').\
            replace('"', '')

    def unable_to_open_message():
        return 'An error has occurred in the included files. ' \
           'Please ensure that all necessary files have been uploaded ' \
           'and check the internal relations between them.'

    # Create temporal output log
    __output = outputs.split('\n')

    # Create temporal error log
    __errors = errors.split('\n')

    # Search failures at output or errors
    __error = []
    __warning = []
    for __o in range(len(__output)):
        if 'FAILURE' in __output[__o]:
            __error.append(__output[__o + 1])
    for __o in range(len(__errors)):
        if 'FAILURE' in __errors[__o]:
            if 'Unable to open' in __errors[__o + 1]:
                __error.append(unable_to_open_message())
            else:
                __error.append(__errors[__o + 1])

    # Remove empty lines and search only properties
    # from ogrinfo output
    __output = [
        __o for __o in __output
        if __o != '' and ':' in __o and __o[-1] != ':'
        and 'INFO' not in __o
    ]

    # Save and parse warnings / errors
    if len(__errors):

        # Check if there is any message truly
        if __errors[0] != '':

            # Get first message to be parsed
            __message = __errors[0]
            __errors = __errors[1:]
            __message_list = __error if \
                __message.startswith('ERROR') else __warning
            __message = __message[__message.index(':') + 2:]

            for __e in __errors:

                # Detect if string is an error
                if __e.startswith('ERROR'):
                    if 'Unable to open' in __message:
                        __message = unable_to_open_message()
                    __message_list.append(__message)
                    __message_list = __error
                    __message = __e[__e.index(':') + 2:]

                # Detect if string is a warning
                elif __e.startswith('Warning'):
                    if 'Unable to open' in __message:
                        __message = unable_to_open_message()
                    __message_list.append(__message)
                    __message_list = __warning
                    __message = __e[__e.index(':') + 2:]

                # Detect if string is empty
                elif __e == '':
                    if 'Unable to open' in __message:
                        __message = unable_to_open_message()
                    __message_list.append(__message)

                # Detect if string must be added
                else:
                    __message += ' ' + __e

    # Clean duplicates
    __error = list(set(__error))

    # Clean messages
    for __index in range(0, len(__output)):
        __output[__index] = clean_message(__output[__index])
    for __index in range(0, len(__warning)):
        __warning[__index] = clean_message(__warning[__index])
    for __index in range(0, len(__error)):
        __error[__index] = clean_message(__error[__index])

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
        return settings.generate_error_java_exception(errors)

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
                    __index_dash[__key] = utils.find_string(
                        __message, '-', 2
                    ) + 2

                # Get message
                __m = __message[__index_dash[__key]:]

                # Save message
                __return[__key.lower()].append(__m)

    return __return


##########################################################################


class WorkerGIS(object):
    """ This constructor creates only an instance of a
        GIS library for doing transformations or getting
        information from data following the singleton pattern
        (software design pattern).

    Returns:
        class: GIS Worker

    """

    def __init__(self):

        # Set init values
        self.gis_status = False
        self.geo_status = False

        # Set status of GIS configuration
        if utils.check_env_path(['ogr2ogr', 'ogrinfo']):

            # Check GDAL 2.2.0 version
            try:
                from osgeo import gdal
                version_num = int(gdal.VersionInfo('VERSION_NUM'))
                self.gis_status = version_num > 2020000
            except Exception:
                self.gis_status = False

        self.geo_status = utils.check_env_path(['kitchen.sh', 'pan.sh'])
        self.status = self.gis_status and self.geo_status

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
            return settings.generate_error_extension_not_valid()

        # Get information from path
        __path = utils.parse_path(path)
        __path_shp = __path['folder'] + 'shp' + os.sep
        __path_trs = __path['folder'] + 'trs' + os.sep

        # Check if transformation paths exist
        if os.path.exists(__path_shp) and \
           os.path.exists(__path_trs):
            return settings.generate_error_duplicated_transformation(), \
                None, None, None, None

        # Create arguments for transforming to Shapefile
        __command = [__driver, __path_shp, path]

        # Execute OGR
        __g_info = cmd_ogr2ogr(__command)

        # Generate header of messages
        __header = 'GDAL transformation - ' + \
            datetime.now().strftime('%Y-%m-%d %H:%M') + '\n'

        # Get messages from transformation
        __transform_error = len(__g_info['error'])
        __transform_warn = len(__g_info['warn'])

        # Check if there are some errors
        if __transform_error:
            __g_info['error'][-1] += '\n'
            __g_info['error'] = [__header] + \
                __g_info['error']
            return __g_info, None, \
                None, None, None

        # Check if there are some warnings
        if __transform_warn:
            __g_info['warn'][-1] += '\n'
            __g_info['warn'] = [__header] + \
                __g_info['warn']

        # Get all nodes from directory
        __path_files = os.listdir(__path_shp)

        # Rename and generate SHP structure
        __layers_name = []
        __layers_md5 = {}
        for __path_rev in __path_files:

            # Get information from file
            __path_info = utils.parse_path(__path_rev)

            # Check if md5 is saved
            if __path_info['name'] not in __layers_md5:
                __layers_md5[__path_info['name']] = \
                    utils.md5_string(__path_rev)
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
            if len(__gi_info['error']) or \
               __gi_info['info_values']['features'] == 0 or \
               not check_geo_has_extent(
                   __gi_info['info_values']['bounding']
               ):

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

                # Check if there are some errors
                if len(__gi_info['error']):
                    if __path_rev_i < len(__layers_name) - 1:
                        __gi_info['error'][-1] += '\n'

                    # Check if header is present
                    if not __transform_error:
                        __g_info['error'] = [__header] + \
                            __g_info['error']
                        __transform_error = True

                    # Add error messages
                    __g_info['error'].append(
                        'Layer - ' + __layers_name[__path_rev_i] + '\n'
                    )
                    __g_info['error'] += __gi_info['error']

                # Next file
                continue

            # Validate and save messages
            __raw_validate_info, __rem_features = \
                self.validate_fields(__path_rev)

            # Check if there are some warnings
            if len(__raw_validate_info):
                if __path_rev_i < len(__layers_name) - 1:
                    __raw_validate_info[-1] += '\n'

                # Check if header is present
                if not __transform_warn:
                    __g_info['warn'] = [__header] + \
                        __g_info['warn']
                    __transform_warn = True

                # Add warning messages
                __g_info['warn'].append(
                    'Layer - ' + __layers_md5[
                        __layers_name[__path_rev_i]
                    ] + ' - ' + __layers_name[
                        __path_rev_i
                    ] + '\n')
                __g_info['warn'] += __raw_validate_info

            # # Get updated information from GDAL if
            # some features have been removed
            if __rem_features > 0:
                __gi_info = self.get_info(__path_rev)

            # Generate centroid if is a Polygon
            if __gi_info['info_values']['geometry'] == 'Polygon':

                # Execute centroids generation
                set_centroids(__path_rev)

            # Save layers' information
            __raw_layer_info = __gi_info['info']
            if __path_rev_i < len(__layers_name) - 1:
                __raw_layer_info[-1] += '\n'
            __layers_info['raw'].append([
                'Layer - ' + __layers_md5[
                    __layers_name[__path_rev_i]
                ] + ' - ' + __layers_name[
                    __path_rev_i
                ] + '\n'] + __raw_layer_info)
            __layers_info['info'].append(__gi_info['info_values'])

            # Get information about new information fields
            __raw_fields_info = self.get_fields(__path_rev, False, True)
            if len(__raw_fields_info['info']):
                __layers_fields_info['info'].append({
                    'values': __raw_fields_info['info_values'],
                    'dup': __raw_fields_info['info_extended']
                })
                __raw_fields_info = __raw_fields_info['info']
                if __path_rev_i < len(__layers_name) - 1:
                    __raw_fields_info[-1] += '\n'
                __layers_fields_info['raw'].append([
                    'Layer - ' + __layers_md5[
                        __layers_name[__path_rev_i]
                    ] + ' - ' + __layers_name[
                        __path_rev_i
                    ] + '\n'] + __raw_fields_info)

        # Check if file is empty
        if len(__layers_md5) == len(__paths_index_delete):

            # Check if header is present
            if not __transform_error:
                __g_info['error'] = [__header] + \
                    __g_info['error']

            __g_info['error'].append(
                'An error has occurred in the included files. '
                'Please ensure that the file contains geometries '
                'or information necessary for saving.'
            )

        # Check if file is not a GeoJSON
        elif __driver != 'GeoJSON':

            # Generate VRT for GeoJSON transformation
            __vrt_path = set_vrt(
                __path, __layers_name,
                __paths_index_delete
            )

            # Check folder of transformations
            if not os.path.exists(__path_trs) or \
               not os.path.isdir(__path_trs):
                os.mkdir(__path_trs)

            # Execute transformation to GeoJSON
            __geo_path = __path_trs + __path['name'] + '.geojson'
            cmd_ogr2ogr(['GeoJSON', __geo_path, __vrt_path])

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
            tuple: information about the outputs and
                how many features have been eliminated

        """

        # Get information when executes
        __info = self.get_fields(path)

        # Check if any error exist
        if len(__info['error']):
            return []

        # Validate fields from received information
        __rem_fields, __rem_features = validate_ogr_fields(
            path, __info['info_values'].keys()
        )

        # Set empty return structure
        __log_messages = []

        # Check if new fields is the same previous fields
        if len(__rem_fields):

            # Add new possible warning messages
            __log_messages += [
                'Removed field ' + __f +
                ' because is empty'
                for __f in __rem_fields
            ]

        # Check if some features have been removed
        if __rem_features > 0:

            # Add warning message
            __log_messages += [
                'Removed ' + str(__rem_features) + ' features '
                'because they have not any geometry or the '
                'geometry was not valid.'
            ]

        return __log_messages, __rem_features

    def get_fields(self, path, inc_layers=False, extend=False):
        """ This function allows to get fields' information
            from specific file thanks to GDAL tools.

        Args:
            path (string): file's path
            inc_layers (bool): flag to include layers' name
            extend (bool): flag to include extended info

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
            if 'Geometry:' not in __o
            and 'Feature Count:' not in __o
            and 'Extent: (' not in __o
        ]

        # Check if layers must be included
        if not inc_layers:

            # Remove layer name from info
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
                __field_type = __field_type[
                    :__field_type.index('(') - 1
                ]
                __field_type = str(__field_type).lower()

                # Check field info
                if __field_type == 'real':
                    __field_type = 'float'
                elif __field_type == 'integer64':
                    __field_type = 'long'

                # Save field structure
                __values[__field_name] = __field_type

            # Check if extended information
            if extend:

                # Get extra information
                __info['info_extended'] = \
                    extend_ogr_fields(path, __values)

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
        __ext_src = utils.parse_path(path)['extension']

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
        __ext_src = utils.parse_path(path)['extension']

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
