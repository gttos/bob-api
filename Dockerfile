# Dockerfile
FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONPATH=/app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && rm -rf /var/lib/apt/lists/*

FROM base AS dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

FROM dependencies AS production
COPY . .
RUN mkdir -p /app/media
EXPOSE 8010
