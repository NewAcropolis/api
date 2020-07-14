from flask import request
from urllib.parse import urlparse


def is_running_locally():
    return urlparse(request.url_root).netloc.split(':')[0] in ['localhost', '127.0.0.1']
