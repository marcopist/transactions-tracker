FROM python:3.12-slim

COPY . /tmp/app
WORKDIR /tmp/app
RUN python -m pip install .

WORKDIR /root
RUN rm -rf /tmp/app