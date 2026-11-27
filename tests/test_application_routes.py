import pytest
from app import app as flask_app
from models.application import Application
from services import application_service

NON_EXISTENT_ID = 999999

# same as db_alchemy.update_id_alchemy, but flushes() after change and raises error
def mocked_update_id_alchemy(session, app_id, data, user_id):
    application = session.get(Application, app_id)

    if application is None or application.user_id != user_id:
        return None

    application.title = data["title"]

    session.flush()
    raise RuntimeError("Simulated failure after flush")

@pytest.fixture
def existing_application(client, auth_headers):
    """Creates an application for the current test; the database transaction is rolled back during teardown."""
    payload = {
        "company": "Bosch", 
        "title": "Junior Engineer", 
        "status" : "applied", 
        "date_applied": '2026-10-26'
    }
    response = client.post("/applications", json=payload, headers=auth_headers())

    assert response.status_code == 201
    return response.json

# GET

def test_get_all_applications_success(client, existing_application, auth_headers):
    payload = {
        "company": "Kaufland",
        "title": "Senior Engineer",
        "status" : "interview",
        "date_applied": '2026-10-29'
    }

    create_response = client.post("/applications", json=payload, headers=auth_headers())

    assert create_response.status_code == 201

    response = client.get("/applications", headers=auth_headers())

    assert response.status_code == 200
    body = response.json

    # can just check this, make sure to check before popping id
    assert existing_application in body["items"]
    
    for app in body["items"]:
        app_id = app.pop("id", None)
        assert isinstance(app_id, int)


    assert body["items"] == [
    {
        "company": "Kaufland",
        "title": "Senior Engineer",
        "status" : "interview",
        "date_applied": '2026-10-29',
        "date_interview": None,
    },
    {
        "company": "Bosch",
        "title": "Junior Engineer",
        "status": "applied",
        "date_applied": "2026-10-26",
        "date_interview": None,
    }
    ]

# order is descending by default in db anyway, might as well have it "desc" in here for clarity
@pytest.mark.parametrize("status, order, page, limit, companies, envelope",[
    pytest.param(None, "desc", 1, 2, ["Kaufland", "Bosch"], (
        2, 3, 2, 2, True, False
    ), id="page_1_limit_2"),
    pytest.param(None, "desc", 2, 2, ["Bosch"], (
        1, 3, 2, 2, False, True
    ), id="page_2_limit_2"),
    pytest.param("interview", "desc", 1, 2, ["Kaufland", "Kaufland"], (
        2, 2, 2, 1, False, False
    ), id="page_1_limit_2_interview"),
    pytest.param(None, "asc", 1, 3, ["Bosch", "Kaufland", "Kaufland"], (
        3, 3, 3, 1, False, False
    ), id="page_1_limit_3_asc"),
])
def test_get_all_query_params_success(client, existing_application, auth_headers, status, order, page, limit, companies, envelope):
    params = {
    "page": page,
    "limit": limit,
    "status": status,
    "order": order,
    }

    payload = {
        "company": "Kaufland",
        "title": "Senior Engineer",
        "status" : "interview",
        "date_applied": '2026-10-29'
    }

    # create two more applications
    create_response = client.post("/applications", json=payload, headers=auth_headers())
    assert create_response.status_code == 201

    create_response = client.post("/applications", json=payload, headers=auth_headers())
    assert create_response.status_code == 201

    # page (1) and limit(2)
    get_response = client.get(f"/applications", query_string=params, headers=auth_headers())
    assert get_response.status_code == 200
    assert len(get_response.json["items"]) == envelope[0]
    for item in get_response.json["items"]:
        assert item["company"] in companies
    assert get_response.json["total_applications"] == envelope[1]
    assert get_response.json["per_page"] == envelope[2]
    assert get_response.json["total_pages"] == envelope[3]
    assert get_response.json["has_next"] == envelope[4]
    assert get_response.json["has_prev"] == envelope[5]
    assert get_response.json["filter_by"] == status
    assert get_response.json["order"] == order

@pytest.mark.parametrize("status",[
    pytest.param("INVALID_STATUS"),
    pytest.param("", id="missing_status"),
])
def test_get_all_applications_filtering_failure(client, status, existing_application, auth_headers):
    get_response_failure = client.get(f"/applications?page=1&limit1&status={status}", headers=auth_headers())

    assert get_response_failure.status_code == 400
    assert get_response_failure.json["error"] == "VALIDATION_ERROR"
    assert get_response_failure.json["message"] == "Data is invalid."
    # assert "validation for GetApplicationQuery" in get_response_failure.json["details"]

def test_get_all_applications_empty(client, auth_headers):
    response = client.get("/applications", headers=auth_headers())

    assert response.status_code == 200
    assert isinstance(response.json["items"], list)
    assert response.json["items"] == []

def test_get_application_success(client, existing_application, auth_headers):
    app_id = existing_application["id"]
    response = client.get(f"/applications/{app_id}", headers=auth_headers())

    assert response.status_code == 200
    assert response.json == existing_application

def test_get_nonexistent_application(client, auth_headers):
    nonexistent_app_id = NON_EXISTENT_ID
    response = client.get(f"/applications/{nonexistent_app_id}", headers=auth_headers())

    assert response.status_code == 404
    assert response.json["error"] == "MISSING_ERROR"
    assert "Application not found." in response.json["details"]

# POST

def test_post_success(client, auth_headers):
    payload = {
        "company": "Bosch", 
        "title": "Junior Engineer", 
        "status" : "applied", 
        "date_applied": '2026-10-26'
    }

    response = client.post("/applications", json=payload, headers=auth_headers())

    assert response.status_code == 201

    body = response.json
    app_id = body.pop("id", None)

    assert isinstance(app_id, int)
    assert body == {
        "company": "Bosch",
        "title": "Junior Engineer",
        "status": "applied",
        "date_applied": "2026-10-26",
        "date_interview": None,
    }

@pytest.mark.parametrize("payload, expected_details", [
    pytest.param({
        "company": "Bosch",
        "title": "Junior Engineer",
        "status" : "INCORRECT_STATUS",
        "date_applied": '2026-10-26'
    }, 
    "Input should be 'applied', 'interview', 'offer' or 'rejected'",
    id="invalid_status"
    ),
    pytest.param({
        # "company": "Bosch",
        "title": "Junior Engineer",
        "status" : "applied",
        "date_applied": '2026-10-26'
    }, 
    "Field required",
    id="missing_company"
    ),
])
def test_post_failure(client, payload, expected_details, auth_headers):
    response = client.post("/applications", json=payload, headers=auth_headers())

    # print(dir(response))

    assert response.status_code == 400
    assert response.json["error"] == "VALIDATION_ERROR"
    assert expected_details in response.json["details"]

def test_post_applications_unauthorized(client):
    payload = {
        "company": "Kaufland",
        "title": "Senior Engineer",
        "status" : "interview",
        "date_applied": '2026-10-29'
    }

    # no auth_headers() should result in a 401 Unauthorized
    response = client.post("/applications", json=payload)

    assert response.status_code == 401

# PATCH

def test_patch_success(client, existing_application, auth_headers):
    modified_payload = {
        "title": "Senior Software Engineer",
        "status" : "interview"
    }

    app_id = existing_application["id"]
    modified_application = client.patch(f"/applications/{app_id}", json=modified_payload, headers=auth_headers())

    assert modified_application.status_code == 200

    response = client.get(f"/applications/{app_id}", headers=auth_headers())
    assert response.status_code == 200
    assert response.json["title"] == "Senior Software Engineer"
    assert response.json["status"] == "interview"
    assert response.json["company"] == existing_application["company"]
    assert response.json["date_applied"] == existing_application["date_applied"]
    assert response.json["date_interview"] == existing_application["date_interview"]

@pytest.mark.parametrize("payload, expected_details", [
    pytest.param({
        "INCORRECT_FIELD": "Senior Software Engineer"
    }, 
    "No valid fields provided to modify",
    id="invalid_field"
    ),
    pytest.param({
        "title": "Senior Software Engineer",
        "status" : "INCORRECT_STATUS"
    }, 
    "Incorrect status",
    id="invalid_status"
    ),
])
def test_patch_failure(client, existing_application, payload, expected_details, auth_headers):
    app_id = existing_application["id"]
    modified_application = client.patch(f"/applications/{app_id}", json=payload, headers=auth_headers())

    assert modified_application.status_code == 400
    assert modified_application.json["error"] == "VALIDATION_ERROR"
    assert expected_details in modified_application.json["details"]

def test_patch_failure_does_not_modify_application(client, existing_application, auth_headers):
    wrong_application = client.patch(f"/applications/{existing_application["id"]}", json={
    "title": "This change must not persist",
    "status": "WRONG_STATUS",
}, headers=auth_headers())

    assert wrong_application.status_code == 400

    app_id = existing_application["id"]

    response = client.get(f"/applications/{app_id}", headers=auth_headers())
    assert response.status_code == 200
    assert response.json == existing_application

def test_unexpected_error_returns_500(client, existing_application, monkeypatch, auth_headers):
    # Production-like behavior, not needed anymore since there's a global exception handler, but it's good to state this out explicitly
    monkeypatch.setitem(flask_app.config, "PROPAGATE_EXCEPTIONS", False)
    app_id = existing_application["id"]

    monkeypatch.setattr(application_service,"update_application_id_alchemy", mocked_update_id_alchemy)

    response = client.patch(f"/applications/{app_id}", json={"title": "VALID_TITLE"}, headers=auth_headers())

    # print(response.json)
    assert response.status_code == 500
    assert response.is_json
    assert response.json["message"] == "Something went wrong. Please try again later."

def test_patch_transaction_rolls_back_on_exception(client, existing_application, monkeypatch, auth_headers):
    app_id = existing_application["id"]

    monkeypatch.setattr(application_service,"update_application_id_alchemy", mocked_update_id_alchemy)

    modified_application = client.patch(f"/applications/{app_id}", json={"title": "VALID_TITLE"}, headers=auth_headers())

    assert modified_application.status_code == 500
    assert modified_application.json["error"] == "INTERNAL_SERVER_ERROR"

    response = client.get(f"/applications/{app_id}", headers=auth_headers())

    assert response.status_code == 200
    assert response.json == existing_application

def test_patch_applications_unauthorized(client, existing_application):
    modified_payload = {
        "title": "Senior Software Engineer",
        "status" : "interview"
    }

    app_id = existing_application["id"]
    # no auth_headers() should result in a 401 Unauthorized
    modified_application = client.patch(f"/applications/{app_id}", json=modified_payload)

    assert modified_application.status_code == 401

def test_nonexistent_patch(client, auth_headers):
    modified_payload = {
        "title": "Senior Software Engineer",
        "status" : "interview"
    }
    
    modified_application = client.patch(f"/applications/{NON_EXISTENT_ID}", json=modified_payload, headers=auth_headers())

    assert modified_application.status_code == 404
    assert modified_application.json["error"] == "MISSING_ERROR"
    assert "Application not found" in modified_application.json["details"]

# DELETE

def test_delete_success(client, existing_application, auth_headers):
    app_id = existing_application["id"]
    response = client.delete(f"/applications/{app_id}", headers=auth_headers())

    assert response.status_code == 204

    response_to_fail = client.get(f"/applications/{app_id}", headers=auth_headers())

    assert response_to_fail.status_code == 404
    assert response_to_fail.json["error"] == "MISSING_ERROR"
    assert "Application not found" in response_to_fail.json["details"]

def test_missing_delete(client, auth_headers):
    nonexistent_app_id = NON_EXISTENT_ID
    response = client.delete(f"/applications/{nonexistent_app_id}", headers=auth_headers())

    assert response.status_code == 404
    assert response.json["error"] == "MISSING_ERROR"
    assert "Could not find application to delete" in response.json["details"]

# AUTHORIZATION

@pytest.mark.parametrize("method, payload",
    [
     pytest.param("get", None, id="get"),                      
     pytest.param("patch", {
        "title": "Senior Software Engineer",
        "status" : "interview"
    }, id="patch"),                     
     pytest.param("delete", None, id="delete")                        
    ])
def test_protected_application_404(method, payload, client, existing_application, auth_headers):
    # User 1 already created by existing_application
    user_2_header = auth_headers(email="user2@gmail.com")

    app_id = existing_application["id"]

    request_func = getattr(client, method)

    # since get and delete have payload=None, only patch sends json=payload as intended
    response = request_func(f"/applications/{app_id}", json=payload, headers=user_2_header)

    assert response.status_code == 404

# UNEXPECTED

def test_unknown_route_returns_404_json(client, auth_headers):
    response = client.get("/this-route-does-not-exist", headers=auth_headers())

    assert response.status_code == 404
    assert response.is_json
    assert response.json["error"] == "NOT_FOUND"

def test_unsupported_method_returns_405_json(client, auth_headers):
    response = client.put("/applications", headers=auth_headers())

    assert response.status_code == 405
    assert response.is_json
    assert response.json["error"] == "METHOD_NOT_ALLOWED"