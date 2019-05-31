# coding: utf-8
import gzip
import json

from openapi.digest import digest
from test_config import BaseTestCase

LIST_FIELDS = ("count", "limit", "items")


class TestApp(BaseTestCase):
    """PublicController integration test stubs"""

    def test_post_data(self):
        request_body = json.dumps({"a": "ciao"})
        response = self.client.open(
            "/datetime/v1/data",
            method="POST",
            data=request_body,
            headers={"Content-Type": "application/json"},
        )
        self.assert_status(
            response,
            200,
            "Response body is : " + response.data.decode("utf-8"),
        )
        assert "Digest" in response.headers
        assert response.headers["Digest"][8:].encode("ascii") == digest(
            response.data
        )

    def test_post_data_gzip(self):
        request_body = json.dumps({"a": "ciao"})
        response = self.client.open(
            "/datetime/v1/data",
            method="POST",
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Accept-Encoding": "gzip",
            },
        )
        self.assert_status(
            response, 200, "Response body is : " + repr(response.data)
        )
        assert "Digest" in response.headers
        assert response.headers["Digest"][8:].encode("ascii") == digest(
            response.data
        )
        assert "ret" in json.loads(gzip.decompress(response.data))

    def test_echo(self):
        response = self.client.open("/datetime/v1/echo", method="GET")
        self.assert200(
            response, "Response body is : " + response.data.decode("utf-8")
        )
        assert response.json.get("datetime")

    def test_echo_after_request(self):
        response = self.client.open("/datetime/v1/echo", method="GET")
        self.assert200(
            response, "Response body is : " + response.data.decode("utf-8")
        )
        d = response.headers.get("Digest")
        assert d, response.headers
        assert response.headers["Digest"][8:].encode("ascii") == digest(
            response.data
        )

    def test_status(self):
        response = self.client.open("/datetime/v1/status", method="GET")
        self.assert200(
            response, "Response body is : " + response.data.decode("utf-8")
        )
        assert "application/problem+json" == response.headers.get(
            "Content-Type"
        )
