from flask import Flask
from routes.application_routes import application_bp
from routes.auth_routes import auth_bp
from exceptions import register_error_handlers

app = Flask(__name__)

app.register_blueprint(application_bp)
app.register_blueprint(auth_bp)

register_error_handlers(app)