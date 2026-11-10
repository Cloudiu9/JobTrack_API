from sqlalchemy.exc import IntegrityError
from db_alchemy import SessionFactory, login_user_alchemy, register_user_alchemy, retrieve_user_id_alchemy, retrieve_users_all_alchemy
from exceptions import AuthenticationError, ResourceNotFoundError, DuplicateEmailError, ValidationError
from pydantic_rules import CreateNewUser
from security import hash_password
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

# TODO
def login_user(data):
    if not isinstance(data, dict):
        raise ValidationError("Body must be a valid JSON.")

    try:
        with SessionFactory.begin() as session:
            user = login_user_alchemy(session, data)
        return user
    except ResourceNotFoundError as e:
        raise ResourceNotFoundError("User is not registered.") from e
    except AuthenticationError as e:
        raise AuthenticationError("Incorrect email or password.") from e

def get_user_by_id(user_id):
    with SessionFactory() as session:
        user = retrieve_user_id_alchemy(session, user_id)

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