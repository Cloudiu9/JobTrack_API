import pytest
from exceptions import ResourceNotFoundError, ValidationError
from services import application_service
from services.auth_service import register_user

def raise_error(error, func_name, *args):
    """
    Example use case: 
        raise_error(ResourceNotFoundError, "modify_application", app["id"], modified_data, user2["id"])
    """
    target_func = getattr(application_service, func_name)

    with pytest.raises(error):
        target_func(*args)

# CREATE

def test_create_valid_application_success(setup_application_service):
    new_test_application, new_test_user = setup_application_service()
    new_test_application2 = application_service.create_application(
    {
    "company": "Bosch",
    "title": "Junior Engineer",
    "status": "rejected"
    }, 
    new_test_user["id"])

    assert new_test_application["id"] is not None
    assert new_test_application["company"] == "Google"
    assert isinstance(new_test_application, dict)

    assert new_test_application2["id"] is not None
    assert new_test_application2["company"] == "Bosch"
    assert new_test_application2["status"] == "rejected" 

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

# GET

def test_get_applications_success(setup_application_service):
    new_test_application, new_test_user = setup_application_service()
    new_test_application2 = application_service.create_application(
    {
    "company": "Bosch",
    "title": "Junior Engineer",
    "status": "offer"
    }, 
    new_test_user["id"])
    
    get_all_apps = application_service.get_applications(new_test_user["id"], status=None, order=None)
    get_app_1 = application_service.get_application_by_id(new_test_application["id"], new_test_user["id"])
    get_app_2 = application_service.get_application_by_id(new_test_application2["id"], new_test_user["id"])

    assert isinstance(get_all_apps["items"], list)
    assert len(get_all_apps["items"]) == 2
    assert get_app_1["company"] == "Google"
    assert get_app_1["title"] == "Software Engineer"
    assert get_app_1["status"] == "applied"

    assert get_app_2["company"] == "Bosch"
    assert get_app_2["title"] == "Junior Engineer"
    assert get_app_2["status"] == "offer"

@pytest.mark.parametrize("status, order, page, limit, companies, envelope",[
    pytest.param(None, "desc", 1, 3, ["Google", "Bosch"], (
        3, 3, 3, 1, False, False
    ), id="default_page_limit"),
    pytest.param(None, "desc", 2, 2, ["Bosch"], (
        1, 3, 2, 2, False, True
    ), id="page_2_limit_2"),
    pytest.param("rejected", "desc", 1, 2, ["Bosch", "Bosch"], (
        2, 2, 2, 1, False, False
    ), id="page_1_limit_2_rejected"),
    pytest.param(None, "asc", 1, 3, ["Bosch", "Bosch", "Google"], (
        3, 3, 3, 1, False, False
    ), id="page_1_limit_3_asc"),
])
def test_get_query_params_success(setup_application_service, status, order, page, limit, companies, envelope):
    _, new_test_user = setup_application_service()

    app_2 = {
        "company": "Bosch",
        "title": "Junior Engineer",
        "status": "rejected",
        "date_applied": "2010-10-10" # oldest, assuming setup application's date_applied is "today"
    }

    # create two more applications for same user
    application_service.create_application(app_2, new_test_user["id"])
    application_service.create_application(app_2, new_test_user["id"])

    get_all_apps = application_service.get_applications(new_test_user["id"], status=status, order=order, page=page, limit=limit)
    print(get_all_apps)

    assert len(get_all_apps["items"]) == envelope[0]
    for item in get_all_apps["items"]:
        assert item["company"] in companies
    assert get_all_apps["total_applications"] == envelope[1]
    assert get_all_apps["per_page"] == envelope[2]
    assert get_all_apps["total_pages"] == envelope[3]
    assert get_all_apps["has_next"] == envelope[4]
    assert get_all_apps["has_prev"] == envelope[5]
    assert get_all_apps["filter_by"] == status
    assert get_all_apps["order"] == order

@pytest.mark.parametrize("target_user_id, length",
    [
        pytest.param(1, 2, id="success"),
        pytest.param(9999, 0, id="failure")
    ])
def test_get_protected_applications(target_user_id, length, setup_application_service):
    _, new_test_user = setup_application_service()
    _, new_test_user2 = setup_application_service(email="user2@gmail.com")

    app_2 = {
        "company": "Bosch",
        "title": "Junior Engineer",
        "status": "interview",
    }

    # create 2nd application belonging to the first user
    application_service.create_application(app_2, new_test_user["id"])

    # create 2nd application belonging to second user
    application_service.create_application(app_2, new_test_user2["id"])

    # service function doesn't require the user to be logged in, only the route does
    # logged_user_jwt = login_user(user_credentials)

    # for user privacy, to_dict excludes user_id
    protected_apps_1 = application_service.get_applications(target_user_id, status=None, order=None)
    assert len(protected_apps_1["items"]) == length

    # user 2 doesn't see user 1's applications
    protected_apps_2 = application_service.get_applications(new_test_user2["id"], status=None, order=None)
    assert protected_apps_2["items"][0]["id"] == 2
    assert protected_apps_2["items"][0]["company"] == "Google"
    assert protected_apps_2["items"][0]["title"] == "Software Engineer"

# MODIFY

def test_modify_application_success(setup_application_service):
    new_testing_application, new_test_user = setup_application_service()

    modified_data = {
    "title": "Junior Engineer",
    "date_applied": "2026-10-10",
    "date_interview": None
    }
    
    application_service.modify_application(new_testing_application["id"], modified_data, new_test_user["id"])

    modified_app = application_service.get_application_by_id(new_testing_application["id"], new_test_user["id"])

    assert modified_app["title"] == "Junior Engineer"
    assert modified_app["date_applied"] == "2026-10-10"
    assert modified_app["date_interview"] is None
    assert modified_app["company"] == "Google"
    assert modified_app["status"] == "applied"

def test_modify_applications_other_user(setup_application_service):
    new_testing_application, new_test_user = setup_application_service()
    _, new_test_user2 = setup_application_service(email="user2@gmail.com")

    modified_data = {
    "title": "Junior Engineer",
    "date_applied": "2026-10-10",
    "date_interview": None
    }
    
    raise_error(ResourceNotFoundError, "modify_application", new_testing_application["id"], modified_data, new_test_user2["id"])

# DELETE

def test_delete_application_success(setup_application_service):
    new_testing_application, new_test_user = setup_application_service()

    assert new_testing_application["title"] == "Software Engineer"

    get_app_1 = application_service.get_application_by_id(new_testing_application["id"], new_test_user["id"])

    assert get_app_1["id"] == new_testing_application["id"]

    application_service.delete_application(new_testing_application["id"], new_test_user["id"])

    raise_error(ResourceNotFoundError, "get_application_by_id", new_testing_application["id"], new_test_user["id"])


def test_access_nonexistent_id(setup_application_service):
    new_testing_application, new_test_user = setup_application_service()

    raise_error(ResourceNotFoundError, "modify_application", new_testing_application["id"]+1, {"company": "Bosch"}, new_test_user["id"])
    raise_error(ResourceNotFoundError, "delete_application", new_testing_application["id"]+1, new_test_user["id"])