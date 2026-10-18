# Vehicle Maintenance API

FastAPI application providing account creation, login with a JWT bearer token,
an authenticated `/me` endpoint, part configuration CRUD, car management,
maintenance tracking, and expiry alerts.

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
- `GET /history`: view all history for the authenticated account.
- `GET /history?filter_type=car&value=ABC-123`: filter history by car number.
- `GET /history?filter_type=part&value=oil%20filter`: filter by part name.

Car numbers are stored in uppercase. Odometer readings cannot be negative or
lower than the previously saved reading. All car endpoints require
authentication. History records car additions, odometer updates, and part
additions or updates. Deleting a car also deletes its history.

## Maintenance and expiry endpoints

- `PUT /cars/{car_no}/parts/{part}`: record or update a part replacement using
  `changed_km` and `changed_date`.
- `GET /cars/maintenance?filter_type=car&value=...`: view maintenance records
  filtered by car number.
- `GET /cars/maintenance?filter_type=part&value=...`: view maintenance records
  filtered by part name.
- `GET /cars/maintenance`: view all of the authenticated user's maintenance
  records.
- `GET /expiry`: list the authenticated user's expired and soon-to-expire
  maintenance items.

Car and part filters are case-insensitive partial matches. All maintenance
views require authentication and only show the current user's cars.

Maintenance replacements must not be dated in the future, and their odometer
reading cannot exceed the car's current reading. The next due values are
calculated from the effective part configuration. Expiry responses include
items that are past due or within the part's configured kilometer/day limits.

Run the tests with `pytest -q`.