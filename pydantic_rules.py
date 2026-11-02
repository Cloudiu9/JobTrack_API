from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, SecretStr
from datetime import date
from typing import Annotated, Literal
from pydantic import ValidationError as PydanticValidationError
from models import user

# Application
# needs a separate model for PATCH

# POST
class CreateApplicationRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid", # Crash if unexpected fields
        str_strip_whitespace=True
    )

    company: str = Field(min_length=1)
    title: str = Field(min_length=1)
    date_applied: date = Field(default=None) # type: ignore # this can be omitted since it has a default, but can't be None
    status: Literal["applied", "interview"]
    date_interview: date | None = None

valid_input = {
    "company": "  Bosch ",
    "title": "     Junior Engineer  ",
    # "date_applied": None,
    "status": "applied",
    "date_interview": None
}

application = CreateApplicationRequest(**valid_input)
db_data = application.model_dump(exclude_unset=True)
# print(db_data) # Removes the excluded None date_applied


invalid_input = {
    "company": "   ",
    # "title": "     Junior Engineer  ",
    "date_applied": "not-a-date",
    "status": "INVALID_DATA",
    "date_interview": 100,
    "id": 1
}

try:
    CreateApplicationRequest(**invalid_input)
except PydanticValidationError as e:
    print(e)


# User

# Annotated creates a 'metatype' ==> normal type (SecretStr) + something else
PasswordSecretStr = Annotated[SecretStr, Field(min_length=10)]


# BeforeValidator ensures app doesn't crash if email isn't a string (runs this function before normal validation)
NormalizeEmail = BeforeValidator(lambda v: v.strip().lower() if isinstance(v, str) else v)

ValidatedEmail = Annotated[str, NormalizeEmail, Field(min_length=1)]

# POST
class CreateNewUser(BaseModel):
    model_config = ConfigDict(
        extra="forbid", # Crash if unexpected fields
    )

    email: ValidatedEmail
    password: PasswordSecretStr

valid_input = {
    "email": "  testing@gmail.com ",
    "password": "     Junior Engineer  "
}

user = CreateNewUser(**valid_input) # type: ignore
db_data = user.model_dump(exclude_unset=True)
print(db_data)


invalid_input = {
    "email": "   ",
    "password": "123456789",
}

try:
    CreateNewUser(**invalid_input) # type: ignore
except PydanticValidationError as e:
    print(e)