from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from services.application_service import get_application_by_id, get_applications, create_application, get_applications_protected, modify_application, delete_application

application_bp = Blueprint(
    'applications', # Blueprint name
    __name__, # Import name
    url_prefix="/applications" # Prepends /applications to all routes in this BP
)

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

# get all apps from authorized user
@application_bp.route("/user", methods=["GET"])
@jwt_required()
def get_apps_protected():
    user_id = int(get_jwt_identity())

    user_apps = get_applications_protected(user_id)

    return jsonify(user_apps)

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