from flask import current_app as app
from connexion import problem
from .digest import digest


def add_header(response):
    response.headers["Digest"] = b"sha-256=" + digest(response.data)
    app.logger.warning("Adding digest: %r", response.headers["Digest"])
    return response


def check_digest():
    from flask import request

    ret = request.data
    if "Digest" not in request.headers:
        return

    d = request.headers.get("Digest")

    if not d:
        return problem(
            status=400, title="Bad Request", detail="Invalid digest value"
        )

    if not d.startswith("sha-256"):
        return problem(
            status=400,
            detail="expected " + digest(ret),
            title="bad digest",
            headers={"Want-Digest": "sha-256"},
        )
