# URL Shortener

A distributed URL shortener built with FastAPI, Redis, PostgreSQL, Docker, Kubernetes, Nginx, and Prometheus.

## Overview

This project demonstrates a scalable mini-link service where:

- web pods handle URL shortening and redirects
- each pod generates Snowflake-style IDs locally using its Kubernetes pod index
- Redis provides fast cache lookups and an analytics queue
- an analytics worker stores click events into PostgreSQL
- Prometheus exposes application metrics for monitoring

## Architecture

```text
Client
  │
  ▼
Kubernetes Service (NodePort: 30090)
  │
  ├── web-0 Pod
  │    └── generates Snowflake ID locally using pod index
  ├── web-1 Pod
  │    └── generates Snowflake ID locally using pod index
  └── web-2 Pod
       └── generates Snowflake ID locally using pod index

Each web pod:
  ├── reads/writes Redis cache
  └── pushes analytics events to Redis queue

Redis Queue (BLPOP)
  │
  ▼
analytics-worker Pod
  │
  ▼
PostgreSQL Database
```

## Key Features

- Create short URLs from long URLs
- Redirect short codes to the original destination
- Cache hot redirects in Redis for low latency
- Generate distributed IDs without a central counter
- Persist analytics events in PostgreSQL
- Expose Prometheus metrics at /metrics
- Serve a simple frontend from the static folder

## Project Structure

- main.py - FastAPI app, routing, rate limiting, redirect logic, and analytics endpoint
- database.py - SQLAlchemy models and PostgreSQL session setup
- snowflake.py - Distributed Snowflake-style ID generation based on pod name
- worker.py - Background consumer that writes analytics events to PostgreSQL
- janitor.py - Cleanup job for expired links
- static/index.html - Simple frontend UI
- docker-compose.yml - Docker Compose stack for local development
- nginx.conf - Nginx reverse proxy configuration
- prometheus.yml - Prometheus scrape configuration
- k8s/ - Kubernetes manifests for PostgreSQL, Redis, web StatefulSet, and analytics worker

## Tech Stack

- Python 3.10+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- Docker / Docker Compose
- Kubernetes (Minikube example manifests)
- Nginx
- Prometheus

## Local Development with Docker Compose

1. Make sure Docker is running.
2. Start the stack:

```bash
docker compose up --build
```

3. Open the services:

- Frontend: http://localhost:9090/
- API docs: http://localhost:8000/docs
- Prometheus: http://localhost:9095/
- Grafana: http://localhost:3000/

## Kubernetes Deployment

The repository includes Kubernetes manifests under k8s/ for a basic distributed deployment.

### Prerequisites

- Docker installed and running
- Minikube or another Kubernetes cluster
- kubectl configured

### Build and Load the Web Image

```bash
docker build -t mini-link-web:latest .
minikube image load mini-link-web:latest
```

### Apply the Manifests

```bash
kubectl apply -f k8s/infrastructure.yaml
kubectl apply -f k8s/web-statefulset.yaml
kubectl apply -f k8s/worker-deployment.yaml
```

### Access the Service

```bash
kubectl get svc
```

The web service is exposed on NodePort 30090 by default.

## Environment Variables

- DATABASE_URL - PostgreSQL connection string
- REDIS_URL - Redis connection string
- POD_NAME - Kubernetes pod name used by the Snowflake generator

## API Usage

### Shorten a URL

```bash
curl -X POST "http://127.0.0.1:8000/shorten" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

### Redirect a Short Code

```bash
curl -I "http://127.0.0.1:8000/abc123"
```

### View Analytics

```bash
curl "http://127.0.0.1:8000/analytics/abc123"
```

## Monitoring

- Prometheus metrics are exposed at /metrics
- Grafana can be used for dashboards when running the Docker Compose stack

## License

This project is licensed under the MIT License.
