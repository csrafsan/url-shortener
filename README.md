# URL Shortener

A scalable URL shortener service built with FastAPI, PostgreSQL, Redis, Docker, Nginx, and Prometheus.

## Overview

This project demonstrates a distributed URL shortening system with:

- FastAPI endpoints for creating short links and redirecting them
- PostgreSQL for durable storage of original URLs
- Redis for caching and fast lookups
- Nginx for load balancing across multiple app replicas
- Prometheus and Grafana monitoring for app metrics
- A simple frontend UI served from the static folder

## Features

- Create short URLs from long URLs
- Redirect short codes to the original destination
- Persistent storage in PostgreSQL
- Cache redirects in Redis for low latency
- Distributed short-code generation using a Snowflake-style ID generator
- Basic analytics support for redirect events
- Prometheus metrics exposed at /metrics

## Project Structure

- main.py - FastAPI application, routing, rate limiting, and redirect logic
- database.py - SQLAlchemy models and database session setup
- snowflake.py - Distributed ID generation helper
- static/index.html - Simple frontend for shortening URLs
- docker-compose.yml - Compose setup for app, database, Redis, Nginx, worker, and monitoring services
- worker.py - Background worker for analytics processing
- janitor.py - Cleanup utility for expired links
- prometheus.yml - Prometheus scrape configuration

## Quick Start with Docker Compose

1. Make sure Docker is running.
2. Start the full stack:

```bash
docker compose up --build
```

3. Open the app in your browser:

- Frontend: http://localhost:9090/
- API docs: http://localhost:8000/docs
- Prometheus: http://localhost:9095/
- Grafana: http://localhost:3000/

## Local Development

1. Create and activate a Python virtual environment:

```bash
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app locally:

```bash
uvicorn main:app --reload
```

4. Open the API docs at http://127.0.0.1:8000/docs

## Example API Usage

Shorten a URL:

```bash
curl -X POST "http://127.0.0.1:8000/shorten" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

Redirect using a short code:

```bash
curl -I "http://127.0.0.1:8000/abc123"
```

## Environment Variables

- DATABASE_URL - PostgreSQL connection string
- REDIS_URL - Redis connection string
- WORKER_ID - Unique worker ID for distributed ID generation (used in Docker Compose)

## Docker Compose Services

- db - PostgreSQL database
- cache - Redis cache
- web1, web2, web3 - Application replicas
- loadbalancer - Nginx reverse proxy
- analytics_worker - Background analytics worker
- db_janitor - Cleanup job for expired links
- prometheus - Metrics collection
- grafana - Dashboard UI

## License

This project is licensed under the MIT License.
