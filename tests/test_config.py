from flask_testing import TestCase

import logging
from pathlib import Path

import connexion
import yaml
from openapi.callbacks import check_digest_header, add_digest_header


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

config_file = Path(__file__).absolute().parent / "test-config.yaml"
with config_file.open() as fh:
    config = yaml.safe_load(fh)


class BaseTestCase(TestCase):
    def create_app(self):
        logging.getLogger("connexion.operation").setLevel("ERROR")
        zapp = connexion.App(__name__, specification_dir="..")
        #  app.app.json_encoder = DataclassEncoder
        zapp.app.config.update(config)
        zapp.add_api("openapi/service-provider.yaml")
        zapp.app.before_request(check_digest_header)
        zapp.app.after_request(add_digest_header)

        return zapp.app
