from pathlib import Path
from textwrap import dedent

from src.analyzers.openapi_analyzer import analyze_openapi_file
from src.rule_id_manager import assign_rule_ids
from src.dependency_resolver import resolve_dependencies


def test_openapi_rule_dependencies_and_entities(tmp_path):
    spec = dedent(
        """
        openapi: 3.0.0
        paths:
          /demo:
            post:
              requestBody:
                content:
                  application/json:
                    schema:
                      $ref: '#/components/schemas/Root'
                required: true
        components:
          schemas:
            Root:
              type: object
              required: [ child ]
              properties:
                child:
                  $ref: '#/components/schemas/Child'
            Child:
              type: object
              required:
                - name
                - tags
              properties:
                name:
                  type: string
                tags:
                  type: array
                  items:
                    $ref: '#/components/schemas/Tag'
            Tag:
              type: object
              required: [ code ]
              properties:
                code:
                  type: string
                kind:
                  type: string
                  enum: [ a, b ]
        """
    )

    spec_path = tmp_path / "spec.yml"
    spec_path.write_text(spec)

    rules = analyze_openapi_file(spec_path)
    assign_rule_ids(rules, "RULE-100")
    resolve_dependencies(rules)

    by_entity = {rule.endpoint_entity: rule for rule in rules}

    assert by_entity["Root"].depends_on_ids == set()
    assert by_entity["Root.child"].depends_on_ids == {"RULE-100"}
    assert by_entity["Root.child.name"].depends_on_ids == {"RULE-101"}
    assert by_entity["Root.child.tags"].depends_on_ids == {"RULE-101"}
    assert by_entity["Root.child.tags[]"].depends_on_ids == {"RULE-103"}
    assert by_entity["Root.child.tags[].code"].depends_on_ids == {"RULE-103"}
    assert by_entity["Root.child.tags[].kind"].depends_on_ids == {"RULE-103"}

