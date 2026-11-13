"""Unauthenticated portfolio and contact API routes."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_from_directory

from ..resources import clean_text
from ..storage import read_content, write_content


public_api = Blueprint("public_api", __name__, url_prefix="/api")


@public_api.get("/health")
def health():
    return jsonify(status="ok")


@public_api.get("/uploads/<path:filename>")
def uploaded_image(filename):
    return send_from_directory(current_app.config["UPLOAD_DIR"], filename)


@public_api.get("/resume")
def download_resume():
    upload_dir = current_app.config["UPLOAD_DIR"]
    if not (upload_dir / "resume.pdf").is_file():
        return jsonify(error="No résumé has been uploaded yet."), 404
    return send_from_directory(upload_dir, "resume.pdf", as_attachment=True, download_name="resume.pdf", mimetype="application/pdf")


@public_api.get("/content")
def public_content():
    content = read_content()
    public_data = {key: content[key] for key in ("profile", "skills", "projects", "experience", "education", "certifications")}
    public_data["resumeAvailable"] = (current_app.config["UPLOAD_DIR"] / "resume.pdf").is_file()
    return jsonify(public_data)


@public_api.post("/contact")
def contact():
    payload = request.get_json(silent=True) or {}
    if clean_text(payload.get("website"), 200):
        return jsonify(ok=True), 201

    name = clean_text(payload.get("name"), 120)
    email = clean_text(payload.get("email"), 254)
    message = clean_text(payload.get("message"), 5000)
    if not name or not email or not message:
        return jsonify(error="Name, email and message are required."), 400
    if "@" not in email or len(email) < 5:
        return jsonify(error="Please enter a valid email address."), 400

    content = read_content()
    if len(content["messages"]) >= 1000:
        content["messages"] = content["messages"][:999]
    entry = {
        "id": secrets.token_urlsafe(10),
        "name": name,
        "email": email,
        "subject": clean_text(payload.get("subject"), 200),
        "message": message,
        "createdAt": clean_text(payload.get("createdAt"), 40) or datetime.now(timezone.utc).isoformat(),
    }
    content["messages"].insert(0, entry)
    write_content(content)
    return jsonify(ok=True, message="Thanks for reaching out. Your message has been received."), 201
