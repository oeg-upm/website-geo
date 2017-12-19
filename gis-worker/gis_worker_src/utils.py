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
import hashlib
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


def check_env_path(executables):
    """ This function detects if executables are included
        on the current environment (PATH variable). This is important
        to avoid full path directories and to be sure that these tools
        are available to execute them.

    Returns:
        bool: True if tools exist, False otherwise.

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

            # Check if executables are on the folder
            s = set(path_files).intersection(set(executables))

            # Check if length of s is the same of source
            if len(s) == len(executables):
                return True

    # Executables were not found
    return False


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
        's4lt0.g30l4nk3dd4t4.3s'
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
