---
id: review-record-tooling
persistence: ephemeral
status: landed
depends_on:
files_owned:
  - docs/changes/review-record-tooling/change.md
  - scripts/review_record_envelope.py
  - tests/test_review_record_envelope.py
  - references/review-record-contract.md
  - docs/roadmap.md
accepted_at: 2026-10-20
started_at: 2026-10-20
landed_at: 2026-10-21
archive_path: docs/changes/archive/2026-10-21-review-record-tooling
---
# Provide offline tooling for the review-record envelope (matrix/ledger/envelope identity)

Status: Landed · 2026-10-21

**Upstream dependencies:** Nothing gated. Implements the already-landed review-record
contract (`references/review-record-contract.md`, `review_contract_id`
`reviewed-change-orchestration.review-record`, version `0.1.0`) as shipped; no contract
semantics change. Independent of all landed changes and of the two trigger-gated deferred
registers in `docs/spec/deferred-work.md` (validation-evidence and review-bound
accept-and-execute, deferred 2026-08-16 by `defer-stale-owner-work`).
**Dependents:** None. The accepted-work envelope validator
(`scripts/accepted_work_envelopes.py` `validate_history`) already imports this contract's
identities (`review_envelope_id`, `matrix_hash`, `envelope_hash`) but had no shipped tool
that computes or verifies them; this change supplies that seam.

**Files owned:** `scripts/review_record_envelope.py` (new) · `tests/test_review_record_envelope.py`
(new) · `references/review-record-contract.md` (editorial: Offline tooling section +
pointer in Deterministic identity; contract semantics unchanged, version stays `0.1.0`) ·
`docs/roadmap.md` (status line + DAG on land). `SKILL.md`, `evals/evals.json`, and
`scripts/accepted_work_envelopes.py` are deliberately untouched (minimal surface; the
contract doc is the canonical place that already documents sibling tooling).

## Why

The review-record envelope — the frozen requirement matrix, append-only findings ledger,
and identity tuple used on EVERY item by orchestrator, pre-implementation reviewer,
reviewer, and fixer — is defined in prose only. The contract mandates that every role
"recomputes `matrix_hash`, validates every ledger link, verifies the predecessor identity
when present, then recomputes `envelope_hash` before relying on the record", but the skill
ships zero machinery for that recomputation. Observed failure mode on 2026-09-17: an
orchestration session hand-rolled `helper.py` (~/.rco) to compute the same hashes, and
every future session would hand-roll its own variant — exactly the silent-divergence risk
the canonical-identity rules exist to prevent. Meanwhile the sibling accepted-work
envelope contract has full offline tooling (`scripts/accepted_work_envelopes.py`, schema,
tests) — the review-record envelope is the remaining contract without a stdlib seam.

## What changes

### Δ ADDED — `scripts/review_record_envelope.py` (stdlib only)

Implements the contract's identity rules verbatim:

- canonical JSON (`sort_keys`, `separators=(',', ':')`, `ensure_ascii=False`,
  `allow_nan=False`, UTF-8, no newline) — identical canonicalizer to
  `scripts/accepted_work_envelopes.py`;
- `matrix_hash` = SHA-256 of canonical matrix object bytes;
- empty ledger root = SHA-256 of canonical `[]`; entry hash = SHA-256 of canonical
  `{seq, prev, payload}`; current ledger hash = last entry hash;
- `envelope_revision` 0 = pending, 1 at freeze, +1 per append;
- `envelope_hash` = SHA-256 of canonical `{envelope_id, namespace, matrix_hash,
  current_ledger_hash, envelope_revision, predecessor}`;
- predecessor lineage: `init --predecessor` binds `{envelope_id, envelope_hash,
  matrix_hash, accepted_artifact}` from a verified predecessor envelope; `verify
  --predecessor` proves the binding against the retained predecessor file.

CLI: `matrix-hash`, `ledger-hash`, `init`, `freeze`, `append`, `verify`. Managed directory
layout `envelope.json` / `matrix.json` / `ledger.json`; storage remains orchestrator-owned.
Result protocol: one canonical result object per command, `result_id`
`reviewed-change-orchestration.review-record-envelope-result`, version `0.1.0`, sorted
value-free errors, exit 0/1/2. Parser guards mirror the accepted-work script (size, depth,
duplicate names, non-finite numbers, NFC).

### Δ ADDED — `tests/test_review_record_envelope.py` (61 cases)

Known-vector identity pins (empty-root and matrix hashes), full lifecycle
(init → freeze → append → verify), revision/revision-hash advancement, tamper detection
(matrix, ledger payload, prev-link, entry swap, revision drift, stale envelope hash,
ledger-hash field drift, pending-state violations), predecessor binding
(valid / unverified / mismatch / artifact-required), value-free error protocol, parser
guards, canonical on-disk storage, and result-protocol stability. The empty-ledger-root
and matrix vectors were independently reproduced by the hand-rolled session helper before
this tool existed (cross-implementation agreement).

### Δ MODIFIED — `references/review-record-contract.md` (editorial)

New `Offline tooling` section documenting the script, CLI, result protocol, and exit
codes, plus a pointer in `Deterministic identity` ("using `scripts/review_record_envelope.py
verify`"). No identity rule, field, or version changes; `review_contract_version` remains
`0.1.0`, so `validate_history` in the accepted-work validator keeps passing.

### Δ UNCHANGED (deliberate)

- `SKILL.md` and `evals/evals.json` — out of scope; the contract doc is the documented
  home for tooling pointers.
- `scripts/accepted_work_envelopes.py` and its schema — untouched; the review-record tool
  is a sibling, not an extension.
- Matrix row structure validation (requirements schema) — prose-owned by the contract; the
  tool validates identity and chain semantics only.

## Tasks

1. Add `scripts/review_record_envelope.py` with the identity math, lifecycle verbs, and
   value-free result protocol per the contract.
2. Add `tests/test_review_record_envelope.py` covering the 31 cases in Δ ADDED.
3. Add the `Offline tooling` section and pointer to `references/review-record-contract.md`.
4. Verify: `uv run --with pytest pytest tests/test_review_record_envelope.py -q` and the
   full suite `uv run --with pytest pytest -q` (sibling accepted-work tests stay green).
5. On land: update `docs/roadmap.md` status line + DAG (via `doc-contract update`), archive
   this folder per the contract.

## Verify

- New suite green: 61 cases, including known-vector identity pins (protect the canonical
  serializer against drift) and every tamper class in Δ ADDED.
- Full suite green: sibling accepted-work envelope tests unaffected
  (`tests/test_accepted_work_envelopes.py` still passes).
- `doc-contract check --repo-root . --offline` reports 0 errors and no new warnings.
- Cross-implementation agreement: the empty-ledger-root and freeze-matrix hashes produced
  by this tool match the independent hand-rolled helper used before the tool existed.
- The tool never echoes payload content in errors (value-free protocol test).
