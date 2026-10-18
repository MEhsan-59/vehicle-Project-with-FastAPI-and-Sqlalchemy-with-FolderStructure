import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SECRET_KEY", "test-only-secret-key-for-auth-tests")
os.environ.setdefault("DATABASE_URL", "sqlite://")

from core.database import Base, get_db
from main import app
from models import Account, Vehicle


ACCOUNT = {
    "user_id": "car-user",
    "user_name": "Car User",
    "password": "strongpass",
}
CAR = {
    "car_no": "abc-123",
    "model": "Civic",
    "company": "Honda",
    "onground_km": 20000,
}


@pytest.fixture
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def authenticate(client, user_id: str = "car-user") -> dict[str, str]:
    client.post("/create_account", json={**ACCOUNT, "user_id": user_id})
    response = client.post(
        "/login_account",
        json={"user_id": user_id, "password": ACCOUNT["password"]},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_car_endpoints_require_authentication(client):
    assert client.post("/cars", json=CAR).status_code in (401, 403)
    assert client.delete("/cars/ABC-123").status_code in (401, 403)
    assert client.put(
        "/cars/ABC-123/km", json={"onground_km": 21000}
    ).status_code in (401, 403)
    assert client.get("/history").status_code in (401, 403)


def test_add_car_normalizes_car_number(client):
    headers = authenticate(client)

    response = client.post("/cars", json=CAR, headers=headers)

    assert response.status_code == 201
    assert response.json() == {
        "status": True,
        "message": "Car added successfully.",
    }


def test_duplicate_car_returns_conflict(client):
    headers = authenticate(client)
    client.post("/cars", json=CAR, headers=headers)

    response = client.post("/cars", json=CAR, headers=headers)

    assert response.status_code == 409
    assert response.json()["detail"] == "Car already exists."


@pytest.mark.parametrize(
    "invalid_car",
    [
        {**CAR, "onground_km": -1},
        {**CAR, "car_no": "   "},
        {**CAR, "model": "   "},
        {**CAR, "company": "   "},
    ],
)
def test_add_car_rejects_invalid_input(client, invalid_car):
    headers = authenticate(client)
    assert client.post("/cars", json=invalid_car, headers=headers).status_code == 422


def test_update_car_km(client):
    headers = authenticate(client)
    client.post("/cars", json=CAR, headers=headers)

    response = client.put(
        "/cars/abc-123/km",
        json={"onground_km": 21000},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Onground km updated successfully."


def test_car_km_cannot_decrease_but_can_stay_the_same(client):
    headers = authenticate(client)
    client.post("/cars", json=CAR, headers=headers)

    same = client.put(
        "/cars/ABC-123/km",
        json={"onground_km": 20000},
        headers=headers,
    )
    lower = client.put(
        "/cars/ABC-123/km",
        json={"onground_km": 19000},
        headers=headers,
    )

    assert same.status_code == 200
    assert lower.status_code == 400
    assert "20000" in lower.json()["detail"]


def test_other_users_cannot_update_or_delete_a_car(client):
    owner_headers = authenticate(client, "car-owner")
    other_headers = authenticate(client, "other-user")
    client.post("/cars", json=CAR, headers=owner_headers)

    update = client.put(
        "/cars/ABC-123/km",
        json={"onground_km": 25000},
        headers=other_headers,
    )
    delete = client.delete("/cars/ABC-123", headers=other_headers)

    assert update.status_code == 404
    assert delete.status_code == 404


def test_delete_car_and_delete_missing_car(client):
    headers = authenticate(client)
    client.post("/cars", json=CAR, headers=headers)

    deleted = client.delete("/cars/abc-123", headers=headers)
    missing = client.delete("/cars/ABC-123", headers=headers)

    assert deleted.status_code == 200
    assert deleted.json()["message"] == "Car deleted successfully."
    assert missing.status_code == 404


def test_car_km_update_rejects_negative_value_and_unknown_car(client):
    headers = authenticate(client)

    assert client.put(
        "/cars/ABC-123/km",
        json={"onground_km": -1},
        headers=headers,
    ).status_code == 422
    assert client.put(
        "/cars/UNKNOWN/km",
        json={"onground_km": 100},
        headers=headers,
    ).status_code == 404


def test_car_history_records_create_and_odometer_update(client):
    headers = authenticate(client)
    client.post("/cars", json=CAR, headers=headers)
    client.put(
        "/cars/ABC-123/km",
        json={"onground_km": 21000},
        headers=headers,
    )

    response = client.get("/history", headers=headers)

    assert response.status_code == 200
    history = response.json()
    assert [entry["action_type"] for entry in history] == [
        "km_updated",
        "car_added",
    ]
    assert history[0]["car_no"] == "ABC-123"
    assert history[0]["details"] == "km: 20000 -> 21000"
    assert history[1]["details"] == "Honda Civic, 20000 km"
    assert all(entry["action_timestamp"] for entry in history)


def test_car_history_is_removed_when_car_is_deleted(client):
    headers = authenticate(client)
    client.post("/cars", json=CAR, headers=headers)
    client.put(
        "/cars/ABC-123/km",
        json={"onground_km": 21000},
        headers=headers,
    )
    client.delete("/cars/ABC-123", headers=headers)

    assert client.get("/history", headers=headers).json() == []


def test_car_history_filter_and_account_scope(client):
    owner_headers = authenticate(client, "history-owner")
    other_headers = authenticate(client, "history-other")
    client.post("/cars", json=CAR, headers=owner_headers)
    client.post(
        "/cars",
        json={**CAR, "car_no": "xyz-987"},
        headers=owner_headers,
    )
    client.post(
        "/cars",
        json={**CAR, "car_no": "other-1"},
        headers=other_headers,
    )

    filtered = client.get(
        "/history?filter_type=car&value=abc-123",
        headers=owner_headers,
    )
    other_user_history = client.get(
        "/history",
        headers=other_headers,
    )
    blank_filter = client.get(
        "/history?filter_type=car&value=%20",
        headers=owner_headers,
    )

    assert filtered.status_code == 200
    assert [entry["car_no"] for entry in filtered.json()] == ["ABC-123"]
    assert [entry["car_no"] for entry in other_user_history.json()] == [
        "OTHER-1"
    ]
    assert blank_filter.status_code == 400


def test_car_history_logs_only_successful_changes(client):
    headers = authenticate(client)

    missing_car_update = client.put(
        "/cars/ABC-123/km",
        json={"onground_km": 21000},
        headers=headers,
    )
    client.post("/cars", json=CAR, headers=headers)
    same_odometer_update = client.put(
        "/cars/ABC-123/km",
        json={"onground_km": 20000},
        headers=headers,
    )

    assert missing_car_update.status_code == 404
    assert same_odometer_update.status_code == 200
    history = client.get("/history", headers=headers).json()
    assert [entry["action_type"] for entry in history] == [
        "km_updated",
        "car_added",
    ]


def test_created_at_is_generated_when_vehicle_is_inserted():
    test_engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=test_engine)
    with Session(test_engine) as db:
        db.add(
            Account(
                user_id="created-at-user",
                user_name="Created At User",
                password="hashed-password",
            )
        )
        db.flush()
        vehicle = Vehicle(
            car_no="CREATED-1",
            model="Model",
            company="Company",
            active_user="created-at-user",
        )
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)

        assert vehicle.created_at is not None
    test_engine.dispose()
