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
import base64
import datetime
import settings
import traceback
from Crypto.Cipher import AES
from Crypto.Hash import MD5

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

    try:

        # Create new MD5 instance
        __md5 = MD5.new()

        # Configure MD5 instance
        __md5.update(str_to_encrypt)

        # Return MD5 hexadecimal value
        return str(__md5.hexdigest()).lower()

    except Exception:

        print_exception()
        return None


def encrypt_aes256(str_to_encrypt, key):
    """ This function allows to generate an AES 256 string
        from specific string and provided key.

    Args:
        str_to_encrypt (string): string to be cyphered
        key (string): key for encrypt

    Returns:
        string: AES 256 - BASE 64

    """

    try:

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

    except Exception:

        print_exception()
        return None


def decrypt_aes256(str_to_decrypt, key):
    """ This function allows to generate a string from
        specific AES 256 string and provided key.

    Args:
        str_to_decrypt (string): string to be de-cyphered
        key (string): key for decrypt

    Returns:
        string: original value

    """

    try:

        # Create Vector
        __IV = 16 * '\x00'

        # Configure AES instance
        __cipher = AES.new(key, AES.MODE_CBC, __IV)

        # Generate decrypted value
        __str = __cipher.decrypt(base64.b64decode(str_to_decrypt))
        __str = __str[:-ord(__str[len(__str) - 1:])]

        # Return decoded value
        return __str.decode('utf-8')

    except Exception:

        print_exception()
        return None


##########################################################################


def encrypt_dict(dict_to_encrypt, key=None):
    """ This function allows to generate an AES 256 string
        from specific dictionary and provided key.

    Args:
        dict_to_encrypt (dict): dictionary to be cyphered
        key (string): key for encrypt (optional)

    Returns:
        string: AES 256 - BASE 64

    """

    # Check if key is present
    if key is None:

        # Generate number from current month
        __crp_number = datetime.datetime.now().month % \
            len(config.keys.crypto)

        # Get key from configuration
        __crp_key = config.keys.crypto[__crp_number]

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
        string: original value

    """

    # Check if key is present
    if key is None:

        # Generate number from current month
        __crp_number = datetime.datetime.now().month % \
            len(config.keys.crypto)

        # Get key from configuration
        __crp_key = config.keys.crypto[__crp_number]

    else:

        # Get provided key
        __crp_key = key

    # Return decoded value
    return decrypt_aes256(json.loads(dict_to_decrypt), __crp_key)
