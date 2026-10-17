import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SECRET_KEY", "test-only-secret-key-for-auth-tests")

from core.database import Base, get_db
from main import app


@pytest.fixture
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
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


def test_create_account_success(client):
    response = client.post(
        "/create_account",
        json={"user_id": "user123", "user_name": "John", "password": "strongpass"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": True, "message": "Account Successfully created."}


def test_create_duplicate_account_returns_conflict(client):
    payload = {"user_id": "user123", "user_name": "John", "password": "strongpass"}
    client.post("/create_account", json=payload)

    response = client.post("/create_account", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "Account already exists."


def test_login_returns_bearer_access_token(client):
    client.post(
        "/create_account",
        json={"user_id": "user123", "user_name": "John", "password": "strongpass"},
    )

    response = client.post(
        "/login_account",
        json={"user_id": "user123", "password": "strongpass"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]
    assert "token" not in response.json()


def test_login_with_wrong_password_returns_unauthorized(client):
    client.post(
        "/create_account",
        json={"user_id": "user123", "user_name": "John", "password": "strongpass"},
    )

    response = client.post(
        "/login_account",
        json={"user_id": "user123", "password": "wrongpass"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid user_id or password"


def test_me_returns_authenticated_account(client):
    client.post(
        "/create_account",
        json={"user_id": "user123", "user_name": "John", "password": "strongpass"},
    )
    login_response = client.post(
        "/login_account",
        json={"user_id": "user123", "password": "strongpass"},
    )

    response = client.get(
        "/me",
        headers={"Authorization": f"Bearer {login_response.json()['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome, John!",
        "user_id": "user123",
        "name": "John",
    }


def test_create_account_rejects_short_password(client):
    response = client.post(
        "/create_account",
        json={"user_id": "user123", "user_name": "John", "password": "short"},
    )

    assert response.status_code == 422
