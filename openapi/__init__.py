import datetime
from functools import wraps
from os.path import join as pjoin
from random import randint
from time import sleep, time

from connexion import problem
from flask import request, after_this_request
import gzip
import json

from openapi.callbacks import add_digest_header
from .digest import check_digest
from flask import Response
from opencensus.trace import execution_context


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
        tracer = execution_context.get_opencensus_tracer()
        with tracer.span(name="parent_span") as parent_span:
            assert parent_span
            sleep(1)
        return problem(status=200, title="Accepted", detail="Async")
    elif case < 8:
        for i in range(5):
            pass
    else:
        tracer = execution_context.get_opencensus_tracer()
        with tracer.span(name="parent_span") as parent_span:
            assert parent_span
            raise NotImplementedError
    return problem(status=200, title="OK", detail="API is working normally")


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

from .signatures import Signature
from flask import request


def get_echo():  # noqa: E501
    """Ritorna un timestamp in formato RFC5424.

    Ritorna un timestamp in formato RFC5424 prendendola dal server attuale.  # noqa: E501


    :rtype: Timestampa
    """
    @after_this_request
    def foo(response):
        add_digest_header(response)
        return response
    @after_this_request
    def sign(response):
        s_data = {
            "v": "draft-cavage-11rpolli",
            "keyId": "test-rsa",
            "algorithm": "rsa-256",
            "created": int(time()),
            "expires": int(time() + 2),
            "headers": "(request-target) (created) (expires) content-type"
        }
        ss = Signature(**s_data)
        signature = ss.sign(request, response)
        response.headers['Signature'] = signature
        response.headers['Signature-String'] = ss.signature_string(request, response).replace("\n", "%")
        return response

    return {"datetime": str(datetime.datetime.utcnow())}
