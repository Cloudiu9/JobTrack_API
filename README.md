# JobTrack API

A multi-user REST API for tracking job applications, built with Flask, PostgreSQL, SQLAlchemy and Pydantic. Users register, log in with JWT authentication, and manage their own applications, with strict per-user data isolation.

Built to practice production-style backend patterns: authentication, ownership checks, request validation, pagination, migrations and automated testing.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Error Format](#error-format)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Known Limitations & Roadmap](#known-limitations--roadmap)

## Features

- **User authentication:** registration and login with Werkzeug password hashing and short-lived JWT access tokens (Flask-JWT-Extended, 15-minute expiry).
- **Timing-attack mitigation:** login always performs a password-hash check, even for unknown emails.
- **Multi-user ownership:** every application belongs to a user. Reading, updating or deleting someone else's application returns `404 Not Found`, so its existence is not revealed.
- **Pagination, filtering and sorting:** page/limit pagination (`limit` 1-50), filtering by status, and sorting by application date with a deterministic tie-breaker (`id`).
- **Strict validation:** request bodies and query parameters are validated with Pydantic v2. Unknown fields are rejected, and input is normalized (trimmed strings, lowercased emails).
- **Consistent error responses:** centralized JSON error handlers for validation, authentication, not-found and conflict errors.
- **Database migrations:** version-controlled schema management with Alembic, applied automatically on container start.
- **Tested:** Pytest unit and integration tests for services, routes and security, run against an in-memory SQLite database (no Postgres needed to test).
- **Containerized:** Docker and Docker Compose for one-command local setup.

## Tech Stack

| Area | Tools |
| :--- | :--- |
| Language | Python 3.13 |
| Framework | Flask 3 |
| Database / ORM | PostgreSQL 15, SQLAlchemy 2, Alembic, psycopg 3 |
| Validation | Pydantic v2 |
| Authentication | Flask-JWT-Extended, Werkzeug |
| Testing | Pytest |
| DevOps | Docker, Docker Compose |

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose

### 1. Clone the repository

```bash
git clone https://github.com/Cloudiu9/JobTrack_API.git
cd JobTrack_API
```

### 2. Configure environment variables (optional)

Docker Compose ships with development defaults, so the project starts without a `.env` file. To use your own values, create a `.env` file in the project root:

```env
DB_NAME=job_tracker
DB_USER=postgres
DB_PASSWORD=change-me
JWT_SECRET_KEY=change-me-to-a-long-random-string
```

Generate a strong secret with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

> `DB_HOST` and `DB_PORT` are set to `db` and `5432` by Docker Compose and do not need to be defined.

### 3. Start the application

```bash
docker compose up --build
```

On startup, the `web` container applies all database migrations (`alembic upgrade head`) and then starts the API. It is available at **http://localhost:5000**.

### 4. Run the tests

```bash
docker compose exec web pytest
```

### Running without Docker

1. Start a PostgreSQL instance and create a database.
2. Create a virtual environment and install dependencies: `pip install -r requirements.txt`
3. Export `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` and `JWT_SECRET_KEY` (or put them in a `.env` file).
4. Apply migrations: `alembic upgrade head`
5. Run the API: `python app.py`

## Usage Examples

### Register and log in

```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "me@example.com", "password": "a-strong-password"}'
```

```json
{ "id": 1, "email": "me@example.com" }
```

```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "me@example.com", "password": "a-strong-password"}'
```

```json
{ "access_token": "<JWT>" }
```

Send the token in the `Authorization` header on all `/applications` requests. Tokens expire after 15 minutes.

### Create an application

```bash
curl -X POST http://localhost:5000/applications \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{"company": "Bosch", "title": "Junior Engineer", "status": "applied"}'
```

```json
{
  "id": 1,
  "company": "Bosch",
  "title": "Junior Engineer",
  "date_applied": "2026-11-26",
  "status": "applied",
  "date_interview": null
}
```

### List applications (filtered, sorted, paginated)

```bash
curl "http://localhost:5000/applications?status=interview&order=asc&page=1&limit=10" \
  -H "Authorization: Bearer <JWT>"
```

```json
{
  "items": [ ... ],
  "total_applications": 4,
  "per_page": 10,
  "total_pages": 1,
  "has_next": false,
  "has_prev": false,
  "filter_by": "interview",
  "order": "asc"
}
```

### Update an application

```bash
curl -X PATCH http://localhost:5000/applications/1 \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{"status": "interview", "date_interview": "2026-12-03"}'
```

## API Reference

### Authentication

| Method | Endpoint | Description | Auth required |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/register` | Register a new user | No |
| `POST` | `/auth/login` | Log in and receive a JWT access token | No |
| `GET` | `/auth/secure` | Check that a token is valid (returns the user id) | Yes |
| `GET` | `/auth` | List registered users (id and email) | No (see [limitations](#known-limitations--roadmap)) |
| `GET` | `/auth/{id}` | Retrieve a user (id and email) | No (see [limitations](#known-limitations--roadmap)) |

**Registration rules:** `email` is trimmed and lowercased; `password` must be at least 10 characters. Duplicate emails return `409`.

### Applications

All application endpoints require `Authorization: Bearer <token>`.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/applications` | List the current user's applications |
| `POST` | `/applications` | Create an application (`201`) |
| `GET` | `/applications/{id}` | Retrieve one application |
| `PATCH` | `/applications/{id}` | Partially update an application |
| `DELETE` | `/applications/{id}` | Delete an application (`204`, empty body) |

**Query parameters for `GET /applications`**

| Parameter | Values | Default | Notes |
| :--- | :--- | :--- | :--- |
| `status` | `applied`, `interview` | none (all) | Case-insensitive |
| `order` | `asc`, `desc` | `desc` | Sorts by `date_applied`; ties are broken by `id` |
| `page` | integer >= 1 | `1` | |
| `limit` | integer 1-50 | `3` | |

Invalid or unknown query parameters are rejected with `400`.

**Application fields**

| Field | Type | Required on create | Notes |
| :--- | :--- | :--- | :--- |
| `company` | string | Yes | Non-empty |
| `title` | string | Yes | Non-empty |
| `status` | string | Yes | `applied` or `interview` |
| `date_applied` | date (`YYYY-MM-DD`) | No | Defaults to the current date |
| `date_interview` | date (`YYYY-MM-DD`) or `null` | No | |

`PATCH` accepts any subset of these fields (at least one). The `id` cannot be changed, and unknown fields are rejected.

## Error Format

Application errors return JSON in a consistent shape:

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Data is invalid.",
  "details": "..."
}
```

| Status | Error code | When |
| :--- | :--- | :--- |
| `400` | `VALIDATION_ERROR` | Invalid body or query parameters |
| `401` | `AUTHENTICATION_ERROR` | Wrong email or password on login (a missing or invalid token on protected routes also returns `401`) |
| `404` | `MISSING_ERROR` | Resource not found, or owned by another user |
| `409` | `DUPLICATE_EMAIL_ERROR` | Email already registered |
| `500` | `INTERNAL_SERVER_ERROR` | Unexpected server error |

## Project Structure

```text
.
├── app.py                 # Entry point: Flask app, JWT setup, blueprints, error handlers
├── routes/                # HTTP layer: auth and application blueprints
├── services/              # Business logic and validation orchestration
├── db_alchemy.py          # Data-access layer (SQLAlchemy queries and session factory)
├── models/                # SQLAlchemy models (User, Application)
├── pydantic_rules.py      # Pydantic request and query schemas
├── security.py            # Password hashing helpers
├── exceptions.py          # Custom exceptions and centralized error handlers
├── migrations/            # Alembic migrations
├── tests/                 # Pytest unit and integration tests
├── postman/               # Postman collection
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

Requests flow through three layers: **routes** (HTTP) -> **services** (rules and validation) -> **db_alchemy** (queries). Every query on applications is scoped by the authenticated user's id.

## Testing

```bash
docker compose exec web pytest
```

The suite covers services, routes and security helpers, and uses an in-memory SQLite database with per-test transaction rollback, so tests are isolated and fast.
