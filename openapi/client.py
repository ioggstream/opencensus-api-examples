"""
Client implementation for generating signed requests
and processing signed responses.
"""
from dataclasses import dataclass

from requests import Request, Session
import json
from time import time
from openapi.signatures import Signature, parse_signature_header


@dataclass
class Client(object):
    keyId: str

    def __init__(self):
        pass


s = Session()
MOCK_KID = "foo"


def send_request(url, method, signed_headers, payload_body, expires_window=2):
    from openapi.callbacks import digest

    headers = {}
    request = Request(method, url, headers, data=payload_body)

    if method not in ("GET", "HEAD", "DELETE"):
        request.headers["Digest"] = b"sha-256=" + digest(
            request.data if request.data else b""
        )
        assert "Digest" in request.headers

    if signed_headers:
        created = time()
        signature = Signature(
            keyId=MOCK_KID,
            algorithm="bar",
            headers=signed_headers,
            created=int(created),
            expires=created + expires_window,
        )
        request["Signature"] = signature.sign(request)
        request["Signature-String"] = signature.signature_string(
            request
        ).replace(b"\n", "%")
    prepared_request = request.prepare()
    response = s.send(prepared_request, verify=0)

    return response


def test_get():
    url, method = "https://localhost:8443/datetime/v1/echo", "GET"
    signed_headers = "(request-target) (created) (expires)"
    payload_body = None
    response = send_request(url, method, signed_headers, payload_body)

    digest = response.headers.get("digest")
    if method in ("GET", "HEAD", "DELETE"):
        assert not digest, f"Digest should not be sent on {method} requests"

    signature = response.headers.get("signature")
    shash = parse_signature_header(signature)
    signature = Signature(**shash)
    signature.verify()
    raise NotImplementedError


def test_post():
    url, method = "https://localhost:8443/datetime/v1/echo", "GET"
    signed_headers = "(request-target) (created) (expires) digest"
    payload_body = json.dumps({"a": 1}).encode()
    response = send_request(url, method, signed_headers, payload_body)

    digest = response.headers.get("digest")
    if method in ("GET", "HEAD", "DELETE"):
        assert not digest, f"Digest should not be sent on {method} requests"

    assert digest(response.data) == digest, digest(response.data)

    raise NotImplementedError
