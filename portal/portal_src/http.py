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
import json
import uuid
import crypto
import random
import settings
import user_agents
from datetime import datetime
from flask import redirect, make_response, render_template

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
cookie_language = '_geo_portal_lang'
cookie_user = '_geo_portal_usr_id'
cookie_token = '_geo_portal_usr_token'
cookie_device = '_geo_portal_usr_device'


##########################################################################


def parse_headers(request):
    """ This function allows to parse all the cookies stored
        on a request and the User Agent too.

    Args:
        request (Request): request to be parsed

    Returns:
        dict: headers values including login status

    """

    # Init parameters
    __headers = {'logged': True}

    # Check user is present
    if cookie_user in request.cookies:
        __headers['user_id'] = request.cookies[cookie_user]
    else:
        __headers['logged'] = False

    # Check token is present
    if cookie_token in request.cookies:
        __headers['user_token'] = request.cookies[cookie_token]
    else:
        __headers['logged'] = False

    # Get language cookie or default value
    __headers['device_lang'] = request.cookies.get(
        cookie_language, 'en'
    )

    # Check device is present
    if cookie_device in request.cookies:
        __headers['device_token'] = request.cookies[cookie_device]

    # Create device token
    else:

        # Generate constraints
        __ua = user_agents.parse(request.user_agent.string)
        __device_is_present = __ua.device.model is not None
        __device_value = __ua.device.model + ' (' if \
            __device_is_present else ''

        # Join OS and Browser version
        __device_value += __ua.os.family + ' ' + \
            __ua.os.version_string + ', ' + \
            __ua.browser.family + ' ' + \
            __ua.browser.version_string
        if __device_is_present:
            __device_value += ')'

        # Join UUID
        __device_value += '-|-' + uuid.uuid4().hex

        # Get one of random key
        __crp_number = random.randint(
            0, len(config.keys['crypto']) - 1
        )
        __crp_key = config.keys['crypto'][__crp_number]
        __device_value = crypto.encrypt_aes256(
            __device_value, __crp_key
        )
        __device_value += str(__crp_number)
        __headers['device_token'] = __device_value

    # Return information
    return __headers


##########################################################################


def generate_error_response(error_message, status):
    """ This function allows to generate a custom response
        with application/json Content-Type header and
        custom error message and status code.

    Args:
        error_message (string): message to print
        status (int): HTTP status code

    Returns:
        Response: flask response

    """

    return generate_json_response({
        "message": error_message,
        "code": str(status)
    }, status)


def generate_json_response(json_object, status=200):
    """ This function allows to generate a custom response
        with application/json Content-Type header and
        custom json and status code.

    Args:
        json_object (dict): json to return
        status (int): HTTP status code, by default OK

    Returns:
        Response: flask response

    """

    resp = make_response(json.dumps(json_object), status)
    resp.headers['Content-Type'] = 'application/json'
    return resp


def generate_complete_redirection(request, url=None):
    """ This function allows to generate a redirection
        to the domain directly.

    Args:
        request (Request): request to be rebuilt
        url (string): url to add (optional)

    Returns:
        Response: flask response (redirect)

    """

    __url = config.flask_host + '/'
    if url is not None:
        __url += url
    resp = redirect(__url)
    clean_all_cookies(resp, request)
    return resp


def generate_redirection(url, next_url=None):
    """ This function allows to generate a redirection
        to a custom path of the domain directly.

    Args:
        url (string): path to go
        next_url (string): path to go next (optional)

    Returns:
        Response: flask response (redirect)

    """

    __url = config.flask_host + '/' + url
    if next_url is not None:
        __url += '?next=' + next_url
    resp = redirect(__url)
    return resp


def generate_render(app, html_name, headers, values=None):
    """ This function allows to generate the render of a
        custom path of the domain. It allows to set a
        specific language and also injected parameters
        to the html file through Jinja2 template.

    Args:
        app (Flask): flask application to load the render
        html_name (string): name to search on templates
        headers (dict): dict with values about request
        values (dict): dict to be merged with kargs

    Returns:
        Response: rendered template

    """

    # Get locale from cookies if it is available
    # Format: ISO 639-1 code
    __locale = headers['device_lang']

    # Set language to file name or not otherwise
    __html_name = html_name + '.html'

    # Set new values to jinja arguments
    __values = {} if values is None else values.copy()
    __values['headers'] = {
        'session': headers, 'tokens': config.keys,
        'debug': config.debug, 'time': datetime.utcnow(),
        'translations': config.translations[__locale],
        'domain': config.flask_host
    }

    # Return rendered template
    r = app.make_response(render_template(__html_name, **__values))
    r.headers['content-type'] = 'text/html; charset=utf-8'
    r.headers['content-language'] = __locale
    return r


##########################################################################


def clean_all_cookies(response, request):
    """ This function allows to clean a request from
        all the possible cookies else language cookie.
        To do this, it sets the deletion on the
        custom response passed by parameter.

    Args:
        response (Response): response to be rebuilt
        request (Request): request to be parsed

    """

    for i in request.cookies:
        if i != cookie_language:
            response.delete_cookie(i, path='/')
