import argparse
from logging import basicConfig
from logging.config import dictConfig
from os.path import isfile

import connexion

from datetime import datetime
import yaml
from opencensus.trace.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.trace.exporters.jaeger_exporter import JaegerExporter


def configure_logger(log_config="logging.yaml"):
    """Configure the logging subsystem."""
    if not isfile(log_config):
        return basicConfig()

    with open(log_config) as fh:
        log_config = yaml.load(fh)
        return dictConfig(log_config)


# Connecto to the jaeger.thrift agent UDP port.
je = JaegerExporter(
    service_name="flask-%s" % datetime.now().isoformat(),
    agent_host_name="jaeger",
    agent_port=6831,
    endpoint="/api/traces",
)


if __name__ == "__main__":
    configure_logger()
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--insecure-add-idp",
        dest="insecure_idp",
        required=False,
        help="Point to the IdP metadata URL",
        default=False,
    )
    args = parser.parse_args()

    zapp = connexion.FlaskApp(__name__, port=443, specification_dir="./")
    zapp.add_api(
        "service-provider.yaml", arguments={"title": "Hello World Example"}
    )

    middleware = FlaskMiddleware(zapp.app, exporter=je)
    zapp.run(host="0.0.0.0", debug=True, ssl_context="adhoc")
