"""Admin token creation and request authorization."""

from __future__ import annotations

from functools import wraps

from flask import current_app, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"],
        salt=current_app.config["TOKEN_SALT"],
    )


def create_admin_token() -> str:
    return _serializer().dumps({"admin": True})


def admin_required(handler):
    @wraps(handler)
    def wrapped(*args, **kwargs):
        authorization = request.headers.get("Authorization", "")
        token = authorization.removeprefix("Bearer ").strip()
        if not token:
            return jsonify(error="Admin login required."), 401
        try:
            _serializer().loads(token, max_age=current_app.config["TOKEN_MAX_AGE"])
        except SignatureExpired:
            return jsonify(error="Your admin session expired. Please sign in again."), 401
        except BadSignature:
            return jsonify(error="Invalid admin session."), 401
        return handler(*args, **kwargs)

    return wrapped
