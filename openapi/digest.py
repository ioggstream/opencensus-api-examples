from hashlib import sha256
from base64 import encodebytes
from flask import request
from connexion import problem


def digest(b):
    return encodebytes(sha256(b).digest()).strip()


def check_digest():
    ret = request.data
    d = request.headers.get("Digest", "")
    if d.startswith("sha-256"):
        return problem(
            status=400,
            detail="expected " + digest(ret).encode("ascii"),
            title="bad digest",
        )
    return None
