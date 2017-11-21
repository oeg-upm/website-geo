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
import settings
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


def generate_complete_redirection(request):
    """ This function allows to generate a redirection
        to the domain directly.

    Args:
        request (Request): request to be rebuilt

    Returns:
        Response: flask response (redirect)

    """

    resp = redirect(config.flask_host + '/')
    clean_all_cookies(resp, request)
    return resp


def generate_redirection(url, next_url=None):
    """ This function allows to generate a redirection
        to a custom path of the domain directly.

    Args:
        url (string): path to go
        next_url (string): path to go next

    Returns:
        Response: flask response (redirect)

    """

    __url = config.flask_host + '/' + url
    if next_url is not None:
        __url += '?next=' + next_url
    resp = redirect(__url)
    return resp


def generate_render(app, request, html_name, values=None):
    """ This function allows to generate the render of a
        custom path of the domain. It allows to set a
        specific language and also injected parameters
        to the html file through Jinja2 template.

    Args:
        app (Flask): flask application to load the render
        request (Request): request to be analysed
        html_name (string): name to search on templates
        values (dict): dict to be merged with kargs

    Returns:
        Response: rendered template

    """

    # Get locale from cookies if it is available
    # Format: ISO 639-1 code
    __locale = request.cookies.get(cookie_language, 'en')

    # Set language to file name or not otherwise
    __html_name = html_name
    if __locale != 'en':
        __html_name += '_' + __locale
    __html_name += '.html'

    # Set new values to jinja arguments
    __values = {} if values is None else values.copy()
    __values['headers'] = {
        'debug': config.debug, 'locale': __locale,
        'domain': config.flask_host,
        'time': datetime.utcnow()
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
