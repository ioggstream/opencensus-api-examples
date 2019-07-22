# coding: utf-8
from pathlib import Path

from flask import Request

from openapi.digest import digest
from openapi.signatures import (
    Signature,
    load_pubkey,
    parse_signature_header,
    verify_string,
)
from test_config import BaseTestCase

LIST_FIELDS = ("count", "limit", "items")


class TestApp(BaseTestCase):
    """PublicController integration test stubs"""

    def test_echo(self):
        response = self.client.open("/datetime/v1/echo", method="GET")
        self.assert200(
            response, "Response body is : " + response.data.decode("utf-8")
        )
        assert response.json.get("datetime")

    def test_echo_digest(self):
        response = self.client.open("/datetime/v1/echo", method="GET")
        self.assert200(
            response, "Response body is : " + response.data.decode("utf-8")
        )
        d = response.headers.get("Digest")
        assert d, response.headers
        assert response.headers["Digest"][8:].encode("ascii") == digest(
            response.data
        )

    def test_echo_signature(self):
        response = self.client.open("/datetime/v1/echo", method="GET")
        request = Request.from_values(
            base_url="http://localhost",
            path="/datetime/v1/echo",
            method="GET",
        )
        self.assert200(
            response, "Response body is : " + response.data.decode("utf-8")
        )
        s_header = response.headers.get("Signature")
        assert s_header, response.headers

        p = parse_signature_header(s_header)
        ss = Signature(**p)
        sstring = ss.signature_string(request, response)
        verify_string(
            load_pubkey(Path("rsa.pub").read_bytes()), sstring, p["signature"]
        )

    def test_echo_signature_ko(self):
        response = self.client.open("/datetime/v1/echo", method="GET")
        request = Request.from_values(
            base_url="http://localhost",
            path="/datetime/v1/echo",
            method="GET",
        )
        self.assert200(
            response, "Response body is : " + response.data.decode("utf-8")
        )
        s_header = response.headers.get("Signature")
        assert s_header, response.headers

        p = parse_signature_header(s_header)
        ss = Signature(**p)
        sstring = ss.signature_string(request, response)
        verify_string(
            load_pubkey(Path("rsa.pub").read_bytes()),
            sstring + "1",
            p["signature"],
        )
        raise NotImplementedError
