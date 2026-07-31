---
persistence: living
---

# Review record contract

The orchestrator stores one review-record envelope outside the repository index for one matrix revision and attempt. Every role receives the envelope path and ID, immutable `matrix_hash`, current envelope revision/hash, namespace, and predecessor identity when any. The envelope contains immutable matrix bytes and an append-only findings ledger; adding a finding or disposition changes only the ledger and envelope revision/hash, never matrix bytes or `matrix_hash`.

## Authority and matrix creation

Create a matrix for every accepted item before implementation. Pin the accepted artifact and every supplied durable contract as `<item-start-commit>:<path>`. When the risk decision is `none`, the orchestrator derives accepted obligations and applicable start-commit invariants directly. When review triggers, it incorporates the read-only pre-review report before freezing. The accepted artifact is the source of accepted scope. Repository-wide instructions and accepted ADR invariants apply only when they explicitly govern every affected path. A requirement found only in another durable document is an `accepted_artifact_gap`; a conflict with the accepted artifact is a `contradiction` and stops for user adjudication.

The orchestrator alone allocates matrix requirement IDs once before adjudication: accepted-artifact rows in document order; applicable durable-contract rows in supplied-contract order then source location; source-less gaps; new-scope proposals; and reviewer concerns in reviewer-report order. Use `REQ-001` onward and never renumber within a matrix revision. Pre-reviewers report proposed rows and package membership by source reference or provisional ordinal in discovery order; they never allocate `REQ-*` IDs.

Each matrix row has:

- `id`, classification, and source reference;
- invariant or evidence field;
- authoritative acquisition point and required re-observation points;
- comparison or rejection point and side-effect cutoff;
- value-free diagnostic requirement and focused regression obligation;
- live-verification mode: `not_required`, `automated`, or `operator_gated`;
- unresolved ambiguity; and
- explicit `not_applicable` plus a reason for every field that does not apply.

Matrix classifications are `accepted_obligation`, `accepted_artifact_gap`, `new_scope`, `contradiction`, and `reviewer_concern`. The matrix and any applicable failure-domain work packages are frozen inputs to the implementer and final reviewer. Create packages when an item has more than one failure domain, or when owned file/test groups have differing side-effect cutoffs or evidence dependencies. A work package names its requirement IDs, invariants, owned files, side-effect cutoff, focused tests, and evidence dependencies; it does not create a lifecycle folder, commit, concurrent item, or new mutation authority.

## Deterministic identity

The frozen matrix bytes are canonical UTF-8 JSON: standard-library `json.dumps` with `sort_keys=True`, `separators=(',', ':')`, `ensure_ascii=False`, and `allow_nan=False`, encoded as UTF-8. The frozen object includes the matrix revision, pinned source references, requirement rows, and all work packages. `matrix_hash` is its SHA-256 digest, so package membership is immutable and independently verifiable.

The ledger is ordered and append-only. Its empty root is the SHA-256 digest of canonical JSON `[]`. Each entry contains its sequence number, previous ledger hash, and its value-free finding or disposition payload; its ledger hash is the SHA-256 digest of that canonical entry. The current ledger hash is the last entry hash, which commits to every preceding entry in order. `envelope_revision` starts at `1` when the matrix is frozen and increments once per append. `envelope_hash` is the SHA-256 digest of canonical JSON containing `envelope_id`, namespace, `matrix_hash`, current ledger hash, `envelope_revision`, and predecessor. A role recomputes `matrix_hash`, validates every ledger link, verifies the predecessor identity when present, then recomputes `envelope_hash` before relying on the record.

## Superseded-envelope lineage

An envelope never receives a replacement matrix. On an authoritative artifact revision/reacceptance, retain the prior envelope unchanged and mark it superseded in the orchestrator's reporting state; retain it through the required reporting and recovery boundary. Create a fresh, uniquely identified successor envelope and path for the new matrix revision/attempt. Its envelope revision starts at `1`, its ledger starts at the defined empty root, and requirement and finding counters restart as `REQ-001` and `F-001` within a new explicit namespace; IDs therefore carry that namespace and cannot collide with the predecessor's IDs.

The successor's canonical `predecessor` object contains the predecessor envelope ID, final predecessor `envelope_hash`, predecessor `matrix_hash`, and predecessor accepted-artifact reference. It is part of the successor `envelope_hash` input. The initial envelope uses an explicit canonical `predecessor: null`. A reviewer verifies the predecessor object against the retained predecessor envelope, confirms that the prior matrix and ledger are unchanged, and recomputes the successor identity. This binds each new attempt deterministically to its superseded lineage without rewriting either envelope.

## Findings ledger and convergence

The orchestrator allocates finding IDs as `F-001` onward in discovery order when appending to the ledger; never reuse an ID. An initial final reviewer reports newly discovered findings as provisional ordinals in discovery order, not `F-*` IDs. A split finding receives new child IDs and `parent_id`. A merge retains one canonical ID and records `related_ids`. Fixers and re-reviewers use the IDs already assigned by the orchestrator.

Every finding records its stable ID, requirement IDs, class, severity, disposition, evidence, and rationale. Finding classes are `implementation_defect`, `accepted_artifact_gap`, `new_scope`, `contradiction`, and `reviewer_concern`; severity and disposition are independent fields. Valid dispositions include `open`, `fixed`, `accepted_residual`, `rejected_as_reviewer_error`, and `user_ruling_required`. Only the orchestrator may record `rejected_as_reviewer_error`, with rationale.

Only a matrix containing accepted obligations may proceed automatically. The orchestrator resolves each reviewer concern into another class or returns it to the user. Any open accepted-artifact gap, new scope, or contradiction has disposition `user_ruling_required`, stops implementation or re-review convergence, and never enters fixer dispatch. Critical and Important implementation defects enter the three-round fixer loop. Minor implementation defects are fixed when low-risk and in scope or recorded as `accepted_residual`.

Resuming after a user ruling requires the repository lifecycle to revise and reaccept the accepted artifact, or an equivalently authoritative replacement for named local-only context. Preserve the superseded envelope, then repeat entry reconciliation and pre-implementation review in a fresh successor envelope with a new artifact reference, matrix revision, explicit ID namespace, `matrix_hash`, reset ledger/counters, and predecessor binding. An ephemeral chat ruling cannot rewrite a frozen matrix.
