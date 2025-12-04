from __future__ import annotations

"""Human-friendly description templates for validation rules.

The functions here provide small, focused templates for Kotlin and OpenAPI
rule sources. They intentionally avoid heavy natural-language generation and
stick to deterministic phrasing that can be validated in tests.
"""

from typing import Iterable


def _clean_message(message: str | None) -> str | None:
    if message is None:
        return None
    cleaned = message.strip()
    if cleaned.startswith("\"") and cleaned.endswith("\"") and len(cleaned) >= 2:
        cleaned = cleaned[1:-1].strip()
    return cleaned


def describe_kotlin_if_throw(condition: str, *, exception: str | None = None, message: str | None = None) -> str:
    """Describe a Kotlin `if (...) { throw ... }` construct.

    - Always includes the condition.
    - Mentions the thrown exception type when provided.
    - Appends the exception message when present (cleaned of wrapping quotes).
    """

    cleaned_message = _clean_message(message)
    parts = [f"If {condition}, the code throws"]
    if exception:
        parts.append(exception)
    else:
        parts.append("an exception")

    description = " ".join(parts)
    if cleaned_message:
        description += f" with message '{cleaned_message}'"

    return description + "."


def describe_kotlin_require(condition: str, *, message: str | None = None) -> str:
    """Describe a `require(condition)` validation.

    The description asserts that the condition must hold and mentions failure if
    violated, optionally echoing the provided message.
    """

    cleaned_message = _clean_message(message)
    base = f"The input must satisfy {condition}; otherwise the call fails"
    if cleaned_message:
        base += f" with '{cleaned_message}'"
    return base + "."


def describe_openapi_request_body_required(method: str, path: str, media_type: str, schema: str) -> str:
    """Template for required request bodies in OpenAPI endpoints."""

    return (
        f"For the {method.upper()} {path} endpoint, a {media_type} request body "
        f"conforming to {schema} MUST be provided; requests without a body are invalid."
    )


def describe_openapi_required_property(schema: str, property_name: str, type_hint: str | None = None) -> str:
    """Template for required object properties."""

    requirement = f"The {schema} object MUST contain a '{property_name}' property"
    if type_hint:
        requirement += f" of type {type_hint}"
    return requirement + "."


def describe_openapi_enum(property_path: str, allowed_values: Iterable[str]) -> str:
    """Template for enum constraints."""

    values = ", ".join(allowed_values)
    return f"The '{property_path}' field MUST be one of: {values}. Any other value is invalid."


def describe_openapi_array_items(array_path: str, item_requirement: str) -> str:
    """Template for array item constraints."""

    return f"Each item in '{array_path}' MUST satisfy: {item_requirement}."
