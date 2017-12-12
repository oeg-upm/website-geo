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

import sys
from celery import Celery
from kombu import Exchange, Queue
from portal_mailer_src import settings


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


class Singleton(type):
    """ Method to create singleton pattern

    """

    def __call__(cls, *args, **kwargs):
        try:
            return cls.__instance
        except AttributeError:
            cls.__instance = super(Singleton, cls).__call__(*args, **kwargs)
            return cls.__instance


class PortalMailer(object):
    """ Method to create class

    """

    _metaclass__ = Singleton

    def __init__(self):

        # Generate basic structure
        self.app = None

        # Generate structures
        self.generate_celery_app()

    def generate_celery_app(self):
        """ This function allows to configure a Celery instance.
        """

        # Create new Celery instance
        self.app = Celery('portal_mailer')

        # Configure exchanges of RabbitMQ
        default_exchange = Exchange('geo.default', type='direct')
        mailer_exchange = Exchange('geo.mailer', type='direct')

        # Get RabbitMQ URL
        self.app.conf.broker_url = 'pyamqp://' + \
            config.celery_user + ':' + config.celery_pwd + '@' + \
            config.celery_host + '//'

        # Compatibility with previous AMQP protocols
        self.app.conf.task_protocol = 1

        # Import registered tasks
        self.app.conf.imports = ('portal_mailer_tasks',)

        # Configure queues of RabbitMQ
        self.app.conf.task_queues = (
            Queue(
                'geo-mailer-contact', mailer_exchange,
                routing_key='geo.mailer.contact'
            ),
            Queue(
                'geo-default', default_exchange,
                routing_key='geo.default'
            )
        )

        # Configure default queue of RabbitMQ
        self.app.conf.task_default_queue = 'geo-default'
        self.app.conf.task_default_exchange_type = 'direct'
        self.app.conf.task_default_routing_key = 'geo.default'

        # Configure tasks of Celery - RabbitMQ
        self.app.conf.task_routes = {
            'portal_mailer_tasks.send_contact_notification': {
                'queue': 'geo-mailer-contact',
                'exchange': mailer_exchange,
                'routing_key': 'geo.mailer.contact'
            },
            'portal_mailer_tasks.default': {
                'queue': 'geo-default',
                'exchange': default_exchange,
                'routing_key': 'geo.default'
            }
        }


# Create Celery Worker and export Celery app
worker = PortalMailer()
app = worker.app
