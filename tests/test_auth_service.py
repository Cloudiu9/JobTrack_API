from datetime import timedelta

from flask_jwt_extended import decode_token
import pytest
from app import app
from models.user import User
from security import verify_password
from services import auth_service
from exceptions import AuthenticationError, DuplicateEmailError, ValidationError
from sqlalchemy import select


def raise_error(error, func_name, data):
    target_func = getattr(auth_service, func_name)

    with pytest.raises(error):
        target_func(data)

def register_test_user():
    data = {
        "email": "    USER@gmail.com  ",
        "password": "  passwordtenchars  ",
    }

    user = auth_service.register_user(data)

    with auth_service.SessionFactory() as session:
        stored_user = session.scalar(
            select(User).where(User.email == "user@gmail.com")
        )

    assert stored_user is not None
    assert stored_user.password_hash != data["password"]
    assert verify_password(stored_user.password_hash, data["password"] )
    
    return user
    

def test_user_creation_success():
    user = register_test_user()


    assert user["id"] is not None
    assert user["email"] == "user@gmail.com"

    assert isinstance(user, dict)

@pytest.mark.parametrize("data",
    [
    pytest.param({
        "email": "Google@gmail.com",
        "password": "shortpass"
    }, id="invalid_password_length"),
    pytest.param({
        "email": "Google@gmail.com",
        # "password": "Software Engineer"
    }, id="missing_field"),
        pytest.param({
        "email": None,
        "password": "Software Engineer"
    }, id="null_email"),
    pytest.param({
        "email": 123,
        "password": "Software Engineer"
    }, id="invalid_data"),
    pytest.param({
        "email": "Google@gmail.com",
        "password": "Software Engineer",
        "banana": "Google@gmail.com"
    }, id="invalid_field"),
    pytest.param({
        "email": "    ",
        "password": "Software Engineer"
    }, id="only_whitespace"),
    pytest.param([], id="not_dict"),
    ])
def test_register_user_validation_failure(data):
    raise_error(ValidationError, "register_user", data)

def test_user_duplication_failure():
    data = {
        "email": "    USER@gmail.com  ",
        "password": "  passwordtenchars  ",
    }

    register_test_user()

    # create a second user with the same email
    raise_error(DuplicateEmailError, "register_user", data)

    all_users = auth_service.get_all_users()

    assert len(all_users) == 1

def test_empty_database():
    all_users = auth_service.get_all_users()

    assert isinstance(all_users, list)
    assert len(all_users) == 0

def test_user_login_success():
    user = register_test_user()

    user_credentials = {
        "email": "    USER@gmail.com  ",
        "password": "  passwordtenchars  ",
    }

    with app.app_context():
        logged_user_jwt = auth_service.login_user(user_credentials)
        decoded_jwt = decode_token(logged_user_jwt)

    assert logged_user_jwt is not None
    assert decoded_jwt["sub"] == str(user["id"])

    # 15 minutes
    valid_time = decoded_jwt["exp"] - decoded_jwt["iat"]
    assert valid_time == 15*60

@pytest.mark.parametrize("invalid_credentials, error", [
    pytest.param({

    },
    ValidationError,
    id="empty_dict"),
    pytest.param({
        # "email": "    INVALID@gmail.com  ",
        "password": "  passwordtenchars  "
    },
    ValidationError,
    id="missing_email"),
    pytest.param({
        "email": "    INVALID@gmail.com  ",
        # "password": "  passwordtenchars  "
    },
    ValidationError,
    id="missing_password"),
    pytest.param({
        "email": "    USER@gmail.com  ",
        "password": "  INVALID_PASSWORD  "
    },
    AuthenticationError,
    id="incorrect_password"),
    pytest.param({
        "email": 123,
        "password": "  INVALID_PASSWORD  "
    },
    ValidationError,
    id="invalid_email"),
    pytest.param({
        "email": "    USER@gmail.com  ",
        "password": 123
    },
    ValidationError,
    id="invalid_password"),
    pytest.param({
        "email": "    USER@gmail.com  ",
        "password": "  INVALID_PASSWORD  ",
        "INVALID_FIELD": "INVALID_VALUE"
    },
    ValidationError,
    id="invalid_field"),
    pytest.param({
        "email": "    USER@gmail.com  ",
        "password": "short"
    },
    ValidationError,
    id="short_pass"),
])
def test_user_login_failure(invalid_credentials, error):
    register_test_user()

    with app.app_context():
        raise_error(error, "login_user", invalid_credentials)