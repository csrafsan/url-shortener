# URL Shortener

A simple URL shortener service built with FastAPI, SQLite, Docker, and Nginx.

## Features

- Create short URLs from long URLs
- Redirect short links to the original destination
- Persist links in SQLite
- Run with Docker Compose

## Project Structure

- `main.py` - FastAPI application
- `database.py` - SQLite database helpers
- `docker-compose.yml` - Docker Compose configuration
- `Dockerfile` - Container image definition
- `nginx.conf` - Nginx reverse proxy configuration

## Run locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Run with Docker Compose

```bash
docker compose up --build
```

## License

This project is licensed under the MIT License.
