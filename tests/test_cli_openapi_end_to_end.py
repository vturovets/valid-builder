from src import cli


def test_cli_openapi_end_to_end(tmp_path):
    """Running the CLI on the sample OpenAPI file yields the golden CSV output."""

    output = tmp_path / "validation_rules.csv"

    exit_code = cli.main([
        "docs/openapi-spec - sample.yml",
        "--output",
        str(output),
    ])

    expected = (
        "Rule ID,Description,Source file,Lines,Endpoint,Endpoint entity,Depends on\n"
        "RULE-001,\"For the POST /v3/package/search/results endpoint, a application/json request body conforming to PackageSearchRequestParams MUST be provided; requests without a body are invalid.\",openapi-spec - sample.yml,19-26,/v3/package/search/results [POST],PackageSearchRequestParams,\n"
        "RULE-002,The PackageSearchRequestParams object MUST contain a 'from' property of type array.,openapi-spec - sample.yml,49-58,/v3/package/search/results [POST],PackageSearchRequestParams.from,RULE-001\n"
        "RULE-003,Each item in 'PackageSearchRequestParams.from[]' MUST satisfy: items must follow From.,openapi-spec - sample.yml,55-58,/v3/package/search/results [POST],PackageSearchRequestParams.from[],RULE-002\n"
        "RULE-004,The PackageSearchResponse object MUST contain a 'holidays' property.,openapi-spec - sample.yml,59-66,/v3/package/search/results [POST],PackageSearchResponse.holidays,RULE-001\n"
        "RULE-005,The From object MUST contain a 'code' property of type string.,openapi-spec - sample.yml,67-78,/v3/package/search/results [POST],PackageSearchRequestParams.from[].code,RULE-002\n"
        "RULE-006,The 'PackageSearchRequestParams.from[].type' field MUST be one of: AIRPORT. Any other value is invalid.,openapi-spec - sample.yml,76-78,/v3/package/search/results [POST],PackageSearchRequestParams.from[].type,RULE-002\n"
        "RULE-007,The Holidays object MUST contain a 'offers' property of type array.,openapi-spec - sample.yml,80-90,/v3/package/search/results [POST],PackageSearchResponse.holidays.offers,RULE-004\n"
        "RULE-008,Each item in 'PackageSearchResponse.holidays.offers[]' MUST satisfy: items must follow Offer.,openapi-spec - sample.yml,86-90,/v3/package/search/results [POST],PackageSearchResponse.holidays.offers[],RULE-007\n"
        "RULE-009,The Offer object MUST contain a 'productID' property of type string.,openapi-spec - sample.yml,91-99,/v3/package/search/results [POST],PackageSearchResponse.holidays.offers[].productID,RULE-007\n"
    )

    assert exit_code == 0
    assert output.read_text() == expected
