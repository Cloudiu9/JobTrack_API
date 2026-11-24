import math
from pydantic_rules import ApplicationStatus, CreateApplicationRequest
from models.application import STATUS, ALLOWED_KEYS
from services.helper import LIMIT_DEFAULT, PAGE_DEFAULT, enforce_rules, validate_dates
from exceptions import ResourceNotFoundError, ValidationError
from pydantic import ValidationError as PydanticValidationError
from db_alchemy import SessionFactory, insert_application_alchemy, retrieve_application_id_alchemy, retrieve_applications_alchemy, update_application_id_alchemy, delete_application_id_alchemy

def get_applications(user_id: int, status: ApplicationStatus | None, page = PAGE_DEFAULT, limit = LIMIT_DEFAULT):
    """
    Pagination:

    status -> filter by applied/interview (query parameter)

    page -> which page number (query parameter)

    limit -> how many items per page (query parameter)

    """
    with SessionFactory() as session:
        apps, total_apps = retrieve_applications_alchemy(session, user_id, status, page, limit)

    total_pages = math.ceil(total_apps/limit)

    json_envelope = {
        "items": apps,
        "total_applications": total_apps,
        "per_page": limit,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
        "filter_by": status
    }

    return json_envelope

def get_application_by_id(app_id, user_id):
    with SessionFactory() as session:
        application = retrieve_application_id_alchemy(session, app_id, user_id)

    if application is None:
        raise ResourceNotFoundError("Application not found.")

    return application

def create_application(data: dict, user_id: int):
    # Can be ommitted now, thanks to Pydantic
    # if not isinstance(data, dict):
    #     raise ValidationError("Body must be a valid JSON.")

    # if "id" in data:
    #     raise ValidationError("Bad request. (Do not provide an id)")
    
    # if data.get("status") not in STATUS:
    #     raise ValidationError("Bad request. (Missing or wrong status)")
    
    # if not data.get("company"):
    #     raise ValidationError("Bad request. (Missing company)")
    
    # if not data.get("title"):
    #     raise ValidationError("Bad request. (Missing title)")

    try:
        application = CreateApplicationRequest.model_validate(data)
        validated_pydantic_data = application.model_dump(exclude_unset=True)
    except PydanticValidationError as e:
        raise ValidationError(str(e)) from e

    # Can be ommitted now, thanks to Pydantic
    # unknown_keys = set(data) - set(ALLOWED_KEYS)
    # if unknown_keys:
    #     raise ValidationError(f"Unknown field(s): {', '.join(sorted(unknown_keys))}")

    # Can be ommitted now, thanks to Pydantic
    # enforce_rules(validated_pydantic_data)
    # validate_dates(validated_pydantic_data)

    # insert trusted user_id
    validated_pydantic_data["user_id"] = user_id

    # .begin() automatically handles (try/except) commit() and rollback()
    with SessionFactory.begin() as session:
        new_job = insert_application_alchemy(session, validated_pydantic_data)

    return new_job


def modify_application(app_id: int, data: dict, user_id: int):
    if not isinstance(data, dict):
        raise ValidationError( "Body must be a valid JSON.")

    if "id" in data:
        raise ValidationError("Cannot modify id.")

    # all keys in allowed keys, is there any valid key in data
    if not any(key in data for key in ALLOWED_KEYS):
        raise ValidationError("No valid fields provided to modify.") 

    # all keys in data, is there any key not allowed
    if any(key not in ALLOWED_KEYS for key in data):
        raise ValidationError("Invalid field found.")   

    # TODO replace manual validation with Pydantic validation
    enforce_rules(data)
    validate_dates(data)
    
    if "status" in data and data["status"] not in STATUS:
        raise ValidationError("Incorrect status.")

    # is this even needed? should I pass it in update_application_id_alchemy()? 
    with SessionFactory.begin() as session:
        application_to_modify = update_application_id_alchemy(session, app_id, data, user_id)

    if application_to_modify is None:
        raise ResourceNotFoundError("Application not found.")
    
    return application_to_modify

def delete_application(app_id: int, user_id: int):
    with SessionFactory.begin() as session:
        result = delete_application_id_alchemy(session, app_id, user_id)

    if result is None:
        raise ResourceNotFoundError("Could not find application to delete.")
    
    return result