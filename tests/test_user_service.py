import pytest
from security import hash_password, verify_password
from services import user_service
from exceptions import DuplicateEmailError, ValidationError


def raise_error(error, func_name, data):
    target_func = getattr(user_service, func_name)

    with pytest.raises(error):
        target_func(data)

def create_test_user():
    data = {
        "email": "    USER@gmail.com  ",
        "password": "  passwordtenchars  ",
    }

    user = user_service.register_user(data)

    # TODO retrieve_user_id_alchemy returns to_dict(), so I can't access stored_user's password_hash
    # seems that even without to_dict(), it still doesn't return password_hash, just this
    # {'id': 1, 'email': 'user@gmail.com'}
    stored_user = user_service.get_user_by_id(user["id"])
    print(stored_user)
    # assert verify_password(data["password"], stored_user.password_hash)
    
    return user
    

def test_user_creation_success():
    user = create_test_user()
    print(user)


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

    create_test_user()
    raise_error(DuplicateEmailError, "register_user", data)

