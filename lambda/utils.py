import base64
from itertools import chain


def flatmap(f, items):
    return chain.from_iterable(map(f, items))


def encode_in_base64(string: str) -> str:
    return base64.b64encode(string.encode('utf8')).decode('utf8')