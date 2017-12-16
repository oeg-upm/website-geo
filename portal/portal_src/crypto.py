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
import time
import hmac
import json
import base64
import random
import requests
import datetime
import settings
import traceback
from Crypto.Cipher import AES
from Crypto.Hash import MD5, SHA256

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
        if e is not None:
            config.error_logger.error(e)
        else:
            tb = traceback.format_exc()
            config.error_logger.error(tb)


##########################################################################


def encrypt_md5(str_to_encrypt):
    """ This function allows to generate a MD5 string
        from specific string.

    Args:
        str_to_encrypt (string): string to be cyphered

    Returns:
        string: MD5

    """

    # Create new MD5 instance
    __md5 = MD5.new()

    # Configure MD5 instance
    __md5.update(str_to_encrypt)

    # Return MD5 hexadecimal value
    return str(__md5.hexdigest()).lower()


def encrypt_sha256(str_to_encrypt):
    """ This function allows to generate an SHA 256 string
        from specific string

    Args:
        str_to_encrypt (string): string to be cyphered

    Returns:
        string: SHA 256 or None

    """

    # Generate signature
    __kk = int(random.random() * len(config.keys['crypto']))
    __sig = '' + str_to_encrypt
    __sig += '|time=' + str(time.time())
    __sig += '|n1=' + str(random.random() * 99)
    __sig += '|n2=' + str(random.random() * 99)
    __sig += '|kk=' + str(__kk)
    __sig += '|kv=' + config.keys['crypto'][__kk]

    # Get string parameters for H-MAC
    # Bug 2.7 https://bugs.python.org/issue5285
    __sig = str(__sig)
    __kv = str(config.keys['crypto'][__kk])

    # Return SHA 256
    return hmac.new(
        __kv, __sig, SHA256
    ).hexdigest().lower()


def encrypt_sha256_file(source_file):
    """ This function allows to generate an SHA 256 string
        from specific file

    Args:
        source_file (file): file to be cyphered

    Returns:
        string: SHA 256 or None

    """

    def hash_iterator(bytes_iteration, hash_iteration):
        for block in bytes_iteration:
            hash_iteration.update(block)
        return hash_iteration.hexdigest().lower()

    def file_as_block(src_file):
        __block_size = SHA256.block_size * 64
        __block = src_file.read(__block_size)
        while len(__block) > 0:
            yield __block
            __block = src_file.read(
                __block_size
            )

    return hash_iterator(
        file_as_block(source_file),
        SHA256.new()
    )


def encrypt_aes256(str_to_encrypt, key):
    """ This function allows to generate an AES 256 string
        from specific string and provided key.

    Args:
        str_to_encrypt (string): string to be cyphered
        key (string): key for encrypt

    Returns:
        string: AES 256 - BASE 64 or None

    """

    # Create Vector
    __IV = 16 * '\x00'

    # Configure AES instance
    __cipher = AES.new(key, AES.MODE_CBC, __IV)

    # Configure AES longitude
    __l = 16 - (len(str_to_encrypt) % 16)

    # String padding
    __str = str_to_encrypt + (chr(__l) * __l)

    # Generate AES 256
    __str = __cipher.encrypt(__str)

    # Return AES base64 value
    return base64.b64encode(__str)


def decrypt_aes256(str_to_decrypt, key):
    """ This function allows to generate a string from
        specific AES 256 string and provided key.

    Args:
        str_to_decrypt (string): string to be de-cyphered
        key (string): key for decrypt

    Returns:
        string: original value or None

    """

    # Create Vector
    __IV = 16 * '\x00'

    # Configure AES instance
    __cipher = AES.new(key, AES.MODE_CBC, __IV)

    # Generate decrypted value
    __str = __cipher.decrypt(base64.b64decode(str_to_decrypt))
    __str = __str[:-ord(__str[len(__str) - 1:])]

    # Return decoded value
    return __str.decode('utf-8')


##########################################################################


def encrypt_password(password):
    """ This function allows to encrypt a specific
        password to SHA 256 string

    Args:
        password (string): password to be cyphered

    Returns:
        string: SHA 256 or None

    """

    # Get key from configuration
    __crp_key = config.keys['master']

    # Generate signature
    __sig = ''
    __n = 0
    for i in config.keys['crypto']:
        __sig += '|key(' + str(__n) + ')=' + i
        __n += 1
    __sig += '|pwd=' + password

    # Get string parameters for H-MAC
    # Bug 2.7 https://bugs.python.org/issue5285
    __sig = str(__sig)
    __crp_key = str(__crp_key)

    # Return SHA 256
    return hmac.new(
        __crp_key, __sig, SHA256
    ).hexdigest().lower()


def encrypt_dict(dict_to_encrypt, key=None):
    """ This function allows to generate an AES 256 string
        from specific dictionary and provided key.

    Args:
        dict_to_encrypt (dict): dictionary to be cyphered
        key (string): key for encrypt (optional)

    Returns:
        string: AES 256 - BASE 64 or None

    """

    # Check if key is present
    if key is None:

        # Generate number from current month
        __crp_number = datetime.datetime.now().month % \
            len(config.keys['crypto'])

        # Get key from configuration
        __crp_key = config.keys['crypto'][__crp_number]

    else:

        # Get provided key
        __crp_key = key

    # Return AES base64 value
    return encrypt_aes256(json.dumps(dict_to_encrypt), __crp_key)


def decrypt_dict(dict_to_decrypt, key=None):
    """ This function allows to generate a dictionary from
        specific AES 256 string and provided key.

    Args:
        dict_to_decrypt (string): dictionary to be de-cyphered
        key (string): key for decrypt (optional)

    Returns:
        string: original value or None

    """

    # Check if key is present
    if key is None:

        # Generate number from current month
        __crp_number = datetime.datetime.now().month % \
            len(config.keys['crypto'])

        # Get key from configuration
        __crp_key = config.keys['crypto'][__crp_number]

    else:

        # Get provided key
        __crp_key = key

    # Return decoded value
    return decrypt_aes256(json.loads(dict_to_decrypt), __crp_key)


##########################################################################


def verify_google_captcha(response):
    """ This function allows to verify if a user token
        is validated on Google reCAPTCHA API.

    Args:
        response (string): captcha user token

    Returns:
        bool: True if everything was good or False otherwise

    """

    # Request trough Google API
    try:

        # Get information from Google Geocode API
        __response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify', data={
                'secret': config.keys['captcha_server'],
                'response': response
            }, verify=False
        )

        # Check if request was good
        if __response.status_code == 200:
            return __response.json().get('success')

    except Exception:
        pass

    return False
