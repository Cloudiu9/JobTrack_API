from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    return generate_password_hash(password)

def verify_password(password_hash, password):
    """Takes in the password hash, then the password."""
    return check_password_hash(password_hash, password)