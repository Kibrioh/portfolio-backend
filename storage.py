"""JSON-backed persistence for portfolio content."""

from __future__ import annotations

import json

from flask import current_app

from .defaults import DEFAULT_CONTENT


def read_content() -> dict:
    """Read stored content and fill missing fields from the defaults."""
    data_file = current_app.config["DATA_FILE"]
    data_file.parent.mkdir(parents=True, exist_ok=True)
    if not data_file.exists():
        write_content(DEFAULT_CONTENT)

    try:
        stored = json.loads(data_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        stored = {}

    content = {**DEFAULT_CONTENT, **stored}
    for key, default_value in DEFAULT_CONTENT.items():
        if isinstance(default_value, list):
            stored_value = stored.get(key)
            content[key] = stored_value if isinstance(stored_value, list) else default_value
    content["profile"] = {**DEFAULT_CONTENT["profile"], **(stored.get("profile") or {})}
    return content


def write_content(content: dict) -> None:
    """Write content atomically so interrupted writes don't corrupt the JSON file."""
    data_file = current_app.config["DATA_FILE"]
    data_file.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = data_file.with_suffix(".tmp")
    temporary_file.write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary_file.replace(data_file)
