FROM python:3.7-alpine
RUN apk add gcc make musl-dev libffi-dev openssl-dev
ADD requirements.txt .
RUN pip install -rrequirements.txt
