FROM python:3.12-alpine

WORKDIR /app

COPY model .
RUN pip install ./model

COPY task .
RUN pip install ./task
COPY task/crontab /etc/crontabs/root



