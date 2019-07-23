import re
from base64 import decodebytes, encodebytes
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
)
from dataclasses import dataclass


def format_parameter(k, v):
    if k == "created":
        return int(v)
    if k == "expires":
        return float(v) if "." in v else int(v)
    if isinstance(v, str):
        return v.strip('"')
    return v


def parse_signature_header(s):
    """
    Parse a given `Signature` header into a dict.
    :param s: the `Signature` header value.
    :return: a dict representing the Signature parameters
    """
    if s.startswith("Signature:"):
        raise ValueError(
            "You should pass the Signature header value,"
            " not the whole header string."
        )

    parameters = re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', s)
    parameters = [x.split("=", 1) for x in parameters]

    # TODO validate parameters' name.
    c = Counter(x[0] for x in parameters)
    duplicate_params = [k for k, v in c.items() if v > 1]
    if duplicate_params:
        raise ValueError("Duplicate headers %r" % c)

    # TODO validate parameters' content.
    return {k: format_parameter(k, v) for k, v in parameters}


def serialize_signature(signature_parameters):
    signature_header = f"Signature: "
    for p, v in signature_parameters.items():
        if isinstance(v, str):
            v = f'"{v}"'
        signature_header += f"{p}={v},"

    # remove last comma.
    return signature_header.strip(",")


def load_pubkey(x509_pem):
    """
    Load a PEM-encoded public key in a python-cryptography object.
    :param x509_pem: a PEM-encoded public key
    :return: A python-cryptography public key.
    """
    return load_pem_public_key(x509_pem, default_backend())


def load_key(key):
    """
    Load a PEM-encoded private key in a python-cryptography object.
    :param x509_pem: a PEM-encoded private key
    :return: A python-cryptography public key.
    """

    return load_pem_private_key(key, password=None, backend=default_backend())


def sign_string(private_key, signature_string: bytes):
    # HTTP Headers SHOULD only use ascii
    return sign_bytes(private_key, signature_string.encode("ascii"))


def verify_string(public_key, signature_string: str, b64_signature: str):
    # HTTP Headers SHOULD only use ascii
    return verify_bytes(
        public_key, signature_string.encode("ascii"), b64_signature
    )


def sign_bytes(private_key, signature_bytes: bytes):
    """
    Sign a byte sequence with the given private key.
    :param private_key:
    :param signature_bytes:
    :return: a base-64 encoded signature of `signature_bytes`
    """
    signature = private_key.sign(
        signature_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    return encodebytes(signature).replace(b"\n", b"").decode("ascii")


def verify_bytes(public_key, signature_bytes: bytes, b64_signature: str):
    """
    Verify that a base64 encoded signature matches the `signature_bytes`.
    :param public_key:
    :param signature_bytes:
    :param b64_signature:
    :return: None on success, an exception on failure.
    """
    public_key.verify(
        decodebytes(b64_signature.encode("ascii")),
        signature_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    return True


@dataclass
class Signature(object):
    keyId: str
    algorithm: str
    created: int
    v: str = None
    expires: float = None
    headers: str = "created"
    signature: str = None

    def _validate_digest(self, message_headers):
        unsigned_headers = {k.lower() for k in message_headers.keys()} - set(
            self.headers.split(" ")
        )

        # the following logic is only valid with signatures
        if "signature" not in unsigned_headers:
            return True
        if "digest" not in message_headers:
            return True

        if "content-type" in unsigned_headers:
            raise ValueError("content-type should be signed")

        if "content-encoding" in unsigned_headers:
            raise ValueError("content-encoding should be signed")

        if "digest" in unsigned_headers:
            raise ValueError("You should not send an unsigned digest")

    def validate_headers(self, message_headers=None):
        if not self.headers:
            raise ValueError("At least one headers should be specified")

        self._validate_digest(message_headers)

    def signature_string(self, method, path, message_headers):

        expected_string = f"(v): {self.v}\n" if self.v else ""
        expected_string += (
            f"(request-target): {method.lower()} {path}\n"
            f"(created): {self.created}\n"
            f"(expires): {self.expires}\n"
        )

        self.validate_headers(message_headers)

        for h in self.headers.split(" "):
            if h in "(request-target) (v) (created) (expires)".split(" "):
                print(f"skipping {h}")
                continue
            print(f"adding {h} {message_headers[h]}")

            expected_string += f"{h.lower()}: {message_headers[h]}\n"

        # Remove last CR
        return expected_string[:-1]

    def resolve_key(self):
        """Override this method for resolving keys.
        """
        self.encryption_key = load_key(Path("rsa.key").read_bytes())
        return self.encryption_key

    def resolve_cert(self):
        """Override this method for resolving public keys.
        """
        self.decryption_key = load_pubkey(Path("rsa.pub").read_bytes())
        return self.decryption_key

    def sign(self, method, path, message_headers):
        signature_string = self.signature_string(
            method, path, message_headers
        )
        s = sign_string(self.resolve_key(), signature_string)
        return (
            f'keyId="{self.keyId}", algorithm="{self.algorithm}"'
            f", created={self.created}, expires={self.expires}"
            f', v="{self.v}", headers="{self.headers}"'
            f', signature="{s}"'
        )

    @staticmethod
    def _get_message_info(request, response=None):
        # Get path from flask.Request | requests.Request
        path = (
            request.path
            if hasattr(request, "path")
            else urlparse(request.url).path
        )

        message_headers = response.headers if response else request.headers

        return request.method, path, message_headers

    def sign_http_message(self, request, response=None):
        method, path, message_headers = Signature._get_message_info(
            request, response
        )
        return self.sign(method, path, message_headers)

    @staticmethod
    def verify_http_message(self, request, response=None):
        method, path, message_headers = Signature._get_message_info(
            request, response
        )
        return self.verify(method, path, message_headers)

    def verify(self, method, path, message_headers):
        if not self.signature:
            raise ValueError("Missing signature")

        pubkey = self.resolve_cert()
        if not pubkey:
            raise ValueError("Cannot retrieve pubkey")

        signature_bytes = self.signature
        signature_string = self.signature_string(
            method, path, message_headers
        )
        self.validate_headers(message_headers)

        verify_string(pubkey, signature_string, signature_bytes)
