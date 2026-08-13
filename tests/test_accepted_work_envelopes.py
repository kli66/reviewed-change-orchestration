from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "accepted_work_envelopes.py"
FIXTURE = ROOT / "tests" / "fixtures" / "accepted_work_envelopes_v0_1_0.json"
SCHEMA_ID = "reviewed-change-orchestration.accepted-work-envelope-context"
RESULT_ID = "reviewed-change-orchestration.accepted-work-envelope-validation-result"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def repair(document: dict[str, Any]) -> dict[str, Any]:
    if document["kind"] == "AttemptBinding":
        body = document["body"]
        body["fencing_identity"] = digest({"schema_id": document["schema_id"], "schema_version": document["schema_version"], "kind": "AttemptBinding", "body": {key: value for key, value in body.items() if key != "fencing_identity"}})
    document["id"] = digest({key: document[key] for key in ("schema_id", "schema_version", "kind", "body")})
    return document


def context_for(document: dict[str, Any]) -> dict[str, Any]:
    body: dict[str, Any] = document["body"]
    observations: dict[str, Any]
    if document["kind"] == "AcceptedBundle":
        observations = {
            "repository": {"repository_id": body["repository_id"]},
            "membership": {"item_ids": [entry["item_id"] for entry in body["membership"]], "dependency_edges": body["dependencies"]},
            "authority_evidence": [{"item_id": item["item_id"], "authority_id": item["authority"]["authority_id"], "decision_id": item["authority"]["decision_id"], "accepted_source_sha256": item["accepted_source"]["sha256"]} for item in body["items"]],
        }
    elif document["kind"] == "AttemptBinding":
        observations = {
            "binding": {field: body[field] for field in ("accepted_bundle_id", "item_id", "run_id", "attempt_id", "repository_id", "base", "candidate", "branch", "worktree", "fencing_identity")},
            "readiness": {"status": body["dependency_readiness"]["status"], "required_item_ids": body["dependency_readiness"]["required_item_ids"], "dependencies": body["dependency_readiness"]["dependencies"], "reconciliation_outcome": body["reconciliation"]["outcome"], "reconciliation_evidence_sha256": body["reconciliation"]["evidence"]["sha256"]},
            "grants": {"ceiling": body["grant_ceiling"], "selected_paths": body["selected_paths"], "selected_capabilities": body["selected_capabilities"], "selected_actions": body["selected_actions"], "next_actions": body["next_actions"]},
            "authority_budget": {"authority_ids": [authority["authority_id"] for authority in body["authorities"]], "budgets": body["budgets"]},
        }
    elif document["kind"] == "ReviewedItemHistory":
        observations = {
            "binding": {field: body[field] for field in ("accepted_bundle_id", "item_id", "run_id", "attempt_binding_id", "attempt_id", "candidate_base", "ticket_branch", "final_tip")},
            "git_lineage": [{field: commit[field] for field in ("commit", "tree", "parent")} for commit in body["commits"]],
            "review": {field: body[field] for field in ("review_id", "review_envelope_id", "matrix_hash", "envelope_hash", "namespace", "predecessor", "compliance_verdict", "quality_verdict")},
            "evidence": {"accepted_artifact_sha256": body["accepted_artifact"]["sha256"], "validation": [{"obligation_id": entry["obligation_id"], "status": entry["status"], "evidence_sha256": entry["evidence"]["sha256"]} for entry in body["validation_observations"]]},
            "outcome": {"outcome": body["outcome"], "finding_ids": [finding["finding_id"] for finding in body["findings"]], "residuals": body["residuals"]},
        }
    else:
        observations = {
            "binding": {field: body[field] for field in ("accepted_bundle_id", "run_id", "candidate_base", "assembled_tip", "status")},
            "histories": [{"history_id": history["id"], "item_id": history["body"]["item_id"], "final_tree": history["body"]["final_tip"]["tree"]} for history in body["histories"]],
            "item_outcomes": body["item_outcomes"],
            "assembly": [{field: step[field] for field in ("before", "after", "input_history_ids", "input_trees")} for step in body["assembly"]["steps"]],
            "artifacts": {"aggregate": [{"obligation_id": entry["obligation_id"], "final_tree": entry["final_tree"], "status": entry["status"], "evidence_sha256": entry["evidence"]["sha256"]} for entry in body["aggregate_interactions"]], "packet": {"sha256": body["packet"]["reference"]["sha256"], "final_tree": body["packet"]["final_tree"]}, "artifact": {"sha256": body["artifact"]["reference"]["sha256"], "final_tree": body["artifact"]["final_tree"]}},
        }
    observations.update({"envelope_id": document["id"], "canonical_document_sha256": digest(document)})
    return {"context_schema_id": SCHEMA_ID, "context_schema_version": "0.1.0", "kind": document["kind"], "observations": observations}


class AcceptedWorkEnvelopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.corpus = json.loads(FIXTURE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError("fixture corpus is unavailable or invalid") from error

    def document(self, kind: str) -> dict[str, Any]:
        return copy.deepcopy(self.corpus["valid"][kind])

    def invoke(self, operation: str, kind: str, document: Any, *, level: str = "structural", context: Any = None, stdin: bool = False, copied_script: Path | None = None, out: str = "-") -> subprocess.CompletedProcess[bytes]:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            input_path = temporary / "input.json"
            try:
                input_path.write_bytes(canonical(document))
            except OSError as error:
                self.fail("unable to write CLI input: " + str(error))
            script = copied_script or SCRIPT
            command = [sys.executable, str(script), operation, "--kind", kind, "--input", "-" if stdin else str(input_path), "--out", out]
            input_bytes = canonical(document) if stdin else None
            if operation == "validate":
                command.extend(["--level", level])
                if context is not None:
                    context_path = temporary / "context.json"
                    try:
                        context_path.write_bytes(canonical(context))
                    except OSError as error:
                        self.fail("unable to write CLI context: " + str(error))
                    command.extend(["--context", str(context_path)])
            working_directory = script.resolve().parent if copied_script is not None else ROOT
            return subprocess.run(command, input=input_bytes, capture_output=True, check=False, cwd=working_directory)

    def invoke_raw(self, kind: str, raw: bytes, *, context_raw: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            input_path = temporary / "input.json"
            try:
                input_path.write_bytes(raw)
            except OSError as error:
                self.fail("unable to write raw CLI input: " + str(error))
            command = [sys.executable, str(SCRIPT), "validate", "--kind", kind, "--level", "contextual" if context_raw is not None else "structural", "--input", str(input_path)]
            if context_raw is not None:
                context_path = temporary / "context.json"
                try:
                    context_path.write_bytes(context_raw)
                except OSError as error:
                    self.fail("unable to write raw CLI context: " + str(error))
                command.extend(["--context", str(context_path)])
            return subprocess.run(command, capture_output=True, check=False, cwd=ROOT)

    def assert_invalid(self, kind: str, document: dict[str, Any], code: bytes) -> None:
        result = self.invoke("validate", kind, document)
        self.assertEqual(result.returncode, 1, result.stderr.decode())
        self.assertIn(code, result.stdout)

    def test_fixture_envelopes_validate_and_canonicalize(self) -> None:
        for kind in self.corpus["valid"]:
            document = self.document(kind)
            result = self.invoke("validate", kind, document)
            self.assertEqual(result.returncode, 0, result.stdout.decode())
            try:
                parsed_result = json.loads(result.stdout)
            except json.JSONDecodeError as error:
                self.fail("CLI returned invalid JSON: " + str(error))
            self.assertTrue(parsed_result["structural_valid"])
            canonicalized = self.invoke("canonicalize", kind, document)
            self.assertEqual(canonicalized.returncode, 0, canonicalized.stdout.decode())
            self.assertEqual(canonicalized.stdout, canonical(document))

    def test_contextual_observations_match_and_fail_closed_per_kind(self) -> None:
        for kind in self.corpus["valid"]:
            document = self.document(kind)
            context = context_for(document)
            matched = self.invoke("validate", kind, document, level="contextual", context=context)
            self.assertEqual(matched.returncode, 0, matched.stdout.decode())
            context["observations"].pop("envelope_id")
            missing = self.invoke("validate", kind, document, level="contextual", context=context)
            self.assertEqual(missing.returncode, 1)
            self.assertIn(b"missing-observation", missing.stdout)

    def test_cycle_is_deterministic_not_recursive(self) -> None:
        document = self.document("AcceptedBundle")
        document["body"]["dependencies"] = [{"before": "item-a", "after": "item-b"}, {"before": "item-b", "after": "item-a"}]
        repair(document)
        self.assert_invalid("AcceptedBundle", document, b"dependency-cycle")

    def test_uri_and_opaque_locator_rules(self) -> None:
        candidate = self.document("CandidateBundle")
        candidate["body"]["artifact"]["reference"]["locator"]["value"] = "//usér:päss@not-a-uri"
        repair(candidate)
        self.assertEqual(candidate["body"]["artifact"]["reference"]["locator"]["value"], "//usér:päss@not-a-uri")
        opaque_bytes = candidate["body"]["artifact"]["reference"]["locator"]["value"].encode("utf-8")
        self.assertEqual(opaque_bytes, b"//us\xc3\xa9r:p\xc3\xa4ss@not-a-uri")
        canonicalized = self.invoke("canonicalize", "CandidateBundle", candidate)
        self.assertEqual(canonicalized.returncode, 0, canonicalized.stderr.decode())
        try:
            retained = json.loads(canonicalized.stdout)
        except json.JSONDecodeError as error:
            self.fail("canonicalized envelope is invalid JSON: " + str(error))
        self.assertEqual(retained["body"]["artifact"]["reference"]["locator"]["value"], "//usér:päss@not-a-uri")
        self.assertEqual(retained["body"]["artifact"]["reference"]["locator"]["value"].encode("utf-8"), opaque_bytes)
        self.assertEqual(canonicalized.stdout, canonical(candidate))
        candidate["body"]["packet"]["reference"]["locator"] = {"scheme": "uri", "value": "https://user:password@example.invalid/a"}
        repair(candidate)
        self.assert_invalid("CandidateBundle", candidate, b"uri-userinfo-forbidden")

    def test_identity_and_canonical_bytes_are_stable(self) -> None:
        document = self.document("AcceptedBundle")
        serialized = json.dumps(document, indent=2, sort_keys=False)
        try:
            reordered = json.loads(serialized)
        except json.JSONDecodeError as error:
            self.fail("test serialization produced invalid JSON: " + str(error))
        first = self.invoke("validate", "AcceptedBundle", document)
        second = self.invoke("validate", "AcceptedBundle", reordered)
        self.assertEqual(first.stdout, second.stdout)
        changed = copy.deepcopy(document)
        changed["body"]["repository_id"] = "fixture:other"
        repair(changed)
        self.assertNotEqual(document["id"], changed["id"])

    def test_candidate_precedence_and_history_finding_legality(self) -> None:
        partial = copy.deepcopy(self.corpus["candidates"]["partial"])
        self.assertEqual(self.invoke("validate", "CandidateBundle", partial).returncode, 0)
        partial["body"]["status"] = "local_complete"
        repair(partial)
        self.assert_invalid("CandidateBundle", partial, b"candidate-status-precedence")
        history = self.document("ReviewedItemHistory")
        history["body"]["findings"][0]["disposition"] = "open"
        repair(history)
        self.assert_invalid("ReviewedItemHistory", history, b"reviewed-success-incomplete")

    def test_parser_bounds_and_duplicate_names(self) -> None:
        document = self.document("AcceptedBundle")
        document["body"]["repository_id"] = "x" * (1024 * 1024 + 1)
        repair(document)
        self.assert_invalid("AcceptedBundle", document, b"string-too-large")
        with tempfile.TemporaryDirectory() as directory:
            duplicated = Path(directory) / "duplicate.json"
            duplicated.write_text('{"schema_id":"a","schema_id":"b"}', encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), "validate", "--kind", "AcceptedBundle", "--level", "structural", "--input", str(duplicated)], capture_output=True, check=False, cwd=ROOT)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"duplicate-object-name", result.stdout)
        self.assertEqual(result.stderr, b"")

    def test_io_failure_uses_operational_exit_code(self) -> None:
        missing = ROOT / "tests" / "fixtures" / "does-not-exist.json"
        result = subprocess.run([sys.executable, str(SCRIPT), "validate", "--kind", "AcceptedBundle", "--level", "structural", "--input", str(missing)], capture_output=True, check=False, cwd=ROOT)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.stderr, b"accepted_work_envelopes: io-failure\n")

    def test_stdin_and_atomic_output(self) -> None:
        document = self.document("AcceptedBundle")
        result = self.invoke("validate", "AcceptedBundle", document, stdin=True)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            input_path = temporary / "input.json"
            result_path = temporary / "result.json"
            canonical_path = temporary / "canonical.json"
            input_path.write_bytes(canonical(document))
            result_path.write_bytes(b"previous-result")
            canonical_path.write_bytes(b"previous-envelope")
            expected_validation = self.invoke("validate", "AcceptedBundle", document)
            self.assertEqual(expected_validation.returncode, 0, expected_validation.stderr.decode())
            result_inode = result_path.stat().st_ino
            canonical_inode = canonical_path.stat().st_ino
            validate = subprocess.run([sys.executable, str(SCRIPT), "validate", "--kind", "AcceptedBundle", "--level", "structural", "--input", str(input_path), "--out", str(result_path)], capture_output=True, check=False, cwd=ROOT)
            self.assertEqual(validate.returncode, 0, validate.stderr.decode())
            self.assertEqual(result_path.read_bytes(), expected_validation.stdout)
            self.assertNotEqual(result_path.stat().st_ino, result_inode)
            canonicalize = subprocess.run([sys.executable, str(SCRIPT), "canonicalize", "--kind", "AcceptedBundle", "--input", str(input_path), "--out", str(canonical_path)], capture_output=True, check=False, cwd=ROOT)
            self.assertEqual(canonicalize.returncode, 0, canonicalize.stderr.decode())
            self.assertEqual(canonical_path.read_bytes(), canonical(document))
            self.assertNotEqual(canonical_path.stat().st_ino, canonical_inode)
            self.assertEqual(list(temporary.glob(".accepted-work-*")), [])

    def test_document_context_and_structural_bounds_are_inclusive(self) -> None:
        document = self.document("AcceptedBundle")
        raw = canonical(document)
        exact_document = raw + b" " * (8 * 1024 * 1024 - len(raw))
        self.assertEqual(len(exact_document), 8 * 1024 * 1024)
        exact = self.invoke_raw("AcceptedBundle", exact_document)
        self.assertEqual(exact.returncode, 0, exact.stderr.decode())
        over = self.invoke_raw("AcceptedBundle", exact_document + b" ")
        self.assertEqual(over.returncode, 1)
        self.assertIn(b"document-too-large", over.stdout)
        self.assertEqual(over.stderr, b"")

        context = context_for(document)
        context_raw = canonical(context)
        exact_context = context_raw + b" " * (8 * 1024 * 1024 - len(context_raw))
        contextual = self.invoke_raw("AcceptedBundle", raw, context_raw=exact_context)
        self.assertEqual(contextual.returncode, 0, contextual.stdout.decode())
        context_over = self.invoke_raw("AcceptedBundle", raw, context_raw=exact_context + b" ")
        self.assertEqual(context_over.returncode, 1)
        self.assertIn(b"document-too-large", context_over.stdout)
        self.assertEqual(context_over.stderr, b"")

        for wraps, expected_code in ((61, None), (62, b"depth-exceeded")):
            bounded = self.document("AcceptedBundle")
            nested: dict[str, Any] = {}
            for _index in range(wraps):
                nested = {"x": nested}
            bounded["body"]["extra"] = nested
            repair(bounded)
            result = self.invoke("validate", "AcceptedBundle", bounded)
            self.assertEqual(result.returncode, 1)
            if expected_code is None:
                self.assertNotIn(b"depth-exceeded", result.stdout)
                self.assertIn(b"schema-additional-property", result.stdout)
            else:
                self.assertIn(expected_code, result.stdout)

        for count, expected_code in ((10_000, None), (10_001, b"container-too-large")):
            bounded = self.document("AcceptedBundle")
            bounded["body"]["items"][0]["accepted_outcomes"] = [f"outcome-{index:05d}" for index in range(count)]
            repair(bounded)
            result = self.invoke("validate", "AcceptedBundle", bounded)
            self.assertEqual(result.returncode, 0 if expected_code is None else 1)
            if expected_code is None:
                self.assertNotIn(b"container-too-large", result.stdout)
            else:
                self.assertIn(expected_code, result.stdout)

        for size, expected_code in ((1024 * 1024, None), (1024 * 1024 + 1, b"string-too-large")):
            bounded = self.document("AcceptedBundle")
            bounded["body"]["repository_id"] = "x" * size
            repair(bounded)
            result = self.invoke("validate", "AcceptedBundle", bounded)
            self.assertEqual(result.returncode, 0 if expected_code is None else 1)
            if expected_code is None:
                self.assertNotIn(b"string-too-large", result.stdout)
            else:
                self.assertIn(expected_code, result.stdout)

        for size, expected_code in ((2048, None), (2049, b"locator-value-too-large")):
            bounded = self.document("AcceptedBundle")
            bounded["body"]["items"][0]["accepted_source"]["locator"]["value"] = "x" * size
            repair(bounded)
            result = self.invoke("validate", "AcceptedBundle", bounded)
            self.assertEqual(result.returncode, 0 if expected_code is None else 1)
            if expected_code is None:
                self.assertNotIn(b"locator-value-too-large", result.stdout)
            else:
                self.assertIn(expected_code, result.stdout)

    def test_unicode_integer_uri_and_context_version_fail_closed(self) -> None:
        document = self.document("AcceptedBundle")
        document["body"]["repository_id"] = "e\u0301"
        repair(document)
        self.assert_invalid("AcceptedBundle", document, b"string-not-nfc")
        document = self.document("AcceptedBundle")
        document["body"]["items"][0]["accepted_source"]["byte_length"] = True
        repair(document)
        self.assert_invalid("AcceptedBundle", document, b"schema-type")
        for uri, code in (("relative/path", b"invalid-uri-scheme"), ("1bad:value", b"invalid-uri-scheme"), ("https://user@example.invalid", b"uri-userinfo-forbidden"), ("https://:password@example.invalid", b"uri-userinfo-forbidden")):
            candidate = self.document("CandidateBundle")
            candidate["body"]["packet"]["reference"]["locator"] = {"scheme": "uri", "value": uri}
            repair(candidate)
            self.assert_invalid("CandidateBundle", candidate, code)
        context = context_for(self.document("AttemptBinding"))
        context["context_schema_version"] = "9.9.9"
        result = self.invoke("validate", "AttemptBinding", self.document("AttemptBinding"), level="contextual", context=context)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"unknown-context-version", result.stdout)

    def test_every_attempt_binding_observation_is_compared(self) -> None:
        document = self.document("AttemptBinding")
        binding_fields = ("accepted_bundle_id", "item_id", "run_id", "attempt_id", "repository_id", "base", "candidate", "branch", "worktree", "fencing_identity")
        for field in binding_fields:
            context = context_for(document)
            context["observations"]["binding"][field] = "stale" if isinstance(context["observations"]["binding"][field], str) else {}
            result = self.invoke("validate", "AttemptBinding", document, level="contextual", context=context)
            self.assertEqual(result.returncode, 1, field)
            self.assertIn(b"mismatched-observation", result.stdout, field)
        context = context_for(document)
        context["observations"]["grants"]["ceiling"]["capabilities"] = []
        result = self.invoke("validate", "AttemptBinding", document, level="contextual", context=context)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"mismatched-observation", result.stdout)

        history = self.document("ReviewedItemHistory")
        context = context_for(history)
        context["observations"]["git_lineage"][-1]["tree"] = "stale-tree"
        result = self.invoke("validate", "ReviewedItemHistory", history, level="contextual", context=context)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"mismatched-observation", result.stdout)

        candidate = self.document("CandidateBundle")
        context = context_for(candidate)
        context["observations"]["artifacts"]["packet"]["sha256"] = "sha256:" + "0" * 64
        result = self.invoke("validate", "CandidateBundle", candidate, level="contextual", context=context)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"mismatched-observation", result.stdout)

    def test_history_outcomes_require_matching_verdict_signals(self) -> None:
        history = self.document("ReviewedItemHistory")
        history["body"]["outcome"] = "failed"
        repair(history)
        self.assert_invalid("ReviewedItemHistory", history, b"history-outcome-verdict-mismatch")

        history["body"]["compliance_verdict"] = "fail"
        repair(history)
        result = self.invoke("validate", "ReviewedItemHistory", history)
        self.assertEqual(result.returncode, 0, result.stdout.decode())

        history = self.document("ReviewedItemHistory")
        history["body"]["outcome"] = "ambiguous"
        history["body"]["validation_observations"][0]["status"] = "unknown"
        repair(history)
        result = self.invoke("validate", "ReviewedItemHistory", history)
        self.assertEqual(result.returncode, 0, result.stdout.decode())

    def test_non_ready_binding_allows_only_non_mutation_actions(self) -> None:
        document = self.document("AttemptBinding")
        document["body"]["dependency_readiness"]["status"] = "blocked"
        document["body"]["grant_ceiling"]["actions"] = ["fixture:edit", "fixture:read"]
        document["body"]["selected_actions"] = ["fixture:edit", "fixture:read"]
        document["body"]["next_actions"] = ["fixture:read"]
        repair(document)
        result = self.invoke("validate", "AttemptBinding", document)
        self.assertEqual(result.returncode, 0, result.stdout.decode())

        document["body"]["next_actions"] = ["fixture:edit"]
        repair(document)
        self.assert_invalid("AttemptBinding", document, b"mutation-action-not-permitted-when-not-ready")

    def test_candidate_requires_success_histories_or_explicit_outcomes(self) -> None:
        candidate = self.document("CandidateBundle")
        candidate["body"]["histories"][0]["body"]["outcome"] = "incomplete"
        candidate["body"]["histories"][0]["body"]["validation_observations"][0]["status"] = "unknown"
        repair(candidate["body"]["histories"][0])
        candidate["body"]["assembly"]["steps"][0]["input_history_ids"] = [history["id"] for history in candidate["body"]["histories"]]
        repair(candidate)
        self.assert_invalid("CandidateBundle", candidate, b"non-success-history-must-be-item-outcome")

    def test_invalid_fixture_corpus_and_no_effect_cutoff(self) -> None:
        wrapper_source = """import pathlib, subprocess, sys\nprocess = subprocess.run(sys.argv[1:-1], capture_output=True)\nsys.stdout.buffer.write(process.stdout)\nsys.stderr.buffer.write(process.stderr)\nif process.returncode == 0:\n    pathlib.Path(sys.argv[-1]).write_text('effect', encoding='utf-8')\nraise SystemExit(process.returncode)\n"""
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            wrapper = temporary / "consumer.py"
            wrapper.write_text(wrapper_source, encoding="utf-8")
            for name, case in self.corpus["invalid"].items():
                input_path = temporary / (name + ".json")
                effect_marker = temporary / (name + ".effect")
                input_path.write_bytes(canonical(case["document"]))
                command = [sys.executable, str(SCRIPT), "validate", "--kind", case["kind"], "--level", "structural", "--input", str(input_path)]
                result = subprocess.run([sys.executable, str(wrapper), *command, str(effect_marker)], capture_output=True, check=False, cwd=ROOT)
                self.assertEqual(result.returncode, 1, name + ": " + result.stderr.decode())
                self.assertIn(case["expected_code"].encode("ascii"), result.stdout, name)
                self.assertFalse(effect_marker.exists(), name)

    def test_copied_owner_portability_and_result_version_rejection(self) -> None:
        document = self.document("AcceptedBundle")
        original_validation = self.invoke("validate", "AcceptedBundle", document)
        self.assertEqual(original_validation.returncode, 0, original_validation.stderr.decode())
        with tempfile.TemporaryDirectory() as directory:
            owner = Path(directory) / "owner"
            shutil.copytree(ROOT / "scripts", owner / "scripts")
            shutil.copytree(ROOT / "schemas", owner / "schemas")
            copied = owner / "scripts" / "accepted_work_envelopes.py"
            canonicalized = self.invoke("canonicalize", "AcceptedBundle", document, copied_script=copied)
            self.assertEqual(canonicalized.returncode, 0, canonicalized.stderr.decode())
            self.assertEqual(canonicalized.stdout, canonical(document))
            copied_validation = self.invoke("validate", "AcceptedBundle", document, copied_script=copied)
            self.assertEqual(copied_validation.returncode, 0, copied_validation.stderr.decode())
            self.assertEqual(copied_validation.stdout, original_validation.stdout)
        for result in self.corpus["downstream_result_cases"]:
            self.assertNotEqual((result["result_schema_id"], result["result_schema_version"]), (RESULT_ID, "0.1.0"))


if __name__ == "__main__":
    unittest.main()
