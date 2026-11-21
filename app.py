import os
from flask import Flask
from flask_jwt_extended import JWTManager
from routes.application_routes import application_bp
from routes.auth_routes import auth_bp
from exceptions import register_error_handlers

app = Flask(__name__)

jwt_secret = os.environ.get("JWT_SECRET_KEY")
if not jwt_secret:
    raise RuntimeError(
        "JWT_SECRET_KEY environment variable was not provided."
    )

app.config["JWT_SECRET_KEY"] = jwt_secret

jwt = JWTManager(app)

app.register_blueprint(application_bp)
app.register_blueprint(auth_bp)

register_error_handlers(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
