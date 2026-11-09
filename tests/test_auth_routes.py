import pytest
from security import hash_password, verify_password

NON_EXISTENT_ID = 9999999999

@pytest.fixture
def existing_user(client):
    """Creates a user for the current test; the database transaction is rolled back during teardown."""
    password = "     TEST PASSWORD123"
    password_hash = hash_password(password)

    payload = {
        "email": "test@gmail.com", 
        "password": password_hash
    }
    response = client.post("/auth", json=payload)
    print(response.json)

    assert response.status_code == 201
    assert verify_password(password_hash, password) == True

    return response.json

def test_get_all_users_success(client, existing_user):
    password = "     TEST PASSWORD123"
    password_hash = hash_password(password)

    payload2 = {
        "email": "test2@gmail.com",
        "password": password_hash
    }

    create_response = client.post("/auth", json=payload2)

    assert create_response.status_code == 201

    response = client.get("/auth")

    assert response.status_code == 200
    body = response.json

    assert len(body) == 2

    assert existing_user in body

# no user is created since existing_user isn't provided as an argument
def test_get_all_users_empty(client):
    response = client.get("/auth")

    assert response.status_code == 200
    assert isinstance(response.json, list)
    assert response.json == []

def test_get_user_success(client, existing_user):
    user_id = existing_user["id"]
    response = client.get(f"/auth/{user_id}")

    assert response.status_code == 200
    assert response.json == existing_user

def test_get_nonexistent_user(client):
    nonexistent_app_id = NON_EXISTENT_ID
    response = client.get(f"/auth/{nonexistent_app_id}")

    assert response.status_code == 404
    assert response.json["error"] == "MISSING_ERROR"
    assert "User not found." in response.json["details"]

# TODO further sad path testing