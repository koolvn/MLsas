FROM python:3.7-slim-buster

COPY requirements.txt /app/

RUN pip install -r /app/requirements.txt --no-cache-dir

COPY . /app
EXPOSE 8443
CMD ["python", "/app/bot_webhooks.py"]