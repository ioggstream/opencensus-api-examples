"""
Client implementation for generating signed requests
and processing signed responses.
"""
from dataclasses import dataclass

from requests import Request, Session
import json
from time import time

from requests.structures import CaseInsensitiveDict

from openapi.digest import digest
from openapi.signatures import Signature, parse_signature_header
from urllib.parse import urlparse


@dataclass
class Client(object):
    keyId: str

    def __init__(self):
        pass


s = Session()
MOCK_KID = "foo"


def send_request(
    url,
    method,
    headers=None,
    signed_headers=None,
    payload_body=None,
    expires_window=2,
):
    from openapi.callbacks import digest

    request = Request(
        method,
        url,
        headers=CaseInsensitiveDict(headers or {}),
        data=payload_body,
    )

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
        request.headers["Signature"] = signature.sign_http_message(request)
        request.headers["Signature-String"] = signature.signature_string(
            method, urlparse(url).path, request.headers
        ).replace("\n", "%")
    prepared_request = request.prepare()
    response = s.send(prepared_request, verify=0)

    return response


def check_digest_header(content, headers):
    digest_value = headers.get("digest")
    if not digest_value:
        return

    digest_value = digest_value.replace("sha-256=", "")
    assert digest(content).decode("ascii") == digest_value, digest(content)


def check_signature_header(method, path, headers):
    signature_value = headers.get("signature")
    if not signature_value:
        return

    shash = parse_signature_header(signature_value)
    signature = Signature(**shash)
    signature.verify(method, path, headers)


def test_get():
    echo_path = "/datetime/v1/echo"
    url, method = "https://localhost:8443" + echo_path, "GET"
    signed_headers = "(request-target) (created) (expires)"
    payload_body = None
    response = send_request(
        url, method, signed_headers=signed_headers, payload_body=payload_body
    )

    check_digest_header(response.content, response.headers)

    check_signature_header(method, echo_path, response.headers)


def test_post():
    data_path = "/datetime/v1/data"

    url, method = "https://localhost:8443" + data_path, "POST"
    signed_headers = (
        "(request-target) (created) (expires) digest content-type"
    )
    payload_body = json.dumps({"a": 1}).encode()
    response = send_request(
        url,
        method,
        headers={"content-type": "application/json"},
        signed_headers=signed_headers,
        payload_body=payload_body,
    )
    check_digest_header(response.content, response.headers)
    check_signature_header(method, data_path, response.headers)

    raise NotImplementedError
