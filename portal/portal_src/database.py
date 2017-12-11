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

import re
import sys
import redis
import crypto
import settings
import traceback
from random import randint
from redis import TimeoutError, ConnectionError

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
expire_one_day = 86400
expire_one_week = 604800
expire_one_month = 2419200
regex_username = re.compile('^[A-Za-z0-9_.]{4,20}$')
regex_email = re.compile('^[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,4}$')
regex_password = re.compile('^[A-Za-z0-9@#$%^&+=]{8,}$')
regex_url = re.compile(
    r'^(?:[a-z0-9\.\-\+]*)://'  # scheme
    r'(?:\S+(?::\S*)?@)?'  # user:pass authentication
    r'(?:' + r'(?:25[0-5]|2[0-4]\d|[0-1]?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}' +  # ipv4
    '|' + r'\[[0-9a-f:\.]+\]' +  # ipv6
    '|' + '(' + r'[a-z' + '\u00a1-\uffff' + r'0-9](?:[a-z' + '\u00a1-\uffff' +
    r'0-9-]{0,61}[a-z' + '\u00a1-\uffff' + r'0-9])?' + r'(?:\.(?!-)[a-z' +
    '\u00a1-\uffff' + r'0-9-]{1,63}(?<!-))*' + (
        r'\.'  # dot
        r'(?!-)'  # can't start with a dash
        r'(?:[a-z' + '\u00a1-\uffff' + '-]{2,63}'  # domain
        r'|xn--[a-z0-9]{1,59})'  # punycode
        r'(?<!-)'  # can't end with a dash
        r'\.?'  # may have a trailing dot
    ) + '|localhost)' + ')'
    r'(?::\d{2,5})?'  # port
    r'(?:[/?#][^\s]*)?'  # resource path
    r'\Z', re.IGNORECASE)


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


def create_redis_pool(redis_host, redis_port, redis_pass, redis_db):
    """ This function creates a connection pool for Redis Database
        with a specific configuration. This is important to create
        connections and execute queries easily.

    Args:
        redis_host (string): host where Redis is available
        redis_port (int): port for Redis connection
        redis_pass (string): password for Redis connection
        redis_db (int): database for Redis client

    Returns:
        class: Redis Pool or None if something went wrong

    """

    __redis_pool = redis.ConnectionPool(
        socket_connect_timeout=5,
        host=redis_host,
        port=redis_port,
        password=redis_pass,
        db=redis_db
    )
    try:

        # Detect if Redis is running
        __connection = __redis_pool.get_connection('ping')
        __connection.send_command('ping')
        return __redis_pool

    except (ConnectionError, TimeoutError):

        # Disconnect connection pool
        __redis_pool.disconnect()

        return None


def configure_redis(configuration):
    """ This function creates a connection pool for any of Redis
        configuration saved on configuration parameter.

    Args:
        configuration (dict): settings for Redis

    Returns:
        dict: Redis connection pools

    """

    __number_redis = 0
    __redis_connections = {}
    __redis_pools = {}

    # Generate connection pools to Redis Database
    for __redis_name in configuration['dbs']:

        # Create new connection pool
        __redis_pools[__redis_name] = create_redis_pool(
            configuration['host'], configuration['port'],
            configuration['pass'], __number_redis
        )

        # Test connection pool
        if __redis_pools[__redis_name] is None:

            # Disconnect other connection pools
            for __redis_pool_name in __redis_pools.keys():
                if __redis_pools[__redis_pool_name] is not None:
                    __redis_pools[__redis_pool_name].disconnect()

            return None

        else:

            # Save connection to structure
            __redis_connections[__redis_name] = redis.Redis(
                connection_pool=__redis_pools[__redis_name]
            )

            config.flask_logger.info(
                'Redis DB (' + __redis_name + ') '
                'connected at port: ' + str(configuration['port'])
            )

        # Add new number for next connection pool
        __number_redis += 1

    return __redis_connections


# Execute method to create new instance Redis
__redis = configure_redis(config.redis)

# Execute method to create new instance of Redis Cache
__redis_cache = configure_redis(config.redis_cache)

# Raise exception if any of databases are not connected
if __redis is None or __redis_cache is None:
    raise Exception('Bad redis configuration or not running')


##########################################################################


def generate_identifier(dictionary, kind):
    """ This function allows to generate a specific
        identifier from a specific dictionary

    Args:
        dictionary (dict): values to be cyphered
        kind (string): kind to append at identifier

    Returns:
        string: SHA 256 identifier or None (22 length)

    """

    # Generate string from values
    __values = ''
    for __key in dictionary.keys():
        __values += '|%s=%s' % (__key, dictionary[__key])

    # Generate identifier
    return crypto.encrypt_sha256(__values)[0:16] + \
        kind + str(randint(0, 10000))


def check_csrf(headers, csrf_token):
    """ This function allows to check if a specific
        csrf token exists

    Args:
        headers (dict): HTTP headers
        csrf_token (string): CSRF token

    Returns:
        bool: True if it exists or False otherwise

    """

    # Check if device exists
    if __redis_cache['tokens'].exists(
        headers['device_token']
    ):

        # Get CSRF token
        __csrf = __redis_cache['tokens'].get(
            headers['device_token']
        )

        if __csrf is None:

            return False

        else:

            # Delete CSRF token
            __redis_cache['tokens'].delete(
                headers['device_token']
            )

            return __csrf == csrf_token

    else:
        return False


def set_csrf(headers):
    """ This function allows to generate a specific
        csrf token from a specific headers

    Args:
        headers (dict): HTTP headers

    Returns:
        string: SHA 256 identifier or None

    """

    # Generate CSRF token
    __csrf = crypto.encrypt_sha256(
        '|lang=' + headers['device_lang'] +
        '|device=' + headers['device_token'] +
        '|salt=' + 's4lt0.g30l4nk3dd4t4.3s'
    )

    # Save token on database
    __redis_cache['tokens'].set(
        headers['device_token'], __csrf
    )

    return __csrf


##########################################################################


def remove_account_credentials(identifier, device_token):
    """ This function allows to check a token for specific user.

    Args:
        identifier (string): internal user id
        device_token (string): device unique identifier

    """

    # Create cookie key
    __cookie_key = device_token + '_' + identifier

    # Delete cookie key
    __redis['tokens'].delete(__cookie_key)


def check_account_id(identifier):
    """ This function allows to check if an identifier exists

    Args:
        identifier (string): id to check

    Returns:
        bool: True if exists or False otherwise

    """

    return False if identifier is None else \
        __redis['users'].exists(identifier)


def check_account_username(username):
    """ This function allows to check if a username exists
        and return the identifier of that user

    Args:
        username (string): username to check

    Returns:
        string: identifier or None otherwise

    """

    # Generate MD5 from username
    __md5 = crypto.encrypt_md5(username)

    return __redis['users'].get(__md5) \
        if __redis['users'].exists(__md5) else None


def check_account_password(identifier, password):
    """ This function allows to check if a password is valid
        for a specific user identifier

    Args:
        identifier (string): internal user id
        password (string): password to check

    Returns:
        bool: True if exists or False otherwise

    """

    # Check if identifier exists
    if check_account_id(identifier):

        # Hash password
        __password = crypto.encrypt_password(password)

        return __redis['users'].hget(identifier, 'password') == \
            __password

    else:
        return False


def check_account_credentials(identifier, device_token, cookie):
    """ This function allows to check a token for specific user.

    Args:
        identifier (string): internal user id
        device_token (string): device unique identifier
        cookie (string): token of user

    Returns:
        True if it exists or False otherwise

    """

    # Create cookie key
    __cookie_key = device_token + '_' + identifier

    # Get cookie value
    if not __redis['tokens'].exists(__cookie_key):
        return False
    else:

        # Check if identifier is valid
        if not check_account_id(identifier):
            return False

        # Get database cookie
        __saved_cookie = __redis['tokens'].get(__cookie_key)

        # Check if cookies are the same
        if __saved_cookie != cookie:
            __redis['tokens'].delete(__cookie_key)
            return False
        else:
            return True


def set_account_fields(fields, kind):
    """ This function allows to save a user with specific values.

    Args:
        fields (dict): parameters of user
        kind (integer): kind of user (normal = 0, org = 1)

    Returns:
        dict: identifier of new user or error
        # Status = 0 -> all ok
        # Status = 1 -> bad username
        # Status = 2 -> bad password
        # Status = 3 -> bad email

    """

    # Create deep copy of parameter
    __user = fields.copy()

    # Verify if required fields are valid
    if 'username' not in __user:
        return {'status': 1}
    elif regex_username.match(__user['username']) is None:
        return {'status': 1}
    elif check_account_username(__user['username']) is not None:
        return {'status': 1}
    elif 'password' not in __user:
        return {'status': 2}
    elif regex_password.match(__user['password']) is None:
        return {'status': 2}
    elif 'email' not in __user:
        return {'status': 3}
    elif regex_email.match(__user['email']) is None:
        return {'status': 3}
    else:

        # Generate common fields
        __fields = [
            'username', 'password', 'email',
            'name', 'picture', 'website',
            'description'
        ]

        # Add fields depending on kind
        if kind == 1:
            __fields += [
                'address', 'phone',
                'coordinates_lat',
                'coordinates_long'
            ]

        # Iterate and remove other non-valid fields
        # description* is a valid key because it might be
        # some of these keys at the dictionary
        __user_keys = __user.keys()
        for __key in __user_keys:
            if __key not in __fields:
                del __user[__key]

        # Generate identifier from values
        __id = generate_identifier(__user, 'U')

        # Check if identifier exists
        # so we need to generate another id
        while check_account_id(__id):
            __id = generate_identifier(__user, 'U')

        # Hash password field before save info
        __user['password'] = crypto.encrypt_password(
            __user['password']
        )

        # Save kind on dictionary
        __user['kind'] = str(kind)

        # Save information to database
        __redis['users'].hmset(__id, __user)

        # Save username as MD5 to check faster
        __md5 = crypto.encrypt_md5(__user['username'])
        __redis['users'].set(__md5, __id)

        # Return new identifier
        return {'status': 0, 'id': __id}


def set_account_credentials(identifier, device_token, cookie):
    """ This function allows to save a token for specific user.

    Args:
        identifier (string): internal user id
        device_token (string): device unique identifier
        cookie (string): token of user

    """

    # Create cookie key
    __cookie_key = device_token + '_' + identifier

    # Save code on database
    __redis['tokens'].set(__cookie_key, cookie)
    __redis['tokens'].expire(__cookie_key, expire_one_month)


def get_account_fields(identifier, fields=None, privacy=False):
    """ This function allows to get information about a
        specific user and you can specify the fields that
        you want to receive.

    Args:
        identifier (string): internal user id
        fields (list): list of fields (optional)
        privacy (bool): password flag

    Returns:
        dict: information about user or None

    """

    # Detect if it exists
    if not check_account_id(identifier):

        # Remove information from cache
        __redis_cache['users'].delete(identifier)

        return None

    # Get all information from cache
    __user = __redis_cache['users'].hgetall(identifier)

    # Check if it is available
    if not len(__user):

        # Get user information from Redis
        __user = __redis['users'].hgetall(identifier)

        # Check if it is available
        if not len(__user):
            return None

        # Save on cache for next time
        __redis_cache['users'].hmset(identifier, __user)
        __redis_cache['users'].expire(identifier, expire_one_day)

    # Generate user dictionary from specific fields
    if fields is not None:
        __user = {
            it: __user[it] for it in fields
            if it in __user
        }

    # Remove fields without content
    __user = {
        it: __user[it] for it in __user.keys()
        if str(__user[it]).replace(' ', '') != ''
    }

    # Normalize values
    if 'website' in __user:
        if 'http' not in __user['website']:
            __user['website'] = 'http://' + __user['website']
    if 'coordinates_lat' in __user:
        __user['coordinates_lat'] = float(__user['coordinates_lat'])
    if 'coordinates_long' in __user:
        __user['coordinates_long'] = float(__user['coordinates_long'])
    if not privacy and 'password' in __user:
        del __user['password']
    if 'kind' in __user:
        __user['kind'] = int(__user['kind'])

    return __user


def update_account_fields(identifier, fields):
    """ This function allows to update a user with specific values.

    Args:
        identifier (string): internal user id
        fields (dict): parameters of user

    Returns:
        dict: fields with errors
        # Length = 0 -> all ok
        # Length > 0 -> something went wrong

    """

    # Get all previous values for the specific user
    __user = get_account_fields(identifier, None, True)

    # Create structure to check fields
    __basic_args = ['description', 'name']
    __args = [
        'username', 'current_password', 'new_password',
        'verify_password', 'email', 'picture',
        'picture_flag', 'website'
    ]

    # Add more fields if the user is an organization
    if __user['kind'] == 1:
        __basic_args += ['address', 'phone']
        __args += ['coordinates_lat', 'coordinates_long']
    __args += __basic_args

    # Rebuild structure with fields and remove the
    # fields that are not valid (XSS attacks)
    __args = {
        __arg: fields[__arg]
        for __arg in fields.keys()
        if __arg in __args
    }

    # Create structure for errors
    __bad_args = []
    __old_md5 = None
    __new_md5 = None

    # Validate coordinates (org)
    if __user['kind'] == 1:
        if 'coordinates_lat' in __args:
            try:
                __args['coordinates_lat'] = \
                    float(__args['coordinates_lat'])
                if __args['coordinates_lat'] > 90 or \
                   __args['coordinates_lat'] < -90:
                    __bad_args.append('coordinates_lat')
                else:
                    if __user['coordinates_lat'] != \
                       __args['coordinates_lat']:
                        __user['coordinates_lat'] = \
                            __args['coordinates_lat']
            except Exception:
                __bad_args.append('coordinates_lat')
        if 'coordinates_long' in __args:
            try:
                __args['coordinates_long'] = \
                    float(__args['coordinates_long'])
                if __args['coordinates_long'] > 180 or \
                        __args['coordinates_long'] < -180:
                    __bad_args.append('coordinates_long')
                else:
                    if __user['coordinates_long'] != \
                       __args['coordinates_long']:
                        __user['coordinates_long'] = \
                            __args['coordinates_long']
            except Exception:
                __bad_args.append('coordinates_long')

    # Validate Website URL
    try:
        if 'website' in __args and \
           __user['website'] != __args['website']:
            if bool(regex_url.search(__args['website'])) or \
               __args['website'] == '':
                __user['website'] = __args['website']
            else:
                __bad_args.append('website')
    except Exception:
        __bad_args.append('website')

    # Validate Picture URL
    try:
        if 'picture' in __args and \
           'picture_flag' in __args and \
           __user['picture'] != __args['picture']:
            if bool(__args['picture_flag']) and (
             bool(regex_url.search(__args['picture'])) or
             __args['picture'] == ''
            ):
                __user['picture'] = __args['picture']
            else:
                __bad_args.append('picture')
    except Exception:
        __bad_args.append('picture')

    # Validate Email
    try:
        if 'email' in __args and \
           __user['email'] != __args['email']:
            if regex_email.match(
                __args['email']
            ) is None:
                __bad_args.append('email')
            else:
                __user['email'] = __args['email']
    except Exception:
        __bad_args.append('email')

    # Validate username
    try:
        if 'username' in __args and \
           __user['username'] != __args['username']:
            if regex_username.match(
                __args['username']
            ) is None:
                __bad_args.append('username')
            elif check_account_username(
                __args['username']
            ) is not None:
                __bad_args.append('username_invalid')
            else:
                __old_md5 = crypto.encrypt_md5(__user['username'])
                __new_md5 = crypto.encrypt_md5(__args['username'])
                __user['username'] = __args['username']
    except Exception:
        __bad_args.append('username')

    # Break (1) flow if there are some errors
    if len(__bad_args):
        return __bad_args

    # Validate password
    try:
        if 'current_password' in __args and \
           'new_password' in __args and \
           'verify_password' in __args and \
           __args['current_password'] != '' and \
           __args['new_password'] != '' and \
           __args['verify_password']:
            if __args['new_password'] != \
               __args['verify_password']:
                __bad_args.append('password_mismatch')
            elif regex_password.match(
                __args['new_password']
            ) is None:
                __bad_args.append('password')
            elif crypto.encrypt_password(
                __args['current_password']
            ) != __user['password']:
                __bad_args.append('password_invalid')
            else:
                __user['password'] = crypto.encrypt_password(
                    __args['new_password']
                )
    except Exception:
        __bad_args.append('password')

    # Validate other values
    for __arg in __basic_args:
        if __user[__arg] != __args[__arg]:
            __user[__arg] = __args[__arg]

    # Break (2) flow if there are some errors
    if len(__bad_args):
        return __bad_args

    # Rebuild links if it is necessary
    if __old_md5 is not None and __new_md5 is not None:
        __redis['users'].delete(__old_md5)
        __redis['users'].set(__new_md5, identifier)

    # Remove cache
    __redis_cache['users'].delete(identifier)

    # Set new values on database
    __redis['users'].hmset(identifier, __user)

    return []