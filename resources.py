"""Portfolio resource fields, validation, and normalization."""

from __future__ import annotations

import secrets


RESOURCE_FIELDS = {
    "projects": ("title", "category", "description", "stack", "image", "github", "demo", "featured"),
    "experience": ("role", "period", "company", "description", "skills"),
    "education": ("degree", "institution", "period", "description"),
    "certifications": ("title", "issuer", "date", "credentialUrl", "description"),
    "skills": ("name", "category"),
}

RESOURCE_REQUIRED_FIELDS = {
    "projects": ("title",),
    "experience": ("role",),
    "education": ("degree", "institution"),
    "certifications": ("title",),
    "skills": ("name",),
}


def clean_text(value, limit: int = 10_000) -> str:
    if value is None:
        return ""
    return str(value).strip()[:limit]


def normalize_resource(resource: str, payload: dict) -> dict:
    item = {field: payload.get(field, "") for field in RESOURCE_FIELDS[resource]}
    for field, value in item.items():
        if field == "featured":
            item[field] = bool(value)
        elif field in ("stack", "skills"):
            values = value if isinstance(value, list) else str(value).split(",")
            item[field] = [clean_text(tag, 50) for tag in values if clean_text(tag, 50)]
        else:
            item[field] = clean_text(value, 5000 if field == "description" else 500)
    item["id"] = clean_text(payload.get("id"), 100) or secrets.token_urlsafe(9)
    return item


def missing_required_fields(resource: str, item: dict) -> list[str]:
    return [field for field in RESOURCE_REQUIRED_FIELDS[resource] if not item.get(field)]


def required_fields_error(missing_fields: list[str]) -> str:
    field_labels = {"degree": "Degree or certificate", "institution": "institution name"}
    labels = [field_labels.get(field, field.capitalize()) for field in missing_fields]
    return f"{' and '.join(labels)} {'are' if len(labels) > 1 else 'is'} required."
