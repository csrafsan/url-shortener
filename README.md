# URL Shortener

A scalable URL shortener service built with FastAPI, PostgreSQL, Redis, Docker, and Nginx.

## Features

- Create short URLs from long URLs
- Redirect short links to the original destination
- Persist links in PostgreSQL
- Cache lookups in Redis for fast redirect response
- Load balance across multiple web replicas with Nginx
- Distributed Base62 short-code generation using Redis counters

## Project Structure

- `main.py` - FastAPI application and cache-first redirect flow
- `database.py` - PostgreSQL database helpers and SQLAlchemy setup
- `docker-compose.yml` - Multi-container orchestration for app, DB, cache, and load balancer
- `Dockerfile` - Container image definition
- `nginx.conf` - Nginx reverse proxy/load balancer configuration

## Run locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Run with Docker Compose

```bash
docker compose up --build
```

## Notes

- `DATABASE_URL` now defaults to PostgreSQL when set in the environment.
- `REDIS_URL` is used for cache lookups and distributed ID generation.
- The Docker Compose setup includes:
  - `db` : PostgreSQL service
  - `cache` : Redis service
  - `web1`, `web2`, `web3` : app replicas
  - `loadbalancer` : Nginx reverse proxy

## License

This project is licensed under the MIT License.
