from flask_jwt_extended import get_jwt_identity
import pytest
from app import app
from exceptions import AuthenticationError, ResourceNotFoundError, ValidationError
from services import application_service
from services.auth_service import register_user

def raise_error(error, func_name, *args):
    target_func = getattr(application_service, func_name)

    with pytest.raises(error):
        target_func(*args)

def create_test_user(email="    USER@gmail.com  "):
    return register_user({
        "email": email,
        "password": "  passwordtenchars  ",
    })

def create_test_application(user_id: int):
    data = {
        "company": "Google",
        "title": "Software Engineer",
        "status": "applied",
        "date_interview": "2026-12-12",
    }

    return application_service.create_application(data, user_id)

def test_create_valid_application_success():
    user = create_test_user()
    result = create_test_application(user["id"])
    
    assert result["id"] is not None
    assert result["company"] == "Google"
    assert isinstance(result, dict)

@pytest.mark.parametrize("data",
    [
    pytest.param({
        "company": "Google",
        "title": "Software Engineer",
        "status": "WRONG_STATUS"
    }, id="invalid_status"),
    pytest.param({
        "company": "Google",
        # "title": "Software Engineer",
        "status": "interview"
    }, id="missing_field"),
        pytest.param({
        "company": "Google",
        "title": None,
        "status": "interview"
    }, id="null_title"),
    pytest.param({
        "company": 123,
        "title": "Software Engineer",
        "status": "applied"
    }, id="invalid_data"),
    pytest.param({
        "company": "   Google",
        "title": "Software Engineer",
        "status": "applied",
        "banana": "Google"
    }, id="invalid_field"),
    pytest.param({
        "company": "Bosch",
        "title": "Software Engineer",
        "status": "interview",
        "date_applied": None
    }, id="date_none"),
    pytest.param({
        "company": "     ",
        "title": "Software Engineer",
        "status": "interview",
    }, id="only_whitespace"),
    pytest.param({
        "company": "Google",
        "title": "Software Engineer",
        "status": "interview",
        "user_id": "1"
    }, id="unexpected_user_id_in_payload"),
    pytest.param([], id="not_dict"),
    ])
def test_create_application_failure(data):
    raise_error(ValidationError, "create_application", data, 1)

def test_get_applications_success():
    user = create_test_user()

    data2 = {
        "company": "Bosch",
        "title": "Junior Engineer",
        "status": "interview",
    }

    app1 = create_test_application(user["id"])
    app2 = application_service.create_application(data2, user["id"])

    get_all_apps = application_service.get_applications()
    get_app_1 = application_service.get_application_by_id(app1["id"])
    get_app_2 = application_service.get_application_by_id(app2["id"])

    assert isinstance(get_all_apps, list)
    assert len(get_all_apps) == 2
    assert get_app_1["company"] == "Google"
    assert get_app_1["title"] == "Software Engineer"
    assert get_app_1["status"] == "applied"

    assert get_app_2["company"] == "Bosch"
    assert get_app_2["title"] == "Junior Engineer"
    assert get_app_2["status"] == "interview"

@pytest.mark.parametrize("target_user_id, length",
    [
        pytest.param(1, 2, id="success"),
        pytest.param(9999, 0, id="failure")
    ])
def test_get_protected_applications(target_user_id, length):
    user = create_test_user()

    app_2 = {
        "company": "Bosch",
        "title": "Junior Engineer",
        "status": "interview",
    }

    # create 2 applications belonging to the same user
    create_test_application(user["id"])
    application_service.create_application(app_2, user["id"])

    # service function doesn't require the user to be logged in, only the route does
    # logged_user_jwt = login_user(user_credentials)

    # for user privacy, to_dict excludes user_id
    protected_apps = application_service.get_applications_protected(target_user_id)
    assert len(protected_apps) == length

def test_modify_application_success():
    user = create_test_user()

    modified_data = {
    "title": "Junior Engineer",
    "date_applied": "2026-10-10",
    "date_interview": None
    }
    
    app = create_test_application(user["id"])

    application_service.modify_application(app["id"], modified_data, user["id"])

    modified_app = application_service.get_application_by_id(app["id"])

    assert modified_app["title"] == "Junior Engineer"
    assert modified_app["date_applied"] == "2026-10-10"
    assert modified_app["date_interview"] is None
    assert modified_app["company"] == "Google"
    assert modified_app["status"] == "applied"

def test_delete_application_success():
    user = create_test_user()
    app = create_test_application(user["id"])

    assert app["title"] == "Software Engineer"

    get_app_1 = application_service.get_application_by_id(app["id"])

    assert get_app_1["id"] == app["id"]

    application_service.delete_application(app["id"], user["id"])

    raise_error(ResourceNotFoundError, "get_application_by_id", app["id"])


def test_access_nonexistent_id():
    user = create_test_user()
    
    data = {
        "company": "Google",
        "title": "Software Engineer",
        "status": "applied",
        "date_interview": "2026-12-12",
    }

    app = application_service.create_application(data, user["id"])

    raise_error(ResourceNotFoundError, "modify_application", app["id"]+1, {"company": "Bosch"}, user["id"])
    raise_error(ResourceNotFoundError, "delete_application", app["id"]+1, user["id"])