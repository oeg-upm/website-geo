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
import shutil
import threading
import logging.handlers
from ontospy import Ontospy

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


class Singleton(object):

    _instance = None
    _lock = threading.RLock()

    @staticmethod
    def get_instance():
        if Singleton._instance is None:
            Singleton._lock.acquire()
            if Singleton._instance is None:
                Singleton._instance = Singleton()
            Singleton._lock.release()
        return Singleton._instance
    
    def __init__(self):

        def check_upload_folder(path):
            """ This function allows you to check if the
                path is accessible. If it is False, it will
                create the folder for the application.

            Args:
                path (string): path of the folder

            """

            try:

                # Create directory directly
                os.makedirs(path)
                return True
            except OSError:

                # If the directory does not exist
                if not os.path.isdir(path):
                    raise Exception(
                        'Check the upload folder: ' + path
                    )
                return True

        def get_configuration_semantic():
            """ This function iterates over all the declared namespaces
                and get the object from ontologies

            Returns:
                dict: configuration ontologies.

            """

            # Create structure for ontologies
            __onto = {}

            # Iterate over namespaces
            for __ns in self.semantic_ns:

                # Optional link
                if 'link' in __ns:
                    __onto[__ns['name']] = Ontospy(__ns['link'])
                else:
                    __onto[__ns['name']] = Ontospy(__ns['url'])

            return __onto

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

        def get_configuration_translations():
            """ This function allows you to load translation files.

            Returns:
                 dict: translations fields and values.

            """

            __translations = {}

            # Configuration folder
            __config_path = os.path.dirname(os.path.realpath(__file__))

            # Get current files of the current directory
            __files = os.listdir(__config_path)

            # Iterate over files
            for __file in __files:

                # Check if file is a translation file
                if 'configuration_' in __file:

                    # Get language from file
                    __lang = __file[14:].replace('.json', '')

                    # Open file to load configuration
                    with open(__config_path + os.sep + __file) as __file_data:

                        # Return dictionary as configuration
                        __translations[__lang] = dict(json.load(__file_data))

            return __translations

        # Get configuration for the current instance
        settings = get_configuration_file()
        self.debug = logging.DEBUG if settings['debug'] else logging.INFO

        # FLASK CONFIGURATION
        self.flask_port = settings['web']['port']
        self.flask_host = settings['web']['url'] if self.flask_port == 80 or \
            self.flask_port == 443 else settings['web']['url'] + \
            ':' + str(self.flask_port)

        # UPLOAD CONFIGURATION
        if check_upload_folder(settings['upload']['folder']):
            self.upload_folder = settings['upload']['folder']
        shutil.rmtree(
            settings['upload']['tmp'],
            ignore_errors=True
        )
        if check_upload_folder(settings['upload']['tmp']):
            self.upload_tmp_folder = settings['upload']['tmp']
        self.upload_limit = settings['upload']['max_uploads']
        self.upload_size = settings['upload']['max_size']
        self.upload_mime = settings['upload']['types']

        # CELERY CONFIGURATION
        self.celery_port = settings['celery']['port']
        self.celery_host = settings['celery']['url'] if self.celery_port == 80 or \
            self.celery_port == 443 else settings['celery']['url'] + \
            ':' + str(self.celery_port)
        self.celery_user = settings['celery']['username']
        self.celery_pwd = settings['celery']['password']

        # DATABASE CONFIGURATION
        self.redis = settings['redis']
        self.redis_cache = settings['redis_cache']
        self.redis_worker = settings['redis_worker']

        # SEMANTIC CONFIGURATION
        self.semantic_ns = settings['namespaces']
        self.semantic_nsd = {k['name']: k['url'] for k in self.semantic_ns}
        self.semantic_nso = get_configuration_semantic()

        # TRANSLATIONS
        self.translations = get_configuration_translations()

        # SECURITY KEYS
        self.keys = {
            'captcha': settings['keys']['google_captcha'],
            'captcha_server': settings['keys']['google_captcha_server'],
            'analytics': settings['keys']['google_analytics'],
            'crypto': settings['keys']['cryptography'],
            'master': settings['keys']['master']
        }

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

        Singleton._instance = self

    def check_rdf_property(self, uri_predicate, type_object):
        """ This function allows you to check if URI
            of the predicate and object are good. Also,
            it searches if the namespace is known.

        Args:
            self (Singleton): configuration object
            uri_predicate (string): predicate's URI
            type_object (string): object's URI

        Returns:
            bool: True if everything was good or
                False otherwise

        """

        # Set namespaces
        __ns_known = None

        # Iterate over namespaces
        for __ns in self.semantic_nsd.keys():
            if not uri_predicate.startswith('http'):
                if uri_predicate.startswith(__ns + ':'):
                    __ns_known = __ns
                    break
            else:
                if uri_predicate.startswith(
                    self.semantic_nsd[__ns]
                ):
                    __ns_known = __ns
                    break

        # Returns the same because we need to
        # trust on the user knowledge
        if __ns_known is None:
            return uri_predicate.startswith('http')

        # Get property from ontology
        __predicate = uri_predicate
        if not uri_predicate.startswith('http'):
            __predicate = __predicate.replace(
                __ns_known + ':',
                self.semantic_nsd[__ns_known]
            )
        __p = self.semantic_nso[__ns_known].getProperty(
            uri=__predicate
        )

        # Check if the property exists
        if __p is None:
            return False

        # Check if range exists
        if not len(__p.ranges) and \
           type_object == 'rdfs:Literal':
            return True

        # Iterate over the ranges
        for __r in __p.ranges:

            # Check if type is good
            if __r.qname == type_object:
                return True

        return False

    lockPrint = threading.Lock()


config = Singleton.get_instance()
