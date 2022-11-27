FROM python:3.10-slim

RUN apt-get update && apt-get install -y git libpq-dev gcc

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install -e .

ENTRYPOINT [ "uvicorn", "iot_data_receiver.main:app", "--port", "7770", "--host", "0.0.0.0"]