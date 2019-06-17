from pathlib import Path
from openapi.signatures import (
    load_key,
    load_pubkey,
    parse_signature_header,
    sign_string,
)
import yaml

from requests.structures import CaseInsensitiveDict

from dataclasses import dataclass
from flask import request, Flask
from nose.tools import assert_equal, assert_dict_contains_subset, assert_is_not_none


def test_load_key():
    assert load_key(Path("rsa.key").read_bytes())


def test_load_pubkey():
    assert load_pubkey(Path("rsa.pub").read_bytes())


def create_mock_request(trace):
    head, body = trace.split("\n\n", 1)
    target, headers = head.split("\n", 1)
    headers = CaseInsensitiveDict(
        x.split(": ", 1) for x in headers.splitlines()
    )
    method, path, proto = target.split(" ")
    app = Flask(__name__)
    return app.test_request_context(
        path=path, method=method, data=body, headers=dict(headers)
    )


def test_create_signature_string():
    test = yaml_read("request.yaml")
    for http_trace in test['test_rsa']:
        trace = http_trace["http"]
        for t in http_trace['tests']:

            s_data = t["params"]
            with create_mock_request(trace):
                ss = Signature(**s_data)
                ret = ss.sign(request)

                p = parse_signature_header(ret[10:])
                assert_dict_contains_subset(s_data, p)
                sstring = ss.signature_string(request)
                assert_equal(t['expected_string'], sstring)


def yaml_read(fpath):
    return yaml.safe_load(Path(fpath).read_text())


def test_parse_signature():
    tests = yaml.read("request.yaml")
    for t in tests['test_parse_signatures']:
        signature_header = t['signature_header']
        signature = parse_signature_header(signature_header.strip("Signature: "))
        assert signature["headers"]
        assert signature["signature"]
        assert signature["algorithm"]
        assert signature["keyId"]
        assert signature["expires"]
        assert signature["created"]
        yield assert_is_not_none, t['test_name']


@dataclass
class Signature(object):
    keyId: str
    algorithm: str
    created: int
    v: str = None
    expires: float = None
    headers: str = "created"
    signature: str = None

    def validate(self):
        if not self.headers:
            raise ValueError("At least one headers should be specified")

    def signature_string(self, request):
        expected_string = f"(v): {self.v}\n" if self.v else ""
        expected_string += (
            f"(request-target): {request.method.lower()} {request.path}\n"
            f"(created): {self.created}\n"
            f"(expires): {self.expires}\n"
        )
        for h in self.headers.split(" "):
            if h in "(request-target) (v) (created) (expires)".split(" "):
                print(f"skipping {h}")
                continue
            expected_string += f"{h.lower()}: {request.headers[h]}\n"

        # Remove last CR
        return expected_string[:-1]

    def resolve_key(self):
        """Override this method for resolving keys.
        """
        self.encryption_key = load_key(Path("rsa.key").read_bytes())
        return self.encryption_key

    def sign(self, request):
        signature_string = self.signature_string(request)
        s = sign_string(self.resolve_key(), signature_string)
        return (
            f'Signature: keyId="{self.keyId}", algorithm="{self.algorithm}"'
            f", created={self.created}, expires={self.expires}"
            f', v="{self.v}", headers="{self.headers}"'
            f', signature="{s}"'
        )
