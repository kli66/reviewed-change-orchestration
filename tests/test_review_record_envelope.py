from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "review_record_envelope.py"

EMPTY_LEDGER_ROOT = "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
SIMPLE_MATRIX = {"matrix_revision": "1", "pinned_sources": {}, "requirements": [], "work_packages": []}
SIMPLE_MATRIX_HASH = "26a2795bce6aa02a09584eb68094a43d98a9e10fa522f7972056161f17f2fde2"
FREEZE_MATRIX = {"matrix_revision": "1", "requirements": []}
FREEZE_MATRIX_HASH = "ce1660c2d7e874a324fba4e413bd378ee524ec62d44fea1a3625e9f98a7b3ebb"


def invoke_bytes(*args: str, stdin: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=stdin,
        capture_output=True,
        check=False,
    )


def invoke(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess[bytes]:
    return invoke_bytes(*args, stdin=None if stdin is None else stdin.encode("utf-8"))


def result_of(proc: subprocess.CompletedProcess[bytes]) -> dict[str, Any]:
    return json.loads(proc.stdout.decode("utf-8"))


def edit_json(path: Path, edit: Callable[[dict[str, Any]], None]) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))
    edit(value)
    path.write_text(json.dumps(value), encoding="utf-8")


class ReviewRecordEnvelopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name) / "env"
        self.simple_matrix = json.dumps(SIMPLE_MATRIX)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def init(self, envelope_id: str = "rco-test-001", namespace: str = "test-ns-1", *, predecessor: str | None = None, artifact: str | None = None) -> subprocess.CompletedProcess[bytes]:
        args = ["init", "--dir", str(self.dir), "--envelope-id", envelope_id, "--namespace", namespace]
        if predecessor is not None:
            args += ["--predecessor", predecessor, "--predecessor-artifact", artifact or "0b5e245:path/change.md"]
        return invoke(*args)

    def freeze(self, matrix: dict[str, Any] | None = None, *, predecessor: str | None = None) -> subprocess.CompletedProcess[bytes]:
        args = ["freeze", "--dir", str(self.dir), "--matrix", "-"]
        if predecessor is not None:
            args += ["--predecessor", predecessor]
        return invoke(*args, stdin=json.dumps(matrix if matrix is not None else FREEZE_MATRIX))

    def append(self, payload: dict[str, Any], *, predecessor: str | None = None) -> subprocess.CompletedProcess[bytes]:
        args = ["append", "--dir", str(self.dir), "--payload", "-"]
        if predecessor is not None:
            args += ["--predecessor", predecessor]
        return invoke(*args, stdin=json.dumps(payload))

    def verify(self, predecessor: str | None = None) -> subprocess.CompletedProcess[bytes]:
        args = ["verify", "--dir", str(self.dir)]
        if predecessor is not None:
            args += ["--predecessor", predecessor]
        return invoke(*args)

    def prepared(self) -> None:
        init = self.init()
        self.assertEqual(init.returncode, 0, init.stdout)
        freeze = self.freeze()
        self.assertEqual(freeze.returncode, 0, freeze.stdout)

    # --- identity primitives -------------------------------------------------

    def test_matrix_hash_known_vector(self) -> None:
        proc = invoke("matrix-hash", "--input", "-", stdin=self.simple_matrix)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = result_of(proc)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["identities"]["matrix_hash"], SIMPLE_MATRIX_HASH)

    def test_matrix_hash_requires_object(self) -> None:
        proc = invoke("matrix-hash", "--input", "-", stdin="[1,2]")
        self.assertEqual(proc.returncode, 1)
        self.assertFalse(result_of(proc)["ok"])
        self.assertEqual(result_of(proc)["errors"][0]["code"], "required-object")

    def test_empty_ledger_root_known_vector(self) -> None:
        proc = invoke("ledger-hash", "--input", "-", stdin="[]")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(result_of(proc)["identities"]["current_ledger_hash"], EMPTY_LEDGER_ROOT)

    def test_canonical_identity_ignores_key_order_and_whitespace(self) -> None:
        proc = invoke("matrix-hash", "--input", "-", stdin='{ "work_packages" : [], "requirements" : [], "pinned_sources" : {}, "matrix_revision" : "1" }')
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(result_of(proc)["identities"]["matrix_hash"], SIMPLE_MATRIX_HASH)

    # --- lifecycle -----------------------------------------------------------

    def test_init_creates_pending_envelope(self) -> None:
        proc = self.init()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        envelope = json.loads((self.dir / "envelope.json").read_text(encoding="utf-8"))
        self.assertEqual(envelope["envelope_revision"], 0)
        self.assertEqual(envelope["matrix_hash"], "PENDING")
        self.assertEqual(envelope["current_ledger_hash"], EMPTY_LEDGER_ROOT)
        self.assertIsNone(envelope["predecessor"])
        verify = self.verify()
        self.assertEqual(verify.returncode, 0, verify.stdout)
        self.assertEqual(result_of(verify)["identities"]["envelope_revision"], 0)

    def test_init_refuses_existing(self) -> None:
        self.init()
        proc = self.init()
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(result_of(proc)["errors"][0]["code"], "already-initialized")

    def test_freeze_transitions_to_revision_one(self) -> None:
        self.init()
        proc = self.freeze()
        self.assertEqual(proc.returncode, 0, proc.stdout)
        payload = result_of(proc)
        self.assertEqual(payload["identities"]["matrix_hash"], FREEZE_MATRIX_HASH)
        self.assertEqual(payload["identities"]["envelope_revision"], 1)
        self.assertEqual(payload["identities"]["current_ledger_hash"], EMPTY_LEDGER_ROOT)
        verify = self.verify()
        self.assertEqual(verify.returncode, 0, verify.stdout)
        self.assertEqual(result_of(verify)["identities"]["matrix_hash"], FREEZE_MATRIX_HASH)

    def test_freeze_refuses_active_state(self) -> None:
        self.init()
        self.freeze()
        proc = self.freeze()
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(result_of(proc)["errors"][0]["code"], "freeze-on-active-state")

    def test_append_before_freeze_refused(self) -> None:
        self.init()
        proc = self.append({"finding_id": "F-001"})
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(result_of(proc)["errors"][0]["code"], "not-frozen")

    def test_append_chains_entries_and_advances_revision(self) -> None:
        self.prepared()
        first = self.append({"finding_id": "F-001", "severity": "Minor"})
        self.assertEqual(first.returncode, 0, first.stdout)
        first_payload = result_of(first)
        self.assertEqual(first_payload["identities"]["seq"], 1)
        self.assertEqual(first_payload["identities"]["envelope_revision"], 2)
        second = self.append({"finding_id": "F-001", "disposition": "accepted_residual"})
        self.assertEqual(second.returncode, 0, second.stdout)
        second_payload = result_of(second)
        self.assertEqual(second_payload["identities"]["seq"], 2)
        self.assertEqual(second_payload["identities"]["envelope_revision"], 3)
        self.assertNotEqual(first_payload["identities"]["current_ledger_hash"], second_payload["identities"]["current_ledger_hash"])
        ledger = json.loads((self.dir / "ledger.json").read_text(encoding="utf-8"))
        self.assertEqual([entry["seq"] for entry in ledger], [1, 2])
        self.assertEqual(ledger[1]["prev"], ledger[0]["hash"])
        verify = self.verify()
        self.assertEqual(verify.returncode, 0, verify.stdout)
        self.assertEqual(result_of(verify)["identities"]["current_ledger_hash"], second_payload["identities"]["current_ledger_hash"])
        self.assertEqual(result_of(verify)["identities"]["envelope_hash"], second_payload["identities"]["envelope_hash"])

    def test_ledger_hash_independent_recompute(self) -> None:
        self.prepared()
        self.append({"finding_id": "F-001"})
        ledger = (self.dir / "ledger.json").read_text(encoding="utf-8")
        proc = invoke("ledger-hash", "--input", "-", stdin=ledger)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(result_of(proc)["identities"]["current_ledger_hash"], result_of(self.verify())["identities"]["current_ledger_hash"])

    # --- tamper detection ----------------------------------------------------

    def test_verify_detects_matrix_tamper(self) -> None:
        self.prepared()
        edit_json(self.dir / "matrix.json", lambda matrix: matrix["requirements"].append({"id": "REQ-999"}))
        proc = self.verify()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("matrix-hash-mismatch", [error["code"] for error in result_of(proc)["errors"]])

    def test_verify_detects_ledger_payload_tamper(self) -> None:
        self.prepared()
        self.append({"finding_id": "F-001"})
        edit_json(self.dir / "ledger.json", lambda ledger: ledger[0]["payload"].update({"severity": "Critical"}))
        proc = self.verify()
        self.assertEqual(proc.returncode, 1)
        codes = [error["code"] for error in result_of(proc)["errors"]]
        self.assertIn("ledger-entry-hash-mismatch", codes)

    def test_verify_detects_prev_link_break(self) -> None:
        self.prepared()
        self.append({"finding_id": "F-001"})
        self.append({"finding_id": "F-001"})
        edit_json(self.dir / "ledger.json", lambda ledger: ledger[1].update({"prev": "0" * 64}))
        proc = self.verify()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("ledger-link-broken", [error["code"] for error in result_of(proc)["errors"]])

    def test_verify_detects_entry_swap(self) -> None:
        self.prepared()
        self.append({"finding_id": "F-001", "note": "first"})
        self.append({"finding_id": "F-001", "note": "second"})
        edit_json(self.dir / "ledger.json", lambda ledger: ledger.reverse())
        proc = self.verify()
        self.assertEqual(proc.returncode, 1)
        codes = [error["code"] for error in result_of(proc)["errors"]]
        self.assertIn("ledger-seq-mismatch", codes)
        self.assertIn("ledger-link-broken", codes)

    def test_verify_detects_revision_drift(self) -> None:
        self.prepared()
        self.append({"finding_id": "F-001"})
        self.append({"finding_id": "F-001"})
        edit_json(self.dir / "envelope.json", lambda envelope: envelope.update({"envelope_revision": 2}))
        proc = self.verify()
        self.assertEqual(proc.returncode, 1)
        codes = [error["code"] for error in result_of(proc)["errors"]]
        self.assertIn("revision-mismatch", codes)
        self.assertIn("envelope-hash-mismatch", codes)

    def test_verify_detects_stale_envelope_hash(self) -> None:
        self.prepared()
        self.append({"finding_id": "F-001"})
        edit_json(self.dir / "envelope.json", lambda envelope: envelope.update({"namespace": "tampered-ns"}))
        proc = self.verify()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("envelope-hash-mismatch", [error["code"] for error in result_of(proc)["errors"]])

    def test_verify_detects_ledger_hash_field_drift(self) -> None:
        self.prepared()
        self.append({"finding_id": "F-001"})
        edit_json(self.dir / "envelope.json", lambda envelope: envelope.update({"current_ledger_hash": "1" * 64}))
        proc = self.verify()
        self.assertEqual(proc.returncode, 1)
        codes = [error["code"] for error in result_of(proc)["errors"]]
        self.assertIn("ledger-hash-field-mismatch", codes)
        self.assertIn("envelope-hash-mismatch", codes)

    def test_verify_detects_pending_state_violations(self) -> None:
        self.init()
        (self.dir / "matrix.json").write_text(json.dumps(FREEZE_MATRIX), encoding="utf-8")
        edit_json(self.dir / "envelope.json", lambda envelope: envelope.update({"matrix_hash": "1" * 64}))
        proc = self.verify()
        self.assertEqual(proc.returncode, 1)
        codes = [error["code"] for error in result_of(proc)["errors"]]
        self.assertIn("pending-state-violation", codes)
        self.assertIn("envelope-hash-mismatch", codes)

    def test_verify_missing_envelope(self) -> None:
        proc = self.verify()
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(result_of(proc)["errors"][0]["code"], "file-missing")

    # --- predecessor lineage -------------------------------------------------

    def _predecessor_env(self, name: str) -> Path:
        directory = Path(self._tmp.name) / name
        proc = invoke("init", "--dir", str(directory), "--envelope-id", "rco-pred-" + name, "--namespace", "ns-" + name)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        proc = invoke("freeze", "--dir", str(directory), "--matrix", "-", stdin=json.dumps({"matrix_revision": "1", "requirements": []}))
        self.assertEqual(proc.returncode, 0, proc.stdout)
        proc = invoke("append", "--dir", str(directory), "--payload", "-", stdin=json.dumps({"finding_id": "F-001"}))
        self.assertEqual(proc.returncode, 0, proc.stdout)
        return directory

    def test_successor_binds_predecessor_lineage(self) -> None:
        predecessor_dir = self._predecessor_env("alpha")
        proc = self.init(envelope_id="rco-test-succ-001", namespace="ns-succ-1", predecessor=str(predecessor_dir / "envelope.json"), artifact="0b5e245:docs/changes/x/change.md")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        envelope = json.loads((self.dir / "envelope.json").read_text(encoding="utf-8"))
        predecessor = envelope["predecessor"]
        self.assertIsNotNone(predecessor)
        self.assertEqual(predecessor["envelope_id"], "rco-pred-alpha")
        self.assertEqual(predecessor["accepted_artifact"], "0b5e245:docs/changes/x/change.md")
        self.assertEqual(len(predecessor["envelope_hash"]), 64)
        self.assertEqual(len(predecessor["matrix_hash"]), 64)
        self.assertEqual(envelope["matrix_hash"], "PENDING")
        proc = self.freeze(predecessor=str(predecessor_dir / "envelope.json"))
        self.assertEqual(proc.returncode, 0, proc.stdout)
        proc = self.append({"finding_id": "F-002"}, predecessor=str(predecessor_dir / "envelope.json"))
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertEqual(result_of(proc)["identities"]["envelope_revision"], 2)
        proc = self.verify(predecessor=str(predecessor_dir / "envelope.json"))
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertTrue(result_of(proc)["ok"])

    def test_verify_requires_predecessor_proof(self) -> None:
        predecessor_dir = self._predecessor_env("bravo")
        self.init(envelope_id="rco-test-succ-002", namespace="ns-succ-2", predecessor=str(predecessor_dir / "envelope.json"), artifact="0b5e245:path")
        proc = self.freeze(predecessor=str(predecessor_dir / "envelope.json"))
        self.assertEqual(proc.returncode, 0, proc.stdout)
        proc = self.verify()
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(result_of(proc)["errors"][0]["code"], "predecessor-unverified")

    def test_verify_detects_predecessor_mismatch(self) -> None:
        predecessor_dir = self._predecessor_env("charlie")
        wrong_dir = self._predecessor_env("delta")
        self.init(envelope_id="rco-test-succ-003", namespace="ns-succ-3", predecessor=str(predecessor_dir / "envelope.json"), artifact="0b5e245:path")
        proc = self.freeze(predecessor=str(predecessor_dir / "envelope.json"))
        self.assertEqual(proc.returncode, 0, proc.stdout)
        proc = self.verify(predecessor=str(wrong_dir / "envelope.json"))
        self.assertEqual(proc.returncode, 1)
        codes = [error["code"] for error in result_of(proc)["errors"]]
        self.assertIn("predecessor-identity-mismatch", codes)

    def test_init_predecessor_requires_artifact(self) -> None:
        predecessor_dir = self._predecessor_env("echo")
        proc = invoke("init", "--dir", str(self.dir), "--envelope-id", "x", "--namespace", "y", "--predecessor", str(predecessor_dir / "envelope.json"))
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(result_of(proc)["errors"][0]["code"], "predecessor-artifact-required")

    # --- value-free and parser guards ----------------------------------------

    def test_errors_are_value_free(self) -> None:
        secret = "supersecretvalue-xyz-123"
        self.prepared()
        proc = self.append({"finding_id": "F-001", "secret_marker": secret, secret: 1})
        self.assertEqual(proc.returncode, 0, proc.stdout)
        edit_json(self.dir / "ledger.json", lambda ledger: ledger[0]["payload"].update({secret: 1.5}))
        self.assertIn(secret, (self.dir / "ledger.json").read_text(encoding="utf-8"))
        proc = self.verify()
        self.assertEqual(proc.returncode, 1)
        self.assertFalse(result_of(proc)["ok"])
        self.assertIn("non-integer-number", [error["code"] for error in result_of(proc)["errors"]])
        for output in (proc.stdout, proc.stderr):
            self.assertNotIn(secret.encode("utf-8"), output)

    def test_invalid_json_rejected(self) -> None:
        proc = invoke("matrix-hash", "--input", "-", stdin="{not json")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(result_of(proc)["errors"][0]["code"], "invalid-json")

    def test_duplicate_names_rejected(self) -> None:
        proc = invoke("matrix-hash", "--input", "-", stdin='{"a": 1, "a": 2}')
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(result_of(proc)["errors"][0]["code"], "duplicate-object-name")

    def test_non_finite_rejected(self) -> None:
        proc = invoke("matrix-hash", "--input", "-", stdin='{"a": NaN}')
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(result_of(proc)["errors"][0]["code"], "non-finite-number")

    def test_non_integer_number_rejected(self) -> None:
        proc = invoke("matrix-hash", "--input", "-", stdin='{"a": 1.5}')
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(result_of(proc)["errors"][0]["code"], "non-integer-number")

    def test_document_size_guard_bounds(self) -> None:
        raw = json.dumps(SIMPLE_MATRIX).encode("utf-8")
        exact = raw + b" " * (8 * 1024 * 1024 - len(raw))
        self.assertEqual(len(exact), 8 * 1024 * 1024)
        exact_proc = invoke_bytes("matrix-hash", "--input", "-", stdin=exact)
        self.assertEqual(exact_proc.returncode, 0, exact_proc.stdout)
        self.assertTrue(result_of(exact_proc)["ok"])
        over_proc = invoke_bytes("matrix-hash", "--input", "-", stdin=exact + b" ")
        self.assertEqual(over_proc.returncode, 1)
        self.assertEqual(result_of(over_proc)["errors"][0]["code"], "document-too-large")

    def test_depth_guard_bounds(self) -> None:
        for wraps, expected_ok in ((63, True), (64, False)):
            nested: dict[str, Any] = {}
            for _ in range(wraps):
                nested = {"x": nested}
            proc = invoke("matrix-hash", "--input", "-", stdin=json.dumps(nested))
            payload = result_of(proc)
            if expected_ok:
                self.assertEqual(proc.returncode, 0, proc.stdout)
                self.assertTrue(payload["ok"])
            else:
                self.assertEqual(proc.returncode, 1)
                self.assertEqual(payload["errors"][0]["code"], "depth-exceeded")

    def test_container_guard_bounds(self) -> None:
        for count, expected_ok in ((10_000, True), (10_001, False)):
            document = {f"k{index:05d}": index for index in range(count)}
            proc = invoke("matrix-hash", "--input", "-", stdin=json.dumps(document))
            payload = result_of(proc)
            if expected_ok:
                self.assertEqual(proc.returncode, 0, proc.stdout)
                self.assertTrue(payload["ok"])
            else:
                self.assertEqual(proc.returncode, 1)
                self.assertEqual(payload["errors"][0]["code"], "container-too-large")

    def test_string_size_guard_bounds(self) -> None:
        for size, expected_ok in ((1024 * 1024, True), (1024 * 1024 + 1, False)):
            document = {"a": "x" * size}
            proc = invoke("matrix-hash", "--input", "-", stdin=json.dumps(document))
            payload = result_of(proc)
            if expected_ok:
                self.assertEqual(proc.returncode, 0, proc.stdout)
                self.assertTrue(payload["ok"])
            else:
                self.assertEqual(proc.returncode, 1)
                self.assertEqual(payload["errors"][0]["code"], "string-too-large")

    def test_string_not_nfc_rejected(self) -> None:
        proc = invoke("matrix-hash", "--input", "-", stdin=json.dumps({"a": "e\u0301"}))
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(result_of(proc)["errors"][0]["code"], "string-not-nfc")

    def snapshot(self) -> dict[str, bytes]:
        if not self.dir.exists():
            return {}
        return {path.name: path.read_bytes() for path in self.dir.iterdir() if path.is_file()}

    def assert_refused(self, proc: subprocess.CompletedProcess[bytes], code: str, *, exit_code: int = 1) -> None:
        self.assertEqual(proc.returncode, exit_code, proc.stdout + proc.stderr)
        payload = result_of(proc)
        self.assertFalse(payload["ok"])
        self.assertIn(code, [error["code"] for error in payload["errors"]])

    def assert_protocol(self, proc: subprocess.CompletedProcess[bytes], operation: str) -> None:
        payload = result_of(proc)
        self.assertEqual(payload["result_id"], "reviewed-change-orchestration.review-record-envelope-result")
        self.assertEqual(payload["result_version"], "0.1.0")
        self.assertEqual(payload["operation"], operation)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.assertEqual(proc.stdout, canonical + b"\n")
        self.assertEqual(proc.stderr, b"")

    def test_init_rejects_invalid_identity_without_writes(self) -> None:
        for envelope_id, namespace in (("", "ns"), ("id", ""), ("id\n", "ns"), ("id", "e\u0301")):
            with self.subTest(envelope_id=envelope_id, namespace=namespace):
                proc = self.init(envelope_id=envelope_id, namespace=namespace)
                self.assertEqual(proc.returncode, 1, proc.stdout)
                self.assertFalse(result_of(proc)["ok"])
                self.assertFalse(self.dir.exists())

    def test_freeze_rejects_parser_errors_without_writes(self) -> None:
        self.assertEqual(self.init().returncode, 0)
        before = self.snapshot()
        for matrix, code in (({"bad": 1.5}, "non-integer-number"), ({"bad": "e\u0301"}, "string-not-nfc")):
            with self.subTest(code=code):
                proc = self.freeze(matrix)
                self.assert_refused(proc, code)
                self.assertEqual(self.snapshot(), before)

    def test_append_rejects_parser_errors_without_writes(self) -> None:
        self.prepared()
        before = self.snapshot()
        for payload, code in (({"bad": 1.5}, "non-integer-number"), ({"bad": "e\u0301"}, "string-not-nfc")):
            with self.subTest(code=code):
                proc = self.append(payload)
                self.assert_refused(proc, code)
                self.assertEqual(self.snapshot(), before)

    def test_init_rejects_predecessor_parser_errors_without_writes(self) -> None:
        predecessor = self._predecessor_env("parser-error") / "envelope.json"
        edit_json(predecessor, lambda envelope: envelope.update({"extra": "e\u0301"}))
        proc = self.init(predecessor=str(predecessor))
        self.assert_refused(proc, "string-not-nfc")
        self.assertFalse(self.dir.exists())

    def test_verify_rejects_non_object_matrix(self) -> None:
        self.prepared()
        for matrix in ([], None, "matrix", 1, True):
            with self.subTest(matrix=matrix):
                (self.dir / "matrix.json").write_text(json.dumps(matrix), encoding="utf-8")
                self.assert_refused(self.verify(), "required-object")

    def test_verify_rejects_non_array_ledger(self) -> None:
        self.prepared()
        for ledger in ({}, None, "ledger", 1, True):
            with self.subTest(ledger=ledger):
                (self.dir / "ledger.json").write_text(json.dumps(ledger), encoding="utf-8")
                self.assert_refused(self.verify(), "required-array")

    def test_ledger_sequence_uses_stored_type_and_value(self) -> None:
        self.prepared()
        self.assertEqual(self.append({"finding_id": "F-005"}).returncode, 0)
        path = self.dir / "ledger.json"
        original = path.read_bytes()
        for sequence in (True, 1.0, "1", 2):
            with self.subTest(sequence=sequence):
                path.write_bytes(original)
                edit_json(path, lambda ledger: ledger[0].update({"seq": sequence}))
                proc = self.verify()
                self.assert_refused(proc, "ledger-seq-mismatch")
                self.assertIn("ledger-entry-hash-mismatch", [error["code"] for error in result_of(proc)["errors"]])
                self.assert_refused(invoke("ledger-hash", "--input", str(path)), "ledger-seq-mismatch")

    def test_verify_requires_explicit_predecessor_null(self) -> None:
        self.prepared()
        edit_json(self.dir / "envelope.json", lambda envelope: envelope.pop("predecessor"))
        self.assert_refused(self.verify(), "envelope-field-missing")

    def test_predecessor_rejects_stored_entry_hash_tamper(self) -> None:
        predecessor_dir = self._predecessor_env("entry-hash")
        self.assertEqual(self.init(predecessor=str(predecessor_dir / "envelope.json")).returncode, 0)
        edit_json(predecessor_dir / "ledger.json", lambda ledger: ledger[0].update({"hash": "0" * 64}))
        self.assert_refused(self.verify(predecessor=str(predecessor_dir / "envelope.json")), "ledger-entry-hash-mismatch")

    def test_predecessor_rejects_broken_link_suffix(self) -> None:
        predecessor_dir = self._predecessor_env("broken-link")
        self.assertEqual(self.init(predecessor=str(predecessor_dir / "envelope.json")).returncode, 0)
        edit_json(predecessor_dir / "ledger.json", lambda ledger: ledger.append({"seq": 2, "prev": "0" * 64, "payload": {}, "hash": "0" * 64}))
        self.assert_refused(self.verify(predecessor=str(predecessor_dir / "envelope.json")), "ledger-link-broken")

    def test_predecessor_propagates_ledger_parse_errors(self) -> None:
        predecessor_dir = self._predecessor_env("ledger-parse")
        self.assertEqual(self.init(predecessor=str(predecessor_dir / "envelope.json")).returncode, 0)
        (predecessor_dir / "ledger.json").write_text('[{"seq":1,"seq":1}]', encoding="utf-8")
        self.assert_refused(self.verify(predecessor=str(predecessor_dir / "envelope.json")), "duplicate-object-name")

    def test_predecessor_propagates_envelope_parser_errors(self) -> None:
        predecessor = self._predecessor_env("envelope-parse") / "envelope.json"
        self.assertEqual(self.init(predecessor=str(predecessor)).returncode, 0)
        edit_json(predecessor, lambda envelope: envelope.update({"extra": "e\u0301"}))
        self.assert_refused(self.verify(predecessor=str(predecessor)), "string-not-nfc")

    def test_argument_errors_emit_canonical_result(self) -> None:
        for args, operation in (((), "invocation"), (("unknown-secret-marker",), "invocation"), (("matrix-hash",), "matrix-hash"), (("verify", "--dir", str(self.dir), "--secret-marker"), "verify")):
            with self.subTest(args=args):
                proc = invoke(*args)
                self.assert_refused(proc, "invocation-error", exit_code=2)
                self.assert_protocol(proc, operation)
                self.assertNotIn(b"secret-marker", proc.stdout + proc.stderr)

    def test_missing_input_emits_io_result(self) -> None:
        for operation in ("matrix-hash", "ledger-hash"):
            with self.subTest(operation=operation):
                proc = invoke(operation, "--input", str(self.dir / "missing.json"))
                self.assert_refused(proc, "file-missing", exit_code=2)
                self.assert_protocol(proc, operation)

    def test_mutation_missing_input_preserves_state(self) -> None:
        self.assertEqual(self.init().returncode, 0)
        before = self.snapshot()
        proc = invoke("freeze", "--dir", str(self.dir), "--matrix", str(self.dir / "missing.json"))
        self.assert_refused(proc, "file-missing", exit_code=2)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.freeze().returncode, 0)
        before = self.snapshot()
        proc = invoke("append", "--dir", str(self.dir), "--payload", str(self.dir / "missing.json"))
        self.assert_refused(proc, "file-missing", exit_code=2)
        self.assertEqual(self.snapshot(), before)

    def test_unpaired_surrogates_emit_value_free_result(self) -> None:
        for raw in (b'{"marker":"\\ud800"}', b'{"\\udfff":1}'):
            with self.subTest(raw=raw):
                proc = invoke_bytes("matrix-hash", "--input", "-", stdin=raw)
                self.assert_refused(proc, "invalid-unicode")
                self.assert_protocol(proc, "matrix-hash")
                self.assertNotIn(b"marker", proc.stdout + proc.stderr)
                self.assertNotIn(b"Traceback", proc.stdout + proc.stderr)

    def test_mutation_rejects_surrogate_without_writes(self) -> None:
        self.assertEqual(self.init().returncode, 0)
        before = self.snapshot()
        proc = invoke_bytes("freeze", "--dir", str(self.dir), "--matrix", "-", stdin=b'{"marker":"\\ud800"}')
        self.assert_refused(proc, "invalid-unicode")
        self.assert_protocol(proc, "freeze")
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.freeze().returncode, 0)
        before = self.snapshot()
        proc = invoke_bytes("append", "--dir", str(self.dir), "--payload", "-", stdin=b'{"marker":"\\ud800"}')
        self.assert_refused(proc, "invalid-unicode")
        self.assert_protocol(proc, "append")
        self.assertEqual(self.snapshot(), before)

    def test_append_checks_wrapped_payload_depth_before_writes(self) -> None:
        self.prepared()
        payload: dict[str, Any] = {}
        for _ in range(61):
            payload = {"nested": payload}
        proc = self.append(payload)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.verify().returncode, 0)
        payload = {"nested": payload}
        standalone = invoke("matrix-hash", "--input", "-", stdin=json.dumps(payload))
        self.assertEqual(standalone.returncode, 0, standalone.stdout + standalone.stderr)
        before = self.snapshot()
        proc = self.append(payload)
        self.assert_refused(proc, "depth-exceeded")
        self.assert_protocol(proc, "append")
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.verify().returncode, 0)

    def test_append_checks_complete_ledger_size_before_writes(self) -> None:
        self.prepared()
        payload = {"part-" + str(index): "x" * (1024 * 1024) for index in range(7)}
        proc = self.append(payload)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        ledger = json.loads((self.dir / "ledger.json").read_bytes())
        next_entry = {"seq": 2, "prev": ledger[-1]["hash"], "payload": {"tail": ""}, "hash": "0" * 64}
        size_without_tail = len(json.dumps(ledger + [next_entry], sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8"))
        tail_size = 8 * 1024 * 1024 - size_without_tail
        self.assertGreater(tail_size, 0)
        self.assertLessEqual(tail_size, 1024 * 1024)
        proc = self.append({"tail": "x" * tail_size})
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual((self.dir / "ledger.json").stat().st_size, 8 * 1024 * 1024)
        self.assertEqual(self.verify().returncode, 0)
        before = self.snapshot()
        proc = self.append({})
        self.assert_refused(proc, "document-too-large")
        self.assert_protocol(proc, "append")
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.verify().returncode, 0)

    def test_append_checks_ledger_container_limit_before_writes(self) -> None:
        self.prepared()
        ledger = []
        current = EMPTY_LEDGER_ROOT
        for sequence in range(1, 10_001):
            entry = {"seq": sequence, "prev": current, "payload": {}}
            current = hashlib.sha256(json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()
            entry["hash"] = current
            ledger.append(entry)
        (self.dir / "ledger.json").write_bytes(json.dumps(ledger, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8"))
        envelope = json.loads((self.dir / "envelope.json").read_bytes())
        envelope["current_ledger_hash"] = current
        envelope["envelope_revision"] = 10_001
        identity = {key: value for key, value in envelope.items() if key != "envelope_hash"}
        envelope["envelope_hash"] = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()
        (self.dir / "envelope.json").write_bytes(json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8"))
        self.assertEqual(self.verify().returncode, 0)
        before = self.snapshot()
        proc = self.append({})
        self.assert_refused(proc, "container-too-large")
        self.assert_protocol(proc, "append")
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.verify().returncode, 0)

    def test_append_checks_complete_envelope_size_before_writes(self) -> None:
        self.prepared()
        for _ in range(8):
            proc = self.append({})
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        envelope = json.loads((self.dir / "envelope.json").read_bytes())
        self.assertEqual(envelope["envelope_revision"], 9)
        envelope.update({"part-" + str(index): "x" * (1024 * 1024) for index in range(7)})
        envelope["tail"] = ""
        empty_tail_bytes = json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
        tail_size = 8 * 1024 * 1024 - len(empty_tail_bytes)
        self.assertGreater(tail_size, 0)
        self.assertLessEqual(tail_size, 1024 * 1024)
        envelope["tail"] = "x" * tail_size
        (self.dir / "envelope.json").write_bytes(json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8"))
        self.assertEqual((self.dir / "envelope.json").stat().st_size, 8 * 1024 * 1024)
        self.assertEqual(self.verify().returncode, 0)
        before = self.snapshot()
        proc = self.append({})
        self.assert_refused(proc, "document-too-large")
        self.assert_protocol(proc, "append")
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.verify().returncode, 0)

    def test_decoder_integer_conversion_emits_value_free_result(self) -> None:
        raw = b'{"private-input-marker":' + b"9" * 5000 + b"}"
        input_path = Path(self._tmp.name) / "large-integer.json"
        input_path.write_bytes(raw)
        for input_arg in ("-", str(input_path)):
            with self.subTest(input_arg=input_arg):
                proc = invoke_bytes("matrix-hash", "--input", input_arg, stdin=raw if input_arg == "-" else None)
                self.assert_refused(proc, "invalid-json")
                self.assert_protocol(proc, "matrix-hash")
                self.assertNotIn(b"private-input-marker", proc.stdout + proc.stderr)

    def test_mutation_decoder_integer_conversion_preserves_state(self) -> None:
        raw = b'{"private-input-marker":' + b"9" * 5000 + b"}"
        self.assertEqual(self.init().returncode, 0)
        before = self.snapshot()
        proc = invoke_bytes("freeze", "--dir", str(self.dir), "--matrix", "-", stdin=raw)
        self.assert_refused(proc, "invalid-json")
        self.assert_protocol(proc, "freeze")
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.freeze().returncode, 0)
        before = self.snapshot()
        proc = invoke_bytes("append", "--dir", str(self.dir), "--payload", "-", stdin=raw)
        self.assert_refused(proc, "invalid-json")
        self.assert_protocol(proc, "append")
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.verify().returncode, 0)

    def test_decoder_resource_failures_emit_value_free_result(self) -> None:
        for exception_name, code in (("RecursionError", "depth-exceeded"), ("MemoryError", "json-resource-exceeded")):
            with self.subTest(exception_name=exception_name):
                program = (
                    "import json, runpy, sys\n"
                    "def reject_decoder(*args, **kwargs):\n"
                    f"    raise {exception_name}('private-decoder-marker')\n"
                    "json.loads = reject_decoder\n"
                    "script = sys.argv[1]\n"
                    "sys.argv = [script, 'matrix-hash', '--input', '-']\n"
                    "runpy.run_path(script, run_name='__main__')\n"
                )
                proc = subprocess.run([sys.executable, "-c", program, str(SCRIPT)], input=b'{"private-input-marker":1}', capture_output=True, check=False)
                self.assert_refused(proc, code)
                self.assert_protocol(proc, "matrix-hash")
                self.assertNotIn(b"private-input-marker", proc.stdout + proc.stderr)
                self.assertNotIn(b"private-decoder-marker", proc.stdout + proc.stderr)

    def test_invocation_error_exit_two(self) -> None:
        proc = invoke("bogus-operation")
        self.assertEqual(proc.returncode, 2)

    def test_stored_files_are_canonical(self) -> None:
        self.prepared()
        self.append({"finding_id": "F-001"})
        matrix_bytes = (self.dir / "matrix.json").read_bytes()
        canonical = json.dumps(FREEZE_MATRIX, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.assertEqual(matrix_bytes, canonical)
        envelope = json.loads((self.dir / "envelope.json").read_text(encoding="utf-8"))
        self.assertEqual(set(envelope), {"envelope_id", "namespace", "matrix_hash", "current_ledger_hash", "envelope_revision", "predecessor", "envelope_hash"})
        self.assertEqual(json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False), (self.dir / "envelope.json").read_text(encoding="utf-8"))

    def test_result_protocol_is_stable(self) -> None:
        proc = invoke("matrix-hash", "--input", "-", stdin=self.simple_matrix)
        payload = result_of(proc)
        self.assertEqual(payload["result_id"], "reviewed-change-orchestration.review-record-envelope-result")
        self.assertEqual(payload["result_version"], "0.1.0")
        self.assertEqual(payload["operation"], "matrix-hash")
        self.assertEqual(set(payload), {"result_id", "result_version", "operation", "ok", "identities", "errors"})


if __name__ == "__main__":
    unittest.main()
