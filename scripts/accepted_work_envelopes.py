#!/usr/bin/env python3
"""Offline validator and canonicalizer for accepted-work envelopes v0.1.0."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import tempfile
import unicodedata
from collections.abc import Iterable
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

SCHEMA_ID = "reviewed-change-orchestration.accepted-work-envelopes"
SCHEMA_VERSION = "0.1.0"
CONTEXT_ID = "reviewed-change-orchestration.accepted-work-envelope-context"
RESULT_ID = "reviewed-change-orchestration.accepted-work-envelope-validation-result"
KINDS = frozenset(("AcceptedBundle", "AttemptBinding", "ReviewedItemHistory", "CandidateBundle"))
MAX_DOCUMENT_BYTES = 8 * 1024 * 1024
MAX_DEPTH = 64
MAX_CONTAINER_ENTRIES = 10_000
MAX_STRING_BYTES = 1024 * 1024
MAX_LOCATOR_BYTES = 2048
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "accepted-work-envelopes-v0.1.0.schema.json"
_SCHEMA: dict[str, Any] | None = None
ID_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
NAME_RE = re.compile(r"[a-z][a-z0-9.-]{0,63}\Z")
NAMESPACED_RE = re.compile(r"[a-z][a-z0-9.-]{0,63}:[a-z][a-z0-9._-]{0,127}\Z")
SCHEMA_PATTERNS = {
    "^sha256:[0-9a-f]{64}$": re.compile(r"sha256:[0-9a-f]{64}\Z"),
    "^[a-z][a-z0-9.-]{0,63}$": re.compile(r"[a-z][a-z0-9.-]{0,63}\Z"),
    "^[a-z][a-z0-9.-]{0,63}:[a-z][a-z0-9._-]{0,127}$": re.compile(r"[a-z][a-z0-9.-]{0,63}:[a-z][a-z0-9._-]{0,127}\Z"),
}


class ContractError(Exception):
    pass


class DuplicateNameError(ContractError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def pointer_part(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def diagnostic(path: str, code: str, related_ids: Iterable[str] = ()) -> dict[str, Any]:
    stable_ids = sorted({value for value in related_ids if isinstance(value, str) and ID_RE.fullmatch(value)})
    return {"code": code, "instance_path": path or "/", "related_ids": stable_ids}


def add(errors: list[dict[str, Any]], path: str, code: str, related_ids: Iterable[str] = ()) -> None:
    errors.append(diagnostic(path, code, related_ids))


def sort_errors(errors: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(errors, key=lambda item: (item["instance_path"], item["code"], item["related_ids"]))


def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateNameError("duplicate-object-name")
        result[key] = value
    return result


def parse_json(raw: bytes) -> Any:
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise ContractError("document-too-large")
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=no_duplicates,
                          parse_constant=lambda _value: (_ for _ in ()).throw(ContractError("non-finite-number")))
    except UnicodeDecodeError as error:
        raise ContractError("invalid-utf8") from error
    except json.JSONDecodeError as error:
        raise ContractError("invalid-json") from error


def parser_errors(value: Any) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    stack: list[tuple[Any, str, int]] = [(value, "", 1)]
    while stack:
        current, path, depth = stack.pop()
        if depth > MAX_DEPTH:
            add(errors, path, "depth-exceeded")
            continue
        if isinstance(current, str):
            if len(current.encode("utf-8")) > MAX_STRING_BYTES:
                add(errors, path, "string-too-large")
            if unicodedata.normalize("NFC", current) != current:
                add(errors, path, "string-not-nfc")
        elif isinstance(current, float):
            if not math.isfinite(current) or not current.is_integer():
                add(errors, path, "non-integer-number")
        elif isinstance(current, dict):
            if len(current) > MAX_CONTAINER_ENTRIES:
                add(errors, path, "container-too-large")
            for key, child in reversed(list(current.items())):
                stack.append((child, path + "/" + pointer_part(key), depth + 1))
        elif isinstance(current, list):
            if len(current) > MAX_CONTAINER_ENTRIES:
                add(errors, path, "container-too-large")
            for index in range(len(current) - 1, -1, -1):
                stack.append((current[index], path + "/" + str(index), depth + 1))
    return errors


def exact_object(value: Any, fields: set[str], errors: list[dict[str, Any]], path: str, code: str) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        add(errors, path, "required-object")
        return None
    if set(value) != fields:
        add(errors, path, code)
    return value


def required_string(value: Any, errors: list[dict[str, Any]], path: str) -> bool:
    if not isinstance(value, str) or not value:
        add(errors, path, "required-string")
        return False
    return True


def identifier(value: Any, errors: list[dict[str, Any]], path: str, code: str = "invalid-content-id") -> bool:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        add(errors, path, code)
        return False
    return True


def nonnegative_integer(value: Any, errors: list[dict[str, Any]], path: str) -> bool:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        add(errors, path, "non-negative-integer")
        return False
    return True


def string_set(value: Any, errors: list[dict[str, Any]], path: str, *, namespaced: bool = False) -> list[str]:
    if not isinstance(value, list):
        add(errors, path, "required-array")
        return []
    pattern = NAMESPACED_RE if namespaced else None
    if not all(isinstance(entry, str) and entry and (pattern is None or pattern.fullmatch(entry)) for entry in value):
        add(errors, path, "invalid-namespaced-identifier" if namespaced else "invalid-string-set")
        return []
    if value != sorted(set(value)):
        add(errors, path, "unsorted-or-duplicate-set")
    return list(value)


def validate_locator(value: Any, errors: list[dict[str, Any]], path: str) -> None:
    locator = exact_object(value, {"scheme", "value"}, errors, path, "unknown-or-missing-locator-field")
    if locator is None:
        return
    scheme, text = locator.get("scheme"), locator.get("value")
    if not isinstance(scheme, str) or not NAME_RE.fullmatch(scheme):
        add(errors, path + "/scheme", "invalid-locator-scheme")
    if not isinstance(text, str) or not text:
        add(errors, path + "/value", "required-string")
        return
    if len(text.encode("utf-8")) > MAX_LOCATOR_BYTES:
        add(errors, path + "/value", "locator-value-too-large")
    if any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in text):
        add(errors, path + "/value", "locator-value-control-or-whitespace")
    if scheme == "uri":
        try:
            parsed = urlsplit(text, allow_fragments=True)
            malformed_userinfo = parsed.username is not None or parsed.password is not None
        except ValueError:
            add(errors, path + "/value", "invalid-uri")
            return
        parsed_scheme = parsed.scheme.decode("ascii") if isinstance(parsed.scheme, bytes) else parsed.scheme
        if not parsed_scheme or not NAME_RE.fullmatch(parsed_scheme):
            add(errors, path + "/value", "invalid-uri-scheme")
        if malformed_userinfo:
            add(errors, path + "/value", "uri-userinfo-forbidden")


def validate_reference(value: Any, errors: list[dict[str, Any]], path: str) -> None:
    reference = exact_object(value, {"locator", "media_type", "byte_length", "sha256"}, errors, path, "unknown-or-missing-reference-field")
    if reference is None:
        return
    validate_locator(reference.get("locator"), errors, path + "/locator")
    required_string(reference.get("media_type"), errors, path + "/media_type")
    nonnegative_integer(reference.get("byte_length"), errors, path + "/byte_length")
    identifier(reference.get("sha256"), errors, path + "/sha256")


def validate_authority(value: Any, errors: list[dict[str, Any]], path: str) -> None:
    authority = exact_object(value, {"authority_id", "authority_scheme", "subject", "decision_id", "locator"}, errors, path, "unknown-or-missing-authority-field")
    if authority is None:
        return
    for field in ("authority_id", "authority_scheme", "subject", "decision_id"):
        required_string(authority.get(field), errors, path + "/" + field)
    validate_locator(authority.get("locator"), errors, path + "/locator")


def normalized_path(value: Any, errors: list[dict[str, Any]], path: str) -> str | None:
    if not isinstance(value, str):
        add(errors, path, "invalid-repository-path")
        return None
    segments = value.split("/")
    if not value or value.startswith("/") or "\\" in value or "\x00" in value or "" in segments or any(segment in {".", ".."} for segment in segments):
        add(errors, path, "invalid-repository-path")
        return None
    return value


def validate_paths(value: Any, errors: list[dict[str, Any]], path: str) -> list[tuple[str, str]]:
    if not isinstance(value, list):
        add(errors, path, "required-array")
        return []
    result: list[tuple[str, str]] = []
    for index, raw in enumerate(value):
        grant = exact_object(raw, {"path", "scope"}, errors, path + "/" + str(index), "unknown-or-missing-path-field")
        if grant is None:
            continue
        claim = normalized_path(grant.get("path"), errors, path + "/" + str(index) + "/path")
        scope = grant.get("scope")
        if scope not in {"file", "tree"}:
            add(errors, path + "/" + str(index) + "/scope", "invalid-path-scope")
        if claim is not None and scope in {"file", "tree"}:
            if (claim, scope) in result:
                add(errors, path + "/" + str(index), "duplicate-path-grant")
            result.append((claim, scope))
    return result


def path_is_within(selected: tuple[str, str], granted: tuple[str, str]) -> bool:
    selected_path, _selected_scope = selected
    granted_path, granted_scope = granted
    return selected_path == granted_path or (granted_scope == "tree" and selected_path.startswith(granted_path + "/"))


def overlaps(left: str, right: str) -> bool:
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


def validate_commit_point(value: Any, errors: list[dict[str, Any]], path: str) -> None:
    point = exact_object(value, {"commit", "tree"}, errors, path, "unknown-or-missing-commit-point-field")
    if point is None:
        return
    required_string(point.get("commit"), errors, path + "/commit")
    required_string(point.get("tree"), errors, path + "/tree")


def validate_projection(value: Any, errors: list[dict[str, Any]], path: str, body: dict[str, Any]) -> None:
    projection = exact_object(value, {"reference", "accepted_bundle_id", "run_id", "final_tree"}, errors, path, "unknown-or-missing-projection-field")
    if projection is None:
        return
    validate_reference(projection.get("reference"), errors, path + "/reference")
    identifier(projection.get("accepted_bundle_id"), errors, path + "/accepted_bundle_id")
    required_string(projection.get("run_id"), errors, path + "/run_id")
    required_string(projection.get("final_tree"), errors, path + "/final_tree")
    assembled_tip = body.get("assembled_tip")
    expected_tree = assembled_tip.get("tree") if isinstance(assembled_tip, dict) else None
    if projection.get("accepted_bundle_id") != body.get("accepted_bundle_id") or projection.get("run_id") != body.get("run_id") or projection.get("final_tree") != expected_tree:
        add(errors, path, "projection-binding-mismatch")


def validate_accepted(body: dict[str, Any], errors: list[dict[str, Any]]) -> None:
    fields = {"repository_id", "repository_capabilities", "repository_actions", "membership", "items", "dependencies"}
    if set(body) != fields:
        add(errors, "/body", "unknown-or-missing-body-field")
    required_string(body.get("repository_id"), errors, "/body/repository_id")
    ceiling_capabilities = string_set(body.get("repository_capabilities"), errors, "/body/repository_capabilities", namespaced=True)
    ceiling_actions = string_set(body.get("repository_actions"), errors, "/body/repository_actions", namespaced=True)
    raw_items = body.get("items")
    items: list[Any] = raw_items if isinstance(raw_items, list) else []
    if not isinstance(raw_items, list):
        add(errors, "/body/items", "required-array")
    item_ids: list[str] = []
    item_paths: list[tuple[str, str, str]] = []
    authority_ids: set[str] = set()
    evidence_ids: set[str] = set()
    requirement_ids: set[str] = set()
    for index, raw in enumerate(items):
        path = "/body/items/" + str(index)
        item_fields = {"item_id", "authority", "accepted_source", "accepted_outcomes", "preserved_behavior", "exclusions", "controls", "paths", "capabilities", "actions", "verification_obligations", "requirements"}
        item = exact_object(raw, item_fields, errors, path, "unknown-or-missing-item-field")
        if item is None:
            continue
        item_id = item.get("item_id")
        if isinstance(item_id, str) and required_string(item_id, errors, path + "/item_id"):
            item_ids.append(item_id)
        validate_authority(item.get("authority"), errors, path + "/authority")
        validate_reference(item.get("accepted_source"), errors, path + "/accepted_source")
        authority = item.get("authority")
        accepted_source = item.get("accepted_source")
        if isinstance(authority, dict) and isinstance(authority.get("authority_id"), str):
            if authority["authority_id"] in authority_ids:
                add(errors, path + "/authority/authority_id", "duplicate-authority-id")
            authority_ids.add(authority["authority_id"])
        if isinstance(accepted_source, dict) and isinstance(accepted_source.get("sha256"), str):
            if accepted_source["sha256"] in evidence_ids:
                add(errors, path + "/accepted_source/sha256", "duplicate-evidence-id")
            evidence_ids.add(accepted_source["sha256"])
        for field in ("accepted_outcomes", "preserved_behavior", "exclusions", "controls", "verification_obligations", "requirements"):
            values = string_set(item.get(field), errors, path + "/" + field)
            if field == "requirements":
                for requirement_id in values:
                    if requirement_id in requirement_ids:
                        add(errors, path + "/requirements", "duplicate-requirement-id")
                    requirement_ids.add(requirement_id)
        item_grants = validate_paths(item.get("paths"), errors, path + "/paths")
        item_paths.extend((item_id, claim, scope) for claim, scope in item_grants if isinstance(item_id, str))
        capabilities = string_set(item.get("capabilities"), errors, path + "/capabilities", namespaced=True)
        actions = string_set(item.get("actions"), errors, path + "/actions", namespaced=True)
        if not set(capabilities).issubset(ceiling_capabilities):
            add(errors, path + "/capabilities", "capability-exceeds-repository-ceiling")
        if not set(actions).issubset(ceiling_actions):
            add(errors, path + "/actions", "action-exceeds-repository-ceiling")
    if len(item_ids) != len(set(item_ids)):
        add(errors, "/body/items", "duplicate-item-id")
    if item_ids != sorted(item_ids):
        add(errors, "/body/items", "unsorted-item-set")
    membership_value = body.get("membership")
    membership_ids: list[str] = []
    if not isinstance(membership_value, list):
        add(errors, "/body/membership", "required-array")
    else:
        for index, raw in enumerate(membership_value):
            path = "/body/membership/" + str(index)
            assertion = exact_object(raw, {"item_id", "authority", "evidence"}, errors, path, "invalid-membership-assertion")
            if assertion is None:
                continue
            item_id = assertion.get("item_id")
            if isinstance(item_id, str) and item_id:
                membership_ids.append(item_id)
            else:
                add(errors, path + "/item_id", "required-string")
            validate_authority(assertion.get("authority"), errors, path + "/authority")
            validate_reference(assertion.get("evidence"), errors, path + "/evidence")
            membership_authority = assertion.get("authority")
            membership_evidence = assertion.get("evidence")
            if isinstance(membership_authority, dict) and membership_authority.get("authority_id") in authority_ids:
                add(errors, path + "/authority/authority_id", "membership-authority-not-independent")
            if isinstance(membership_evidence, dict) and membership_evidence.get("sha256") in evidence_ids:
                add(errors, path + "/evidence/sha256", "membership-evidence-not-independent")
        if membership_ids != sorted(set(membership_ids)) or set(membership_ids) != set(item_ids):
            add(errors, "/body/membership", "membership-does-not-match-items")
        membership_authority_ids = [assertion.get("authority", {}).get("authority_id") for assertion in membership_value if isinstance(assertion, dict) and isinstance(assertion.get("authority"), dict)]
        membership_evidence_ids = [assertion.get("evidence", {}).get("sha256") for assertion in membership_value if isinstance(assertion, dict) and isinstance(assertion.get("evidence"), dict)]
        if len(membership_authority_ids) != len(set(membership_authority_ids)):
            add(errors, "/body/membership", "duplicate-membership-authority")
        if len(membership_evidence_ids) != len(set(membership_evidence_ids)):
            add(errors, "/body/membership", "duplicate-membership-evidence")
    graph: dict[str, set[str]] = {item_id: set() for item_id in item_ids}
    raw_dependencies = body.get("dependencies")
    dependencies: list[Any] = raw_dependencies if isinstance(raw_dependencies, list) else []
    if not isinstance(raw_dependencies, list):
        add(errors, "/body/dependencies", "required-array")
    seen_edges: set[tuple[str, str]] = set()
    for index, raw in enumerate(dependencies):
        edge = exact_object(raw, {"before", "after"}, errors, "/body/dependencies/" + str(index), "invalid-dependency-edge")
        if edge is None:
            continue
        before, after = edge.get("before"), edge.get("after")
        if not isinstance(before, str) or not isinstance(after, str) or before == after or before not in graph or after not in graph:
            add(errors, "/body/dependencies/" + str(index), "unknown-or-self-dependency")
            continue
        if (before, after) in seen_edges:
            add(errors, "/body/dependencies/" + str(index), "duplicate-dependency")
        seen_edges.add((before, after))
        graph[before].add(after)
    if dependencies != sorted(dependencies, key=lambda edge: (str(edge.get("before", "")), str(edge.get("after", ""))) if isinstance(edge, dict) else ("", "")):
        add(errors, "/body/dependencies", "unsorted-dependency-set")
    indegree = {node: 0 for node in graph}
    for children in graph.values():
        for child in children:
            indegree[child] += 1
    available = sorted(node for node, count in indegree.items() if count == 0)
    ordered: list[str] = []
    while available:
        node = available.pop(0)
        ordered.append(node)
        for child in sorted(graph[node]):
            indegree[child] -= 1
            if indegree[child] == 0:
                available.append(child)
                available.sort()
    if len(ordered) != len(graph):
        add(errors, "/body/dependencies", "dependency-cycle")
        return
    reachable = {node: set() for node in graph}
    for node in reversed(ordered):
        for child in graph[node]:
            reachable[node].add(child)
            reachable[node].update(reachable[child])
    for index, (item_id, claim, _scope) in enumerate(item_paths):
        for other_id, other_claim, _other_scope in item_paths[index + 1:]:
            if item_id != other_id and overlaps(claim, other_claim) and other_id not in reachable[item_id] and item_id not in reachable[other_id]:
                add(errors, "/body/items", "unordered-cross-item-path-overlap")


def validate_attempt(body: dict[str, Any], errors: list[dict[str, Any]]) -> None:
    fields = {"accepted_bundle_id", "item_id", "run_id", "attempt_id", "repository_id", "base", "candidate", "branch", "worktree", "dependency_readiness", "reconciliation", "authorities", "budgets", "grant_ceiling", "selected_paths", "selected_capabilities", "selected_actions", "next_actions", "fencing_identity"}
    if set(body) != fields:
        add(errors, "/body", "unknown-or-missing-body-field")
    for field in ("accepted_bundle_id", "item_id", "run_id", "attempt_id", "repository_id", "branch", "fencing_identity"):
        required_string(body.get(field), errors, "/body/" + field)
    identifier(body.get("accepted_bundle_id"), errors, "/body/accepted_bundle_id")
    identifier(body.get("fencing_identity"), errors, "/body/fencing_identity")
    validate_commit_point(body.get("base"), errors, "/body/base")
    validate_commit_point(body.get("candidate"), errors, "/body/candidate")
    if body.get("worktree") != "not_applicable":
        required_string(body.get("worktree"), errors, "/body/worktree")
    readiness = exact_object(body.get("dependency_readiness"), {"status", "required_item_ids", "dependencies"}, errors, "/body/dependency_readiness", "unknown-or-missing-readiness-field")
    if readiness is not None:
        if readiness.get("status") not in {"ready", "not_ready", "blocked", "ambiguous"}:
            add(errors, "/body/dependency_readiness/status", "invalid-readiness-status")
        required_dependency_ids = string_set(readiness.get("required_item_ids"), errors, "/body/dependency_readiness/required_item_ids")
        dependencies = readiness.get("dependencies")
        observed_dependency_ids: list[str] = []
        if not isinstance(dependencies, list):
            add(errors, "/body/dependency_readiness/dependencies", "required-array")
        else:
            for index, dependency in enumerate(dependencies):
                entry = exact_object(dependency, {"item_id", "history_id", "candidate_tree", "outcome"}, errors, "/body/dependency_readiness/dependencies/" + str(index), "invalid-readiness-dependency")
                if entry is not None:
                    for field in ("item_id", "history_id", "candidate_tree"):
                        required_string(entry.get(field), errors, "/body/dependency_readiness/dependencies/" + str(index) + "/" + field)
                    if isinstance(entry.get("item_id"), str):
                        observed_dependency_ids.append(entry["item_id"])
                    if entry.get("outcome") != "reviewed_success":
                        add(errors, "/body/dependency_readiness/dependencies/" + str(index) + "/outcome", "dependency-not-reviewed-success")
            if observed_dependency_ids != required_dependency_ids:
                add(errors, "/body/dependency_readiness/dependencies", "dependency-readiness-coverage-mismatch")
    reconciliation = exact_object(body.get("reconciliation"), {"outcome", "rationale", "evidence"}, errors, "/body/reconciliation", "unknown-or-missing-reconciliation-field")
    if reconciliation is not None:
        if reconciliation.get("outcome") not in {"acceptance_preserving", "not_preserving", "blocked", "ambiguous"}:
            add(errors, "/body/reconciliation/outcome", "invalid-reconciliation-outcome")
        required_string(reconciliation.get("rationale"), errors, "/body/reconciliation/rationale")
        validate_reference(reconciliation.get("evidence"), errors, "/body/reconciliation/evidence")
    authorities = body.get("authorities")
    if not isinstance(authorities, list):
        add(errors, "/body/authorities", "required-array")
    else:
        for index, authority in enumerate(authorities):
            validate_authority(authority, errors, "/body/authorities/" + str(index))
    grant_ceiling = exact_object(body.get("grant_ceiling"), {"paths", "capabilities", "actions", "mutation_actions"}, errors, "/body/grant_ceiling", "unknown-or-missing-grant-ceiling-field")
    granted_paths: list[tuple[str, str]] = []
    granted_capabilities: list[str] = []
    granted_actions: list[str] = []
    mutation_actions: list[str] = []
    if grant_ceiling is not None:
        granted_paths = validate_paths(grant_ceiling.get("paths"), errors, "/body/grant_ceiling/paths")
        granted_capabilities = string_set(grant_ceiling.get("capabilities"), errors, "/body/grant_ceiling/capabilities", namespaced=True)
        granted_actions = string_set(grant_ceiling.get("actions"), errors, "/body/grant_ceiling/actions", namespaced=True)
        mutation_actions = string_set(grant_ceiling.get("mutation_actions"), errors, "/body/grant_ceiling/mutation_actions", namespaced=True)
        if not set(mutation_actions).issubset(granted_actions):
            add(errors, "/body/grant_ceiling/mutation_actions", "mutation-action-exceeds-ceiling")
    selected_paths = validate_paths(body.get("selected_paths"), errors, "/body/selected_paths")
    selected_capabilities = string_set(body.get("selected_capabilities"), errors, "/body/selected_capabilities", namespaced=True)
    selected_actions = string_set(body.get("selected_actions"), errors, "/body/selected_actions", namespaced=True)
    next_actions = string_set(body.get("next_actions"), errors, "/body/next_actions", namespaced=True)
    if any(not any(path_is_within(selected, granted) for granted in granted_paths) for selected in selected_paths):
        add(errors, "/body/selected_paths", "path-exceeds-item-grant")
    if not set(selected_capabilities).issubset(granted_capabilities):
        add(errors, "/body/selected_capabilities", "capability-exceeds-item-grant")
    if not set(selected_actions).issubset(granted_actions) or not set(next_actions).issubset(selected_actions):
        add(errors, "/body/selected_actions", "action-exceeds-item-grant")
    budgets = body.get("budgets")
    if not isinstance(budgets, list):
        add(errors, "/body/budgets", "required-array")
    else:
        names: set[str] = set()
        ordered_names: list[str] = []
        authority_ids: set[str] = set()
        for index, authority in enumerate(body.get("authorities", [])):
            if isinstance(authority, dict) and isinstance(authority.get("authority_id"), str):
                authority_id = authority["authority_id"]
                if authority_id in authority_ids:
                    add(errors, "/body/authorities/" + str(index) + "/authority_id", "duplicate-authority-id")
                authority_ids.add(authority_id)
        for index, raw in enumerate(budgets):
            budget = exact_object(raw, {"name", "unit", "limit", "consumed", "remaining"}, errors, "/body/budgets/" + str(index), "unknown-or-missing-budget-field")
            if budget is None:
                continue
            for field in ("name", "unit"):
                required_string(budget.get(field), errors, "/body/budgets/" + str(index) + "/" + field)
            for field in ("limit", "consumed", "remaining"):
                nonnegative_integer(budget.get(field), errors, "/body/budgets/" + str(index) + "/" + field)
            if isinstance(budget.get("name"), str):
                ordered_names.append(budget["name"])
                if budget["name"] in names:
                    add(errors, "/body/budgets/" + str(index), "duplicate-budget-name")
                names.add(budget["name"])
            if all(isinstance(budget.get(field), int) and not isinstance(budget.get(field), bool) for field in ("limit", "consumed", "remaining")) and budget["limit"] != budget["consumed"] + budget["remaining"]:
                add(errors, "/body/budgets/" + str(index), "inconsistent-budget")
        if ordered_names != sorted(ordered_names):
            add(errors, "/body/budgets", "unsorted-budget-set")
    expected_fence = digest({"schema_id": SCHEMA_ID, "schema_version": SCHEMA_VERSION, "kind": "AttemptBinding", "body": {field: value for field, value in body.items() if field != "fencing_identity"}})
    if body.get("fencing_identity") != expected_fence:
        add(errors, "/body/fencing_identity", "fencing-identity-mismatch", (expected_fence,))
    if readiness is not None and (readiness.get("status") != "ready" or not isinstance(reconciliation, dict) or reconciliation.get("outcome") != "acceptance_preserving") and set(next_actions).intersection(mutation_actions):
        add(errors, "/body/next_actions", "mutation-action-not-permitted-when-not-ready")


def validate_history(body: dict[str, Any], errors: list[dict[str, Any]]) -> None:
    fields = {"accepted_bundle_id", "item_id", "run_id", "attempt_binding_id", "attempt_id", "review_id", "history_id", "candidate_base", "ticket_branch", "final_tip", "commits", "accepted_artifact", "review_contract_id", "review_contract_version", "review_envelope_id", "matrix_hash", "envelope_hash", "namespace", "predecessor", "requirements", "findings", "compliance_verdict", "quality_verdict", "validation_observations", "residuals", "outcome"}
    if set(body) != fields:
        add(errors, "/body", "unknown-or-missing-body-field")
    for field in ("accepted_bundle_id", "attempt_binding_id", "review_envelope_id"):
        identifier(body.get(field), errors, "/body/" + field)
    for field in ("item_id", "run_id", "attempt_id", "review_id", "history_id", "ticket_branch", "matrix_hash", "envelope_hash", "namespace"):
        required_string(body.get(field), errors, "/body/" + field)
    validate_commit_point(body.get("candidate_base"), errors, "/body/candidate_base")
    validate_commit_point(body.get("final_tip"), errors, "/body/final_tip")
    validate_reference(body.get("accepted_artifact"), errors, "/body/accepted_artifact")
    validation_observations = body.get("validation_observations")
    validation_statuses: list[str] = []
    if not isinstance(validation_observations, list) or not validation_observations:
        add(errors, "/body/validation_observations", "missing-validation-observations")
    else:
        obligation_ids: set[str] = set()
        for index, raw in enumerate(validation_observations):
            path = "/body/validation_observations/" + str(index)
            observation = exact_object(raw, {"obligation_id", "status", "evidence"}, errors, path, "invalid-validation-observation")
            if observation is None:
                continue
            obligation_id = observation.get("obligation_id")
            if not isinstance(obligation_id, str) or not obligation_id or obligation_id in obligation_ids:
                add(errors, path + "/obligation_id", "invalid-validation-obligation")
            else:
                obligation_ids.add(obligation_id)
            status = observation.get("status")
            if status not in {"pass", "fail", "unknown"}:
                add(errors, path + "/status", "invalid-validation-status")
            elif isinstance(status, str):
                validation_statuses.append(status)
            validate_reference(observation.get("evidence"), errors, path + "/evidence")
    if body.get("review_contract_id") != "reviewed-change-orchestration.review-record" or body.get("review_contract_version") != SCHEMA_VERSION:
        add(errors, "/body/review_contract_id", "unknown-review-contract")
    predecessor = body.get("predecessor")
    if predecessor is not None:
        parent = exact_object(predecessor, {"envelope_id", "envelope_hash", "matrix_hash", "accepted_artifact"}, errors, "/body/predecessor", "invalid-predecessor")
        if parent is not None:
            identifier(parent.get("envelope_id"), errors, "/body/predecessor/envelope_id")
            required_string(parent.get("envelope_hash"), errors, "/body/predecessor/envelope_hash")
            required_string(parent.get("matrix_hash"), errors, "/body/predecessor/matrix_hash")
            validate_reference(parent.get("accepted_artifact"), errors, "/body/predecessor/accepted_artifact")
    requirements = string_set(body.get("requirements"), errors, "/body/requirements")
    commits = body.get("commits")
    if not isinstance(commits, list):
        add(errors, "/body/commits", "required-array")
        commits = []
    previous_commit = body.get("candidate_base", {}).get("commit") if isinstance(body.get("candidate_base"), dict) else None
    commit_requirements: set[str] = set()
    for index, raw in enumerate(commits):
        commit = exact_object(raw, {"kind", "commit", "tree", "parent", "requirements"}, errors, "/body/commits/" + str(index), "invalid-meaningful-commit")
        if commit is None:
            continue
        if commit.get("kind") not in {"implementation", "review_fix"}:
            add(errors, "/body/commits/" + str(index) + "/kind", "invalid-meaningful-commit")
        for field in ("commit", "tree", "parent"):
            required_string(commit.get(field), errors, "/body/commits/" + str(index) + "/" + field)
        covered = string_set(commit.get("requirements"), errors, "/body/commits/" + str(index) + "/requirements")
        commit_requirements.update(covered)
        if previous_commit is not None and commit.get("parent") != previous_commit:
            add(errors, "/body/commits/" + str(index) + "/parent", "commit-lineage-mismatch")
        previous_commit = commit.get("commit")
    final_tip = body.get("final_tip")
    if commits and isinstance(final_tip, dict) and isinstance(commits[-1], dict) and (commits[-1].get("commit") != final_tip.get("commit") or commits[-1].get("tree") != final_tip.get("tree")):
        add(errors, "/body/final_tip", "commit-lineage-mismatch")
    if set(requirements) != commit_requirements:
        add(errors, "/body/commits", "commit-requirement-coverage-mismatch")
    findings = body.get("findings")
    if not isinstance(findings, list):
        add(errors, "/body/findings", "required-array")
        findings = []
    finding_ids: set[str] = set()
    blocking_finding = False
    for index, raw in enumerate(findings):
        finding = exact_object(raw, {"finding_id", "class", "severity", "disposition", "requirement_ids", "rationale"}, errors, "/body/findings/" + str(index), "invalid-finding")
        if finding is None:
            blocking_finding = True
            continue
        finding_id = finding.get("finding_id")
        if not required_string(finding_id, errors, "/body/findings/" + str(index) + "/finding_id") or finding_id in finding_ids:
            add(errors, "/body/findings/" + str(index), "duplicate-finding-id")
        if isinstance(finding_id, str):
            finding_ids.add(finding_id)
        finding_class, severity, disposition = finding.get("class"), finding.get("severity"), finding.get("disposition")
        if finding_class not in {"implementation_defect", "accepted_artifact_gap", "new_scope", "contradiction", "reviewer_concern"}:
            add(errors, "/body/findings/" + str(index) + "/class", "invalid-finding-class")
        if severity not in {"Critical", "Important", "Minor"}:
            add(errors, "/body/findings/" + str(index) + "/severity", "invalid-finding-severity")
        if disposition not in {"open", "fixed", "accepted_residual", "rejected_as_reviewer_error", "user_ruling_required"}:
            add(errors, "/body/findings/" + str(index) + "/disposition", "invalid-finding-disposition")
        finding_requirements = string_set(finding.get("requirement_ids"), errors, "/body/findings/" + str(index) + "/requirement_ids")
        if not set(finding_requirements).issubset(requirements):
            add(errors, "/body/findings/" + str(index) + "/requirement_ids", "finding-requirement-mismatch")
        required_string(finding.get("rationale"), errors, "/body/findings/" + str(index) + "/rationale")
        legal = finding_class == "implementation_defect" and ((severity in {"Critical", "Important"} and disposition in {"fixed", "rejected_as_reviewer_error"}) or (severity == "Minor" and disposition in {"fixed", "rejected_as_reviewer_error", "accepted_residual"}))
        if not legal:
            blocking_finding = True
    if body.get("outcome") not in {"reviewed_success", "incomplete", "failed", "blocked", "ambiguous"}:
        add(errors, "/body/outcome", "invalid-history-outcome")
    residuals = string_set(body.get("residuals"), errors, "/body/residuals")
    expected_residuals: list[str] = []
    for finding in findings:
        if isinstance(finding, dict) and finding.get("disposition") == "accepted_residual":
            finding_id = finding.get("finding_id")
            if isinstance(finding_id, str):
                expected_residuals.append(finding_id)
    expected_residuals.sort()
    if residuals != expected_residuals:
        add(errors, "/body/residuals", "residual-finding-mismatch")
    outcome = body.get("outcome")
    success_conditions = bool(commits) and body.get("compliance_verdict") == "pass" and body.get("quality_verdict") == "pass" and bool(validation_statuses) and all(status == "pass" for status in validation_statuses) and not blocking_finding and all(residual in finding_ids for residual in residuals)
    failed_signal = body.get("compliance_verdict") == "fail" or body.get("quality_verdict") == "fail" or "fail" in validation_statuses
    ambiguous_signal = "unknown" in validation_statuses
    if outcome == "reviewed_success" and not success_conditions:
        add(errors, "/body", "reviewed-success-incomplete")
    elif outcome == "failed" and not failed_signal:
        add(errors, "/body/outcome", "history-outcome-verdict-mismatch")
    elif outcome == "ambiguous" and not ambiguous_signal:
        add(errors, "/body/outcome", "history-outcome-verdict-mismatch")
    elif outcome == "blocked" and not blocking_finding:
        add(errors, "/body/outcome", "history-outcome-verdict-mismatch")
    elif outcome == "incomplete" and success_conditions:
        add(errors, "/body/outcome", "history-outcome-verdict-mismatch")


def validate_candidate(body: dict[str, Any], errors: list[dict[str, Any]]) -> None:
    fields = {"accepted_bundle_id", "run_id", "candidate_base", "assembled_tip", "status", "authority_ceiling", "accepted_item_ids", "histories", "item_outcomes", "assembly", "aggregate_interactions", "packet", "artifact"}
    if set(body) != fields:
        add(errors, "/body", "unknown-or-missing-body-field")
    identifier(body.get("accepted_bundle_id"), errors, "/body/accepted_bundle_id")
    required_string(body.get("run_id"), errors, "/body/run_id")
    validate_commit_point(body.get("candidate_base"), errors, "/body/candidate_base")
    validate_commit_point(body.get("assembled_tip"), errors, "/body/assembled_tip")
    if body.get("authority_ceiling") != "local_candidate_only":
        add(errors, "/body/authority_ceiling", "invalid-authority-ceiling")
    accepted_items = string_set(body.get("accepted_item_ids"), errors, "/body/accepted_item_ids")
    raw_histories = body.get("histories")
    histories: list[Any] = raw_histories if isinstance(raw_histories, list) else []
    if not isinstance(raw_histories, list):
        add(errors, "/body/histories", "required-array")
    entries: list[tuple[str, str]] = []
    ambiguous = False
    failed = False
    partial = False
    for index, history in enumerate(histories):
        nested_errors, _nested_id, _nested_digest = validate_envelope(history, "ReviewedItemHistory")
        if nested_errors:
            add(errors, "/body/histories/" + str(index), "invalid-embedded-history")
            ambiguous = True
            continue
        nested = history["body"]
        if nested.get("accepted_bundle_id") != body.get("accepted_bundle_id") or nested.get("run_id") != body.get("run_id"):
            add(errors, "/body/histories/" + str(index), "history-binding-mismatch")
            ambiguous = True
        item_id, outcome = nested.get("item_id"), nested.get("outcome")
        if isinstance(item_id, str):
            entries.append((item_id, outcome))
        if outcome != "reviewed_success":
            add(errors, "/body/histories/" + str(index) + "/body/outcome", "non-success-history-must-be-item-outcome")
            ambiguous = True
    outcomes = body.get("item_outcomes")
    if not isinstance(outcomes, list):
        add(errors, "/body/item_outcomes", "required-array")
        outcomes = []
    for index, raw in enumerate(outcomes):
        outcome = exact_object(raw, {"item_id", "outcome"}, errors, "/body/item_outcomes/" + str(index), "invalid-item-outcome")
        if outcome is None:
            ambiguous = True
            continue
        item_id, value = outcome.get("item_id"), outcome.get("outcome")
        if not isinstance(item_id, str) or value not in {"blocked", "skipped", "failed", "ambiguous", "partial"}:
            add(errors, "/body/item_outcomes/" + str(index), "invalid-item-outcome")
            ambiguous = True
            continue
        entries.append((item_id, value))
        ambiguous = ambiguous or value == "ambiguous"
        failed = failed or value == "failed"
        partial = partial or value in {"blocked", "skipped", "partial"}
    entry_ids = [item_id for item_id, _value in entries]
    if sorted(entry_ids) != accepted_items or len(entry_ids) != len(set(entry_ids)):
        add(errors, "/body", "candidate-item-coverage-mismatch")
        ambiguous = True
    expected_history_ids: list[str] = []
    expected_history_trees: list[str] = []
    for history in histories:
        if isinstance(history, dict) and isinstance(history.get("id"), str) and isinstance(history.get("body"), dict):
            final_tip = history["body"].get("final_tip")
            if history["body"].get("outcome") == "reviewed_success" and isinstance(final_tip, dict) and isinstance(final_tip.get("tree"), str):
                expected_history_ids.append(history["id"])
                expected_history_trees.append(final_tip["tree"])
    assembly = exact_object(body.get("assembly"), {"strategy_id", "steps"}, errors, "/body/assembly", "unknown-or-missing-assembly-field")
    if assembly is not None:
        required_string(assembly.get("strategy_id"), errors, "/body/assembly/strategy_id")
        steps = assembly.get("steps")
        if not isinstance(steps, list) or not steps:
            add(errors, "/body/assembly/steps", "missing-assembly-steps")
            ambiguous = True
        else:
            previous_after: Any = body.get("candidate_base")
            assembled_history_ids: list[str] = []
            assembled_trees: list[str] = []
            for index, raw in enumerate(steps):
                step = exact_object(raw, {"input_history_ids", "input_trees", "before", "after"}, errors, "/body/assembly/steps/" + str(index), "invalid-assembly-step")
                if step is None:
                    ambiguous = True
                    continue
                history_ids = step.get("input_history_ids")
                trees = step.get("input_trees")
                if not isinstance(history_ids, list) or not all(isinstance(value, str) and value for value in history_ids):
                    add(errors, "/body/assembly/steps/" + str(index) + "/input_history_ids", "invalid-assembly-inputs")
                else:
                    assembled_history_ids.extend(history_ids)
                if not isinstance(trees, list) or not all(isinstance(value, str) and value for value in trees):
                    add(errors, "/body/assembly/steps/" + str(index) + "/input_trees", "invalid-assembly-inputs")
                else:
                    assembled_trees.extend(trees)
                validate_commit_point(step.get("before"), errors, "/body/assembly/steps/" + str(index) + "/before")
                validate_commit_point(step.get("after"), errors, "/body/assembly/steps/" + str(index) + "/after")
                if step.get("before") != previous_after:
                    add(errors, "/body/assembly/steps/" + str(index) + "/before", "assembly-lineage-mismatch")
                    ambiguous = True
                previous_after = step.get("after")
            if previous_after != body.get("assembled_tip"):
                add(errors, "/body/assembled_tip", "assembly-lineage-mismatch")
                ambiguous = True
            if assembled_history_ids != expected_history_ids or assembled_trees != expected_history_trees:
                add(errors, "/body/assembly/steps", "assembly-input-mismatch")
                ambiguous = True
    interactions = body.get("aggregate_interactions")
    interaction_statuses: list[str] = []
    assembled_tip = body.get("assembled_tip")
    assembled_tree = assembled_tip.get("tree") if isinstance(assembled_tip, dict) else None
    if not isinstance(interactions, list) or not interactions:
        add(errors, "/body/aggregate_interactions", "missing-aggregate-interactions")
        ambiguous = True
    else:
        obligation_ids: set[str] = set()
        for index, raw in enumerate(interactions):
            path = "/body/aggregate_interactions/" + str(index)
            interaction = exact_object(raw, {"obligation_id", "final_tree", "status", "evidence"}, errors, path, "invalid-aggregate-interaction")
            if interaction is None:
                ambiguous = True
                continue
            obligation_id = interaction.get("obligation_id")
            if not isinstance(obligation_id, str) or not obligation_id or obligation_id in obligation_ids:
                add(errors, path + "/obligation_id", "invalid-aggregate-obligation")
                ambiguous = True
            else:
                obligation_ids.add(obligation_id)
            if interaction.get("final_tree") != assembled_tree:
                add(errors, path + "/final_tree", "aggregate-tree-mismatch")
                ambiguous = True
            status = interaction.get("status")
            if status not in {"pass", "failed", "unknown"}:
                add(errors, path + "/status", "invalid-aggregate-verification")
                ambiguous = True
            else:
                interaction_statuses.append(status)
                ambiguous = ambiguous or status == "unknown"
                failed = failed or status == "failed"
            validate_reference(interaction.get("evidence"), errors, path + "/evidence")
    for field in ("packet", "artifact"):
        validate_projection(body.get(field), errors, "/body/" + field, body)
    expected = "local_ambiguous" if ambiguous else "local_failed" if failed else "local_partial" if partial else "local_complete"
    if body.get("status") != expected:
        add(errors, "/body/status", "candidate-status-precedence")


def schema_definition(schema: dict[str, Any], reference: str) -> dict[str, Any]:
    prefix = "#/$defs/"
    if not reference.startswith(prefix):
        raise ContractError("unsupported-schema-reference")
    definition = schema.get("$defs", {}).get(reference[len(prefix):])
    if not isinstance(definition, dict):
        raise ContractError("invalid-schema-reference")
    return definition


def schema_type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ContractError("unsupported-schema-type")


def evaluate_schema(value: Any, rule: dict[str, Any], schema: dict[str, Any], path: str = "") -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if "$ref" in rule:
        return evaluate_schema(value, schema_definition(schema, rule["$ref"]), schema, path)
    for nested in rule.get("allOf", []):
        errors.extend(evaluate_schema(value, nested, schema, path))
    if "oneOf" in rule:
        matches = [evaluate_schema(value, nested, schema, path) for nested in rule["oneOf"]]
        valid_count = sum(not finding for finding in matches)
        if valid_count != 1:
            add(errors, path, "schema-one-of")
        return errors
    expected_type = rule.get("type")
    if isinstance(expected_type, str) and not schema_type_matches(value, expected_type):
        add(errors, path, "schema-type")
        return errors
    if "const" in rule and value != rule["const"]:
        add(errors, path, "schema-const")
    if "enum" in rule and value not in rule["enum"]:
        add(errors, path, "schema-enum")
    if isinstance(value, str):
        if len(value) < rule.get("minLength", 0):
            add(errors, path, "schema-min-length")
        pattern = rule.get("pattern")
        if isinstance(pattern, str):
            compiled_pattern = SCHEMA_PATTERNS.get(pattern)
            if compiled_pattern is None:
                raise ContractError("unsupported-schema-pattern")
            if compiled_pattern.fullmatch(value) is None:
                add(errors, path, "schema-pattern")
    if isinstance(value, int) and not isinstance(value, bool) and value < rule.get("minimum", value):
        add(errors, path, "schema-minimum")
    if isinstance(value, list):
        if len(value) < rule.get("minItems", 0):
            add(errors, path, "schema-min-items")
        item_rule = rule.get("items")
        if isinstance(item_rule, dict):
            for index, item in enumerate(value):
                errors.extend(evaluate_schema(item, item_rule, schema, path + "/" + str(index)))
    if isinstance(value, dict):
        properties = rule.get("properties", {})
        required = rule.get("required", [])
        for field in required:
            if field not in value:
                add(errors, path + "/" + pointer_part(field), "schema-required")
        additional_properties = rule.get("additionalProperties", True)
        if isinstance(additional_properties, bool) and not additional_properties:
            for field in value:
                if field not in properties:
                    add(errors, path + "/" + pointer_part(field), "schema-additional-property")
        for field, nested in properties.items():
            if field in value:
                errors.extend(evaluate_schema(value[field], nested, schema, path + "/" + pointer_part(field)))
    return errors


def schema_errors(document: Any, kind: str) -> list[dict[str, Any]]:
    global _SCHEMA
    if _SCHEMA is None:
        self_check()
    if _SCHEMA is None:
        raise ContractError("schema-owner-contract-mismatch")
    definition = _SCHEMA.get("$defs", {}).get(kind)
    if not isinstance(definition, dict):
        raise ContractError("schema-owner-contract-mismatch")
    return sort_errors(evaluate_schema(document, definition, _SCHEMA))


def validate_envelope(document: Any, kind: str) -> tuple[list[dict[str, Any]], str | None, str | None]:
    errors = [*parser_errors(document), *schema_errors(document, kind)]
    if not isinstance(document, dict):
        add(errors, "/", "envelope-must-be-object")
        return sort_errors(errors), None, None
    envelope = exact_object(document, {"schema_id", "schema_version", "kind", "id", "body"}, errors, "/", "unknown-or-missing-envelope-field")
    if envelope is None:
        return sort_errors(errors), None, None
    if envelope.get("schema_id") != SCHEMA_ID:
        add(errors, "/schema_id", "unknown-schema-id")
    if envelope.get("schema_version") != SCHEMA_VERSION:
        add(errors, "/schema_version", "unknown-schema-version")
    if kind not in KINDS or envelope.get("kind") != kind:
        add(errors, "/kind", "kind-mismatch")
    body = envelope.get("body")
    if not isinstance(body, dict):
        add(errors, "/body", "required-object")
        body = {}
    computed_id = digest({field: envelope.get(field) for field in ("schema_id", "schema_version", "kind", "body")})
    if envelope.get("id") != computed_id:
        add(errors, "/id", "envelope-identity-mismatch", (computed_id,))
    if kind == "AcceptedBundle":
        validate_accepted(body, errors)
    elif kind == "AttemptBinding":
        validate_attempt(body, errors)
    elif kind == "ReviewedItemHistory":
        validate_history(body, errors)
    elif kind == "CandidateBundle":
        validate_candidate(body, errors)
    return sort_errors(errors), computed_id, digest(envelope)


def observation_error(errors: list[dict[str, Any]], path: str, expected: Any, observed: dict[str, Any]) -> None:
    add(errors, path, "missing-observation" if path.rsplit("/", 1)[-1] not in observed else "mismatched-observation")


def compare_fields(expected: dict[str, Any], observed: Any, fields: Iterable[str], errors: list[dict[str, Any]], path: str) -> None:
    if not isinstance(observed, dict):
        add(errors, path, "missing-observation")
        return
    for field in fields:
        if observed.get(field) != expected.get(field):
            add(errors, path + "/" + field, "missing-observation" if field not in observed else "mismatched-observation")


def validate_context(context: Any, kind: str, envelope: dict[str, Any], errors: list[dict[str, Any]]) -> None:
    wrapper = exact_object(context, {"context_schema_id", "context_schema_version", "kind", "observations"}, errors, "/context", "unknown-or-missing-context-field")
    if wrapper is None:
        return
    if wrapper.get("context_schema_id") != CONTEXT_ID:
        add(errors, "/context/context_schema_id", "unknown-context-id")
    if wrapper.get("context_schema_version") != SCHEMA_VERSION:
        add(errors, "/context/context_schema_version", "unknown-context-version")
    if wrapper.get("kind") != kind:
        add(errors, "/context/kind", "context-kind-mismatch")
    observations = wrapper.get("observations")
    if not isinstance(observations, dict):
        add(errors, "/context/observations", "missing-observations")
        return
    compare_fields({"envelope_id": envelope.get("id"), "canonical_document_sha256": digest(envelope)}, observations, ("envelope_id", "canonical_document_sha256"), errors, "/context/observations")
    body = envelope.get("body", {})
    if not isinstance(body, dict):
        return
    expected_facts: dict[str, Any]
    if kind == "AcceptedBundle":
        items = body.get("items", [])
        membership = body.get("membership", [])
        expected_facts = {
            "repository": {"repository_id": body.get("repository_id")},
            "membership": {
                "item_ids": [entry.get("item_id") for entry in membership if isinstance(entry, dict)],
                "dependency_edges": body.get("dependencies"),
            },
            "authority_evidence": [{
                "item_id": item.get("item_id"),
                "authority_id": item.get("authority", {}).get("authority_id") if isinstance(item.get("authority"), dict) else None,
                "decision_id": item.get("authority", {}).get("decision_id") if isinstance(item.get("authority"), dict) else None,
                "accepted_source_sha256": item.get("accepted_source", {}).get("sha256") if isinstance(item.get("accepted_source"), dict) else None,
            } for item in items if isinstance(item, dict)],
        }
    elif kind == "AttemptBinding":
        readiness = body.get("dependency_readiness", {})
        reconciliation = body.get("reconciliation", {})
        grant_ceiling = body.get("grant_ceiling", {})
        expected_facts = {
            "binding": {field: body.get(field) for field in ("accepted_bundle_id", "item_id", "run_id", "attempt_id", "repository_id", "base", "candidate", "branch", "worktree", "fencing_identity")},
            "readiness": {
                "status": readiness.get("status") if isinstance(readiness, dict) else None,
                "required_item_ids": readiness.get("required_item_ids") if isinstance(readiness, dict) else None,
                "dependencies": readiness.get("dependencies") if isinstance(readiness, dict) else None,
                "reconciliation_outcome": reconciliation.get("outcome") if isinstance(reconciliation, dict) else None,
                "reconciliation_evidence_sha256": reconciliation.get("evidence", {}).get("sha256") if isinstance(reconciliation, dict) and isinstance(reconciliation.get("evidence"), dict) else None,
            },
            "grants": {
                "ceiling": grant_ceiling,
                "selected_paths": body.get("selected_paths"),
                "selected_capabilities": body.get("selected_capabilities"),
                "selected_actions": body.get("selected_actions"),
                "next_actions": body.get("next_actions"),
            },
            "authority_budget": {
                "authority_ids": [authority.get("authority_id") for authority in body.get("authorities", []) if isinstance(authority, dict)],
                "budgets": body.get("budgets"),
            },
        }
    elif kind == "ReviewedItemHistory":
        expected_facts = {
            "binding": {field: body.get(field) for field in ("accepted_bundle_id", "item_id", "run_id", "attempt_binding_id", "attempt_id", "candidate_base", "ticket_branch", "final_tip")},
            "git_lineage": [{field: commit.get(field) for field in ("commit", "tree", "parent")} for commit in body.get("commits", []) if isinstance(commit, dict)],
            "review": {field: body.get(field) for field in ("review_id", "review_envelope_id", "matrix_hash", "envelope_hash", "namespace", "predecessor", "compliance_verdict", "quality_verdict")},
            "evidence": {
                "accepted_artifact_sha256": body.get("accepted_artifact", {}).get("sha256") if isinstance(body.get("accepted_artifact"), dict) else None,
                "validation": [{"obligation_id": entry.get("obligation_id"), "status": entry.get("status"), "evidence_sha256": entry.get("evidence", {}).get("sha256") if isinstance(entry.get("evidence"), dict) else None} for entry in body.get("validation_observations", []) if isinstance(entry, dict)],
            },
            "outcome": {"outcome": body.get("outcome"), "finding_ids": [finding.get("finding_id") for finding in body.get("findings", []) if isinstance(finding, dict)], "residuals": body.get("residuals")},
        }
    else:
        expected_facts = {
            "binding": {field: body.get(field) for field in ("accepted_bundle_id", "run_id", "candidate_base", "assembled_tip", "status")},
            "histories": [{"history_id": history.get("id"), "item_id": history.get("body", {}).get("item_id") if isinstance(history.get("body"), dict) else None, "final_tree": history.get("body", {}).get("final_tip", {}).get("tree") if isinstance(history.get("body"), dict) and isinstance(history.get("body", {}).get("final_tip"), dict) else None} for history in body.get("histories", []) if isinstance(history, dict)],
            "item_outcomes": body.get("item_outcomes"),
            "assembly": [{"before": step.get("before"), "after": step.get("after"), "input_history_ids": step.get("input_history_ids"), "input_trees": step.get("input_trees")} for step in body.get("assembly", {}).get("steps", []) if isinstance(step, dict)] if isinstance(body.get("assembly"), dict) else [],
            "artifacts": {
                "aggregate": [{"obligation_id": entry.get("obligation_id"), "final_tree": entry.get("final_tree"), "status": entry.get("status"), "evidence_sha256": entry.get("evidence", {}).get("sha256") if isinstance(entry.get("evidence"), dict) else None} for entry in body.get("aggregate_interactions", []) if isinstance(entry, dict)],
                "packet": {"sha256": body.get("packet", {}).get("reference", {}).get("sha256"), "final_tree": body.get("packet", {}).get("final_tree")} if isinstance(body.get("packet"), dict) else None,
                "artifact": {"sha256": body.get("artifact", {}).get("reference", {}).get("sha256"), "final_tree": body.get("artifact", {}).get("final_tree")} if isinstance(body.get("artifact"), dict) else None,
            },
        }
    for category, expected in expected_facts.items():
        observed = observations.get(category)
        if observed != expected:
            add(errors, "/context/observations/" + category, "missing-observation" if category not in observations else "mismatched-observation")


def result_object(kind: str, level: str, structural_valid: bool, contextual_valid: bool | None, envelope_id: str | None, document_digest: str | None, errors: Iterable[dict[str, Any]]) -> dict[str, Any]:
    return {"result_schema_id": RESULT_ID, "result_schema_version": SCHEMA_VERSION, "kind": kind, "level": level, "structural_valid": structural_valid, "contextual_valid": contextual_valid, "envelope_id": envelope_id, "canonical_document_sha256": document_digest, "errors": sort_errors(errors)}


def validation_result(kind: str, level: str, document: Any, context: Any) -> dict[str, Any]:
    errors, envelope_id, document_digest = validate_envelope(document, kind)
    structural_valid = not errors
    contextual_valid: bool | None = None
    if level == "contextual":
        contextual_errors: list[dict[str, Any]] = []
        if isinstance(document, dict):
            validate_context(context, kind, document, contextual_errors)
        else:
            add(contextual_errors, "/context", "cannot-validate-context-without-envelope")
        errors = [*errors, *contextual_errors]
        contextual_valid = not errors
    return result_object(kind, level, structural_valid, contextual_valid, envelope_id, document_digest, errors)


def read_input(name: str) -> bytes:
    return sys.stdin.buffer.read() if name == "-" else Path(name).read_bytes()


def atomic_write(destination: str, payload: bytes) -> None:
    if destination == "-":
        sys.stdout.buffer.write(payload)
        return
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".accepted-work-", dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(payload)
        os.replace(temporary, target)
    except BaseException:
        try:
            Path(temporary).unlink(missing_ok=True)
        except OSError as cleanup_error:
            raise ContractError("atomic-output-cleanup-failure") from cleanup_error
        raise


def self_check() -> None:
    global _SCHEMA
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContractError("invalid-checked-in-schema") from error
    supported = {"$schema", "$id", "$defs", "$ref", "title", "description", "type", "properties", "required", "additionalProperties", "const", "enum", "pattern", "minLength", "minimum", "items", "minItems", "oneOf", "allOf"}
    stack: list[tuple[Any, bool]] = [(schema, True)]
    while stack:
        value, schema_position = stack.pop()
        if isinstance(value, dict):
            if schema_position:
                unknown = set(value) - supported
                if unknown:
                    raise ContractError("unsupported-schema-keyword")
            for key, child in value.items():
                stack.append((child, key not in {"properties", "$defs"}))
        elif isinstance(value, list):
            stack.extend((child, schema_position) for child in value)
    if schema.get("$id") != SCHEMA_ID + "/" + SCHEMA_VERSION or set(schema.get("$defs", {})) < KINDS:
        raise ContractError("schema-owner-contract-mismatch")
    used_patterns: set[str] = set()
    pattern_stack: list[Any] = [schema]
    while pattern_stack:
        value = pattern_stack.pop()
        if isinstance(value, dict):
            pattern = value.get("pattern")
            if isinstance(pattern, str):
                used_patterns.add(pattern)
            pattern_stack.extend(value.values())
        elif isinstance(value, list):
            pattern_stack.extend(value)
    if not used_patterns.issubset(SCHEMA_PATTERNS):
        raise ContractError("unsupported-schema-pattern")
    _SCHEMA = schema


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="accepted_work_envelopes")
    commands = parser.add_subparsers(dest="operation", required=True)
    for operation in ("validate", "canonicalize"):
        command = commands.add_parser(operation)
        command.add_argument("--kind", required=True, choices=sorted(KINDS))
        command.add_argument("--input", required=True)
        command.add_argument("--out", default="-")
        if operation == "validate":
            command.add_argument("--level", required=True, choices=("structural", "contextual"))
            command.add_argument("--context")
    args = parser.parse_args(argv)
    try:
        self_check()
        raw_document = read_input(args.input)
        try:
            document = parse_json(raw_document)
        except (ContractError, DuplicateNameError) as error:
            finding = diagnostic("/", str(error).split(":", 1)[0])
            if args.operation == "canonicalize":
                atomic_write(args.out, canonical_bytes({"errors": [finding]}) + b"\n")
            else:
                output = result_object(args.kind, args.level, False, False if args.level == "contextual" else None, None, None, (finding,))
                atomic_write(args.out, canonical_bytes(output) + b"\n")
            return 1
        if args.operation == "canonicalize":
            errors, _identity, _document_digest = validate_envelope(document, args.kind)
            if errors:
                atomic_write(args.out, canonical_bytes({"errors": errors}) + b"\n")
                return 1
            atomic_write(args.out, canonical_bytes(document))
            return 0
        if args.level == "contextual" and not args.context:
            raise ContractError("context-required")
        context = None
        if args.context:
            try:
                context = parse_json(read_input(args.context))
            except (ContractError, DuplicateNameError) as error:
                errors, envelope_id, document_digest = validate_envelope(document, args.kind)
                errors.append(diagnostic("/context", str(error).split(":", 1)[0]))
                output = result_object(args.kind, args.level, not validate_envelope(document, args.kind)[0], False, envelope_id, document_digest, errors)
                atomic_write(args.out, canonical_bytes(output) + b"\n")
                return 1
        output = validation_result(args.kind, args.level, document, context)
        atomic_write(args.out, canonical_bytes(output) + b"\n")
        return 0 if not output["errors"] else 1
    except OSError:
        sys.stderr.write("accepted_work_envelopes: io-failure\n")
        return 2
    except ContractError as error:
        sys.stderr.write("accepted_work_envelopes: " + str(error).split(":", 1)[0] + "\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
