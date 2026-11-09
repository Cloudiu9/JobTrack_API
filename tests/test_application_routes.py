import pytest
from app import app as flask_app
from models.application import Application
from services import application_service 

NON_EXISTENT_ID = 9999999999

# same as db_alchemy.update_id_alchemy, but flushes() after change and raises error
def mocked_update_id_alchemy(session, app_id, data):
    application = session.get(Application, app_id)

    if application is None:
        return None

    application.title = data["title"]

    session.flush()
    raise RuntimeError("Simulated failure after flush")

@pytest.fixture
def existing_application(client):
    """Creates an application for the current test; the database transaction is rolled back during teardown."""
    payload = {
        "company": "Bosch", 
        "title": "Junior Engineer", 
        "status" : "applied", 
        "date_applied": '2026-10-26'
    }
    response = client.post("/applications", json=payload)

    assert response.status_code == 201
    return response.json

def test_get_all_applications_success(client, existing_application):
    payload2 = {
        "company": "Kaufland",
        "title": "Senior Engineer",
        "status" : "interview",
        "date_applied": '2026-10-29'
    }

    create_response = client.post("/applications", json=payload2)

    assert create_response.status_code == 201

    response = client.get("/applications")

    assert response.status_code == 200
    body = response.json

    assert len(body) == 2

    # can just check this, make sure to check before popping id
    assert existing_application in body
    
    for app in body:
        app_id = app.pop("id", None)
        assert isinstance(app_id, int)


    assert body == [
        {
        "company": "Bosch",
        "title": "Junior Engineer",
        "status": "applied",
        "date_applied": "2026-10-26",
        "date_interview": None,
    }, 
    {
        "company": "Kaufland",
        "title": "Senior Engineer",
        "status" : "interview",
        "date_applied": '2026-10-29',
        "date_interview": None,
    }
    ]


def test_get_all_applications_empty(client):
    response = client.get("/applications")

    assert response.status_code == 200
    assert isinstance(response.json, list)
    assert response.json == []

def test_get_application_success(client, existing_application):
    app_id = existing_application["id"]
    response = client.get(f"/applications/{app_id}")

    assert response.status_code == 200
    assert response.json == existing_application

def test_get_nonexistent_application(client):
    nonexistent_app_id = NON_EXISTENT_ID
    response = client.get(f"/applications/{nonexistent_app_id}")

    assert response.status_code == 404
    assert response.json["error"] == "MISSING_ERROR"
    assert "Application not found." in response.json["details"]

def test_post_success(client):
    payload = {
        "company": "Bosch", 
        "title": "Junior Engineer", 
        "status" : "applied", 
        "date_applied": '2026-10-26'
    }

    response = client.post("/applications", json=payload)

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
    "Input should be 'applied' or 'interview'",
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
def test_post_failure(client, payload, expected_details):
    response = client.post("/applications", json=payload)

    # print(dir(response))

    assert response.status_code == 400
    assert response.json["error"] == "VALIDATION_ERROR"
    assert expected_details in response.json["details"]

def test_patch_success(client, existing_application):
    modified_payload = {
        "title": "Senior Software Engineer",
        "status" : "interview"
    }

    app_id = existing_application["id"]
    modified_application = client.patch(f"/applications/{app_id}", json=modified_payload)

    assert modified_application.status_code == 200

    response = client.get(f"/applications/{app_id}")
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
def test_patch_failure(client, existing_application, payload, expected_details):
    app_id = existing_application["id"]
    modified_application = client.patch(f"/applications/{app_id}", json=payload)

    assert modified_application.status_code == 400
    assert modified_application.json["error"] == "VALIDATION_ERROR"
    assert expected_details in modified_application.json["details"]

def test_patch_failure_does_not_modify_application(client, existing_application):
    wrong_application = client.patch(f"/applications/{existing_application["id"]}", json={
    "title": "This change must not persist",
    "status": "WRONG_STATUS",
})

    assert wrong_application.status_code == 400

    app_id = existing_application["id"]

    response = client.get(f"/applications/{app_id}")
    assert response.status_code == 200
    assert response.json == existing_application

def test_unexpected_error_returns_500(client, existing_application, monkeypatch):
    # Production-like behavior, not needed anymore since there's a global exception handler, but it's good to state this out explicitly
    monkeypatch.setitem(flask_app.config, "PROPAGATE_EXCEPTIONS", False)
    app_id = existing_application["id"]

    monkeypatch.setattr(application_service,"update_application_id_alchemy", mocked_update_id_alchemy)

    response = client.patch(f"/applications/{app_id}", json={"title": "VALID_TITLE"})

    # print(response.json)
    assert response.status_code == 500
    assert response.is_json
    assert response.json["message"] == "Something went wrong. Please try again later."

def test_patch_transaction_rolls_back_on_exception(client, existing_application, monkeypatch):
    app_id = existing_application["id"]

    monkeypatch.setattr(application_service,"update_application_id_alchemy", mocked_update_id_alchemy)

    modified_application = client.patch(f"/applications/{app_id}", json={"title": "VALID_TITLE"})

    assert modified_application.status_code == 500
    assert modified_application.json["error"] == "INTERNAL_SERVER_ERROR"

    response = client.get(f"/applications/{app_id}")

    assert response.status_code == 200
    assert response.json == existing_application


def test_unknown_route_returns_404_json(client):
    response = client.get("/this-route-does-not-exist")

    assert response.status_code == 404
    assert response.is_json
    assert response.json["error"] == "NOT_FOUND"

def test_unsupported_method_returns_405_json(client):
    response = client.put("/applications")

    assert response.status_code == 405
    assert response.is_json
    assert response.json["error"] == "METHOD_NOT_ALLOWED"

def test_nonexistent_patch(client):
    modified_payload = {
        "title": "Senior Software Engineer",
        "status" : "interview"
    }
    
    modified_application = client.patch(f"/applications/{NON_EXISTENT_ID}", json=modified_payload)

    assert modified_application.status_code == 404
    assert modified_application.json["error"] == "MISSING_ERROR"
    assert "Application not found" in modified_application.json["details"]

def test_delete_success(client, existing_application):
    app_id = existing_application["id"]
    response = client.delete(f"/applications/{app_id}")

    assert response.status_code == 204

    response_to_fail = client.get(f"/applications/{app_id}")

    assert response_to_fail.status_code == 404
    assert response_to_fail.json["error"] == "MISSING_ERROR"
    assert "Application not found" in response_to_fail.json["details"]

def test_missing_delete(client):
    nonexistent_app_id = NON_EXISTENT_ID
    response = client.delete(f"/applications/{nonexistent_app_id}")

    assert response.status_code == 404
    assert response.json["error"] == "MISSING_ERROR"
    assert "Could not find application to delete" in response.json["details"]