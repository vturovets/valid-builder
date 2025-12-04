from pathlib import Path

from src.analyzers.openapi_analyzer import analyze_openapi_file
from src.csv_writer import write_rules_csv
from src.dependency_resolver import resolve_dependencies
from src.rule_id_manager import assign_rule_ids


def test_sample_openapi_matches_expected_csv(tmp_path):
    openapi_path = Path("docs/openapi-spec - sample.yml")
    rules = analyze_openapi_file(openapi_path)

    assign_rule_ids(rules, "RULE-001")
    resolve_dependencies(rules)

    output_path = tmp_path / "validation_rules.csv"
    write_rules_csv(output_path, rules)

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

    assert output_path.read_text() == expected

