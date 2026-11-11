import os
from flask import Flask
from flask_jwt_extended import JWTManager
from routes.application_routes import application_bp
from routes.auth_routes import auth_bp
from exceptions import register_error_handlers

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY","CnL1QvA3f2YS7ug4TnwYOsIDMJedLbstkHm46swtAhB")

jwt = JWTManager(app)

app.register_blueprint(application_bp)
app.register_blueprint(auth_bp)

register_error_handlers(app)