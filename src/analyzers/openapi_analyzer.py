from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from src.description import (
    describe_openapi_array_items,
    describe_openapi_enum,
    describe_openapi_request_body_required,
    describe_openapi_required_property,
)
from src.models import Rule, SourceType


class OpenAPIAnalyzerError(RuntimeError):
    """Raised when the OpenAPI analyzer cannot proceed."""


@dataclass
class YamlNode:
    value: object
    start_line: int
    end_line: int


def analyze_openapi_file(path: str | Path) -> List[Rule]:
    path = Path(path)
    root = _parse_yaml_with_lines(path.read_text())

    if not isinstance(root.value, dict):
        raise OpenAPIAnalyzerError("Root YAML node must be a mapping")

    schemas = _extract_schemas(root)
    rules: List[Rule] = []
    internal_id = 1

    # Process endpoints and request/response schemas
    paths_node = _get_mapping_node(root, "paths")
    if paths_node:
        for endpoint_path, endpoint_node in _iter_mapping(paths_node):
            methods_node = endpoint_node
            if not isinstance(methods_node.value, dict):
                continue
            for method, method_node in _iter_mapping(methods_node):
                if method.lower() not in {"get", "post", "put", "delete", "patch"}:
                    continue
                endpoint_str = f"{endpoint_path} [{method.upper()}]"
                created, internal_id = _analyze_method(
                    method_node,
                    path.name,
                    endpoint_str,
                    schemas,
                    internal_id,
                    rules,
                )
                internal_id = created

    return rules


def _analyze_method(
    method_node: YamlNode,
    source_file: str,
    endpoint_str: str,
    schemas: Dict[str, YamlNode],
    internal_id: int,
    rules: List[Rule],
) -> Tuple[int, int]:
    current_internal = internal_id
    request_body_node = _get_mapping_node(method_node, "requestBody")
    request_dep: Optional[int] = None

    if request_body_node:
        required_node = _get_scalar_node(request_body_node, "required")
        content_node = _get_mapping_node(request_body_node, "content")
        media_type, schema_ref = _first_schema_ref(content_node)
        if required_node and required_node.value is True and schema_ref:
            description = describe_openapi_request_body_required(
                method=endpoint_str.split()[1].strip("[]"),
                path=endpoint_str.split()[0],
                media_type=media_type or "request body",
                schema=schema_ref,
            )
            rule = Rule(
                internal_id=current_internal,
                description=description,
                source_file=source_file,
                start_line=request_body_node.start_line,
                end_line=request_body_node.end_line,
                source_type=SourceType.OPENAPI,
                endpoint=endpoint_str,
                endpoint_entity=schema_ref,
            )
            rules.append(rule)
            request_dep = rule.internal_id
            current_internal += 1

            if schema_ref in schemas:
                current_internal = _analyze_schema(
                    schema_ref,
                    schemas[schema_ref],
                    source_file,
                    rules,
                    current_internal,
                    endpoint=endpoint_str,
                    base_entity=schema_ref,
                    depends_on=request_dep,
                    schemas=schemas,
                )

    responses_node = _get_mapping_node(method_node, "responses")
    if responses_node:
        for status_code, response_node in _iter_mapping(responses_node):
            content_node = _get_mapping_node(response_node, "content")
            _, schema_ref = _first_schema_ref(content_node)
            if not schema_ref or schema_ref not in schemas:
                continue
            current_internal = _analyze_schema(
                schema_ref,
                schemas[schema_ref],
                source_file,
                rules,
                current_internal,
                endpoint=endpoint_str,
                base_entity=schema_ref,
                depends_on=request_dep,
                schemas=schemas,
            )

    return current_internal, current_internal


def _analyze_schema(
    name: str,
    node: YamlNode,
    source_file: str,
    rules: List[Rule],
    internal_id: int,
    *,
    endpoint: Optional[str],
    base_entity: str,
    depends_on: Optional[int],
    schemas: Dict[str, YamlNode],
) -> int:
    current_internal = internal_id
    required_node = _get_sequence_node(node, "required")
    required_fields: List[str] = []
    if required_node:
        for item in required_node.value:
            if isinstance(item, YamlNode):
                required_fields.append(item.value)
            else:
                required_fields.append(item)

    properties_node = _get_mapping_node(node, "properties")
    if properties_node and isinstance(properties_node.value, dict):
        for prop_name, prop_node in _iter_mapping(properties_node):
            if prop_name not in required_fields:
                continue
            type_hint = _get_scalar_value(prop_node, "type")
            description = describe_openapi_required_property(
                name,
                prop_name,
                type_hint=type_hint,
            )
            endpoint_entity = f"{base_entity}.{prop_name}"
            rule = Rule(
                internal_id=current_internal,
                description=description,
                source_file=source_file,
                start_line=node.start_line,
                end_line=node.end_line,
                source_type=SourceType.OPENAPI,
                endpoint=endpoint,
                endpoint_entity=endpoint_entity,
            )
            if depends_on is not None:
                rule.depends_on_internal.add(depends_on)
            rules.append(rule)
            current_internal += 1
            prop_dep = rule.internal_id

            items_ref = _get_ref_from_items(prop_node)
            if items_ref:
                array_rule = Rule(
                    internal_id=current_internal,
                    description=describe_openapi_array_items(
                        f"{endpoint_entity}[]", f"items must follow {items_ref}",
                    ),
                    source_file=source_file,
                    start_line=prop_node.start_line,
                    end_line=prop_node.end_line,
                    source_type=SourceType.OPENAPI,
                    endpoint=endpoint,
                    endpoint_entity=f"{endpoint_entity}[]",
                )
                array_rule.depends_on_internal.add(prop_dep)
                rules.append(array_rule)
                current_internal += 1
                if items_ref in schemas:
                    current_internal = _analyze_schema(
                        items_ref,
                        schemas[items_ref],
                        source_file,
                        rules,
                        current_internal,
                        endpoint=endpoint,
                        base_entity=f"{endpoint_entity}[]",
                        depends_on=prop_dep,
                        schemas=schemas,
                    )
            else:
                ref = _normalize_ref(_get_scalar_value(prop_node, "$ref"))
                if ref and ref in schemas:
                    current_internal = _analyze_schema(
                        ref,
                        schemas[ref],
                        source_file,
                        rules,
                        current_internal,
                        endpoint=endpoint,
                        base_entity=endpoint_entity,
                        depends_on=prop_dep,
                        schemas=schemas,
                    )

    # Enumerations
    if properties_node and isinstance(properties_node.value, dict):
        for prop_name, prop_node in _iter_mapping(properties_node):
            enum_node = _get_sequence_node(prop_node, "enum")
            if not enum_node:
                continue
            values: List[str] = []
            for item in enum_node.value:
                if isinstance(item, YamlNode):
                    values.append(item.value)
                else:
                    values.append(str(item))
            description = describe_openapi_enum(f"{base_entity}.{prop_name}", values)
            enum_rule = Rule(
                internal_id=current_internal,
                description=description,
                source_file=source_file,
                start_line=prop_node.start_line,
                end_line=prop_node.end_line,
                source_type=SourceType.OPENAPI,
                endpoint=endpoint,
                endpoint_entity=f"{base_entity}.{prop_name}",
            )
            if depends_on is not None:
                enum_rule.depends_on_internal.add(depends_on)
            rules.append(enum_rule)
            current_internal += 1

    return current_internal


def _extract_schemas(root: YamlNode) -> Dict[str, YamlNode]:
    schemas: Dict[str, YamlNode] = {}
    components = _get_mapping_node(root, "components")
    if not components:
        return schemas
    schemas_node = _get_mapping_node(components, "schemas")
    if not schemas_node:
        return schemas
    for name, node in _iter_mapping(schemas_node):
        schemas[name] = node
    return schemas


def _first_schema_ref(content_node: Optional[YamlNode]) -> Tuple[Optional[str], Optional[str]]:
    if not content_node or not isinstance(content_node.value, dict):
        return None, None
    for media_type, node in _iter_mapping(content_node):
        schema_node = _get_mapping_node(node, "schema")
        ref = _normalize_ref(_get_scalar_value(schema_node, "$ref"))
        if ref:
            return media_type, ref
    return None, None


def _get_ref_from_items(prop_node: YamlNode) -> Optional[str]:
    items_node = _get_mapping_node(prop_node, "items")
    if not items_node:
        return None
    ref = _normalize_ref(_get_scalar_value(items_node, "$ref"))
    if ref:
        return ref
    all_of_node = _get_sequence_node(items_node, "allOf")
    if all_of_node and isinstance(all_of_node.value, list):
        for candidate in all_of_node.value:
            if not isinstance(candidate, YamlNode):
                continue
            candidate_ref = _normalize_ref(_get_scalar_value(candidate, "$ref"))
            if candidate_ref:
                return candidate_ref
    return None


def _get_mapping_node(node: YamlNode, key: str) -> Optional[YamlNode]:
    if not isinstance(node.value, dict):
        return None
    return node.value.get(key)


def _get_sequence_node(node: YamlNode, key: str) -> Optional[YamlNode]:
    child = _get_mapping_node(node, key)
    if child and isinstance(child.value, list):
        return child
    return None


def _get_scalar_node(node: YamlNode, key: str) -> Optional[YamlNode]:
    child = _get_mapping_node(node, key)
    if child and not isinstance(child.value, (dict, list)):
        return child
    return None


def _get_scalar_value(node: Optional[YamlNode], key: str) -> Optional[str]:
    if not node:
        return None
    scalar = _get_scalar_node(node, key)
    if scalar:
        return scalar.value
    return None


def _normalize_ref(ref: Optional[str]) -> Optional[str]:
    if ref is None:
        return None
    if "/" in ref:
        return ref.rsplit("/", 1)[-1]
    return ref


def _iter_mapping(node: YamlNode) -> Iterable[Tuple[str, YamlNode]]:
    if not isinstance(node.value, dict):
        return []
    return node.value.items()


# ----------------------
# Minimal YAML parser
# ----------------------


def _parse_yaml_with_lines(text: str) -> YamlNode:
    lines = text.splitlines()
    node, _ = _parse_block(lines, 0, 0)
    if node is None:
        raise OpenAPIAnalyzerError("Empty YAML content")
    return node


def _parse_block(lines: List[str], index: int, indent: int) -> Tuple[Optional[YamlNode], int]:
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index >= len(lines):
        return None, index

    first_line = lines[index]
    first_indent = _leading_spaces(first_line)
    if first_indent < indent:
        return None, index

    use_list = first_line.strip().startswith("- ")
    if use_list:
        return _parse_list(lines, index, indent)
    return _parse_mapping(lines, index, indent)


def _parse_list(lines: List[str], index: int, indent: int) -> Tuple[YamlNode, int]:
    items: List[YamlNode] = []
    while index < len(lines):
        line = lines[index]
        stripped_line = line.strip()
        if not stripped_line or stripped_line in {"}", "]"}:
            index += 1
            continue
        current_indent = _leading_spaces(line)
        if current_indent < indent:
            break
        stripped = line.strip()
        if not stripped.startswith("- "):
            break
        start_line = index + 1
        content = stripped[2:]
        if content == "":
            child, index = _parse_block(lines, index + 1, current_indent + 2)
            if child:
                child.start_line = start_line
                items.append(child)
            continue
        if ":" in content:
            key, value_part = content.split(":", 1)
            key = key.strip().strip("\"\'")
            if value_part.strip() and value_part.strip() not in "{}":
                value_node = _parse_scalar(value_part.strip(), start_line)
                mapping = {key: value_node}
                end_line = value_node.end_line
                items.append(YamlNode(mapping, start_line, end_line))
                index += 1
            else:
                child, index = _parse_block(lines, index + 1, current_indent + 2)
                if child is None:
                    child = YamlNode(None, start_line, start_line)
                mapping = {key: child}
                end_line = child.end_line
                items.append(YamlNode(mapping, start_line, end_line))
            continue
        scalar = _parse_scalar(content, start_line)
        items.append(scalar)
        index += 1

    start = items[0].start_line if items else index + 1
    end = items[-1].end_line if items else start
    return YamlNode(items, start, end), index


def _parse_mapping(lines: List[str], index: int, indent: int) -> Tuple[YamlNode, int]:
    mapping: Dict[str, YamlNode] = {}
    start_line = index + 1
    last_line = start_line

    while index < len(lines):
        line = lines[index]
        stripped_line = line.strip()
        if not stripped_line or stripped_line in {"}", "]"}:
            index += 1
            continue
        current_indent = _leading_spaces(line)
        if current_indent < indent:
            break
        if line.strip().startswith("- ") and current_indent == indent:
            break
        stripped = line.strip()
        if ":" not in stripped:
            index += 1
            continue
        key, value_part = stripped.split(":", 1)
        key = key.strip().strip("\"\'")
        line_no = index + 1
        if value_part.strip() and value_part.strip() not in "{}":
            value_node = _parse_scalar(value_part.strip(), line_no)
            mapping[key] = value_node
            last_line = value_node.end_line
            index += 1
        else:
            child, index = _parse_block(lines, index + 1, current_indent + 2)
            if child is None:
                child = YamlNode(None, line_no, line_no)
            child.start_line = line_no
            mapping[key] = child
            last_line = child.end_line

    end_line = last_line
    if mapping:
        end_line = max(node.end_line for node in mapping.values())
    return YamlNode(mapping, start_line, end_line), index


def _parse_scalar(text: str, line_no: int) -> YamlNode:
    value: object = text
    if (text.startswith("\"") and text.endswith("\"")) or (
        text.startswith("'") and text.endswith("'")
    ):
        text = text[1:-1]
        value = text
    if text.lower() == "true":
        value = True
    elif text.lower() == "false":
        value = False
    elif text.startswith("[") or text.startswith("{"):
        try:
            value = json.loads(text.replace("'", '"'))
        except json.JSONDecodeError:
            if text.startswith("[") and text.endswith("]"):
                inner = text[1:-1].strip()
                if inner:
                    parts = [part.strip() for part in inner.replace(" ", ",").split(",")]
                    value = [part for part in parts if part]
                else:
                    value = []
            else:
                value = text
    return YamlNode(value, line_no, line_no)


def _leading_spaces(line: str) -> int:
    return len(line) - len(line.lstrip(" "))

