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
from geo_worker_log import WorkerLogger

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

    try:
        from osgeo import ogr, osr, gdal
        return True
    except Exception:
        return False


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

        if self.status:

            # Create logger for this Python script
            self.logger = WorkerLogger()
