# Account Authentication API

FastAPI application providing account creation, login with a JWT bearer token,
and an authenticated `/me` endpoint.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and set `SECRET_KEY` to a private random value.
4. Start the API with `uvicorn main:app --reload`.

The SQLite database is created as `auth.db` on startup. Open `/docs` to try the
API.

## Endpoints

- `POST /create_account`: create an account with `user_id`, `user_name`, and `password`.
- `POST /login_account`: verify credentials and return an `access_token`.
- `GET /me`: return the current account; requires `Authorization: Bearer <token>`.

Run the auth tests with `pytest tests/test_auth.py -q`.