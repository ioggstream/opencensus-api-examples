import json

from connexion import problem
from flask import current_app as app

from .digest import digest


def add_digest_header(response):
    response.direct_passthrough = (
        False
    )  # FIXME shouldn't use this, but a proper Flask interface.
    response.headers["Digest"] = b"sha-256=" + digest(response.data)
    app.logger.warning("Adding digest: %r", response.headers["Digest"])
    return response


def check_digest_header():
    from flask import request

    ret = request.data
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
                    % digest(ret).decode("ascii"),
                    title="bad digest",
                )
            ),
            400,
            {"Want-Digest": "sha-256"},
        )

    if d[8:].encode("ascii") == digest(ret):
        # Success!
        return

    default_response = json.dumps(
        dict(
            status=400,
            detail="expected: sha-256=%s" % digest(ret).decode("ascii"),
            title="bad digest",
        )
    )
    return default_response, 400
