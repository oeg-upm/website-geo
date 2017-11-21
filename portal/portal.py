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
import time
import traceback
from celery import Celery
from portal_src import http
from portal_src import settings
from kombu import Exchange, Queue
from flask import Flask, request, url_for, send_from_directory

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
cwd = os.path.dirname(os.path.realpath(__file__))


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


class Singleton(type):
    """
    Method to create singleton pattern
    """

    def __call__(cls, *args, **kwargs):
        try:
            return cls.__instance
        except AttributeError:
            cls.__instance = super(Singleton, cls).__call__(*args, **kwargs)
            return cls.__instance


class Portal(object):
    """
    Method to create class
    """

    __metaclass__ = Singleton

    def __init__(self):

        # Generate basic structure
        self.app = None
        self.celery = None
        self.celery_report = None

        # Generate structures
        self.generate_flask_app()
        self.generate_celery_app()

        # Add Errors and trace endpoints
        self.generate_trace_endpoints()

        # Add Endpoints
        self.generate_fav_endpoints()
        self.generate_root_endpoints()

    def generate_flask_app(self):
        """ Method to configure flask parameters

        """

        self.app = Flask(
            __name__, template_folder=cwd + '/portal_src/templates',
            static_folder=cwd + '/portal_src/static'
        )
        self.app.debug = config.debug
        self.app.logger.disabled = True
        self.app.jinja_env.trim_blocks = True
        self.app.jinja_env.lstrip_blocks = True

    def generate_celery_app(self):
        """ Method to configure celery parameters

        """

        # Create new Celery instance
        self.celery = Celery('portal_sender')

        # Configure exchanges of RabbitMQ
        default_exchange = Exchange('geo.default', type='direct')
        mapping_exchange = Exchange('geo.mapping', type='direct')

        # Get RabbitMQ URL
        self.celery.conf.broker_url = 'pyamqp://' + \
            config.celery_user + ':' + config.celery_pwd + '@' + \
            config.celery_host + '//'

        # Compatibility with previous AMQP protocols
        self.celery.conf.task_protocol = 1

        # Configure queues of RabbitMQ
        self.celery.conf.task_queues = (
            Queue(
                'geo-mapping-create', mapping_exchange,
                routing_key='geo.mapping.create'
            ),
            Queue(
                'geo-mapping-extend', mapping_exchange,
                routing_key='geo.mapping.extend'
            ),
            Queue(
                'geo-default', default_exchange,
                routing_key='geo.default'
            )
        )

        # Configure default queue of RabbitMQ
        self.celery.conf.task_default_queue = 'geo-default'
        self.celery.conf.task_default_exchange_type = 'direct'
        self.celery.conf.task_default_routing_key = 'geo.default'

        # Update configuration with flask parameters
        self.celery.conf.update(self.app.config)

    def generate_trace_endpoints(self):
        """ Method to catch exceptions

        """

        @self.app.errorhandler(Exception)
        def exceptions(e):
            tb = traceback.format_exc()
            timestamp = time.strftime('[%Y-%b-%d %H:%M]')
            config.error_logger.error(
                '%s %s %s %s %s Exception !\n%s', timestamp,
                request.remote_addr, request.method,
                request.scheme, request.full_path, tb
            )
            if 'status_code' in e:
                return e.status_code
            else:
                return '', 500

        @self.app.after_request
        def after_request(response):
            timestamp = time.strftime('[%Y-%b-%d %H:%M]')
            config.flask_logger.info(
                '%s %s %s %s %s %s', timestamp, request.remote_addr,
                request.method, request.scheme, request.full_path,
                response.status
            )
            return response

        @self.app.errorhandler(400)
        def error_400(e):
            print_exception(e, False)
            return http.generate_redirection('400')

        @self.app.errorhandler(500)
        def error_500(e):
            print_exception(e, False)
            return http.generate_redirection('400')

        @self.app.errorhandler(401)
        def error_401(e):
            print_exception(e)
            return http.generate_redirection('401')

        @self.app.errorhandler(403)
        def error_403(e):
            print_exception(e)
            return http.generate_redirection('401')

        @self.app.errorhandler(404)
        def error_404(e):
            print_exception(e)
            return http.generate_redirection('404')

        @self.app.errorhandler(405)
        def error_405(e):
            print_exception(e)
            return http.generate_error_response('Method not allowed', 405)

        @self.app.errorhandler(406)
        def error_406(e):
            print_exception(e)
            return http.generate_error_response('Bad Accept HTTP header', 406)

        @self.app.errorhandler(415)
        def error_415(e):
            print_exception(e)
            return http.generate_error_response('Type not supported', 415)

        @self.app.errorhandler(422)
        def error_422(e):
            print_exception(e)
            return http.generate_error_response('Bad format', 422)

    def generate_fav_endpoints(self):
        """ Method for generating favicon compatibility

        """

        @self.app.route('/favicon.ico')
        def favicon():
            return send_from_directory(
                cwd + '/static/img-fav', 'favicon.ico',
                mimetype='image/vnd.microsoft.icon'
            )

    def generate_root_endpoints(self):
        """ Method for generating root endpoints

        """

        @self.app.route('/', methods=['GET'])
        def root():
            """ Decorator for / endpoint

            Returns:
                Response: Website root

            """

            return http.generate_render(self.app, request, 'base')          


# Create instance and export Flask app
portal = Portal()
app = portal.app

# Save celery to global reference for getting
# from other python resources (same memory pointer)
config.CELERY_APP = portal.celery

if __name__ == '__main__':

    app.run(
        threaded=config.debug, host='0.0.0.0',
        port=config.flask_port
    )
