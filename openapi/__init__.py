import datetime
from os.path import join as pjoin
from random import randint
from time import sleep
from flask import request


def get_echo():  # noqa: E501
    """Ritorna un timestamp in formato RFC5424.

    Ritorna un timestamp in formato RFC5424 prendendola dal server attuale.  # noqa: E501


    :rtype: Timestampa
    """
    case = randint(0, 10)
    if case < 4:
        sleep(1)
    elif case < 8:
        for i in range(100000):
            pass
    else:
        raise NotImplementedError
    return {"datetime": str(datetime.datetime.utcnow())}


def index():
    return {
        "message": "Welcome to the Jungle 1",
        "_links": [
            {"url": pjoin(request.url_root, "echo")},
            {
                "url": "http://localhost:16686/search",
                "description": "Jaeger endpoint",
            },
        ],
    }
