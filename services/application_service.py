from db_alchemy import SessionFactory, retrieve_applications_all_alchemy, retrieve_application_id_alchemy, insert_application_alchemy, update_application_id_alchemy, delete_application_id_alchemy
from models.application import STATUS, ALLOWED_KEYS
from exceptions import ResourceNotFoundError, ValidationError, enforce_rules, validate_dates
from pydantic_rules import CreateApplicationRequest
from pydantic import ValidationError as PydanticValidationError

def get_application_by_id(app_id):
    with SessionFactory() as session:
        application = retrieve_application_id_alchemy(session, app_id)

    if application is None:
        raise ResourceNotFoundError("Application not found.")

    return application


def get_applications():
    with SessionFactory() as session:
        all_apps = retrieve_applications_all_alchemy(session)
    return all_apps


def create_application(data):
    if not isinstance(data, dict):
        raise ValidationError("Body must be a valid JSON.")

    # Can be ommitted now, thanks to Pydantic
    # if "id" in data:
    #     raise ValidationError("Bad request. (Do not provide an id)")
    
    # if data.get("status") not in STATUS:
    #     raise ValidationError("Bad request. (Missing or wrong status)")
    
    # if not data.get("company"):
    #     raise ValidationError("Bad request. (Missing company)")
    
    # if not data.get("title"):
    #     raise ValidationError("Bad request. (Missing title)")

    try:
        application = CreateApplicationRequest(**data)
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

    # .begin() automatically handles (try/except) commit() and rollback()
    with SessionFactory.begin() as session:
        new_job = insert_application_alchemy(session, validated_pydantic_data)

    return new_job


def modify_application(app_id, data):
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

    enforce_rules(data)
    validate_dates(data)
    
    if "status" in data and data["status"] not in STATUS:
        raise ValidationError("Incorrect status.") 

    with SessionFactory.begin() as session:
        application_to_modify = update_application_id_alchemy(session, app_id, data)

    if application_to_modify is None:
        raise ResourceNotFoundError("Application not found.")
    
    return application_to_modify

def delete_application(app_id):
    with SessionFactory.begin() as session:
        result = delete_application_id_alchemy(session, app_id)

    if result is None:
        raise ResourceNotFoundError("Could not find application to delete.")
    
    return result