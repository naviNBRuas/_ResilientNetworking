import pytest
import jsonschema
from idl_contracts import load_schema, validate_data, get_schema_path

def test_load_retry_outcome_schema() -> None:
    schema = load_schema("retry_outcome")
    assert schema["title"] == "RetryOutcome"
    assert "attempts" in schema["properties"]

def test_load_transport_response_schema() -> None:
    schema = load_schema("transport_response")
    assert schema["title"] == "TransportResponse"
    assert "status" in schema["properties"]

def test_validate_retry_outcome_valid() -> None:
    data = {
        "attempts": 3,
        "result": {"foo": "bar"},
        "error": None,
        "duration": 1.5
    }
    # Should not raise
    validate_data(data, "retry_outcome")

def test_validate_retry_outcome_invalid() -> None:
    data = {
        "attempts": "three", # Should be integer
        "duration": 1.5
    }
    with pytest.raises(jsonschema.ValidationError):
        validate_data(data, "retry_outcome")

def test_validate_transport_response_valid() -> None:
    data = {
        "status": 200,
        "body": {"message": "ok"},
        "headers": {"content-type": "application/json"}
    }
    validate_data(data, "transport_response")

def test_validate_transport_response_missing_required() -> None:
    data = {
        "status": 200
        # missing body
    }
    with pytest.raises(jsonschema.ValidationError):
        validate_data(data, "transport_response")

def test_get_schema_path_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        get_schema_path("non_existent_schema")
