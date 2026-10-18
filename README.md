# Account and Part API

FastAPI application providing account creation, login with a JWT bearer token,
an authenticated `/me` endpoint, and authenticated part configuration CRUD.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Create a `.env` file and set `SECRET_KEY` to a private random value. Set
   `DATABASE_URL` if you do not want to use the default SQLite database.
4. Start the API with `uvicorn main:app --reload`.

Database tables and default part configurations are initialized on startup.
Open `/docs` to try the API.

## Endpoints

- `POST /create_account`: create an account with `user_id`, `user_name`, and `password`.
- `POST /login_account`: verify credentials and return an `access_token`.
- `GET /me`: return the current account; requires `Authorization: Bearer <token>`.

## Part endpoints

- `POST /parts`: add a part configuration; requires authentication and settings unlock.
- `GET /parts`: list the authenticated account's parts; requires authentication.
- `PUT /parts/{part}`: update a part configuration; requires authentication and settings unlock.
- `DELETE /parts/{part}`: delete a part configuration; requires authentication and settings unlock.

Part configurations use `part`, `km_life`, `month_life`, `km_limit`, and
`day_limit`. Part names are trimmed and stored in lowercase. Life values must
be positive, while limits may be zero.

The account and part endpoints are separated into routers. Updating or deleting
parts, and adding new parts, requires a short-lived settings token from
`POST /settings/unlock`. Default parts are shared; user updates create a
user-specific override.

## Car endpoints

- `POST /cars`: add a car with `car_no`, `model`, `company`, and optional `onground_km`.
- `DELETE /cars/{car_no}`: delete a car owned by the authenticated account.
- `PUT /cars/{car_no}/km`: update the car's odometer reading using `onground_km`.

Car numbers are stored in uppercase. Odometer readings cannot be negative or
lower than the previously saved reading. All car endpoints require
authentication.

Run the tests with `pytest -q`.