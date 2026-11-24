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

# def create_test_user(email="    USER@gmail.com  "):
#     return register_user({
#         "email": email,
#         "password": "  passwordtenchars  ",
#     })

# def create_test_application(user_id: int):
#     data = {
#         "company": "Google",
#         "title": "Software Engineer",
#         "status": "applied",
#         "date_interview": "2026-12-12",
#     }

#     return application_service.create_application(data, user_id)

# CREATE

def test_create_valid_application_success(setup_application_service):
    new_test_application, _ = setup_application_service()

    assert new_test_application["id"] is not None
    assert new_test_application["company"] == "Google"
    assert isinstance(new_test_application, dict)

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
    new_test_application2 = application_service.create_application({"company": "Bosch",
                                                                "title": "Junior Engineer",
                                                                "status": "interview"}, 
                                                                new_test_user["id"])
    
    get_all_apps = application_service.get_applications(new_test_user["id"], status=None)
    get_app_1 = application_service.get_application_by_id(new_test_application["id"], new_test_user["id"])
    get_app_2 = application_service.get_application_by_id(new_test_application2["id"], new_test_user["id"])

    assert isinstance(get_all_apps["items"], list)
    assert len(get_all_apps["items"]) == 2
    assert get_app_1["company"] == "Google"
    assert get_app_1["title"] == "Software Engineer"
    assert get_app_1["status"] == "applied"

    assert get_app_2["company"] == "Bosch"
    assert get_app_2["title"] == "Junior Engineer"
    assert get_app_2["status"] == "interview"

def test_get_pagination_filtering_success(setup_application_service):
    _, new_test_user = setup_application_service()

    app_2 = {
        "company": "Bosch",
        "title": "Junior Engineer",
        "status": "interview",
    }

    # create two more applications for same user
    new_test_application_2 = application_service.create_application(app_2, new_test_user["id"])
    application_service.create_application(app_2, new_test_user["id"])

    # default page (1) and limit (3)
    get_all_apps_1_3 = application_service.get_applications(new_test_user["id"], status=None)

    assert len(get_all_apps_1_3["items"]) == 3
    assert get_all_apps_1_3["total_applications"] == 3
    assert get_all_apps_1_3["per_page"] == 3
    assert get_all_apps_1_3["total_pages"] == 1
    assert get_all_apps_1_3["has_next"] == False
    assert get_all_apps_1_3["has_prev"] == False

    # page (2) and limit (2)
    get_all_apps_2_3 = application_service.get_applications(new_test_user["id"], status=None, page=2, limit=2)

    assert len(get_all_apps_2_3["items"]) == 1
    assert get_all_apps_2_3["total_applications"] == 3
    assert get_all_apps_2_3["per_page"] == 2
    assert get_all_apps_2_3["total_pages"] == 2
    assert get_all_apps_2_3["has_next"] == False
    assert get_all_apps_2_3["has_prev"] == True

    # page (1), limit (2) and status = "interview"
    get_all_apps_2_3_int = application_service.get_applications(new_test_user["id"], new_test_application_2["status"], page=1, limit=2)

    assert len(get_all_apps_2_3_int["items"]) == 2
    assert get_all_apps_2_3_int["total_applications"] == 2
    assert get_all_apps_2_3_int["per_page"] == 2
    assert get_all_apps_2_3_int["total_pages"] == 1
    assert get_all_apps_2_3_int["has_next"] == False
    assert get_all_apps_2_3_int["has_prev"] == False
    assert get_all_apps_2_3_int["filter_by"] == new_test_application_2["status"]

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
    protected_apps_1 = application_service.get_applications(target_user_id, status=None)
    assert len(protected_apps_1["items"]) == length

    # user 2 doesn't see user 1's applications
    protected_apps_2 = application_service.get_applications(new_test_user2["id"], status=None)
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