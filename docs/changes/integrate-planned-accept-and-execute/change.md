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
  - references/acceptance-checkpoint.md
  - evals/evals.json
---

# Integrate planned accept-and-execute orchestration

Status: Blocked on local evidence readiness and doc-contract review-bound acceptance plans · Proposed 2026-07-31

**Upstream dependencies:** `docs/changes/deepen-evidence-and-readiness/` must land first so the acceptance checkpoint can use the common readiness and evidence-record contract. The external doc-contract proposal `review-bound-acceptance-plan` must also land and expose versioned JSON planning plus apply-time `plan_id` expectation. The current installed interface exposes `accept --dry-run` as human text without a machine-readable plan or reviewed-plan binding, so this change remains blocked.
**Dependents:** None identified.
**Files owned:** `SKILL.md` · `references/orchestrator-checklist.md` · `references/worktree-lifecycle.md` · `references/validation-policy.md` · `references/acceptance-checkpoint.md` (new) · `evals/evals.json`. This change does not own doc-contract status, roadmap, fingerprint, journal, or acceptance-plan implementation.

## Why

The skill currently requires an item to be accepted before orchestration begins. A user may instead explicitly authorize `accept and execute` for one named change. Without a defined prerequisite boundary, an agent can stage unrelated proposals or recreate doc-contract's lifecycle semantics while trying to establish the accepted baseline.

The orchestration skill should consume a provider-owned acceptance plan for exactly the named change, inspect both its content-free manifest and complete human diff before mutation, bind execution to that reviewed `plan_id`, and checkpoint only the resulting lifecycle paths from an owned clean baseline. Acceptance remains distinct from implementation and from the item's landing commit. Until doc-contract exposes that contract, the current accepted-only hard stop is safer and remains authoritative.

## What changes

**Delta ADDED** - A narrowly triggered `accept and execute` prerequisite path that consumes a machine-readable doc-contract plan, verifies the complete paired diff, validates target and path scope, executes with the reviewed `plan_id` as a precondition, creates a separate exact acceptance checkpoint, and records it as the item start commit.

**Delta MODIFIED** - Authority establishment, tracked-baseline ordering, execution-map provenance, checkpoint reporting, and eval coverage. Ordinary `execute` requests continue to require an already accepted artifact.

**Delta REMOVED** - Ad hoc acceptance staging and any implication that implementation/commit authority alone permits acceptance. The skill never reimplements doc-contract lifecycle mutations.

## Tasks

1. Before implementation, require a versioned provider capability equivalent to `doc-contract accept <folder> --repo-root <repo> --dry-run --format json` plus apply-time `--expect-plan-id <id>`. The JSON schema and plan identifier must be machine-detectable. Stop this item as blocked if the interface is absent, ambiguous, exposes private document contents, or cannot reject a stale or malformed expectation before creating a journal or mutating lifecycle paths.
2. Add `references/acceptance-checkpoint.md` as the consumer contract. Combine the provider report with an orchestrator-owned record of canonical repository/common-Git identity, canonical named change path and accepted-artifact fingerprint, base `HEAD`, index tree, tracked-worktree fingerprint, provider/config version, plan ID, ordered path actions, complete reviewed diff, and expected post-state. Do not require doc-contract to own Git staging, commit, or worktree identity.
3. Define the trigger as explicit current-turn wording that unambiguously authorizes both acceptance and execution of one canonical named change. `accept and execute docs/changes/<name>/` is the preferred form; an equivalent request must still name the canonical path and acceptance action. This authority includes the separate acceptance checkpoint commit but never a push. Stop on a shorthand name that resolves ambiguously.
4. Preserve the normal accepted-only path. If the named artifact is already accepted, record that fact and continue without manufacturing an acceptance checkpoint. If it is proposed and explicit acceptance authority is absent, stop before mutation.
5. Resolve pre-existing tracked landing-checkout changes through the existing tracked-baseline policy before planning acceptance. Snapshot current branch and `HEAD`, index tree, Git config/refs within the provider's declared mutation capability, staged and unstaged tracked status, all untracked and ignored names, provider-managed lifecycle paths, and protected-path byte identities. Do not mix unrelated dirty state into the acceptance checkpoint.
6. Request and inspect the provider's JSON dry-run for the exact named change, then inspect the complete text dry-run under the same `--expect-plan-id`. Permit the named change, roadmap, provider-managed global metadata, and mechanically required dependent fingerprint updates only. A dependent proposal path is permitted only when it is already tracked, clean at the owned baseline, and the reviewed diff is limited to provider-managed metadata. Reject adding an untracked sibling proposal, any sibling semantic change, or any unexplained source, test, path, mutation kind, or destination.
7. After plan inspection and immediately before execution, snapshot byte identities for every planned path and every collision with untracked, ignored, or protected material. Reject a collision, a changed precondition, or a plan whose paired text and JSON renderings do not resolve to the same expected identifier. Keep recorded unrelated and protected identities outside the provider transaction domain.
8. Execute acceptance only through doc-contract using `--format json --expect-plan-id <reviewed-id>`. A malformed or mismatched expectation, planning blocker, or preflight rejection must occur before a new journal or lifecycle mutation. If execution is interrupted or otherwise fails after the transaction starts, do not stage, commit, re-plan around it, or hand-edit lifecycle state; preserve the provider journal and repository state, report recovery coordinates, and resume only through the provider's recovery path under the same expected plan identity. Continue only after a successful final provider report and verification that no journal or temporary residue remains.
9. Compare the complete post-state with the plan and before snapshot. Stage only the executed plan's exact path set, then mandatorily inspect staged name-status, statistics, whitespace, and full diff. Create a neutral acceptance checkpoint separate from the item's landing commit and record it as the new item start commit.
10. Confirm unrelated proposals, untracked material, ignored material, protected bytes, and non-plan tracked paths remain unchanged and outside the index. Then create the item worktree and continue the ordinary entry reconciliation, implementation, independent review, final-fixed-point, landing, commit, integration, and cleanup workflow.
11. Report the acceptance checkpoint separately from the item landing commit. Do not push either commit without separate authorization.
12. Add eval scenarios for `accept and execute docs/changes/change-a/` alongside unrelated proposed `change-b`, an unexplained mutation or path, a tracked sibling semantic mutation, an untracked sibling fingerprint update that would add the whole proposal, a stale plan precondition, an untracked-path collision, an interrupted journaled transaction, an already accepted item, absent explicit acceptance authority, and missing provider capability.

## Verify

- The change remains blocked until `deepen-evidence-and-readiness` lands and a versioned provider capability exposes content-free JSON planning, complete paired diff inspection, apply-time expected-plan enforcement, and journaled recovery.
- `python -m json.tool evals/evals.json` succeeds and `git diff --check` reports no errors.
- A forward eval proves only lifecycle-planned paths for `change-a` enter the acceptance checkpoint while `change-b`, untracked files, and ignored material remain untouched.
- Forward evals prove an unexplained path/mutation, tracked sibling semantic change, untracked sibling proposal addition, untracked-path collision, stale plan, missing provider capability, or absent explicit acceptance authority stops before acceptance mutation or staging. An injected interruption preserves journaled recovery state, enters no checkpoint, and resumes only under the reviewed plan identity.
- A forward eval proves an already accepted item follows the existing path without an unnecessary checkpoint.
- Named eval assertions separately preserve one-item sequencing, worktree containment, model-selection records, independent review, final-fixed-point validation, exact staging, fast-forward-only integration, cleanup, and the no-push boundary.
