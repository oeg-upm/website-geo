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
import json
import logging
from logging.handlers import RotatingFileHandler

__author__ = "Alejandro F. Carrera"
__copyright__ = "Copyright 2017 © GeoLinkeddata Platform"
__credits__ = ["Alejandro F. Carrera", "Oscar Corcho"]
__license__ = "Apache"
__version__ = "2.0"
__maintainer__ = "Alejandro F. Carrera"
__email__ = "alejfcarrera@mail.ru"


##########################################################################


def get_configuration_file():
    """ This function allows you to load a configuration from file.

    Returns:
        Dict: Return configuration constraints.

    """

    # Configuration folder
    base_path = './geo_worker_config'

    # Check if application is on Debug mode
    if int(os.environ.get('OEG_DEBUG_MODE', 1)) == 1:

        # Get development configuration
        config_file_path = os.environ.get(
            'OEG_CONFIG_DEBUG_FILE', base_path + '/config_debug.json'
        )
    else:

        # Get production configuration
        config_file_path = os.environ.get(
            'OEG_CONFIG_FILE', base_path + '/config_production.json'
        )

    # Load current directory of geo_worker.py
    cwd = os.path.dirname(os.path.realpath(__file__)) + '/'

    # Open file to load configuration
    with open(cwd + config_file_path) as data_file:

        # Return dictionary as configuration
        return dict(json.load(data_file))


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


class WorkerLogger(object):
    """ This constructor creates only an instance of a Logger
        following the singleton pattern (software design pattern).

    """

    # Create singleton instance
    __metaclass__ = Singleton

    def __init__(self):
        
        # Create logger - formatter
        logger_formatter = logging.Formatter(
            fmt='%(asctime)s %(levelname)-8s %(message)s',
            datefmt='%a, %d %b %Y %H:%M:%S'
        )

        # Create logger - handler
        logger_handler = RotatingFileHandler(
            get_configuration_file()['logging'],
            maxBytes=10*1024*1024, backupCount=5
        )
        logger_handler.setFormatter(logger_formatter)

        # Create logger
        self.log = logging.getLogger("WorkerLogger")

        # Set configuration for logger
        self.log.setLevel(logging.DEBUG)
        self.log.addHandler(logger_handler)
