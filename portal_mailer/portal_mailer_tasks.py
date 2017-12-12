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

import sys
import smtplib
import traceback
from celery.task import task
from email.header import Header
from email.mime.text import MIMEText
from portal_mailer_src import settings
from celery.utils.log import get_task_logger

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


def print_exception(e=None, skip=True):
    """
    Method to log exceptions
    """

    if not skip:

        # Create logger to log messages to specific log file
        __logger = get_task_logger(__name__)

        if e is not None:
            config.error_logger.error(e)
            __logger.error(e)

        else:
            tb = traceback.format_exc()
            config.error_logger.error(tb)
            __logger.error(tb)


##########################################################################


def send_generic_email(msg):
    """ Method to send a generic email with specific metadata

    Args:
        msg (MIMEText): message to be send

    """

    try:
        __smtp = smtplib.SMTP_SSL(
            host=config.mailer_server, port=config.mailer_port,
            local_hostname=config.mailer_host, timeout=60
        )
        __smtp.set_debuglevel(config.debug)
        __smtp.ehlo()
        __smtp.login(config.mailer_sender, config.mailer_pwd)
        __smtp.sendmail(msg['From'], msg['To'], msg.as_string())
        __smtp.quit()
    except Exception as e:
        print_exception(e)


##########################################################################


@task(bind=True, name='portal_mailer_tasks.send_contact_notification', max_retries=5)
def send_contact_email(self, name, email, subject, description):
    """ This function allows create an initial mapping
        from a specific task from AMQP messages.

    Args:
        self (Celery): celery request
        name (string): name of contact's form
        email (string): email of contact's form
        subject (string): subject to be send
        description (string): issue or request to be send

    """

    try:

        # Generate plain text for email
        __text = '\n'
        __text += ' * Nombre: ' + name + '\n'
        __text += ' * Email: ' + email + '\n'
        __text += ' * Descripción:\n'
        __text += description + '\n'
        __text = __text.decode('utf8')

        # Generate Email
        __msg = MIMEText(__text.encode('utf-8'), 'plain', 'utf-8')
        __msg['Subject'] = Header('[Contacto] - ' + subject, 'utf-8')
        __msg['From'] = config.mailer_sender
        __msg['To'] = config.mailer_inbox
        send_generic_email(__msg)

    except Exception as exc:

        # Retry task (max 5)
        if self.request.retries < 5:
            raise self.retry(
                exc='', countdown=(self.request.retries + 1) * 1
            )
        else:
            print_exception(exc, False)


@task(bind=True, name='portal_mailer_tasks.default', max_retries=5)
def default(self):
    """ This function allows to receive the messages from
        the default queue from AMQP messages.

    Args:
        self (Celery): celery request

    """
    
    # Create logger to log messages to specific log file
    logger = get_task_logger(__name__)

    # Print message
    logger.warn('\n * Received task from default queue')
