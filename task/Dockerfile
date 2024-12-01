FROM python:3.12-alpine

WORKDIR /app
COPY pyproject.toml .
RUN pip install .

COPY src .
RUN pip install .

# Set up cron job
RUN touch /tmp/cron.log
COPY crontab /etc/cron.d/crontab
RUN crontab /etc/cron.d/crontab
CMD crond && tail -f /tmp/cron.log