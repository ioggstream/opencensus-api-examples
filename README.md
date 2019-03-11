# opencensus-api-examples

Minimal examples of api usage with opencensus.

opencensus is a library for exporting metrics and traces
of your software to an external platform (eg. jaeger, ...).


## Running

The following command spawns:

  - a connexion API at https://localhost:8443/
  - a Jaeger container with a tracing webui at http://localhost:16686/search

        docker-compose up

Now point the browser to the local API
and after issuing some requests, show the tracings on Jaeger.

        firefox https://localhost:8443/


