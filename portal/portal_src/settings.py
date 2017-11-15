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

import os
import sys
import json
import logging.handlers

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


class Singleton(type):

    def __call__(cls, *args, **kwargs):
        try:
            return cls.__instance
        except AttributeError:
            cls.__instance = super(Singleton, cls).__call__(*args, **kwargs)
            return cls.__instance


class Config(object):
    __metaclass__ = Singleton

    def __init__(self):

        def get_configuration_file():
            """ This function allows you to load a configuration from file.

            Returns:
                 dict: configuration fields and values.

            """

            # Configuration folder
            __config_path = os.path.dirname(os.path.realpath(__file__)) + \
                os.sep + 'configuration.json'

            # Open file to load configuration
            with open(__config_path) as __file_data:

                # Return dictionary as configuration
                __dict = dict(json.load(__file_data))
                return __dict

        # Get configuration for the current instance
        settings = get_configuration_file()
        self.debug = logging.DEBUG if settings['debug'] else logging.INFO

        # FLASK CONFIGURATION
        self.flask_port = settings['web']['port']
        self.flask_host = settings['web']['url'] if self.flask_port == 80 or \
            self.flask_port == 443 else settings['web']['url'] + \
            ':' + str(self.flask_port)
        self.flask_keys = settings['keys']

        # CELERY CONFIGURATION
        self.celery_port = settings['celery']['port']
        self.celery_host = settings['celery']['url'] if self.celery_port == 80 or \
            self.celery_port == 443 else settings['celery']['url'] + \
            ':' + str(self.celery_port)
        self.celery_user = settings['celery']['username']
        self.celery_pwd = settings['celery']['password']

        # LOGGING
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s - %(message)s"
        )
        self.flask_logger = logging.Logger("portal-logger")
        flask_handler = logging.handlers.RotatingFileHandler(
            settings['logging'], maxBytes=1024 * 1024,
            backupCount=5
        )
        flask_handler.setLevel(self.debug)
        flask_handler.setFormatter(formatter)
        self.flask_logger.addHandler(flask_handler)
        self.error_logger = logging.Logger('portal-error-logger')
        error_logger_handler = logging.handlers.RotatingFileHandler(
            settings['logging'].replace('.log', '.error.log'),
            maxBytes=1024 * 1024, backupCount=5
        )
        error_logger_handler.setLevel(logging.DEBUG)
        error_logger_handler.setFormatter(formatter)
        self.error_logger.addHandler(error_logger_handler)
        internal_logger = logging.getLogger('werkzeug')
        internal_logger.disabled = True
