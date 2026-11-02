import pytest
from exceptions import ResourceNotFoundError, ValidationError
from services import application_service

def raise_error(error, func_name, data):
    target_func = getattr(application_service, func_name)

    with pytest.raises(error):
        target_func(data)

def create_test_application():
    data = {
        "company": "Google",
        "title": "Software Engineer",
        "status": "applied",
        "date_interview": "2026-12-12"
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
    pytest.param([], id="not_dict"),
    ])
def test_create_application_failure(data):
    raise_error(ValidationError, "create_application", data)

def test_get_applications_success():
    data2 = {
        "company": "Bosch",
        "title": "Junior Engineer",
        "status": "interview"
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

    with pytest.raises(ResourceNotFoundError):
        application_service.get_application_by_id(app["id"])


def test_access_nonexistent_id():
    data = {
        "company": "Google",
        "title": "Software Engineer",
        "status": "applied",
        "date_interview": "2026-12-12"
    }

    app = application_service.create_application(data)

    with pytest.raises(ResourceNotFoundError):
        application_service.modify_application(app["id"]+1, {"company": "Bosch"})

    with pytest.raises(ResourceNotFoundError):
        application_service.delete_application(app["id"]+1)