#!/usr/bin/env python3
"""Offline review-record envelope tooling.

Implements `references/review-record-contract.md` (review_contract_id
"reviewed-change-orchestration.review-record", version 0.1.0): canonical JSON
identity, frozen-matrix hash, the ordered append-only findings ledger, and the
envelope identity tuple. Every orchestrator role recomputes these identities
with this script before relying on a record; the script itself never changes
contract semantics and has zero third-party dependencies.

Canonical JSON is `json.dumps(sort_keys=True, separators=(',', ':'),
ensure_ascii=False, allow_nan=False)` encoded as UTF-8 without a newline.

Managed directory layout (storage remains orchestrator-owned; this tool only
creates and verifies these three files):

    <dir>/envelope.json   identity tuple (envelope_id, namespace, matrix_hash,
                          current_ledger_hash, envelope_revision, predecessor,
                          envelope_hash)
    <dir>/matrix.json     frozen matrix object bytes (written by `freeze`)
    <dir>/ledger.json     ordered ledger entries [{seq, prev, payload, hash}]

Identity rules implemented verbatim:

- `matrix_hash` is SHA-256 of canonical matrix object bytes.
- The empty ledger root is SHA-256 of canonical `[]`.
- Each entry contains its sequence number, previous ledger hash, and its
  value-free payload; the entry hash is SHA-256 of canonical {seq, prev,
  payload}. The current ledger hash is the last entry hash (or the empty
  root).
- `envelope_revision` starts at 1 when the matrix is frozen and increments
  once per append; revision 0 is the pending pre-freeze state.
- `envelope_hash` is SHA-256 of canonical {envelope_id, namespace,
  matrix_hash, current_ledger_hash, envelope_revision, predecessor}.

Result protocol: every command emits one canonical JSON result object with
result_id `reviewed-change-orchestration.review-record-envelope-result`,
version `0.1.0`, the operation, `ok`, recomputed identities, and sorted
value-free errors. Exit 0 means success; exit 1 means invalid, incomplete, or
mismatched input or state; exit 2 is invocation or I/O failure. Errors carry
only codes and JSON Pointer instance paths, never payload content.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
import unicodedata
from collections.abc import Iterable
from pathlib import Path
from typing import Any

RESULT_ID = "reviewed-change-orchestration.review-record-envelope-result"
RESULT_VERSION = "0.1.0"
PENDING_MATRIX_HASH = "PENDING"
MAX_DOCUMENT_BYTES = 8 * 1024 * 1024
MAX_DEPTH = 64
MAX_CONTAINER_ENTRIES = 10_000
MAX_STRING_BYTES = 1024 * 1024
HEX_RE = frozenset("0123456789abcdef")


class ContractError(Exception):
    pass


class DuplicateNameError(ContractError):
    pass


class InvocationError(ContractError):
    pass


class ResultArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise InvocationError("invocation-error")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(value: Any) -> str:
    return sha256_hex(canonical_bytes(value))


def diagnostic(path: str, code: str) -> dict[str, Any]:
    return {"code": code, "instance_path": path or "/", "related_ids": []}


def add(errors: list[dict[str, Any]], path: str, code: str) -> None:
    errors.append(diagnostic(path, code))


def sort_errors(errors: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(errors, key=lambda item: (item["instance_path"], item["code"]))


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
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=no_duplicates,
            parse_constant=lambda _value: (_ for _ in ()).throw(ContractError("non-finite-number")),
        )
    except UnicodeDecodeError as error:
        raise ContractError("invalid-utf8") from error
    except ValueError as error:
        raise ContractError("invalid-json") from error
    except RecursionError as error:
        raise ContractError("depth-exceeded") from error
    except MemoryError as error:
        raise ContractError("json-resource-exceeded") from error


def parser_errors(value: Any) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    stack: list[tuple[Any, int]] = [(value, 1)]
    while stack:
        current, depth = stack.pop()
        if depth > MAX_DEPTH:
            add(errors, "", "depth-exceeded")
            continue
        if isinstance(current, str):
            try:
                string_bytes = current.encode("utf-8")
            except UnicodeEncodeError:
                add(errors, "", "invalid-unicode")
                continue
            if len(string_bytes) > MAX_STRING_BYTES:
                add(errors, "", "string-too-large")
            if unicodedata.normalize("NFC", current) != current:
                add(errors, "", "string-not-nfc")
        elif isinstance(current, float):
            if not math.isfinite(current) or not current.is_integer():
                add(errors, "", "non-integer-number")
        elif isinstance(current, dict):
            if len(current) > MAX_CONTAINER_ENTRIES:
                add(errors, "", "container-too-large")
            for key, child in reversed(list(current.items())):
                stack.append((key, depth + 1))
                stack.append((child, depth + 1))
        elif isinstance(current, list):
            if len(current) > MAX_CONTAINER_ENTRIES:
                add(errors, "", "container-too-large")
            for child in reversed(current):
                stack.append((child, depth + 1))
    return errors


def read_json(path: Path, errors: list[dict[str, Any]], label: str) -> Any:
    if not path.is_file():
        add(errors, "/" + label, "file-missing")
        return None
    try:
        raw = path.read_bytes()
    except OSError:
        add(errors, "/" + label, "file-unreadable")
        return None
    try:
        value = parse_json(raw)
    except ContractError as error:
        add(errors, "/" + label, str(error))
        return None
    value_errors = parser_errors(value)
    errors.extend(value_errors)
    return None if value_errors else value


def write_atomic(path: Path, data: bytes) -> None:
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def dump_canonical(path: Path, value: Any) -> None:
    write_atomic(path, canonical_bytes(value))


def hex_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in HEX_RE for character in value)


def validate_identity(value: Any, errors: list[dict[str, Any]], path: str) -> None:
    if not isinstance(value, str) or not value or any(ord(character) < 32 or ord(character) == 127 for character in value):
        add(errors, path, "invalid-identity-string")


def validate_predecessor(value: Any, errors: list[dict[str, Any]], path: str) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        add(errors, path, "predecessor-invalid")
        return
    for field in ("envelope_id", "envelope_hash", "matrix_hash", "accepted_artifact"):
        if field not in value:
            add(errors, path + "/" + field, "predecessor-field-missing")
    validate_identity(value.get("envelope_id"), errors, path + "/envelope_id")
    for field in ("envelope_hash", "matrix_hash"):
        candidate = value.get(field)
        if isinstance(candidate, str) and not hex_sha256(candidate):
            add(errors, path + "/" + field, "invalid-hash")
    if value.get("accepted_artifact") is None:
        add(errors, path + "/accepted_artifact", "predecessor-artifact-missing")


def load_envelope(path: Path, errors: list[dict[str, Any]]) -> dict[str, Any] | None:
    value = read_json(path, errors, "envelope")
    if value is None:
        return None
    if not isinstance(value, dict):
        add(errors, "/envelope", "required-object")
        return None
    return value


def matrix_hash_of(matrix: Any) -> str:
    return digest(matrix)


def empty_ledger_root() -> str:
    return digest([])


def entry_hash_of(entry: dict[str, Any]) -> str:
    return digest({"seq": entry["seq"], "prev": entry["prev"], "payload": entry["payload"]})


def envelope_digest_input(envelope: dict[str, Any]) -> dict[str, Any]:
    return {
        "envelope_id": envelope["envelope_id"],
        "namespace": envelope["namespace"],
        "matrix_hash": envelope["matrix_hash"],
        "current_ledger_hash": envelope["current_ledger_hash"],
        "envelope_revision": envelope["envelope_revision"],
        "predecessor": envelope["predecessor"],
    }


def envelope_hash_of(envelope: dict[str, Any]) -> str:
    return digest(envelope_digest_input(envelope))


def verify_ledger(ledger: Any, errors: list[dict[str, Any]]) -> str:
    if not isinstance(ledger, list):
        add(errors, "/ledger", "required-array")
        return empty_ledger_root()
    current = empty_ledger_root()
    for index, entry in enumerate(ledger):
        path = "/ledger/" + str(index)
        if not isinstance(entry, dict):
            add(errors, path, "required-object")
            continue
        seq = entry.get("seq")
        expected_seq = index + 1
        if type(seq) is not int or seq != expected_seq:
            add(errors, path + "/seq", "ledger-seq-mismatch")
        if not isinstance(entry.get("prev"), str) or not hex_sha256(str(entry.get("prev", ""))):
            add(errors, path + "/prev", "invalid-hash")
        if "payload" not in entry:
            add(errors, path + "/payload", "ledger-payload-missing")
        if entry.get("prev") != current:
            add(errors, path + "/prev", "ledger-link-broken")
        stored_hash = entry.get("hash")
        if not isinstance(stored_hash, str) or not hex_sha256(stored_hash):
            add(errors, path + "/hash", "invalid-hash")
        if not all(field in entry for field in ("seq", "prev", "payload")):
            continue
        entry_hash = entry_hash_of(entry)
        if isinstance(stored_hash, str) and stored_hash != entry_hash:
            add(errors, path + "/hash", "ledger-entry-hash-mismatch")
        current = entry_hash
    return current


def verify_envelope_dir(directory: Path, errors: list[dict[str, Any]], predecessor_path: Path | None = None) -> dict[str, Any]:
    envelope_path = directory / "envelope.json"
    matrix_path = directory / "matrix.json"
    ledger_path = directory / "ledger.json"
    envelope = load_envelope(envelope_path, errors)
    identities: dict[str, Any] = {}
    if envelope is None:
        return identities
    for field in ("envelope_id", "namespace", "matrix_hash", "current_ledger_hash", "envelope_revision", "predecessor", "envelope_hash"):
        if field not in envelope:
            add(errors, "/envelope/" + field, "envelope-field-missing")
    validate_identity(envelope.get("envelope_id"), errors, "/envelope/envelope_id")
    validate_identity(envelope.get("namespace"), errors, "/envelope/namespace")
    revision = envelope.get("envelope_revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
        add(errors, "/envelope/envelope_revision", "non-negative-integer")
        revision = 0
    validate_predecessor(envelope.get("predecessor"), errors, "/envelope/predecessor")
    ledger = read_json(ledger_path, errors, "ledger")
    current_ledger_hash = verify_ledger(ledger, errors)
    stored_matrix_hash = envelope.get("matrix_hash")
    stored_ledger_hash = envelope.get("current_ledger_hash")
    if isinstance(stored_ledger_hash, str) and not hex_sha256(stored_ledger_hash):
        add(errors, "/envelope/current_ledger_hash", "invalid-hash")
    if revision == 0:
        if stored_matrix_hash != PENDING_MATRIX_HASH:
            add(errors, "/envelope/matrix_hash", "pending-state-violation")
        if stored_ledger_hash != empty_ledger_root():
            add(errors, "/envelope/current_ledger_hash", "pending-state-violation")
        if ledger:
            add(errors, "/ledger", "pending-state-violation")
        if matrix_path.exists():
            add(errors, "/matrix", "pending-state-violation")
    else:
        if stored_ledger_hash != current_ledger_hash:
            add(errors, "/envelope/current_ledger_hash", "ledger-hash-field-mismatch")
        if stored_matrix_hash != PENDING_MATRIX_HASH and not hex_sha256(str(stored_matrix_hash)):
            add(errors, "/envelope/matrix_hash", "invalid-hash")
        matrix = read_json(matrix_path, errors, "matrix")
        if not isinstance(matrix, dict):
            add(errors, "/matrix", "required-object")
        else:
            recomputed = matrix_hash_of(matrix)
            if stored_matrix_hash != recomputed:
                add(errors, "/envelope/matrix_hash", "matrix-hash-mismatch")
            identities["matrix_hash"] = recomputed
        if isinstance(ledger, list) and revision != len(ledger) + 1:
            add(errors, "/envelope/envelope_revision", "revision-mismatch")
    identities["current_ledger_hash"] = current_ledger_hash
    identities["envelope_revision"] = revision
    stored_hash = envelope.get("envelope_hash")
    if isinstance(stored_hash, str) and not hex_sha256(stored_hash):
        add(errors, "/envelope/envelope_hash", "invalid-hash")
    if all(field in envelope for field in ("envelope_id", "namespace", "matrix_hash", "current_ledger_hash", "envelope_revision", "predecessor")):
        recomputed_envelope_hash = envelope_hash_of(envelope)
        if stored_hash != recomputed_envelope_hash:
            add(errors, "/envelope/envelope_hash", "envelope-hash-mismatch")
        identities["envelope_hash"] = recomputed_envelope_hash
    predecessor = envelope.get("predecessor")
    if predecessor is not None:
        identities["predecessor"] = "present"
        if predecessor_path is None:
            add(errors, "/envelope/predecessor", "predecessor-unverified")
        else:
            verify_predecessor_binding(predecessor, predecessor_path, errors)
    elif predecessor_path is not None:
        add(errors, "/envelope/predecessor", "predecessor-not-declared")
    return identities


def verify_predecessor_binding(predecessor: Any, predecessor_path: Path, errors: list[dict[str, Any]]) -> None:
    if not isinstance(predecessor, dict):
        add(errors, "/envelope/predecessor", "predecessor-invalid")
        return
    pred_errors: list[dict[str, Any]] = []
    pred_envelope = load_envelope(predecessor_path, pred_errors)
    if pred_envelope is None:
        for error in pred_errors:
            add(errors, "/envelope/predecessor" + error["instance_path"], error["code"])
        return
    for field in ("envelope_id", "namespace", "matrix_hash", "current_ledger_hash", "envelope_revision", "predecessor"):
        if field not in pred_envelope:
            add(pred_errors, "/envelope/" + field, "envelope-field-missing")
    if all(field in pred_envelope for field in ("envelope_id", "namespace", "matrix_hash", "current_ledger_hash", "envelope_revision", "predecessor")):
        recomputed = envelope_hash_of(pred_envelope)
        if predecessor.get("envelope_id") != pred_envelope.get("envelope_id"):
            add(errors, "/envelope/predecessor/envelope_id", "predecessor-identity-mismatch")
        if predecessor.get("envelope_hash") != recomputed:
            add(errors, "/envelope/predecessor/envelope_hash", "predecessor-identity-mismatch")
        if predecessor.get("matrix_hash") != pred_envelope.get("matrix_hash"):
            add(errors, "/envelope/predecessor/matrix_hash", "predecessor-identity-mismatch")
    pred_ledger = read_json(predecessor_path.parent / "ledger.json", pred_errors, "ledger")
    current = verify_ledger(pred_ledger, pred_errors)
    if pred_envelope.get("current_ledger_hash") != current:
        add(errors, "/envelope/predecessor/current_ledger_hash", "predecessor-identity-mismatch")
    for error in pred_errors:
        add(errors, "/envelope/predecessor" + error["instance_path"], error["code"])


def emit(result: dict[str, Any], out: str | None = None) -> int:
    data = canonical_bytes(result)
    if out is None or out == "-":
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.write(b"\n")
    else:
        write_atomic(Path(out), data)
    if result["ok"]:
        return 0
    if any(error["code"] in {"file-missing", "file-unreadable"} for error in result["errors"]):
        return 2
    return 1


def result(operation: str, ok: bool, identities: dict[str, Any], errors: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "result_id": RESULT_ID,
        "result_version": RESULT_VERSION,
        "operation": operation,
        "ok": ok,
        "identities": identities,
        "errors": sort_errors(errors),
    }


def fail(operation: str, message: str) -> int:
    emit(result(operation, False, {}, [diagnostic("/", message)]))
    return 2


def read_input(path_value: str) -> tuple[Any, list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    if path_value == "-":
        raw = sys.stdin.buffer.read()
        try:
            value = parse_json(raw)
        except ContractError as error:
            add(errors, "/input", str(error))
            return None, errors
    else:
        value = read_json(Path(path_value), errors, "input")
        return value, errors
    if value is not None:
        errors.extend(parser_errors(value))
    return value, errors


def op_matrix_hash(args: argparse.Namespace) -> int:
    value, errors = read_input(args.input)
    if errors or value is None:
        return emit(result("matrix-hash", False, {}, errors)) or 1
    if not isinstance(value, dict):
        return emit(result("matrix-hash", False, {}, [diagnostic("/input", "required-object")])) or 1
    return emit(result("matrix-hash", True, {"matrix_hash": matrix_hash_of(value)}, []))


def op_ledger_hash(args: argparse.Namespace) -> int:
    value, errors = read_input(args.input)
    if errors or value is None:
        return emit(result("ledger-hash", False, {}, errors)) or 1
    if not isinstance(value, list):
        return emit(result("ledger-hash", False, {}, [diagnostic("/input", "required-array")])) or 1
    current = verify_ledger(value, errors)
    if errors:
        return emit(result("ledger-hash", False, {}, errors)) or 1
    return emit(result("ledger-hash", True, {"current_ledger_hash": current}, []))


def op_init(args: argparse.Namespace) -> int:
    errors: list[dict[str, Any]] = []
    validate_identity(args.envelope_id, errors, "/envelope_id")
    validate_identity(args.namespace, errors, "/namespace")
    errors.extend(parser_errors({"envelope_id": args.envelope_id, "namespace": args.namespace}))
    predecessor = None
    if args.predecessor is not None:
        if args.predecessor_artifact is None:
            return fail("init", "predecessor-artifact-required")
        validate_identity(args.predecessor_artifact, errors, "/predecessor/accepted_artifact")
        errors.extend(parser_errors(args.predecessor_artifact))
        pred_envelope = load_envelope(Path(args.predecessor), errors)
        if pred_envelope is None:
            return emit(result("init", False, {}, errors)) or 1
        if not all(field in pred_envelope for field in ("envelope_id", "namespace", "matrix_hash", "current_ledger_hash", "envelope_revision", "predecessor")):
            return emit(result("init", False, {}, [diagnostic("/predecessor", "predecessor-invalid")])) or 1
        predecessor = {
            "envelope_id": pred_envelope["envelope_id"],
            "envelope_hash": envelope_hash_of(pred_envelope),
            "matrix_hash": pred_envelope["matrix_hash"],
            "accepted_artifact": args.predecessor_artifact,
        }
        verify_predecessor_binding(predecessor, Path(args.predecessor), errors)
    if errors:
        return emit(result("init", False, {}, errors)) or 1
    directory = Path(args.dir)
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        return fail("init", "directory-unwritable")
    envelope_path = directory / "envelope.json"
    ledger_path = directory / "ledger.json"
    if envelope_path.exists() or ledger_path.exists():
        return emit(result("init", False, {}, [diagnostic("/", "already-initialized")])) or 1
    root = empty_ledger_root()
    envelope = {
        "envelope_id": args.envelope_id,
        "namespace": args.namespace,
        "matrix_hash": PENDING_MATRIX_HASH,
        "current_ledger_hash": root,
        "envelope_revision": 0,
        "predecessor": predecessor,
    }
    envelope["envelope_hash"] = envelope_hash_of(envelope)
    try:
        dump_canonical(ledger_path, [])
        dump_canonical(envelope_path, envelope)
    except OSError:
        return fail("init", "directory-unwritable")
    return emit(
        result(
            "init",
            True,
            {"envelope_id": args.envelope_id, "namespace": args.namespace, "current_ledger_hash": root, "envelope_revision": 0},
            [],
        )
    )


def op_freeze(args: argparse.Namespace) -> int:
    errors: list[dict[str, Any]] = []
    directory = Path(args.dir)
    verify_envelope_dir(directory, errors, Path(args.predecessor) if args.predecessor else None)
    if errors:
        return emit(result("freeze", False, {}, errors)) or 1
    envelope = load_envelope(directory / "envelope.json", errors)
    if envelope is None:
        return emit(result("freeze", False, {}, errors)) or 1
    if envelope.get("envelope_revision") != 0:
        return emit(result("freeze", False, {}, [diagnostic("/envelope/envelope_revision", "freeze-on-active-state")])) or 1
    ledger = read_json(directory / "ledger.json", errors, "ledger")
    if ledger is None:
        ledger = []
    if ledger:
        return emit(result("freeze", False, {}, [diagnostic("/ledger", "freeze-on-active-state")])) or 1
    matrix, matrix_errors = read_input(args.matrix)
    errors.extend(matrix_errors)
    if errors or not isinstance(matrix, dict):
        if not errors:
            errors.append(diagnostic("/matrix", "required-object"))
        return emit(result("freeze", False, {}, errors)) or 1
    matrix_path = directory / "matrix.json"
    try:
        dump_canonical(matrix_path, matrix)
    except OSError:
        return fail("freeze", "directory-unwritable")
    matrix_h = matrix_hash_of(matrix)
    envelope["matrix_hash"] = matrix_h
    envelope["current_ledger_hash"] = empty_ledger_root()
    envelope["envelope_revision"] = 1
    envelope["envelope_hash"] = envelope_hash_of(envelope)
    try:
        dump_canonical(directory / "envelope.json", envelope)
    except OSError:
        return fail("freeze", "directory-unwritable")
    return emit(
        result(
            "freeze",
            True,
            {"matrix_hash": matrix_h, "current_ledger_hash": envelope["current_ledger_hash"], "envelope_revision": 1, "envelope_hash": envelope["envelope_hash"]},
            [],
        )
    )


def op_append(args: argparse.Namespace) -> int:
    errors: list[dict[str, Any]] = []
    directory = Path(args.dir)
    verify_envelope_dir(directory, errors, Path(args.predecessor) if args.predecessor else None)
    if errors:
        return emit(result("append", False, {}, errors)) or 1
    envelope = load_envelope(directory / "envelope.json", errors)
    if envelope is None:
        return emit(result("append", False, {}, errors)) or 1
    if envelope.get("envelope_revision", 0) < 1:
        return emit(result("append", False, {}, [diagnostic("/envelope/envelope_revision", "not-frozen")])) or 1
    ledger = read_json(directory / "ledger.json", errors, "ledger")
    if ledger is None:
        ledger = []
    if not isinstance(ledger, list):
        return emit(result("append", False, {}, [diagnostic("/ledger", "required-array")])) or 1
    current = verify_ledger(ledger, errors)
    if errors:
        return emit(result("append", False, {}, errors)) or 1
    payload, payload_errors = read_input(args.payload)
    errors.extend(payload_errors)
    if errors or not isinstance(payload, dict):
        if not errors:
            errors.append(diagnostic("/payload", "required-object"))
        return emit(result("append", False, {}, errors)) or 1
    entry = {"seq": len(ledger) + 1, "prev": current, "payload": payload}
    entry["hash"] = entry_hash_of(entry)
    ledger.append(entry)
    envelope["current_ledger_hash"] = entry["hash"]
    envelope["envelope_revision"] = int(envelope["envelope_revision"]) + 1
    envelope["envelope_hash"] = envelope_hash_of(envelope)
    prospective_writes: list[tuple[Path, bytes]] = []
    for document_path, document in ((directory / "ledger.json", ledger), (directory / "envelope.json", envelope)):
        document_errors = parser_errors(document)
        errors.extend(document_errors)
        if document_errors:
            continue
        data = canonical_bytes(document)
        if len(data) > MAX_DOCUMENT_BYTES:
            add(errors, "/" + document_path.stem, "document-too-large")
        prospective_writes.append((document_path, data))
    if errors:
        return emit(result("append", False, {}, errors)) or 1
    try:
        for document_path, data in prospective_writes:
            write_atomic(document_path, data)
    except OSError:
        return fail("append", "directory-unwritable")
    return emit(
        result(
            "append",
            True,
            {"seq": entry["seq"], "current_ledger_hash": entry["hash"], "envelope_revision": envelope["envelope_revision"], "envelope_hash": envelope["envelope_hash"]},
            [],
        )
    )


def op_verify(args: argparse.Namespace) -> int:
    errors: list[dict[str, Any]] = []
    identities = verify_envelope_dir(Path(args.dir), errors, Path(args.predecessor) if args.predecessor else None)
    if errors:
        return emit(result("verify", False, identities, errors)) or 1
    return emit(result("verify", True, identities, []))


def build_parser() -> argparse.ArgumentParser:
    parser = ResultArgumentParser(prog="review_record_envelope.py", description="Offline review-record envelope tooling.")
    subparsers = parser.add_subparsers(dest="operation", required=True)

    matrix_parser = subparsers.add_parser("matrix-hash", help="hash a frozen matrix object")
    matrix_parser.add_argument("--input", required=True, help="matrix JSON path or - for stdin")
    matrix_parser.set_defaults(handler=op_matrix_hash)

    ledger_parser = subparsers.add_parser("ledger-hash", help="validate a ledger and report the current ledger hash")
    ledger_parser.add_argument("--input", required=True, help="ledger JSON path or - for stdin")
    ledger_parser.set_defaults(handler=op_ledger_hash)

    init_parser = subparsers.add_parser("init", help="create a pending envelope directory")
    init_parser.add_argument("--dir", required=True, help="envelope directory (created if missing)")
    init_parser.add_argument("--envelope-id", required=True, help="envelope identifier")
    init_parser.add_argument("--namespace", required=True, help="requirement and finding namespace")
    init_parser.add_argument("--predecessor", default=None, help="predecessor envelope.json path to bind as lineage")
    init_parser.add_argument("--predecessor-artifact", default=None, help="predecessor accepted-artifact reference (required with --predecessor)")
    init_parser.set_defaults(handler=op_init)

    freeze_parser = subparsers.add_parser("freeze", help="freeze a matrix (pending -> revision 1)")
    freeze_parser.add_argument("--dir", required=True, help="envelope directory")
    freeze_parser.add_argument("--matrix", required=True, help="matrix JSON path or - for stdin")
    freeze_parser.add_argument("--predecessor", default=None, help="predecessor envelope.json path to bind against")
    freeze_parser.set_defaults(handler=op_freeze)

    append_parser = subparsers.add_parser("append", help="append a finding/disposition payload entry")
    append_parser.add_argument("--dir", required=True, help="envelope directory")
    append_parser.add_argument("--payload", required=True, help="payload JSON object path or - for stdin")
    append_parser.add_argument("--predecessor", default=None, help="predecessor envelope.json path to bind against")
    append_parser.set_defaults(handler=op_append)

    verify_parser = subparsers.add_parser("verify", help="recompute and verify all envelope identities")
    verify_parser.add_argument("--dir", required=True, help="envelope directory")
    verify_parser.add_argument("--predecessor", default=None, help="predecessor envelope.json path to bind against")
    verify_parser.set_defaults(handler=op_verify)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = sys.argv[1:] if argv is None else argv
    operation = arguments[0] if arguments and arguments[0] in {"matrix-hash", "ledger-hash", "init", "freeze", "append", "verify"} else "invocation"
    try:
        args = parser.parse_args(arguments)
    except InvocationError:
        return fail(operation, "invocation-error")
    try:
        return args.handler(args)
    except OSError:
        return fail(operation, "io-error")


if __name__ == "__main__":
    sys.exit(main())
