import datetime
from os.path import join as pjoin
from random import randint
from time import sleep

from connexion import problem
from flask import request
import gzip
import json
from .digest import check_digest
from flask import Response


def decode_content(ret):
    if "gzip" in request.headers.get("Content-Encoding", ""):
        print("clen", request.headers.get("Content-Length"))
        print("gunzip", repr(gzip.decompress(ret)))
        return gzip.decompress(ret)
    return ret


def post_data(data=None):
    err = check_digest()
    if err:
        return err

    ret = request.data  # request.data
    res = {"ret": repr(ret)}
    hdr = {}
    cres = json.dumps(res).encode()
    if "gzip" in request.headers.get("Accept-Encoding", ""):
        cres = gzip.compress(cres)
        hdr["Content-Encoding"] = "gzip"

    # Control the response serialization, as
    #  I need a valid digest.
    return Response(response=cres, status=200, headers=hdr)


def get_status():
    case = randint(0, 10)
    if case < 4:
        sleep(1)
    elif case < 8:
        for i in range(100000):
            pass
    return problem(status=200, title="OK", detail="API is working normally")


def get_echo():  # noqa: E501
    """Ritorna un timestamp in formato RFC5424.

    Ritorna un timestamp in formato RFC5424 prendendola dal server attuale.  # noqa: E501


    :rtype: Timestampa
    """

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
