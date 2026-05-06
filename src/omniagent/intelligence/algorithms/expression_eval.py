"""Simple expression evaluator for Decision Graph conditions."""

from __future__ import annotations

import operator
import re
from typing import Any

OPERATORS: dict[str, Any] = {
    "==": operator.eq,
    "!=": operator.ne,
    "<=": operator.le,
    ">=": operator.ge,
    "<": operator.lt,
    ">": operator.gt,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
    "contains": lambda a, b: b in a if isinstance(a, (str, list)) else False,
}

# Order matters: check multi-char operators first
OPERATOR_TOKENS = sorted(OPERATORS.keys(), key=len, reverse=True)


def evaluate_expression(expr: str, variables: dict[str, Any]) -> bool:
    """
    Evaluate expressions like:
      "request.model == 'gpt-4' && context.cost < 5.0"
      "user.tier in ['premium', 'enterprise'] || request.priority > 3"
    """
    expr = expr.strip()
    if not expr:
        return True

    # Split on || first (lower precedence)
    or_parts = _split_logical(expr, "||")
    if len(or_parts) > 1:
        return any(evaluate_expression(part, variables) for part in or_parts)

    # Then split on &&
    and_parts = _split_logical(expr, "&&")
    if len(and_parts) > 1:
        return all(evaluate_expression(part, variables) for part in and_parts)

    return _eval_condition(expr, variables)


def _split_logical(expr: str, op: str) -> list[str]:
    parts = []
    depth = 0
    current = ""
    i = 0
    while i < len(expr):
        if expr[i] == "(":
            depth += 1
            current += expr[i]
        elif expr[i] == ")":
            depth -= 1
            current += expr[i]
        elif depth == 0 and expr[i:i + len(op)] == op:
            parts.append(current.strip())
            current = ""
            i += len(op)
            continue
        else:
            current += expr[i]
        i += 1
    if current.strip():
        parts.append(current.strip())
    return parts


def _eval_condition(condition: str, variables: dict[str, Any]) -> bool:
    condition = condition.strip()
    if condition.startswith("(") and condition.endswith(")"):
        return evaluate_expression(condition[1:-1], variables)

    for op_str in OPERATOR_TOKENS:
        separator = f" {op_str} "
        if separator in condition:
            parts = condition.split(separator, 1)
            left = _resolve_value(parts[0].strip(), variables)
            right = _resolve_value(parts[1].strip(), variables)
            try:
                return OPERATORS[op_str](left, right)
            except (TypeError, ValueError):
                return False

    return False


def _resolve_value(token: str, variables: dict[str, Any]) -> Any:
    if token.startswith("'") and token.endswith("'"):
        return token[1:-1]
    if token.startswith('"') and token.endswith('"'):
        return token[1:-1]
    if token.startswith("[") and token.endswith("]"):
        items = token[1:-1].split(",")
        return [_resolve_value(item.strip(), variables) for item in items if item.strip()]
    if token == "true":
        return True
    if token == "false":
        return False
    if token == "null" or token == "None":
        return None
    try:
        return int(token)
    except ValueError:
        pass
    try:
        return float(token)
    except ValueError:
        pass
    return _resolve_path(token, variables)


def _resolve_path(path: str, variables: dict[str, Any]) -> Any:
    parts = path.split(".")
    current: Any = variables
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current
