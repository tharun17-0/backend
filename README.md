# FlyRank Task Auth API

A secure FastAPI application that demonstrates user authentication and protected API routes using Supabase Auth.

The project combines a FastAPI backend, PostgreSQL for task data, and Supabase Auth for user authentication and JWT-based authorization.

## Features

* User signup with Supabase Auth
* User login with email and password
* JWT access token authentication
* Protected user profile endpoint
* Protected dashboard endpoint
* Protected logout endpoint
* Reusable FastAPI authentication dependency
* Public API endpoint
* Swagger UI with Bearer Token authorization
* Dockerized FastAPI and PostgreSQL setup

## Technology Stack

* Python 3.12
* FastAPI
* Supabase Auth
* PostgreSQL 16
* Docker / Docker Compose
* Pydantic
* Uvicorn
* Git / GitHub

## Project Structure

```text
backend_intern/
│
├── auth.py
├── main.py
├── supabase_client.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
│
└── repositories/
    └── task_repository.py
```

## Environment Variables

Create a `.env` file in the project root.

```env
DATABASE_URL=postgresql://taskuser:taskpassword@db:5432/taskdb
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

Do not commit the `.env` file to GitHub.

The `.env` file contains environment-specific credentials and is excluded through `.gitignore`.

## Running the Application

Make sure Docker Desktop is running.

Build and start the application:

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

Stop the application with:

```bash
docker compose down
```

## Swagger UI

FastAPI automatically provides Swagger UI at:

```text
http://localhost:8000/docs
```

The Swagger documentation includes the API routes and Bearer Token authorization.

To test protected endpoints:

1. Call `POST /auth/login`.
2. Copy the returned `access_token`.
3. Click the `Authorize` button in Swagger.
4. Enter the access token.
5. Click `Authorize`.
6. Use `Try it out` on protected endpoints.

## API Reference

| Method | Endpoint               | Authentication | Description                               | Success |
| ------ | ---------------------- | -------------- | ----------------------------------------- | ------- |
| POST   | `/auth/signup`         | No             | Create a user account                     | 201     |
| POST   | `/auth/login`          | No             | Authenticate a user and return JWT tokens | 200     |
| POST   | `/auth/logout`         | Yes            | Log out an authenticated user             | 204     |
| GET    | `/public/info`         | No             | Return public information                 | 200     |
| GET    | `/protected/profile`   | Yes            | Return authenticated user's profile       | 200     |
| GET    | `/protected/dashboard` | Yes            | Return protected dashboard information    | 200     |
| GET    | `/tasks`               | No             | Get all tasks                             | 200     |
| GET    | `/tasks/{task_id}`     | No             | Get a task by ID                          | 200     |
| POST   | `/tasks`               | No             | Create a task                             | 201     |
| PUT    | `/tasks/{task_id}`     | No             | Update a task                             | 200     |
| DELETE | `/tasks/{task_id}`     | No             | Delete a task                             | 204     |

## Authentication Flow

The authentication flow uses Supabase Auth.

```text
Client
   │
   │ email + password
   ▼
Supabase Auth
   │
   │ access token (JWT)
   ▼
Client
   │
   │ Authorization: Bearer <token>
   ▼
FastAPI
   │
   │ get_current_user()
   ▼
Supabase Auth
   │
   │ verify JWT
   ▼
Protected Endpoint
```

The reusable authentication dependency is implemented in `auth.py`.

Protected endpoints use:

```python
Depends(get_current_user)
```

The dependency extracts the Bearer token, verifies it with Supabase, and makes the authenticated user available to the endpoint.

## Authentication Error Handling

The API uses the following status codes:

* `400 Bad Request` — missing signup/login input
* `401 Unauthorized` — missing or invalid authentication
* `201 Created` — successful signup
* `200 OK` — successful login or protected read
* `204 No Content` — successful logout

## Testing Authentication

### Signup

Send:

```json
{
  "email": "test@example.com",
  "password": "Password123!"
}
```

to:

```text
POST /auth/signup
```

Expected status:

```text
201 Created
```

### Login

Send:

```json
{
  "email": "test@example.com",
  "password": "Password123!"
}
```

to:

```text
POST /auth/login
```

Expected response contains:

```json
{
  "access_token": "...",
  "refresh_token": "..."
}
```

### Protected Profile

Send the access token using:

```text
Authorization: Bearer <access_token>
```

to:

```text
GET /protected/profile
```

A valid token returns the user's ID, email, and account creation timestamp.

An invalid or expired token returns:

```text
401 Unauthorized
```

## Security

* Supabase manages user authentication and password security.
* JWTs are verified through Supabase Auth.
* Authentication credentials are stored in environment variables.
* `.env` is excluded from Git.
* Supabase credentials must never be committed to the repository.
* Protected routes use a reusable authentication dependency.

![Project Screenshot](image.png)
