from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from pydantic_rules import GetApplicationQuery
from services.application_service import get_application_by_id, create_application, get_applications, modify_application, delete_application
from services.helper import LIMIT_DEFAULT, PAGE_DEFAULT

application_bp = Blueprint(
    'applications', # Blueprint name
    __name__, # Import name
    url_prefix="/applications" # Prepends /applications to all routes in this BP
)

# get specific app
@application_bp.route("/<int:app_id>")
@jwt_required()
def get_app_protected(app_id):
    user_id = int(get_jwt_identity())

    application = get_application_by_id(app_id, user_id)
    
    return jsonify(application)

# get all apps from authorized user
@application_bp.route("", methods=["GET"])
@jwt_required()
def get_apps_protected():
    query = GetApplicationQuery.model_validate(request.args.to_dict())

    user_id = int(get_jwt_identity())

    response = get_applications(user_id, query.status, query.page, query.limit)

    return jsonify(response)

# create new app
@application_bp.route("", methods=["POST"])
@jwt_required()
def create_app():
    user_id = int(get_jwt_identity())

    data = request.get_json()

    new_application = create_application(data, user_id)

    return jsonify(new_application), 201

# modify existing app
@application_bp.route("/<int:app_id>", methods=["PATCH"])
@jwt_required()
def modify(app_id):
    user_id = int(get_jwt_identity())

    data = request.get_json()

    app_data = modify_application(app_id, data, user_id)

    return jsonify(app_data), 200
    

# delete app
@application_bp.route("/<int:app_id>", methods=["DELETE"])
@jwt_required()
def delete(app_id):
    user_id = int(get_jwt_identity())

    delete_application(app_id, user_id)

    return "", 204