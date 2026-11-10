import pytest
from models.user import User
from sqlalchemy import select
from services import auth_service
from security import verify_password

NON_EXISTENT_ID = 999999

@pytest.fixture
def existing_user(client):
    """Creates a valid user for the current test; the database transaction is rolled back during teardown. Also tests password whitespace preservation."""
    payload = {
        "email": "test@gmail.com", 
        "password": "     TEST PASSWORD123"
    }
    response = client.post("/auth", json=payload)

    with auth_service.SessionFactory() as session:
        stored_user = session.scalar(
            select(User).where(User.email == "test@gmail.com")
        )

    # user_data = {k:v for k, v in stored_user.__dict__.items() if k != '_sa_instance_state'}
    # print(user_data)

    assert stored_user is not None
    assert response.status_code == 201
    assert verify_password(stored_user.password_hash, "     TEST PASSWORD123")

    return response.json

def test_get_all_users_success(client, existing_user):
    payload2 = {
        "email": "test2@gmail.com",
        "password": "     TEST PASSWORD123"
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

    assert "password" not in response.json
    assert "password_hash" not in response.json

    for value in response.json.values():
        assert value != "     TEST PASSWORD123"

def test_get_nonexistent_user(client):
    nonexistent_app_id = NON_EXISTENT_ID
    response = client.get(f"/auth/{nonexistent_app_id}")

    assert response.status_code == 404
    assert response.json["error"] == "MISSING_ERROR"
    assert "User not found." in response.json["details"]

def test_post_duplicate_email(client, existing_user):
    payload = {
        "email": "test@gmail.com",
        "password": "   TEST1234567"
    }

    response = client.post("/auth", json=payload)
    # print(response.json)

    assert response.status_code == 409
    assert response.json["error"] == "DUPLICATE_EMAIL_ERROR"
    assert response.json["details"] == "This email is already registered."

@pytest.mark.parametrize("payload",
        [
        pytest.param({
            # "email": "test@gmail.com",
            "password": "   TEST1234567"
        }, id="missing_email"),
        pytest.param({
            "email": "test@gmail.com",
            # "password": "   TEST1234567"
        }, id="missing_password"),
        pytest.param({
            "email": "test@gmail.com",
            "password": 12345
        }, id="invalid_json"),
        pytest.param({
            "email": " ",
            "password": "   TEST1234567"
        }, id="empty_email"),  
        pytest.param({
            "email": "test@gmail.com",
            "password": "SHORTPASS"
        }, id="insufficient_password"),  
        pytest.param({
            "email": "test@gmail.com",
            "password": "   TEST1234567",
            "UNKNOWN_FIELD": "UNKNOWN"
        }, id="unknown_field")
        ])
def test_post_failure(client, payload):
    response = client.post("/auth", json=payload)

    assert response.status_code == 400
    assert response.json["error"] == "VALIDATION_ERROR"

# TODO Test user login