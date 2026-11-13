"""Authenticated content-management API routes."""

from __future__ import annotations

import secrets
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

from ..resources import clean_text, missing_required_fields, normalize_resource, required_fields_error, RESOURCE_FIELDS
from ..security import admin_required, create_admin_token
from ..storage import read_content, write_content


admin_api = Blueprint("admin_api", __name__, url_prefix="/api/admin")


@admin_api.post("/login")
def admin_login():
    admin_password = current_app.config["ADMIN_PASSWORD"]
    if not admin_password:
        return jsonify(error="Admin access is not configured. Set ADMIN_PASSWORD in the backend environment."), 503
    payload = request.get_json(silent=True) or {}
    password = str(payload.get("password", ""))
    if not secrets.compare_digest(password, admin_password):
        return jsonify(error="That password did not match."), 401
    return jsonify(token=create_admin_token())


@admin_api.get("/content")
@admin_required
def admin_content():
    content = read_content()
    content["resumeAvailable"] = (current_app.config["UPLOAD_DIR"] / "resume.pdf").is_file()
    return jsonify(content)


@admin_api.post("/resume")
@admin_required
def upload_resume():
    resume = request.files.get("resume")
    if resume is None or not resume.filename:
        return jsonify(error="Choose a résumé PDF to upload."), 400
    if Path(resume.filename).suffix.lower() != ".pdf" or resume.mimetype != "application/pdf":
        return jsonify(error="Upload a PDF résumé."), 400

    resume_bytes = resume.stream.read(current_app.config["MAX_IMAGE_BYTES"] + 1)
    if len(resume_bytes) > current_app.config["MAX_IMAGE_BYTES"]:
        return jsonify(error="The résumé must be 8 MB or smaller."), 413

    upload_dir = current_app.config["UPLOAD_DIR"]
    upload_dir.mkdir(parents=True, exist_ok=True)
    (upload_dir / "resume.pdf").write_bytes(resume_bytes)
    return jsonify(ok=True, available=True), 201


@admin_api.post("/uploads")
@admin_required
def upload_project_image():
    image = request.files.get("image")
    if image is None or not image.filename:
        return jsonify(error="Choose a screenshot to upload."), 400

    extension = Path(image.filename).suffix.lower()
    expected_type = current_app.config["ALLOWED_IMAGE_TYPES"].get(extension)
    if not expected_type or image.mimetype != expected_type:
        return jsonify(error="Upload a PNG, JPG, or WebP image."), 400

    image_bytes = image.stream.read(current_app.config["MAX_IMAGE_BYTES"] + 1)
    if len(image_bytes) > current_app.config["MAX_IMAGE_BYTES"]:
        return jsonify(error="The screenshot must be 8 MB or smaller."), 413

    filename = f"{secrets.token_hex(16)}{extension}"
    upload_dir = current_app.config["UPLOAD_DIR"]
    upload_dir.mkdir(parents=True, exist_ok=True)
    (upload_dir / filename).write_bytes(image_bytes)
    return jsonify(image=f"/api/uploads/{filename}"), 201


@admin_api.put("/profile")
@admin_required
def update_profile():
    payload = request.get_json(silent=True) or {}
    content = read_content()
    fields = ("name", "headline", "role", "about", "lead", "location", "email", "github", "linkedin", "availability")
    content["profile"] = {
        key: clean_text(payload.get(key, content["profile"].get(key)), 5000 if key == "about" else 500)
        for key in fields
    }
    write_content(content)
    return jsonify(profile=content["profile"])


@admin_api.post("/<resource>")
@admin_required
def create_resource(resource):
    if resource not in RESOURCE_FIELDS:
        return jsonify(error="Unknown content type."), 404
    payload = request.get_json(silent=True) or {}
    item = normalize_resource(resource, payload)
    missing_fields = missing_required_fields(resource, item)
    if missing_fields:
        return jsonify(error=required_fields_error(missing_fields)), 400
    content = read_content()
    content[resource].insert(0, item)
    write_content(content)
    return jsonify(item), 201


@admin_api.put("/<resource>/<item_id>")
@admin_required
def update_resource(resource, item_id):
    if resource not in RESOURCE_FIELDS:
        return jsonify(error="Unknown content type."), 404
    content = read_content()
    for index, existing in enumerate(content[resource]):
        if existing.get("id") == item_id:
            payload = request.get_json(silent=True) or {}
            item = normalize_resource(resource, {**existing, **payload, "id": item_id})
            content[resource][index] = item
            write_content(content)
            return jsonify(item)
    return jsonify(error="Item not found."), 404


@admin_api.delete("/<resource>/<item_id>")
@admin_required
def delete_resource(resource, item_id):
    if resource not in RESOURCE_FIELDS:
        return jsonify(error="Unknown content type."), 404
    content = read_content()
    remaining = [item for item in content[resource] if item.get("id") != item_id]
    if len(remaining) == len(content[resource]):
        return jsonify(error="Item not found."), 404
    content[resource] = remaining
    write_content(content)
    return jsonify(ok=True)


@admin_api.get("/messages")
@admin_required
def messages():
    return jsonify(read_content()["messages"])
