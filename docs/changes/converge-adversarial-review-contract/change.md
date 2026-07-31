---
id: converge-adversarial-review-contract
persistence: ephemeral
status: accepted
depends_on:
files_owned:
  - docs/changes/converge-adversarial-review-contract/change.md
  - SKILL.md
  - references/orchestrator-checklist.md
  - references/model-routing.md
  - references/implementer-prompt.md
  - references/reviewer-prompt.md
  - references/fixer-prompt.md
  - references/pre-implementation-review-prompt.md
  - references/review-record-contract.md
  - references/validation-policy.md
  - evals/evals.json
accepted_at: 2026-07-31
---
# Converge adversarial review before implementation

Status: Accepted · Accepted 2026-07-31

**Upstream dependencies:** Current reviewed-change orchestration contract at `bff8295`; the immutable accepted-artifact, independent read-only review, bounded three-round fixer loop, model-selection records, and final-fixed-point gates are available and must remain authoritative.
**Dependents:** `docs/changes/deepen-evidence-and-readiness/` consumes the stable requirement and finding identities introduced here.
**Files owned:** `SKILL.md` · `references/orchestrator-checklist.md` · `references/model-routing.md` · `references/implementer-prompt.md` · `references/reviewer-prompt.md` · `references/fixer-prompt.md` · `references/pre-implementation-review-prompt.md` (new) · `references/review-record-contract.md` (new) · `references/validation-policy.md` · `evals/evals.json`

## Why

The workflow currently asks the final reviewer to rediscover adversarial requirements after implementation. On changes involving credentials, fail-closed behavior, evidence identity, mutable external inputs, live integrations, provenance, destructive behavior, concurrency, or security-sensitive parsing, this turns requirement discovery into repeated fix rounds. More seriously, the current fixer-loop rule allows a confirmed acceptance gap to enter implementation, which can silently expand accepted scope.

The workflow needs a risk-triggered pre-implementation review that derives a stable execution contract from the accepted artifact without becoming a second source of authority. Final review must then verify that contract, and every finding must retain a stable identity and disposition across fix rounds.

## What changes

**Delta ADDED** - A risk-triggered, fresh-context, read-only pre-implementation reviewer role; an adjudicated requirement matrix with source references; failure-domain work packages for broad items; and stable requirement and finding IDs carried through implementation, review, fixing, and re-review.

**Delta MODIFIED** - The execution map, model-selection role vocabulary, implementer/fixer/reviewer prompts, review convergence rules, and eval coverage. Finding class, severity, and disposition become separate fields. Accepted-artifact gaps, new scope, and contradictions stop for user direction instead of entering the fixer loop.

**Delta REMOVED** - The rule that a confirmed acceptance gap may enter the ordinary fixer loop. No existing independent-review, three-round, final-fixed-point, worktree, staging, integration, or cleanup guarantee is removed.

## Tasks

1. Define an explicit risk decision rule. Inspect the immutable accepted artifact, start-commit repository instructions and durable contracts, and execution map for credentials or secrets, fail-closed behavior, evidence or identity binding, mutable external inputs, live integrations, import or source provenance, destructive behavior, concurrency, and security-sensitive parsing. Trigger when any signal is present or cannot be ruled out; skipping requires a recorded `none` decision with a source-backed rationale for every signal.
2. Add `references/pre-implementation-review-prompt.md`. Give the reviewer the immutable accepted-artifact reference, item worktree and start commit, protected paths, execution map, and relevant durable contracts; keep it read-only and independent from the implementer.
3. Pin relevant durable contracts to the item start commit and define authority precedence. Repository-wide instructions and accepted ADR invariants apply when they explicitly govern every affected path; a requirement present only in another durable document is otherwise an `accepted_artifact_gap`. Any conflict with the accepted artifact is a `contradiction` and stops for user adjudication.
4. Add `references/review-record-contract.md`. Store an immutable matrix plus `matrix_hash` and an append-only findings ledger in one orchestrator-owned envelope outside the repository index. Give every role the envelope path, immutable matrix hash, and current envelope revision/hash. Appending findings or dispositions changes only the envelope revision/hash and never the matrix bytes or `matrix_hash`.
5. Allocate requirement IDs once before adjudication: accepted-artifact rows in document order, applicable durable-contract rows in supplied-contract order and source location, then source-less gaps, new-scope proposals, and reviewer concerns in reviewer-report order. Allocate `REQ-001` onward and never renumber within a matrix revision. Allocate findings as `F-001` onward in discovery order; never reuse an ID. A split finding receives new child IDs with a `parent_id`; a merge retains one canonical ID and records `related_ids`.
6. Define each requirement-matrix row with its source reference, invariant or evidence field, authoritative acquisition point, required re-observation points, comparison or rejection point, side-effect cutoff, value-free diagnostic requirement, focused regression obligation, live-verification mode (`not_required`, `automated`, or `operator_gated`), and unresolved ambiguity. Require explicit `not_applicable` plus a reason rather than blank or invented fields.
7. Separate requirement classification from finding convergence. Matrix rows use `accepted_obligation`, `accepted_artifact_gap`, `new_scope`, `contradiction`, or `reviewer_concern`. Review findings use `implementation_defect`, `accepted_artifact_gap`, `new_scope`, `contradiction`, or `reviewer_concern` plus independent severity and disposition.
8. Define the transition rules. Only a matrix containing accepted obligations may proceed automatically. The orchestrator must resolve each reviewer concern into another class or return it to the user. Any open artifact gap, new scope, or contradiction has disposition `user_ruling_required` and stops. Resumption requires the repository lifecycle to revise and reaccept the artifact, or an equivalently authoritative replacement for named local-only context; then entry reconciliation and pre-implementation review restart with a new artifact reference, matrix revision, ID namespace, and matrix hash. An ephemeral chat ruling alone may not rewrite the frozen matrix. Critical or Important implementation defects enter fixing; Minor implementation defects are fixed when low-risk and in scope or recorded as `accepted_residual`. `rejected_as_reviewer_error` is an orchestrator disposition with rationale.
9. For items with more than one failure domain or with owned file/test groups that have different side-effect cutoffs or evidence dependencies, structure the execution map into failure-domain work packages. Each package names its requirement IDs, invariants, owned files, side-effect cutoff, focused tests, and evidence dependencies. Do not create additional lifecycle folders, commits, concurrent repository items, or mutation authority.
10. Give the frozen matrix and applicable work packages to the implementer and final reviewer. The final reviewer verifies the accepted artifact and matrix together instead of recreating uncited requirements from scratch.
11. Require fixers and re-reviewers to report disposition against stable finding IDs. Preserve separate requirement-compliance and code-quality verdicts, the three-round cap, independent re-review, and capability escalation.
12. Extend model routing and selection records for the pre-implementation reviewer. Use `strongest` for secrets, destructive behavior, concurrency, or security-sensitive parsing; use at least `standard` for the other triggering signals and raise it when signals combine. Do not weaken existing override rules.
13. Add discriminating eval scenarios with explicit assertions for a credential-bearing live gate, a low-risk refactor, an accepted-artifact gap, and a purported new requirement introduced during re-review.

## Verify

- `python -m json.tool evals/evals.json` succeeds and `git diff --check` reports no errors.
- Using the host skill-evaluation facility, record assertion-level results for each new eval; if that facility is unavailable, report behavioral verification as not run rather than passing it by inspection.
- The credential-bearing eval produces the complete frozen requirement record before implementation, including acquisition, re-observation, fail-before-side-effect, value-free error, source-origin, and operator-gated live-test obligations.
- A forward eval of a low-risk local refactor omits pre-implementation review without weakening final independent review.
- The artifact-gap and re-review-scope evals assert `user_ruling_required`, no fixer dispatch, stable IDs, and an unchanged frozen matrix hash.
- Existing evals continue to preserve independent read-only review, separate compliance and quality verdicts, bounded fixing, one-item sequencing, exact staging, final-fixed-point validation, fast-forward-only integration, and recovery-state retention.
