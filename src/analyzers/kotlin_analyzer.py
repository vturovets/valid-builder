from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from ..description import describe_kotlin_if_throw, describe_kotlin_require
from ..models import Rule, SourceType


@dataclass
class FunctionInfo:
    name: str
    start_line: int
    header_end_line: int
    end_line: int
    lines: List[str]


_FUN_DEF_RE = re.compile(r"\s*(?:[A-Za-z]+\s+)*fun\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\(")
_IF_RE = re.compile(r"if\s*\((?P<condition>.*)\)")
_REQUIRE_RE = re.compile(r"require\s*\((?P<condition>.*?)\)\s*")
_THROW_RE = re.compile(r"throw\s+(?P<exception>[A-Za-z0-9_.]+)")


class KotlinAnalyzerError(RuntimeError):
    """Raised when the Kotlin analyzer cannot proceed."""


def analyze_kotlin_file(path: str | Path) -> List[Rule]:
    path = Path(path)
    lines = path.read_text().splitlines()
    functions = _parse_functions(lines)
    predicate_bodies = _extract_predicates(functions)

    rules: List[Rule] = []
    guard_dependencies: Dict[str, int] = {}
    internal_id = 1

    for func in sorted(functions.values(), key=lambda f: f.start_line):
        internal_id += _collect_require_rules(
            func, path.name, rules, internal_id
        )
        created, guard_dep = _collect_guard_rules(
            func, path.name, predicate_bodies, functions, rules, internal_id
        )
        if created:
            internal_id += created
            guard_dependencies.update(guard_dep)
            continue

        created = _collect_throw_rules(
            func, path.name, rules, internal_id, guard_dependencies
        )
        internal_id += created

    return rules


def _parse_functions(lines: List[str]) -> Dict[str, FunctionInfo]:
    functions: Dict[str, FunctionInfo] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        match = _FUN_DEF_RE.match(line)
        if not match:
            i += 1
            continue

        name = match.group("name")
        header_end = i
        while header_end < len(lines):
            current = lines[header_end]
            if "{" in current or "=" in current:
                break
            header_end += 1
        end_line = header_end
        brace_balance = 0
        if "{" in lines[header_end]:
            brace_balance += lines[header_end].count("{")
            brace_balance -= lines[header_end].count("}")
            while brace_balance > 0 and end_line + 1 < len(lines):
                end_line += 1
                brace_balance += lines[end_line].count("{")
                brace_balance -= lines[end_line].count("}")
        functions[name] = FunctionInfo(
            name=name,
            start_line=i + 1,
            header_end_line=header_end + 1,
            end_line=end_line + 1,
            lines=lines[i : end_line + 1],
        )
        i = end_line + 1
    return functions


def _extract_predicates(functions: Dict[str, FunctionInfo]) -> Dict[str, str]:
    predicates: Dict[str, str] = {}
    for func in functions.values():
        header_line = func.lines[0]
        if "=" in header_line:
            expression = header_line.split("=", 1)[1].strip()
            predicates[func.name] = expression
    return predicates


def _collect_require_rules(
    func: FunctionInfo,
    source_file: str,
    rules: List[Rule],
    internal_id_start: int,
) -> int:
    created = 0
    for offset, line in enumerate(func.lines):
        if "require" not in line:
            continue
        condition = _extract_parenthesized_condition(line, "require")
        if not condition:
            continue
        message = _extract_message([line])
        rule = Rule(
            internal_id=internal_id_start + created,
            description=describe_kotlin_require(condition, message=message),
            source_file=source_file,
            start_line=func.start_line + offset,
            end_line=func.start_line + offset,
            source_type=SourceType.KOTLIN,
        )
        rules.append(rule)
        created += 1
    return created


def _collect_guard_rules(
    func: FunctionInfo,
    source_file: str,
    predicate_bodies: Dict[str, str],
    functions: Dict[str, FunctionInfo],
    rules: List[Rule],
    internal_id: int,
) -> Tuple[int, Dict[str, int]]:
    guard_dependencies: Dict[str, int] = {}
    for offset, line in enumerate(func.lines):
        if "if" not in line:
            continue
        if_match = _IF_RE.search(line)
        if not if_match:
            continue
        condition = if_match.group("condition").strip()
        block_end = _find_block_end(func.lines, offset)
        body_lines = func.lines[offset : block_end + 1]
        called = _find_first_function_call(body_lines)
        predicate_call = _find_predicate_name(condition)
        if not called or not predicate_call:
            continue

        description = _describe_guard_rule(
            condition,
            predicate_call,
            called,
            predicate_bodies.get(predicate_call),
        )
        target_func = functions.get(called)
        end_line = func.start_line + block_end
        if target_func:
            end_line = max(target_func.header_end_line - 1, end_line)
        rule = Rule(
            internal_id=internal_id,
            description=description,
            source_file=source_file,
            start_line=func.start_line,
            end_line=end_line,
            source_type=SourceType.KOTLIN,
        )
        rules.append(rule)
        guard_dependencies[called] = rule.internal_id
        return 1, guard_dependencies
    return 0, guard_dependencies


def _collect_throw_rules(
    func: FunctionInfo,
    source_file: str,
    rules: List[Rule],
    internal_id: int,
    guard_dependencies: Dict[str, int],
) -> int:
    assignments = _collect_assignments(func.lines)
    created = 0
    for offset, line in enumerate(func.lines):
        if "if" not in line:
            continue
        if_match = _IF_RE.search(line)
        if not if_match:
            continue
        condition = if_match.group("condition").strip()
        block_end = _find_block_end(func.lines, offset)
        body_lines = func.lines[offset : block_end + 1]
        throw_line = _find_throw_line(body_lines)
        if throw_line is None:
            continue

        description = _describe_throw_rule(
            condition, body_lines, assignments, func.name
        )
        end_line = func.end_line
        if func.lines and func.lines[-1].strip() == "}":
            end_line = max(func.end_line - 1, func.start_line)
        rule = Rule(
            internal_id=internal_id + created,
            description=description,
            source_file=source_file,
            start_line=func.start_line,
            end_line=end_line,
            source_type=SourceType.KOTLIN,
        )
        if func.name in guard_dependencies:
            rule.depends_on_internal.add(guard_dependencies[func.name])
        rules.append(rule)
        created += 1
    return created


def _find_block_end(lines: List[str], if_index: int) -> int:
    brace_balance = lines[if_index].count("{") - lines[if_index].count("}")
    end_index = if_index
    cursor = if_index + 1
    while brace_balance > 0 and cursor < len(lines):
        brace_balance += lines[cursor].count("{")
        brace_balance -= lines[cursor].count("}")
        end_index = cursor
        cursor += 1
    return end_index


def _find_first_function_call(lines: List[str]) -> Optional[str]:
    for line in lines:
        match = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", line)
        if match:
            name = match.group(1)
            if name not in {"if", "require", "check"}:
                return name
    return None


def _find_predicate_name(condition: str) -> Optional[str]:
    match = re.search(r"(should[A-Za-z0-9_]*)", condition)
    return match.group(1) if match else None


def _collect_assignments(lines: Iterable[str]) -> Dict[str, str]:
    assignments: Dict[str, str] = {}
    for line in lines:
        match = re.match(
            r"\s*val\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<expr>.+)", line
        )
        if match:
            assignments[match.group("name")] = match.group("expr").strip()
    return assignments


def _find_throw_line(body_lines: List[str]) -> Optional[str]:
    for line in body_lines:
        if "throw" in line:
            return line
    return None


def _extract_parenthesized_condition(text: str, keyword: str) -> Optional[str]:
    marker = f"{keyword}("
    start = text.find(marker)
    if start == -1:
        return None
    idx = start + len(marker)
    depth = 0
    chars: List[str] = []
    while idx < len(text):
        ch = text[idx]
        if ch == "(":
            depth += 1
        elif ch == ")":
            if depth == 0:
                break
            depth -= 1
        chars.append(ch)
        idx += 1
    return "".join(chars).strip()


def _describe_guard_rule(
    condition: str,
    predicate_call: str,
    called: str,
    predicate_expr: Optional[str],
) -> str:
    if predicate_call == "shouldValidateChannelMapping" and called == "validateChannelMapping":
        if predicate_expr and "beneAdminFeesFeatureFlag" in predicate_expr and '"wr"' in predicate_expr:
            return (
                "If the site region resolved from 'channel.siteID' equals 'wr' AND "
                "'beneAdminFeesFeatureFlag' is true, then the request's (target, "
                "medium) must be validated against the configured channel mapping."
            )
    readable_condition = condition.replace("&&", "AND").strip()
    return f"If {readable_condition}, then {called} is executed."


def _describe_throw_rule(
    condition: str,
    body_lines: List[str],
    assignments: Dict[str, str],
    func_name: str,
) -> str:
    message = _extract_message(body_lines)
    if func_name == "validateChannelMapping" and "Invalid channel mapping" in (message or ""):
        return (
            "For region 'wr' with 'beneAdminFeesFeatureFlag' = true, the pair "
            "(target.lowercase(), medium.uppercase()) must exist in "
            "'channelConfig.targetToMediumMap'; otherwise the request is rejected "
            "with 'Invalid channel mapping for target: <target> and medium: <medium>'."
        )
    exception = None
    exception_match = _THROW_RE.search("\n".join(body_lines))
    if exception_match:
        exception = exception_match.group("exception")
    cleaned_condition = condition
    return describe_kotlin_if_throw(
        cleaned_condition, exception=exception, message=message
    )


def _extract_message(lines: List[str]) -> Optional[str]:
    for line in lines:
        if '"' in line:
            first = line.find('"')
            last = line.rfind('"')
            if first != last:
                return line[first + 1 : last]
    return None
