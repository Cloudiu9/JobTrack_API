from datetime import datetime, timedelta
from freezegun import freeze_time
import pytest

NON_EXISTENT_ID = 999999

def test_get_all_users_success(client, existing_user):
    payload2 = {
        "email": "test2@gmail.com",
        "password": "     TEST PASSWORD123"
    }

    create_response = client.post("/auth/register", json=payload2)

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

def test_post_register_duplicate_email(client, existing_user):
    payload = {
        "email": "test@gmail.com",
        "password": "   TEST1234567"
    }

    response = client.post("/auth/register", json=payload)
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
def test_post_register_failure(client, payload):
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 400
    assert response.json["error"] == "VALIDATION_ERROR"

def test_post_login_success(client, existing_user):
    user_data = {
        "email": "test@gmail.com", 
        "password": "     TEST PASSWORD123"
    }

    response = client.post("/auth/login", json=user_data)

    assert response.status_code == 200
    assert response.json["access_token"] is not None

@pytest.mark.parametrize("payload, error_code, error",
    [
    pytest.param({
        "email": "test@gmail.com",
        "password": "WRONG_PASSWORD"
    }, 
    401,
    "401 UNAUTHORIZED",
    id="incorrect_pass"),
    pytest.param({
        "email": "NEW_EMAIL@gmail.com",
        "password": "WRONG_PASSWORD"
    }, 
    401,
    "401 UNAUTHORIZED", 
    id="unregistered_email"),
    pytest.param({
        # "email": "test@gmail.com",
        "password": "WRONG_PASSWORD"
    },
    400,
    "400 BAD REQUEST", 
    id="missing_email"),
    pytest.param({
        "email": "test@gmail.com"
        # "password": "WRONG_PASSWORD"
    }, 
    400,
    "400 BAD REQUEST", 
    id="missing_pass"),
    pytest.param({
        "email": "test@gmail.com",
        "password": 12345
    }, 
    400,
    "400 BAD REQUEST", 
    id="invalid_type"),
    pytest.param([{
        "email": "test@gmail.com",
        "password": "WRONG_PASSWORD"
    }], 
    400,
    "400 BAD REQUEST", 
    id="invalid_body"),
    pytest.param({
        "email": "test@gmail.com",
        "password": "WRONG_PASSWORD",
        "NEW_FIELD": "NEW_DATA"
    }, 
    400,
    "400 BAD REQUEST", 
    id="unknown_field")
    ])
def test_post_login_failure(client, payload, error_code, error):
    response = client.post("/auth/login", json=payload)
    print(response.json)

    assert response.status_code == error_code
    assert response.status == error

def test_post_secure_success(client, existing_user, auth_headers):
    response = client.get("/auth/secure", headers=auth_headers)

    assert response.status_code == 200
    assert response.json["user_id"] == existing_user["id"]

def test_post_secure_missing_jwt(client):
    response = client.get("/auth/secure", headers={})

    assert response.status_code == 401

def test_post_secure_invalid_jwt(client):
    jwt_auth = {
        "Authorization" : f"Bearer INVALID_JWT"
    }

    response = client.get("/auth/secure", headers=jwt_auth)

    # an altered JWT throws a [422 UNPROCESSABLE ENTITY] instead of a regular 401
    assert response.status_code == 422


@pytest.mark.parametrize("time, status_code, json",
    [
    pytest.param(
        16,
        401,
        {"msg": "Token has expired"}, 
        id="expired_jwt"), 
     pytest.param(
        14,
        200,
        {"user_id": 1}, id="valid_jwt")
    ])
def test_post_secure_token_expiration(client, existing_user, time, status_code, json):
    start_time = datetime(2026, 11, 13, 12, 0, 0)
    with freeze_time(start_time):
        login_res = client.post(
            "/auth/login",
            json={"email": existing_user["email"], "password": "     TEST PASSWORD123"}
        )

        token = login_res.json["access_token"]

    # By default, expires in 15 minutes
    with freeze_time(start_time + timedelta(minutes=time)):
        response = client.get("/auth/secure", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == status_code
    assert response.get_json() == json