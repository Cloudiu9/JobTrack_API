from datetime import datetime


class ResourceNotFoundError(Exception):
    """Missing resource. (404)"""
    pass

class ValidationError(Exception):
    """Invalid data. (400)"""
    pass

class DuplicateEmailError(Exception):
    """This email is already registered. (409)"""
    pass

def validate_dates(data):
    DATE_FIELDS = ["date_interview", "date_applied"]

    for field in DATE_FIELDS:
        if field in data:
            value = data[field]

            if data[field] is None and field == "date_interview":
                continue

            if not isinstance(value, str):
                raise ValidationError(f"The field {field} must be a string.")

            try:
                data[field] = datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                raise ValidationError(
                    f"Invalid date format for {field}. Please use the ISO standard YYYY-MM-DD (e.g., 2026-11-13)"
                )


def enforce_rules(data):
    # don't allow null, except for date_interview
    if any((isinstance(value, str) and value.strip() == "") or (value is None and key != "date_interview") for key, value in data.items()):
        raise ValidationError("Empty field found.") 
    
    # only allow strings, except for date_interview (which can be null)
    if not all(isinstance(value,str) or key == "date_interview" for key, value in data.items()):
        raise ValidationError("Non-string field found.")