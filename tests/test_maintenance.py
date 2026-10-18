import os
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SECRET_KEY", "maintenance-tests-secret")
os.environ.setdefault("DATABASE_URL", "sqlite://")

from core.database import Base, get_db
from main import app
from models import History, Maintenance, Part
from services.default_part_service import seed_default_parts
from services.expiry_service import ExpiryService
from services.maintenance_service import add_months
import default_parts


ACCOUNT = {
    "user_id": "maintenance-user",
    "user_name": "Maintenance User",
    "password": "strongpass",
}
CAR = {
    "car_no": "abc-123",
    "model": "Civic",
    "company": "Honda",
    "onground_km": 20000,
}


@pytest.fixture
def db_session():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)()
    seed_default_parts(session, default_parts.DEFAULT_PARTS)
    try:
        yield session
    finally:
        app.dependency_overrides.clear()
        session.close()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client


def authenticate(client, user_id: str = "maintenance-user"):
    client.post("/create_account", json={**ACCOUNT, "user_id": user_id})
    response = client.post(
        "/login_account",
        json={"user_id": user_id, "password": ACCOUNT["password"]},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_car(client, headers, **overrides):
    return client.post("/cars", json={**CAR, **overrides}, headers=headers)


def update_part(client, headers, car="abc-123", part="oil filter", **payload):
    values = {
        "changed_km": 18000,
        "changed_date": "2024-01-31",
        **payload,
    }
    return client.put(f"/cars/{car}/parts/{part}", json=values, headers=headers)


def test_maintenance_endpoint_requires_login(client):
    payload = {"changed_km": 18000, "changed_date": "2024-01-31"}
    assert client.put("/cars/ABC-123/parts/oil filter", json=payload).status_code in (
        401,
        403,
    )
    assert client.get("/expiry").status_code in (401, 403)
    assert client.get("/history").status_code in (401, 403)


def test_update_part_creates_maintenance_from_part_life(client, db_session):
    headers = authenticate(client)
    create_car(client, headers)

    response = update_part(client, headers)

    assert response.status_code == 200
    assert response.json() == {
        "status": True,
        "message": "oil filter updated successfully.",
    }
    record = db_session.query(Maintenance).one()
    assert record.changed_km == 18000
    assert record.next_changed_km == 21000
    assert record.changed_date == date(2024, 1, 31)
    assert record.next_changed_date == date(2024, 7, 31)


def test_update_part_replaces_existing_record_instead_of_duplicating(
    client, db_session
):
    headers = authenticate(client)
    create_car(client, headers)
    update_part(client, headers, changed_km=10000, changed_date="2024-01-01")

    response = update_part(
        client, headers, part="Oil Filter", changed_km=15000, changed_date="2024-03-15"
    )

    assert response.status_code == 200
    record = db_session.query(Maintenance).one()
    assert record.changed_km == 15000
    assert record.next_changed_km == 18000
    assert record.next_changed_date == date(2024, 9, 15)


def test_maintenance_history_records_part_add_and_update(client, db_session):
    headers = authenticate(client)
    create_car(client, headers)
    update_part(client, headers)
    update_part(
        client,
        headers,
        changed_km=19000,
        changed_date="2024-02-01",
    )

    rows = db_session.query(History).order_by(History.id).all()

    assert [row.action_type for row in rows] == ["car_added", "part_added", "part_updated"]
    assert rows[1].part_name == "oil filter"
    assert rows[1].changed_km == 18000
    assert rows[1].changed_date == date(2024, 1, 31)
    assert rows[1].details == "Next KM: 21000, Next Date: 2024-07-31"
    assert rows[2].changed_km == 19000
    assert rows[2].details == "Next KM: 22000, Next Date: 2024-08-01"


def test_history_filters_by_car_and_part(client):
    headers = authenticate(client)
    create_car(client, headers)
    create_car(client, headers, car_no="XYZ-999")
    update_part(client, headers, part="oil filter")
    update_part(client, headers, car="XYZ-999", part="battery")

    by_car = client.get(
        "/history?filter_type=car&value=xyz-999",
        headers=headers,
    )
    by_part = client.get(
        "/history?filter_type=part&value=OIL%20FILTER",
        headers=headers,
    )
    missing_value = client.get("/history?filter_type=part", headers=headers)
    invalid_filter = client.get(
        "/history?filter_type=unknown",
        headers=headers,
    )

    assert [row["action_type"] for row in by_car.json()] == [
        "part_added",
        "car_added",
    ]
    assert [row["part_name"] for row in by_part.json()] == ["oil filter"]
    assert missing_value.status_code == 400
    assert invalid_filter.status_code == 422


def test_update_part_rejects_missing_car_or_part(client, db_session):
    headers = authenticate(client)
    create_car(client, headers)

    assert update_part(client, headers, car="NOPE").status_code == 404
    assert update_part(client, headers, part="unknown part").status_code == 404
    assert db_session.query(Maintenance).count() == 0


def test_update_part_rejects_future_date_and_km_above_odometer(client, db_session):
    headers = authenticate(client)
    create_car(client, headers)
    future = (date.today() + timedelta(days=1)).isoformat()

    future_response = update_part(client, headers, changed_date=future)
    km_response = update_part(client, headers, changed_km=20001)

    assert future_response.status_code == 400
    assert future_response.json()["detail"] == "Future date not allowed."
    assert km_response.status_code == 400
    assert km_response.json()["detail"] == (
        "New change km must be less than on ground km."
    )
    assert db_session.query(Maintenance).count() == 0


def test_other_users_cannot_update_or_see_another_users_maintenance(client, db_session):
    owner_headers = authenticate(client, "car-owner")
    other_headers = authenticate(client, "other-user")
    create_car(client, owner_headers)
    update_part(client, owner_headers)

    other_update = update_part(client, other_headers)
    other_expiry = client.get("/expiry", headers=other_headers)

    assert other_update.status_code == 404
    assert other_expiry.json() == []
    assert db_session.query(Maintenance).count() == 1


def test_expiry_lists_expired_records_and_follows_car_odometer(client):
    headers = authenticate(client)
    create_car(client, headers)
    update_part(
        client,
        headers,
        changed_km=18000,
        changed_date=(date.today() - timedelta(days=200)).isoformat(),
    )

    expiry = client.get("/expiry", headers=headers)
    assert expiry.status_code == 200
    assert len(expiry.json()) == 1
    assert expiry.json()[0]["status"] == "expired"
    assert expiry.json()[0]["part"] == "oil filter"

    client.put(
        "/cars/ABC-123/km",
        json={"onground_km": 20900},
        headers=headers,
    )
    assert client.get("/expiry", headers=headers).json()[0]["remaining_km"] == 100


def test_expiry_is_empty_when_not_near_due(client):
    headers = authenticate(client)
    create_car(client, headers)
    update_part(
        client,
        headers,
        changed_km=20000,
        changed_date=date.today().isoformat(),
    )

    assert client.get("/expiry", headers=headers).json() == []


def test_view_maintenance_filters_by_car_number_or_part_name(client):
    headers = authenticate(client)
    create_car(client, headers, car_no="ABC-123")
    create_car(client, headers, car_no="XYZ-999")
    update_part(
        client,
        headers,
        car="ABC-123",
        part="oil filter",
        changed_date="2024-01-31",
    )
    update_part(
        client,
        headers,
        car="XYZ-999",
        part="battery",
        changed_date="2024-01-31",
    )

    by_car = client.get(
        "/cars/maintenance?filter_type=car&value=abc-1",
        headers=headers,
    )
    by_part = client.get(
        "/cars/maintenance?filter_type=part&value=BAT",
        headers=headers,
    )

    assert by_car.status_code == 200
    assert [(item["car_no"], item["part"]) for item in by_car.json()] == [
        ("ABC-123", "oil filter")
    ]
    assert by_part.status_code == 200
    assert [(item["car_no"], item["part"]) for item in by_part.json()] == [
        ("XYZ-999", "battery")
    ]


def test_view_maintenance_requires_filter_value_and_login(client):
    assert client.get("/cars/maintenance").status_code in (401, 403)
    headers = authenticate(client)

    assert client.get(
        "/cars/maintenance?filter_type=car", headers=headers
    ).status_code == 400
    assert client.get(
        "/cars/maintenance?filter_type=part&value=%20",
        headers=headers,
    ).status_code == 400
    assert client.get(
        "/cars/maintenance?filter_type=invalid&value=x",
        headers=headers,
    ).status_code == 422


def test_view_maintenance_does_not_expose_another_users_records(client):
    owner_headers = authenticate(client, "car-owner")
    other_headers = authenticate(client, "other-user")
    create_car(client, owner_headers)
    update_part(client, owner_headers)

    response = client.get(
        "/cars/maintenance?filter_type=car&value=ABC",
        headers=other_headers,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_expiry_reports_kilometer_and_date_thresholds():
    detail = SimpleNamespace(
        car_no="ABC-123",
        model="Civic",
        company="Honda",
        onground_km=20000,
        part="oil filter",
        km_limit=200,
        day_limit=15,
        next_changed_km=20150,
        next_changed_date=date(2026, 10, 28),
    )
    today = date(2026, 10, 18)

    result = ExpiryService(None).get_expiry_status(detail, today)

    assert result["status"] == "expiring"
    assert result["remaining_km"] == 150
    assert result["remaining_days"] == 10


@pytest.mark.parametrize(
    ("value", "months", "expected"),
    [
        (date(2024, 1, 31), 6, date(2024, 7, 31)),
        (date(2024, 1, 31), 1, date(2024, 2, 29)),
        (date(2024, 8, 31), 6, date(2025, 2, 28)),
    ],
)
def test_add_months_clamps_to_last_day_of_target_month(value, months, expected):
    assert add_months(value, months) == expected


def test_used_part_cannot_be_deleted_and_deleting_car_removes_maintenance(
    client, db_session
):
    headers = authenticate(client)
    create_car(client, headers)
    update_part(client, headers)
    oil_filter = (
        db_session.query(Part)
        .filter(Part.part == "oil filter", Part.user_id.is_(None))
        .one()
    )

    # A user override is created when a default part is updated.
    settings_response = client.post(
        "/settings/unlock",
        json={"password": ACCOUNT["password"]},
        headers=headers,
    )
    unlocked_headers = {
        **headers,
        "X-Settings-Token": settings_response.json()["settings_token"],
    }
    client.put(
        "/parts/oil filter",
        json={
            "km_life": 4000,
            "month_life": 6,
            "km_limit": 200,
            "day_limit": 15,
        },
        headers=unlocked_headers,
    )
    own_part = (
        db_session.query(Part)
        .filter(Part.part == "oil filter", Part.user_id == ACCOUNT["user_id"])
        .one()
    )
    assert db_session.query(Maintenance).one().part_id == own_part.id
    assert oil_filter.id != own_part.id

    delete_part = client.delete("/parts/oil filter", headers=unlocked_headers)
    assert delete_part.status_code == 409

    delete_car = client.delete("/cars/ABC-123", headers=headers)
    assert delete_car.status_code == 200
    assert db_session.query(Maintenance).count() == 0
