import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SECRET_KEY", "test-only-secret-key-for-auth-tests")
os.environ.setdefault("DATABASE_URL", "sqlite://")

from core.database import Base, get_db
from main import app


PART = {
    "part": "oil filter",
    "km_life": 5000,
    "month_life": 6,
    "km_limit": 200,
    "day_limit": 15,
}
UPDATED_VALUES = {
    "km_life": 7000,
    "month_life": 8,
    "km_limit": 300,
    "day_limit": 20,
}
ACCOUNT = {"user_id": "parts-user", "user_name": "Parts User", "password": "strongpass"}


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


def authenticate(client, user_id: str = "parts-user") -> dict[str, str]:
    client.post("/create_account", json={**ACCOUNT, "user_id": user_id})
    response = client.post(
        "/login_account",
        json={"user_id": user_id, "password": ACCOUNT["password"]},
    )
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    settings_response = client.post(
        "/settings/unlock",
        json={"password": ACCOUNT["password"]},
        headers=headers,
    )
    headers["X-Settings-Token"] = settings_response.json()["settings_token"]
    return headers


def test_part_endpoints_require_authentication(client):
    assert client.post("/parts", json=PART).status_code in (401, 403)
    assert client.get("/parts").status_code in (401, 403)
    assert client.put("/parts/oil filter", json=UPDATED_VALUES).status_code in (401, 403)
    assert client.delete("/parts/oil filter").status_code in (401, 403)


def test_part_changes_require_settings_unlock(client):
    client.post("/create_account", json=ACCOUNT)
    login_response = client.post(
        "/login_account",
        json={"user_id": ACCOUNT["user_id"], "password": ACCOUNT["password"]},
    )
    headers = {
        "Authorization": f"Bearer {login_response.json()['access_token']}"
    }

    assert client.post("/parts", json=PART, headers=headers).status_code == 403
    bad_unlock = client.post(
        "/settings/unlock",
        json={"password": "incorrect-password"},
        headers=headers,
    )
    assert bad_unlock.status_code == 401

    unlock = client.post(
        "/settings/unlock",
        json={"password": ACCOUNT["password"]},
        headers=headers,
    )
    assert unlock.status_code == 200
    headers["X-Settings-Token"] = unlock.json()["settings_token"]
    assert client.post("/parts", json=PART, headers=headers).status_code == 201


def test_add_and_list_parts(client):
    headers = authenticate(client)

    response = client.post("/parts", json=PART, headers=headers)

    assert response.status_code == 201
    assert response.json() == {
        "status": True,
        "message": "Part added successfully.",
    }
    assert client.get("/parts", headers=headers).json() == [
        {
            "id": 1,
            **PART,
            "is_default": False,
        }
    ]


def test_part_name_is_normalized_and_duplicates_are_rejected(client):
    headers = authenticate(client)
    response = client.post("/parts", json={**PART, "part": "  Oil Filter "}, headers=headers)

    assert response.status_code == 201
    assert client.get("/parts", headers=headers).json()[0]["part"] == "oil filter"
    duplicate = client.post("/parts", json=PART, headers=headers)
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Part already exists."


def test_parts_are_isolated_between_accounts(client):
    first_headers = authenticate(client)
    second_headers = authenticate(client, "other-user")
    client.post("/parts", json=PART, headers=first_headers)

    assert client.get("/parts", headers=second_headers).json() == []
    assert client.put(
        "/parts/oil filter", json=UPDATED_VALUES, headers=second_headers
    ).status_code == 404
    assert client.delete("/parts/oil filter", headers=second_headers).status_code == 404


def test_update_part(client):
    headers = authenticate(client)
    client.post("/parts", json=PART, headers=headers)

    response = client.put(
        "/parts/Oil Filter", json=UPDATED_VALUES, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Part updated successfully."
    assert client.get("/parts", headers=headers).json()[0] == {
        "id": 1,
        "part": "oil filter",
        **UPDATED_VALUES,
        "is_default": False,
    }


def test_missing_part_returns_not_found(client):
    headers = authenticate(client)

    assert client.put(
        "/parts/ghost", json=UPDATED_VALUES, headers=headers
    ).status_code == 404
    assert client.delete("/parts/ghost", headers=headers).status_code == 404


def test_delete_part(client):
    headers = authenticate(client)
    client.post("/parts", json=PART, headers=headers)

    response = client.delete("/parts/oil filter", headers=headers)

    assert response.status_code == 200
    assert response.json()["message"] == "Part deleted successfully."
    assert client.get("/parts", headers=headers).json() == []


def test_part_validation_rejects_invalid_values(client):
    headers = authenticate(client)

    assert client.post("/parts", json={**PART, "km_life": 0}, headers=headers).status_code == 422
    assert client.post("/parts", json={**PART, "month_life": -1}, headers=headers).status_code == 422
    assert client.post("/parts", json={**PART, "km_limit": -1}, headers=headers).status_code == 422
    assert client.post("/parts", json={**PART, "part": "  "}, headers=headers).status_code == 422
