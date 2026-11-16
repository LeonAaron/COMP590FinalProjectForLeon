FROM python:3.12-slim-bookworm

RUN python -m pip install --no-cache-dir flask==3.1.3 pytest==9.1.1

WORKDIR /app
COPY app/ /app/
