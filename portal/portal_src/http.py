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
import time
import random
import crypto
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


config = settings.config
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
    if cookie_token in request.cookies and __headers['logged']:
        __headers['user_token'] = request.cookies[cookie_token]
    else:
        __headers['logged'] = False

    # Get language cookie or default value
    if cookie_language in request.cookies:
        __headers['device_lang'] = request.cookies[cookie_language]
        __headers['device_lang_present'] = True
    else:
        __headers['device_lang'] = 'es'
        __headers['device_lang_present'] = False

    # Check device is present
    if cookie_device in request.cookies:
        __headers['device_token'] = request.cookies[cookie_device]
        __headers['device_token_present'] = True

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
        __headers['device_token_present'] = False

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


def generate_redirection(
    url='', clean=False, next_url=None, user_id=None,
    user_token=None
):
    """ This function allows to generate a redirection
        to the specific URL with some settings.

    Args:
        url (string): url to add (optional)
        clean (bool): flag to delete all cookies (optional)
        next_url (string): url to redirect (optional)
        user_id (string): identifier cookie (optional)
        user_token (string): user token cookie (optional)

    Returns:
        Response: flask response (redirect)

    """

    # Create base URL
    __url = url if url[0] != '/' else url[1:]
    __url = config.flask_host + '/' + __url

    # Add next URL param if it is necessary
    if next_url is not None:
        __url += '?next=' + next_url

    # Create base response
    __response = redirect(__url)

    # Set new expiration time
    __expire = int(time.time() + 2419200)

    # Check if remove is necessary
    if clean:
        __response.delete_cookie(cookie_token, path='/')
        __response.delete_cookie(cookie_user, path='/')
    else:

        # Add identifier cookie
        if user_id is not None:
            __response.set_cookie(
                cookie_user, value=user_id,
                path='/', expires=__expire,
                httponly=False
            )

        # Add token cookie
        if user_token is not None:
            __response.set_cookie(
                cookie_token, value=user_token,
                path='/', expires=__expire,
                httponly=False
            )

    return __response


def generate_error_render(headers, value=''):
    """ This function allows to generate the render of a
        custom path of the domain. It allows to set a
        specific language and also injected parameters
        to the html file through Jinja2 template.

    Args:
        headers (dict): dict with values about request
        value (string): string to be merged with values

    Returns:
        Response: rendered template

    """

    return generate_render(
        'error', headers, {'error': value},
        int(value.split('-')[0])
    )


def generate_render(html_name, headers, values=None, status=200):
    """ This function allows to generate the render of a
        custom path of the domain. It allows to set a
        specific language and also injected parameters
        to the html file through Jinja2 template.

    Args:
        html_name (string): name to search on templates
        headers (dict): dict with values about request
        values (dict): dict to be merged with kargs
        status (int): status code of HTTP response

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

    # Check if error is present
    if 'error' not in __values:
        __values['error'] = False

    # Return rendered template
    r = make_response(
        render_template(__html_name, **__values),
        status
    )
    r.headers['content-type'] = 'text/html; charset=utf-8'
    r.headers['content-language'] = __locale

    # Set cookies if it is necessary
    if not headers['device_lang_present']:
        r.set_cookie(
            cookie_language, path='/',
            value=headers['device_lang'],
        )
    if not headers['device_token_present']:
        r.set_cookie(
            cookie_device, path='/',
            value=headers['device_token']
        )

    return r


##########################################################################


def generate_cookie(identifier):
    """ This function allows to create a cookie for
        a specific identifier.

    Args:
        identifier (string): internal user id

    Returns:
        string: SHA 256 cookie or None

    """

    return crypto.encrypt_sha256(
        '|id=' + identifier +
        '|salt=' + 's4lt0.g30l4nk3dd4t4.3s'
    )
