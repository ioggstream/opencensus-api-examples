import json

from connexion import problem
from flask import current_app as app, Response

from .digest import digest


def add_digest_header(message):
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
