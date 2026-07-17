# URL Shortener

A scalable URL shortener service built with FastAPI, PostgreSQL, Redis, Docker, and Nginx.

## Overview

This repository demonstrates a URL shortening system with:

- FastAPI web service for shortening and redirecting URLs
- PostgreSQL for durable storage of original links
- Redis for caching and distributed sequence generation
- Docker Compose orchestration for local development
- Nginx load balancing across multiple backend replicas

## Features

- Create short URLs from long URLs
- Redirect short codes to original URLs
- Persistent storage in PostgreSQL
- Cache redirects in Redis for low latency
- Load balanced web replicas using Nginx
- Distributed Base62 short-code generation using Redis counters

## Project Structure

- `main.py` - FastAPI application and redirect flow
- `database.py` - PostgreSQL setup and database helper functions
- `docker-compose.yml` - Compose file for app, PostgreSQL, Redis, and Nginx
- `Dockerfile` - Application container image definition
- `nginx.conf` - Nginx reverse proxy and load balancer configuration
- `worker.py` - Background worker (if included in the design)
- `janitor.py` - Cleanup or maintenance utility

## Local Development

1. Create and activate a Python virtual environment:

```bash
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate     # Windows
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
uvicorn main:app --reload
```

4. Open the API docs at `http://127.0.0.1:8000/docs`

## Run with Docker Compose

Start all services together:

```bash
docker compose up --build
```

Then access the service through the load balancer or app endpoint.

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string

## Docker Compose Services

- `db` - PostgreSQL database
- `cache` - Redis cache
- `web1`, `web2`, `web3` - application replicas
- `loadbalancer` - Nginx reverse proxy

## License

This project is licensed under the MIT License.
