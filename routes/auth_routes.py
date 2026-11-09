from flask import Blueprint

auth_bp = Blueprint(
    'auth', # Blueprint name
    __name__, # Import name
    url_prefix="/auth" # Prepends /auth to all routes in this BP
)

