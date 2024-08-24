FROM python:3.12

COPY . /app
WORKDIR /app

RUN pip install .
CMD ["gunicorn", "-w", "4", "transactions-api:app"]