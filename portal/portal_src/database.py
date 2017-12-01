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
                __redis_pools[__redis_pool_name].disconnect()

            return None

        else:

            # Save connection to structure
            __redis_connections[__redis_name] = redis.Redis(
                connection_pool=__redis_pools[__redis_name]
            )

        # Add new number for next connection pool
        __number_redis += 1

    config.flask_logger.info(
        'Redis DB connected at port: ' + str(configuration['port'])
    )

    return __redis_connections


# Execute method to create new instance Redis
__redis = configure_redis(config.redis)

# Execute method to create new instance of Redis Cache
__redis_cache = configure_redis(config.redis_cache)


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
        # Check if CSRF is the same
        return __redis_cache['tokens'].get(
            headers['device_token']
        ) == csrf_token

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
            'name', 'picture', 'website'
        ]

        # Add fields depending on kind
        __fields += ['gender'] if kind == 0 else \
            ['address', 'phone']

        # Iterate and remove other non-valid fields
        # description* is a valid key because it might be
        # some of these keys at the dictionary
        __user_keys = __user.keys()
        for __key in __user_keys:
            if __key not in __fields and 'description' not in __key:
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


def get_account_fields(identifier, fields=None):
    """ This function allows to get information about a
        specific user and you can specify the fields that
        you want to receive.

    Args:
        identifier (string): internal user id
        fields (list): list of fields (optional)

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
        __user = {it: __user[it] for it in fields if it in __user}

    # Normalize values
    if 'password' in __user:
        del __user['password']
    if 'kind' in __user:
        __user['kind'] = int(__user['kind'])
    __user['id'] = identifier

    return __user
