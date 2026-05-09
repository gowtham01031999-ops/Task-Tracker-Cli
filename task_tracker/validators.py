"""Validation and normalization helpers."""

from typing import Any

from task_tracker.exceptions import SchemaValidationError, UsageError


def normalize_description(description: str) -> str:
    """Trim and validate a task description."""

    cleaned = description.strip()
    if not cleaned:
        raise UsageError("Description must not be empty.")
    return cleaned


def require_integer(value: Any, field_name: str) -> int:
    """Ensure a payload field is a positive integer."""

    if not isinstance(value, int) or value < 1:
        raise SchemaValidationError(f"{field_name} must be a positive integer.")
    return value


def require_non_empty_string(value: Any, field_name: str) -> str:
    """Ensure a payload field is a non-empty string."""

    if not isinstance(value, str) or not value.strip():
        raise SchemaValidationError(f"{field_name} must be a non-empty string.")
    return value
