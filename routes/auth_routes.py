from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from services.auth_service import get_all_users, get_user_by_id, login_user, register_user

auth_bp = Blueprint(
    'auth', # Blueprint name
    __name__, # Import name
    url_prefix="/auth" # Prepends /auth to all routes in this BP
)

# get specific user
@auth_bp.route("/<int:user_id>")
def get_user(user_id):
    user = get_user_by_id(user_id)
    
    return jsonify(user)

# get all users
@auth_bp.route('')
def get_users():
    users = get_all_users()

    return jsonify(users)

# create user
@auth_bp.route('/register', methods=["POST"])
def create_user():
    data = request.get_json()

    new_user = register_user(data)

    return jsonify(new_user), 201

# login user TODO
@auth_bp.route('/login', methods=["POST"])
def authorize_user():
    data = request.get_json()

    verified_user_jwt = login_user(data)

    return jsonify(verified_user_jwt), 200

# protected route that requires login
@auth_bp.route("/secure", methods=["GET"])
@jwt_required()
def secured_route():
    user_id = get_jwt_identity()

    return jsonify(user_id)