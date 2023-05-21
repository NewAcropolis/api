import base64
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property
from flask import current_app

# ENCODING = 'utf-16'  # 'utf-8'
ENCODING = 'utf-8'


def encrypt(plain, key):
    return base64.b64encode(simpleXor(plain, key)).decode(ENCODING)


def decrypt(scrambled, key):
    return simpleXor(base64.b64decode(scrambled).decode(ENCODING), key).decode(ENCODING)


def simpleXor(in_string, key):
    key_list = []
    output = ""

    # Convert key into array of ASCII values
    for i in range(len(key)):
        key_list.append(ord(key[i]))

    # Step through string a character at a time
    for i in range(len(in_string)):
        # Get ASCII code from string, get ASCII code from key (loop through with MOD),
        #  XOR the two, get the character from the result
        # % is MOD (modulus), ^ is XOR
        output += chr(ord(in_string[i]) ^ (key_list[i % len(key)]))
    return output.encode()


def get_tokens(decrypted_string):
    tokens = dict([tuple(item.split("=")) for item in decrypted_string.split('&')])
    valid_tokens = {}

    for key in tokens.keys():
        if key in current_app.config['EMAIL_TOKENS'].values():
            valid_tokens[key] = tokens[key]

    return valid_tokens
