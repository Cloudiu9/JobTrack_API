from flask import Blueprint, json, jsonify, request
from services.application_service import get_application_by_id, get_applications, create_application, modify_application, delete_application
from exceptions import ResourceNotFoundError, ValidationError
import logging
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

application_bp = Blueprint(
    'applications', # Blueprint name
    __name__, # Import name
    url_prefix="/applications" # Prepends /applications to all routes in this BP
)

@application_bp.app_errorhandler(ValidationError)
def handle_validation_error(e):
    payload = {
        "error": "VALIDATION_ERROR",
        "message": "Data is invalid.",
        "details": str(e)
    }
    return jsonify(payload), 400

@application_bp.app_errorhandler(ResourceNotFoundError)
def handle_missing_error(e):
    payload = {
        "error": "MISSING_ERROR",
        "message": "Application not found.",
        "details": str(e)
    }
    return jsonify(payload), 404

@application_bp.app_errorhandler(Exception)
def handle_500_error(e):
    logger.exception(f"Unexpected server error: {str(e)}")

    payload = {
        "error": "INTERNAL_SERVER_ERROR",
        "message": "Something went wrong. Please try again later.",
    }
    return jsonify(payload), 500

@application_bp.app_errorhandler(HTTPException)
def handle_http_exception(e):
    response = e.get_response()

    response.data = json.dumps({
        "error": e.name.upper().replace(" ","_"),
        "message": e.description,
    })

    response.content_type = "application/json"
    return response

# get specific app
@application_bp.route("/<int:app_id>")
def get_app(app_id):
    application = get_application_by_id(app_id)
    
    return jsonify(application)

# get all apps
@application_bp.route('')
def get_apps():
    applications = get_applications()

    return jsonify(applications)

# create new app
@application_bp.route("", methods=["POST"])
def create_app():
    data = request.get_json()

    new_application = create_application(data)

    return jsonify(new_application), 201

# modify existing app
@application_bp.route("/<int:app_id>", methods=["PATCH"])
def modify(app_id):
    data = request.get_json()

    app_data = modify_application(app_id, data)

    return jsonify(app_data), 200
    

# delete app
@application_bp.route("/<int:app_id>", methods=["DELETE"])
def delete(app_id):
    delete_application(app_id)

    return "", 204