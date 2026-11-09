import logging
from flask import jsonify, json
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

# Custom Core Exceptions
class ResourceNotFoundError(Exception):
    """Missing resource. (404)"""
    pass

class ValidationError(Exception):
    """Invalid data. (400)"""
    pass

class DuplicateEmailError(Exception):
    """This email is already registered. (409)"""
    pass


# Centralized Handler Functions
def handle_validation_error(e):
    return jsonify({
        "error": "VALIDATION_ERROR",
        "message": "Data is invalid.",
        "details": str(e)
    }), 400

def handle_missing_error(e):
    return jsonify({
        "error": "MISSING_ERROR",
        "message": "Resource not found.",
        "details": str(e)
    }), 404

def handle_500_error(e):
    logger.exception(f"Unexpected server error: {str(e)}")
    return jsonify({
        "error": "INTERNAL_SERVER_ERROR",
        "message": "Something went wrong. Please try again later.",
    }), 500

def handle_http_exception(e):
    response = e.get_response()
    response.data = json.dumps({
        "error": e.name.upper().replace(" ", "_"),
        "message": e.description,
    })
    response.content_type = "application/json"
    return response


# Registration Factory
def register_error_handlers(app):
    """Binds all global exception handlers to the Flask app instance."""
    app.register_error_handler(ValidationError, handle_validation_error)
    app.register_error_handler(ResourceNotFoundError, handle_missing_error)
    app.register_error_handler(HTTPException, handle_http_exception)
    app.register_error_handler(Exception, handle_500_error)
