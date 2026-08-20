# Task API

A RESTful Task Management API built with **FastAPI**, **PostgreSQL**, and **Supabase Authentication**. The project began as a CRUD API for managing tasks and was progressively extended throughout the **FlyRank AI Backend Engineering Internship** to include Docker, PostgreSQL, JWT authentication, protected routes, and interactive API documentation with Swagger UI.

The API now supports:

* Task CRUD operations
* PostgreSQL persistence
* User registration and login
* JWT authentication with Supabase
* Protected endpoints
* Logout
* Interactive Swagger UI with Bearer Authentication

---

# Tech Stack

* Python 3.12
* FastAPI
* PostgreSQL
* Psycopg
* Supabase Authentication
* Docker
* Docker Compose
* Uvicorn
* Swagger UI
* uv

---

# Project Overview

This project is the culmination of multiple backend engineering assignments completed during the FlyRank AI Backend Engineering Internship.

The project originally started as a simple CRUD Task Management API and has been enhanced over time with:

* PostgreSQL database integration
* Docker containerization
* Environment variable configuration
* JWT authentication using Supabase
* Reusable authentication dependency for protected routes
* Interactive Swagger documentation with Bearer token authentication

The API demonstrates how authentication can be added to an existing REST API while maintaining clean architecture and reusable code.

---

# Project Structure

```text
task-api/
│
├── images/
│   ├── postgres-tasks.png
│   └── swagger-ui.png
│
├── .dockerignore
├── .env.example
├── .gitignore
├── compose.yaml
├── Dockerfile
├── auth.py
├── main.py
├── supabase_client.py
├── pyproject.toml
├── README.md
├── requirements.txt
└── uv.lock
```

---

# Database

The application uses PostgreSQL as its primary database.

On startup, the application automatically:

* Connects to PostgreSQL
* Creates the required database tables if they do not exist
* Seeds sample tasks when the database is empty

The database is persisted using Docker volumes, ensuring that data remains available after restarting containers.

---

# Environment Variables

Create a `.env` file using `.env.example`.

Example:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
DATABASE_URL=postgresql://postgres:password@localhost:5433/tasks
```

When using Docker Compose:

```env
DATABASE_URL=postgresql://postgres:password@db:5432/tasks
```

---

# Running the Project

## Clone the Repository

```bash
git clone https://github.com/AdebankeDev/todo-crud-api.git

cd todo-crud-api
```

---

## Install Dependencies

```bash
uv sync
```

---

## Run the API

```bash
uv run uvicorn main:app --reload
```

Open:

```
http://127.0.0.1:8000/docs
```

---

## Run with Docker

```bash
docker compose up --build
```

Stop the containers:

```bash
docker compose down
```

Swagger UI will be available at:

```
http://localhost:8000/docs
```

---

# API Reference

| Method | Endpoint               | Description                               | Authentication |
| ------ | ---------------------- | ----------------------------------------- | :------------: |
| GET    | `/`                    | API information                           |        ❌       |
| GET    | `/health`              | Health check                              |        ❌       |
| GET    | `/tasks`               | Retrieve all tasks                        |        ❌       |
| GET    | `/tasks/{id}`          | Retrieve a task by ID                     |        ❌       |
| POST   | `/tasks`               | Create a new task                         |        ❌       |
| PUT    | `/tasks/{id}`          | Update a task                             |        ❌       |
| DELETE | `/tasks/{id}`          | Delete a task                             |        ❌       |
| GET    | `/stats`               | Retrieve task statistics                  |        ❌       |
| POST   | `/auth/signup`         | Register a new user                       |        ❌       |
| POST   | `/auth/login`          | Authenticate a user and receive a JWT     |        ❌       |
| POST   | `/auth/logout`         | Log out the authenticated user            |        ✅       |
| GET    | `/protected/profile`   | Retrieve the authenticated user's profile |        ✅       |
| GET    | `/protected/dashboard` | Example protected endpoint                |        ✅       |

---

# Authentication

Authentication is powered by **Supabase Auth** using JSON Web Tokens (JWT).

## Register a User

```
POST /auth/signup
```

## Login

```
POST /auth/login
```

A successful login returns an **access token**.

## Access Protected Endpoints

1. Open Swagger UI.
2. Click the **Authorize** button.
3. Paste your JWT access token.
4. Execute any protected endpoint.

Protected endpoints automatically verify the token before processing the request.

If the token is:

* Invalid
* Expired
* Tampered with

the API returns:

```http
401 Unauthorized
```

---

# Example Protected Response

```json
{
  "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "email": "user@example.com",
  "created_at": "2026-08-01T09:30:00Z"
}
```

---

# Swagger UI

FastAPI automatically generates interactive API documentation.

The Swagger UI includes:

* Bearer Authentication support
* Authorize button
* Interactive endpoint testing
* Protected endpoint lock icons

![Swagger UI](images/swagger-ui.png)

---

# Docker Features

The project uses Docker Compose to orchestrate the API and PostgreSQL database.

Features include:

* Separate API and database containers
* Automatic PostgreSQL startup
* Health checks
* Persistent Docker volumes
* One-command setup

```bash
docker compose up --build
```

---

# Features

* RESTful CRUD Task API
* PostgreSQL database
* Dockerized deployment
* Docker Compose orchestration
* Persistent data storage
* Automatic database initialization
* JWT authentication using Supabase
* User registration
* User login
* User logout
* Protected endpoints
* Reusable authentication dependency
* Interactive Swagger UI
* Environment variable configuration

---

# Future Improvements

Potential enhancements include:

* Protecting CRUD task endpoints with authentication
* Role-based authorization
* Refresh token support
* Password reset functionality
* User-specific task ownership
* Automated testing with Pytest
* CI/CD using GitHub Actions

### LLM Provider Configuration

The LLM provider is configured through `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL`, so the application code does not need to change when switching providers.

# Author

**Adebanke Peke**

FlyRank AI Backend Engineering Internship

This project represents the progressive development of a FastAPI backend throughout the internship, evolving from a basic CRUD API into a production-style REST API featuring PostgreSQL, Docker, Supabase JWT authentication, protected routes, and interactive Swagger documentation.
