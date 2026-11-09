from flask import Blueprint, jsonify, request

from services.auth_service import get_all_users, get_user_by_id, register_user

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
@auth_bp.route('', methods=["POST"])
def create_user():
    data = request.get_json()

    new_user = register_user(data)

    return jsonify(new_user), 201