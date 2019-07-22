from datetime import datetime
from logging import basicConfig
from logging.config import dictConfig
from os.path import isfile

import connexion
import yaml

# from opencensus.trace.ext.flask.flask_middleware import FlaskMiddleware
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


configure_logger()

zapp = connexion.FlaskApp(__name__, port=443, specification_dir="./")
zapp.add_api(
    "service-provider.yaml", arguments={"title": "Hello World Example"}
)
