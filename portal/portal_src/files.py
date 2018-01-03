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

import re
import os
import sys
import crypto
import shutil
import zipfile
import settings
import traceback
import unicodedata
from os.path import splitext

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


config = settings.config


def print_exception(e=None, skip=True):
    """
    Method to log exceptions
    """

    if not skip:
        if e is not None:
            config.error_logger.error(e)
        else:
            tb = traceback.format_exc()
            config.error_logger.error(tb)


##########################################################################


def extract_zip(src_path, dst_path):
    """ This function allows you to extract
        all the files inside a zip file and
        secure against non-secure paths

    Args:
        src_path (string): path of source zip
        dst_path (string): path of destiny folder

    Returns:
        bool: True if everything was good or False otherwise

    """

    try:
        with zipfile.ZipFile(src_path) as __f:
            for __m in __f.infolist():

                # Remove hidden files or
                # bad files from Mac OS
                if 'MACOSX' not in __m.filename and \
                   __m.filename[0] != '.':
                    __f.extract(__m, dst_path)
        return True

    except Exception as e:
        print_exception(e, False)
        return False


def check_shapefiles_path(path):
    """ This function allows you to check
        all the files inside a folder and verify
        if the shapefile is (possible) good

    Args:
        path (string): path of resource

    Returns:
        tuple: boolean status and file name if it is good

    """

    # Shapefile name
    __name = None

    # Shapefile valid extensions
    __shp_ext = [
        '.shp', '.shx', '.shx', '.prj', '.sbn', '.sbx',
        '.dbf', '.fbn', '.fbx', '.ain', '.aih', '.shp.xml'
    ]

    try:
        # Iterate over files of path
        for __file in os.listdir(path):

            # Generate path structure
            __path_info = parse_path(__file)

            # Check if file is original zip file
            if __path_info['extension'] != '.zip':

                # Check if Shapefile's name is empty
                # First iteration
                if __name is None and \
                   __path_info['extension'] in __shp_ext:
                    __name = __path_info['name']
                else:
                    if not __file.startswith(__name):
                        return False, None

    except Exception as e:
        print_exception(e)
        return False, None

    return True, __name


def save_temporal_path(file_storage):
    """ This function allows you to save a
        Flask FileStorage on a temporal path.

    Args:
        file_storage (FileStorage): Flask's file

    Returns:
        string: new temporal path

    """

    # Generate clean name
    __name = clean_string(file_storage.filename)

    # Generate path for specific file
    __temporal_path = os.path.join(
        config.upload_tmp_folder,
        __name
    )

    # Save specific file on folder
    file_storage.save(__temporal_path)

    return __temporal_path


def save_task_path(identifier, path, name, extension):
    """ This function allows you to move a
        temporal file to task path.

    Args:
        identifier (string): internal task id
        path (string): temporal file's path
        name (string): name of file
        extension (string): extension of file

    Returns:
        tuple: new file's path and file's folder

    """

    # Create path for task
    __f = os.path.join(
        config.upload_folder, identifier
    )

    # Delete folder if it is necessary
    shutil.rmtree(__f, ignore_errors=True)

    # Create directory for task
    os.mkdir(__f)

    # Create path for file
    __f_file = os.path.join(
        __f, name + extension
    )

    # Move file to new folder
    shutil.move(path, __f_file)

    return __f_file, __f


def generate_sha_path(path):
    """ This function allows to generate a specific
        identifier from a specific file

    Args:
        path (string): File's path to be cyphered

    Returns:
        string: SHA 256 identifier or None

    """

    # Open file
    __file = open(path, 'r')

    # Get SHA 256 from content
    __sha = crypto.encrypt_sha256_file(__file)

    # Close file before return
    __file.close()

    return __sha


def remove_task_path(identifier):
    """ This function allows you to remove a
        task from upload folder

    Args:
        identifier (string): internal task id

    """

    # Create path for task
    __f = os.path.join(
        config.upload_folder, identifier
    )

    # Delete folder if it is necessary
    shutil.rmtree(__f, ignore_errors=True)


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


def clean_predicate(string):
    """ This function allows you to remove
        latin characters and spaces or bad chars
        from any string.

    Args:
        string (string): predicate to be parsed

    Returns:
        string: parsed value

    """

    # Check if predicate has prefix
    if ':' in string:

        # Split the string
        __string = string.split(':')

        # Check string
        if len(__string) != 2:
            return None

        return clean_string(__string[0]) + ':' + \
            clean_string(__string[1], False)

    else:
        return None


def clean_string(string, lower=True):
    """ This function allows you to remove
        latin characters and spaces or bad chars
        from any string.

    Args:
        string (string): value to be parsed
        lower (bool): flag for lowering string

    Returns:
        string: parsed value

    """

    __string = string.decode("utf-8")
    __form = unicodedata.normalize('NFKD', __string)
    __form = re.sub(r'[^a-zA-Z0-9]', '', u"".join(
        [c for c in __form if not unicodedata.combining(c)]
    ))
    return __form.lower() if lower else __form


def uppercase_words(string):
    """ This function allows you to convert
        a specific string to uppercase (only words)

    Args:
        string (string): value to be parsed

    Returns:
        string: parsed value

    """

    __string = string.decode("utf-8")
    __form = unicodedata.normalize('NFKD', __string)
    return "".join(w.title() for w in re.compile(
        "[^a-zA-Z0-9]+"
    ).split(__form))
