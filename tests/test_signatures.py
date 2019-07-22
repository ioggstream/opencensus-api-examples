from pathlib import Path

import yaml
from flask import Flask, request
from nose.tools import (
    assert_dict_contains_subset,
    assert_equal,
    assert_is_not_none,
)
from requests.structures import CaseInsensitiveDict

from openapi.signatures import (
    Signature,
    load_key,
    load_pubkey,
    parse_signature_header,
)


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
    for http_trace in test["test_rsa"]:
        trace = http_trace["http"]
        for t in http_trace["tests"]:

            s_data = t["params"]
            with create_mock_request(trace):
                ss = Signature(**s_data)
                ret = ss.sign(request)

                p = parse_signature_header(ret[10:])
                assert_dict_contains_subset(s_data, p)
                sstring = ss.signature_string(request)
                assert_equal(t["expected_string"], sstring)


def yaml_read(fpath):
    return yaml.safe_load(Path(fpath).read_text())


def test_parse_signature():
    tests = yaml_read("request.yaml")
    for t in tests["test_parse_signatures"]:
        signature_header = t["signature_header"]
        signature = parse_signature_header(
            signature_header.strip("Signature: ")
        )
        assert signature["headers"]
        assert signature["signature"]
        assert signature["algorithm"]
        assert signature["keyId"]
        assert signature["expires"]
        assert signature["created"]
        yield assert_is_not_none, t["test_name"]
