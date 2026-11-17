import pytest
from exceptions import AuthenticationError, ResourceNotFoundError, ValidationError
from services import application_service
from services.auth_service import register_user

def raise_error(error, func_name, *args):
    target_func = getattr(application_service, func_name)

    with pytest.raises(error):
        target_func(*args)

def create_test_application():
    data = {
        "company": "Google",
        "title": "Software Engineer",
        "status": "applied",
        "date_interview": "2026-12-12",
        "user_id": "1"
    }
    app = application_service.create_application(data)

    return app

def test_create_valid_application_success():
    result = create_test_application()

    assert result["id"] is not None
    assert result["company"] == "Google"
    assert isinstance(result, dict)

@pytest.mark.parametrize("data",
    [
    pytest.param({
        "company": "Google",
        "title": "Software Engineer",
        "status": "WRONG_STATUS",
        "user_id": "1"
    }, id="invalid_status"),
    pytest.param({
        "company": "Google",
        # "title": "Software Engineer",
        "status": "interview",
        "user_id": "1"
    }, id="missing_field"),
        pytest.param({
        "company": "Google",
        "title": None,
        "status": "interview",
        "user_id": "1"
    }, id="null_title"),
    pytest.param({
        "company": 123,
        "title": "Software Engineer",
        "status": "applied",
        "user_id": "1"
    }, id="invalid_data"),
    pytest.param({
        "company": "   Google",
        "title": "Software Engineer",
        "status": "applied",
        "user_id": "1",
        "banana": "Google"
    }, id="invalid_field"),
    pytest.param({
        "company": "Bosch",
        "title": "Software Engineer",
        "status": "interview",
        "date_applied": None,
        "user_id": "1"
    }, id="date_none"),
    pytest.param({
        "company": "     ",
        "title": "Software Engineer",
        "status": "interview",
        "user_id": "1",
    }, id="only_whitespace"),
    pytest.param({
        "company": "Google",
        "title": "Software Engineer",
        "status": "interview",
        # "user_id": "1",
    }, id="missing_user_id"),
    pytest.param([], id="not_dict"),
    ])
def test_create_application_failure(data):
    raise_error(ValidationError, "create_application", data)

def test_get_applications_success():
    data2 = {
        "company": "Bosch",
        "title": "Junior Engineer",
        "status": "interview",
        "user_id": "1"
    }

    app1 = create_test_application()
    app2 = application_service.create_application(data2)

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

@pytest.mark.parametrize("user_id, length",
    [
        pytest.param(1, 2, id="success"),
        pytest.param(9999, 0, id="failure")
    ])
def test_get_protected_applications(user_id, length):
    app_2 = {
        "company": "Bosch",
        "title": "Junior Engineer",
        "status": "interview",
        "user_id": "1"
    }

    app1 = create_test_application()
    app2 = application_service.create_application(app_2)

    user_credentials = {
        "email": "    USER@gmail.com  ",
        "password": "  passwordtenchars  ",
    }

    user = register_user(user_credentials)

    # service function doesn't require the user to be logged in, only the route does
    # logged_user_jwt = login_user(user_credentials)

    # for user privacy, to_dict excludes user_id
    protected_apps = application_service.get_applications_protected(user_id)
    assert len(protected_apps) == length

# should a user be able to change ownership of user_id from applications? (admin user with privileges?)
def test_modify_application_success():
    modified_data = {
    "title": "Junior Engineer",
    "date_applied": "2026-10-10",
    "date_interview": None
    }
    
    app = create_test_application()

    application_service.modify_application(app["id"], modified_data)

    modified_app = application_service.get_application_by_id(app["id"])

    assert modified_app["title"] == "Junior Engineer"
    assert modified_app["date_applied"] == "2026-10-10"
    assert modified_app["date_interview"] is None
    assert modified_app["company"] == "Google"
    assert modified_app["status"] == "applied"

def test_delete_application_success():
    app = create_test_application()

    assert app["title"] == "Software Engineer"

    get_app_1 = application_service.get_application_by_id(app["id"])

    assert get_app_1["id"] == app["id"]

    application_service.delete_application(app["id"])

    raise_error(ResourceNotFoundError, "get_application_by_id", app["id"])


def test_access_nonexistent_id():
    data = {
        "company": "Google",
        "title": "Software Engineer",
        "status": "applied",
        "date_interview": "2026-12-12",
        "user_id": "1"
    }

    app = application_service.create_application(data)

    raise_error(ResourceNotFoundError, "modify_application", app["id"]+1, {"company": "Bosch"})
    raise_error(ResourceNotFoundError, "delete_application", app["id"]+1)