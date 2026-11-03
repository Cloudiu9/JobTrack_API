from sqlalchemy.exc import IntegrityError

from db_alchemy import SessionFactory, register_user_alchemy, retrieve_user_id_alchemy, retrieve_users_all_alchemy
from exceptions import ResourceNotFoundError, DuplicateEmailError, ValidationError
from pydantic_rules import CreateNewUser
from security import hash_password, verify_password

from pydantic import ValidationError as PydanticValidationError


def register_user(data):
    if not isinstance(data, dict):
        raise ValidationError("Body must be a valid JSON.")
    # data_for_validation = {"email": email, "password": password}

    try:
        # model_validate checks content and rules, ensures email and password are according to schema
        user_schema = CreateNewUser.model_validate(data)

        password = user_schema.password.get_secret_value()
        pass_hash = hash_password(password)
        
        validated_data = user_schema.model_dump()
    except PydanticValidationError as e:
        raise ValidationError(str(e)) from e
    
    db_data = {
        "email": validated_data["email"],
        "password_hash": pass_hash
    }

    try:
        with SessionFactory.begin() as session:
            result = register_user_alchemy(session, db_data)
        return result
    except IntegrityError as e:
        raise DuplicateEmailError("This email is already registered.") from e

def get_user_by_id(app_id):
    with SessionFactory() as session:
        user = retrieve_user_id_alchemy(session, app_id)

    if user is None:
        raise ResourceNotFoundError("User not found.")

    return user

# returns [] when db is empty
def get_all_users():
    with SessionFactory() as session:
        all_users = retrieve_users_all_alchemy(session)

    if all_users is None:
        raise ResourceNotFoundError("No users found.")

    return all_users