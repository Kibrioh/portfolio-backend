"""Flask application factory for the portfolio API."""

from flask import Flask, jsonify
from flask_cors import CORS

from .config import load_config
from .routes.admin import admin_api
from .routes.public import public_api


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.update(load_config())
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    @app.errorhandler(413)
    def request_too_large(_error):
        return jsonify(error="The uploaded file must be 8 MB or smaller."), 413

    app.register_blueprint(public_api)
    app.register_blueprint(admin_api)
    return app
