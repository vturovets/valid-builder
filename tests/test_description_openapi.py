from src.description import (
    describe_openapi_array_items,
    describe_openapi_enum,
    describe_openapi_request_body_required,
    describe_openapi_required_property,
)


def test_request_body_required_template_matches_sdd_language():
    result = describe_openapi_request_body_required(
        method="post",
        path="/v1/pets",
        media_type="application/json",
        schema="PetRequest",
    )

    assert result.startswith("For the POST /v1/pets endpoint")
    assert "request body conforming to PetRequest MUST be provided" in result
    assert "requests without a body are invalid" in result


def test_required_property_mentions_schema_field_and_type():
    description = describe_openapi_required_property("Pet", "name", type_hint="string")

    assert description == "The Pet object MUST contain a 'name' property of type string."


def test_enum_values_are_listed_and_strict():
    description = describe_openapi_enum("Pet.status", ["available", "pending", "sold"])

    assert "MUST be one of: available, pending, sold" in description
    assert description.endswith("Any other value is invalid.")


def test_array_item_requirement_is_explicit():
    description = describe_openapi_array_items("offers[]", "each offer must include an 'id'")

    assert description == "Each item in 'offers[]' MUST satisfy: each offer must include an 'id'."
