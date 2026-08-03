---
id: integrate-planned-accept-and-execute
persistence: ephemeral
status: blocked
depends_on:
  - deepen-evidence-and-readiness
files_owned:
  - docs/changes/integrate-planned-accept-and-execute/change.md
  - SKILL.md
  - references/orchestrator-checklist.md
  - references/worktree-lifecycle.md
  - references/validation-policy.md
  - references/accepted-artifact-snapshot.md
  - evals/evals.json
---

# Integrate planned accept-and-execute orchestration

Status: Blocked on local evidence readiness and doc-contract review-bound acceptance plans · Proposed 2026-07-31

**Upstream dependencies:** `docs/changes/deepen-evidence-and-readiness/` must land first so provisional transfer and the accepted-artifact snapshot can use the common readiness and evidence-record contract. The external doc-contract proposal `review-bound-acceptance-plan` must also land and expose versioned JSON planning plus apply-time `plan_id` expectation. The current installed interface exposes `accept --dry-run` as human text without a machine-readable plan or reviewed-plan binding, so this change remains blocked.
**Dependents:** None identified.
**Files owned:** `SKILL.md` · `references/orchestrator-checklist.md` · `references/worktree-lifecycle.md` · `references/validation-policy.md` · `references/accepted-artifact-snapshot.md` (new) · `evals/evals.json`. This change does not own doc-contract status, roadmap, fingerprint, journal, or acceptance-plan implementation.

## Why

The skill currently requires an item to be accepted and therefore committed before orchestration begins. A user may instead explicitly authorize `accept and execute` for one newly drafted, provisional change. Requiring a prerequisite Git checkpoint in that case forces two commits even though the accepted lineage, implementation, tests, and durable documentation can be reviewed and recorded coherently in one final commit.

The orchestration skill should transfer only the named draft and its exact owned roadmap patch into an isolated item worktree, consume the provider-owned acceptance plan there with `--include-untracked`, and bind acceptance to the reviewed `plan_id`. Immediately after acceptance it should capture the exact accepted `change.md` bytes and SHA-256 outside the mutable tree, run `begin`, and review all implementation against that snapshot. Acceptance remains logically distinct and precedes implementation, but the provisional lineage can be landed and committed with the implementation at the end. Until doc-contract exposes the review-bound plan contract, the current accepted-only hard stop remains authoritative.

## What changes

**Delta ADDED** - A narrowly triggered `accept and execute` path that transfers an exactly owned provisional draft into the item worktree, consumes a machine-readable doc-contract plan, verifies the complete paired diff, executes with the reviewed `plan_id`, captures an immutable accepted-artifact snapshot, and lands provisional lineage plus implementation in one final commit.

**Delta MODIFIED** - Authority establishment, worktree and tracked-baseline ordering, execution-map provenance, accepted-artifact reporting, final staging, and eval coverage. Ordinary `execute` requests continue to require an already accepted artifact.

**Delta REMOVED** - The mandatory separate acceptance checkpoint and ad hoc acceptance staging. Implementation or commit authority alone still does not permit acceptance, and the skill never reimplements doc-contract lifecycle mutations.

## Tasks

1. Before implementation, require a versioned provider capability equivalent to `doc-contract accept <folder> --repo-root <repo> --dry-run --format json --include-untracked` plus apply-time `--expect-plan-id <id>`. The JSON schema and plan identifier must be machine-detectable. Stop this item as blocked if the interface is absent, ambiguous, exposes private document contents, or cannot reject a stale or malformed expectation before creating a journal or mutating lifecycle paths.
2. Add `references/accepted-artifact-snapshot.md` as the consumer contract. Combine the provider report with an orchestrator-owned record of canonical repository/common-Git identity, canonical named change path, base `HEAD`, index tree, tracked-worktree fingerprint, provider/config version, plan ID, ordered path actions, complete reviewed diff, expected post-state, and the exact accepted `change.md` bytes plus SHA-256. Store the accepted bytes and digest outside the mutable worktree and index. Do not require doc-contract to own Git staging, commits, snapshots, or worktree identity.
3. Define the trigger as explicit current-turn wording that unambiguously authorizes acceptance and execution of one canonical named change. `accept and execute docs/changes/<name>/` is the preferred form; an equivalent request must still name the canonical path and acceptance action. For a provisional draft, this authority includes transferring exactly its owned draft and roadmap patch into the item worktree and creating the ordinary final landing commit, but never a push or an unrelated baseline checkpoint. Stop on a shorthand name that resolves ambiguously.
4. Preserve the normal accepted-only path. If the named artifact is already accepted, capture or verify its immutable identity and continue without manufacturing an acceptance checkpoint. If it is proposed and explicit acceptance authority is absent, stop before transfer or mutation.
5. Run host readiness and snapshot current branch and `HEAD`, index tree, Git config/refs within the provider's declared mutation capability, staged and unstaged tracked status, all untracked and ignored names, provider-managed lifecycle paths, and protected-path byte identities. Resolve unrelated tracked landing-checkout changes through the existing tracked-baseline policy. Identify the named provisional draft and its exact owned roadmap patch; reject mixed or unexplained hunks rather than broadening the transfer.
6. Create the item worktree from the owned `HEAD`, then transfer the named draft and exact roadmap patch into it with a reversible transfer ledger. Verify destination bytes before removing only those exact source bytes or hunks from the landing checkout. Preserve unrelated proposals and all other tracked, untracked, ignored, protected, and submodule state. If exact transfer cannot be isolated, stop or use a separately authorized checkpoint fallback; do not silently include mixed state.
7. In the item worktree, run semantic entry reconciliation and `doc-contract reconcile mechanical <change> --phase entry --format json --repo-root . --include-untracked`. Request and inspect the provider's JSON acceptance dry-run for the exact named change, then inspect the complete text dry-run under the same `--expect-plan-id` and `--include-untracked`. Permit only the named change, roadmap, provider-managed global metadata, and mechanically required tracked dependent fingerprint updates. Reject an untracked sibling proposal, sibling semantic change, or unexplained source, test, path, mutation kind, or destination.
8. Immediately before acceptance, re-observe every planned path and collision with untracked, ignored, or protected material. Reject a changed precondition or disagreement between paired text and JSON plans. Execute acceptance only through doc-contract with `--format json --expect-plan-id <reviewed-id> --include-untracked`. On an interruption or post-apply validation failure, preserve the provider journal and item worktree, report recovery coordinates, and resume only through the provider recovery path under the same expected plan identity; do not stage, commit, re-plan around, or hand-edit the transaction.
9. After successful acceptance and final provider validation, copy the exact accepted `change.md` bytes to the external evidence root, compute and verify SHA-256, and record both snapshot identity and `plan_id` in the execution map. Then run `doc-contract begin <change> --repo-root . --include-untracked` before implementation. A missing or changed accepted snapshot is a hard stop; the `plan_id` does not substitute for work-contract identity.
10. Implement, fix, and independently review against the accepted-byte snapshot. Any proposed change to its requirements, exclusions, or verification authority requires a new explicit acceptance boundary. Keep the snapshot immutable and outside the index through sequence completion.
11. At final fixed point, reconcile and land the provisional lineage through doc-contract, using `--include-untracked` where required by the provider. Stage only the complete owned result: implementation, tests, durable documentation, provider-managed roadmap and metadata, and archived change lineage. Inspect staged name-status, statistics, whitespace, and full diff, then create exactly one neutral landing commit for the item and fast-forward it into the landing branch.
12. Keep a separate acceptance or tracked-baseline checkpoint as an explicit fallback only for an audit requirement, multi-session or cross-operator handoff, or state whose owned patch cannot be isolated safely. Such a checkpoint needs separate authority and reporting; doc-contract never requires it, and the ordinary provisional path remains one final commit.
13. Report the accepted artifact digest and final landing commit separately as logical evidence, while stating whether the one-commit path or checkpoint fallback was used. Confirm the transferred source material is consumed, unrelated checkout state is unchanged, and no provider journal or item-owned residue remains. Do not push without separate authorization.
14. Add eval scenarios for a newly drafted untracked `change-a` and owned roadmap patch completing in one final commit; the same flow beside unrelated proposed `change-b`; mixed roadmap hunks; an unexplained mutation or path; a tracked sibling semantic mutation; an untracked sibling fingerprint update; stale plan or accepted-byte identity; transfer collision or interruption; interrupted journal recovery; already accepted input; absent explicit acceptance authority; missing provider capability; and explicit checkpoint fallback.

## Verify

- The change remains blocked until `deepen-evidence-and-readiness` lands and a versioned provider capability exposes content-free JSON planning, complete paired diff inspection, apply-time expected-plan enforcement, and journaled recovery.
- `python -m json.tool evals/evals.json` succeeds and `git diff --check` reports no errors.
- A forward eval transfers a newly drafted untracked `change-a`, accepts and begins it with `--include-untracked`, reviews against captured accepted bytes and SHA-256, lands its archived lineage with implementation, and produces exactly one final commit while `change-b`, other untracked files, and ignored material remain untouched.
- Forward evals prove mixed or unexplained transfer state, an unexplained provider mutation, tracked sibling semantic change, untracked sibling proposal addition, collision, stale plan, changed accepted bytes, missing provider capability, or absent explicit acceptance authority stops before the affected boundary. An injected interruption preserves the transfer ledger or provider journal and resumes only through the recorded recovery path.
- A forward eval proves an already accepted item follows the existing path without an unnecessary checkpoint, while an explicit audit or non-isolatable-state case uses and reports the separately authorized fallback.
- Named eval assertions separately preserve one-item sequencing, worktree containment, model-selection records, independent review, final-fixed-point validation, exact staging, fast-forward-only integration, cleanup, and the no-push boundary.
