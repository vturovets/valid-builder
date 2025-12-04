from src.description import describe_kotlin_if_throw, describe_kotlin_require


def test_if_throw_mentions_condition_exception_and_message():
    result = describe_kotlin_if_throw(
        "the user ID is missing",
        exception="IllegalArgumentException",
        message='"User ID is required"',
    )

    assert "If the user ID is missing" in result
    assert "throws IllegalArgumentException" in result
    assert "message 'User ID is required'" in result
    assert result.endswith("."), "Description should end with a period"


def test_if_throw_defaults_to_generic_exception_phrase():
    result = describe_kotlin_if_throw("validation fails")

    assert result == "If validation fails, the code throws an exception."


def test_require_includes_condition_and_failure_message():
    result = describe_kotlin_require("payload.isValid()", message="invalid payload")

    assert result.startswith("The input must satisfy payload.isValid()")
    assert "call fails" in result
    assert "with 'invalid payload'" in result


def test_require_without_message_still_mentions_failure():
    result = describe_kotlin_require("userId > 0")

    assert result == "The input must satisfy userId > 0; otherwise the call fails."
