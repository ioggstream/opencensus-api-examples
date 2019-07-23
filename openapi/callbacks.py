import json

from connexion import problem
from flask import current_app as app, Response, request
from openapi.signatures import Signature
from time import time

from .digest import digest


def sign(response):
    if response.status_code > 299:
        return response

    s_data = {
        "v": "draft-cavage-11rpolli",
        "keyId": "test-rsa",
        "algorithm": "rsa-256",
        "created": int(time()),
        "expires": int(time() + 2),
        "headers": "(request-target) (created) "
        "(expires) content-type digest",
    }
    ss = Signature(**s_data)
    signature = ss.sign_http_message(request, response)
    response.headers["Signature"] = signature
    response.headers["Signature-String"] = ss.signature_string(
        request.method, request.path, response.headers
    ).replace("\n", "%")
    return response


def add_digest_header(message):
    if message.status_code > 299:
        return message

    if isinstance(message, Response):
        message.direct_passthrough = (
            False
        )  # FIXME shouldn't use this, but a proper Flask interface.
    message.headers["Digest"] = b"sha-256=" + digest(message.data)
    app.logger.warning("Adding digest: %r", message.headers["Digest"])
    return message


def check_digest_header():
    """
    TODO just works for payload_body.
    A semantic-aware version should be implemented.
    :return:
    """
    from flask import request

    payload_body = request.data
    if "Digest" not in request.headers:
        return

    d = request.headers.get("Digest")

    if not d:
        return problem(
            status=400, title="Bad Request", detail="Invalid digest value"
        )

    if not d.startswith("sha-256="):
        return (
            json.dumps(
                dict(
                    status=400,
                    detail="expected: sha-256=%s"
                    % digest(payload_body).decode("ascii"),
                    title="bad digest",
                )
            ),
            400,
            {"Want-Digest": "sha-256"},
        )

    if d[8:].encode("ascii") == digest(payload_body):
        # Success!
        return

    default_response = json.dumps(
        dict(
            status=400,
            detail="expected: sha-256=%s"
            % digest(payload_body).decode("ascii"),
            title="bad digest",
        )
    )
    return default_response, 400
