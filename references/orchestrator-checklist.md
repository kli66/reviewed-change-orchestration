---
persistence: living
---

# Orchestrator checklist

## Sequence setup

- Confirm accepted status and implementation/landing/commit authority.
- Record landing branch HEAD, repository instructions, staged and unstaged tracked changes, untracked paths, and existing worktrees.
- Classify each accepted artifact as repository-managed lifecycle state or named local-only context; do not require intentionally ignored documentation to become tracked.
- Before worktree creation, show any dirty tracked path/status list and combined diffstat, including deletions, then record explicit user permission for a separate tracked-only prerequisite checkpoint.
- If authorized, stop on pre-existing staged additions, then use `git add -u` from the repository root, inspect the complete staged scope and diff, create the checkpoint under normal message/no-attribution rules, and record it as the new item start commit.
- Confirm the checkpoint left untracked and ignored material untouched; if permission was denied, preserve all state and stop for a user resolution or another explicitly authorized bounded approach.
- Order items by user instruction or real dependency edges; keep one active.
- Read and validate optional `.reviewed-change-orchestration.toml` routing and worktree overrides.
- Record the explicit pre-implementation risk decision. A `none` decision has a source-backed rationale for credentials/secrets, fail-closed behavior, evidence/identity binding, mutable external inputs, live integrations, import/source provenance, destructive behavior, concurrency, and security-sensitive parsing; it skips only the reviewer, never the frozen matrix.
- Build validation decisions and a complete selection record for every planned dispatch, including a pre-implementation reviewer when triggered.

## Item isolation and entry

- Create one recorded owned worktree and temporary branch from current landing HEAD under the configured root or the `~/worktrees` default; stop on an exact branch or path collision.
- Canonicalize the root and every existing generated-path ancestor, reject symlink/non-directory/repository traversal, create missing buckets one component at a time, and validate the baseline; clean tracked status alone is insufficient.
- Record initialized submodules recursively, including each checked-out commit and baseline status/index state.
- Allow declared build, test, compile, and generated-artifact commands in submodules; stop for any unapproved submodule commit, checkout/switch/reset/rebase/merge/cherry-pick, index update, checked-out commit change, or superproject gitlink change.
- Copy only a named local-only change artifact when needed, keep it outside the index, and preserve its ignored or untracked policy status.
- Run repository-native entry reconciliation inside that worktree only for repository-managed lifecycle artifacts, never beforehand in the landing checkout; stop on contradiction or scope choice.
- Pin the accepted artifact and supplied durable contracts to the item start commit. Give a triggered item a fresh, read-only pre-implementation reviewer with the immutable references, worktree, protected paths, and execution map; do not give it implementer narrative or write authority. For `none`, derive accepted obligations and applicable invariants directly.
- Create the orchestrator-owned non-indexed review-record envelope for every item: allocate all `REQ-*` IDs, resolve package membership, freeze matrix bytes and `matrix_hash`, then record its current revision/hash, envelope ID, namespace, and predecessor identity. Keep all work packages inside the frozen matrix bytes. Give every role those pointers.
- Stop with `user_ruling_required`, without implementation or fixer dispatch, for an accepted-artifact gap, new scope, or contradiction. Resolve each reviewer concern into another class or return it to the user. On authoritative reacceptance, retain the old envelope unchanged as superseded lineage and create a uniquely identified successor path with reset ledger/revision/counters, a new namespace, and a predecessor binding to the prior final envelope hash, matrix hash, and artifact reference. Restart lifecycle entry and pre-review against that successor.
- Use failure-domain work packages when there is more than one failure domain, or side-effect cutoffs or evidence dependencies differ; each names requirement IDs, invariants, owned files, side-effect cutoff, focused tests, and evidence dependencies without adding lifecycle items or mutation authority.
- Give the implementer an absolute worktree path and no Git/lifecycle authority.
- Include the resolved implementer selection record in its prompt.

## Review fixed point

- Inspect status, changed/untracked files, diff, and implementer evidence manifest.
- Give a fresh read-only reviewer the immutable accepted-artifact reference, frozen matrix/work packages, and the full review-record identity tuple: envelope path, `envelope_id`, `matrix_hash`, current envelope revision/hash, namespace, and predecessor identity. Also give worktree, start commit, protected paths, and command/evidence/exit-status/log pointers; require it to recompute matrix and envelope identity, and supplied diffs are context only while it derives status and the actual diff locally.
- Dispatch the reviewer once and wait for completion or a meaningful message; do not repeatedly resend an unchanged prompt.
- Record reviewer risk signals, overrides, effective tier, model, effort, and rationale before dispatch.
- Require separate compliance and quality verdicts.
- Allocate `F-*` IDs only when appending new initial-review findings reported in provisional discovery order; fixers and re-reviewers use those assigned IDs.
- Send only Critical or Important implementation defects to a fixer, then scoped re-review with the same immutable artifact, frozen matrix, stable finding IDs, evidence-pointer contract, and full review-record identity tuple: envelope path, `envelope_id`, `matrix_hash`, current envelope revision/hash, namespace, and predecessor identity; cap at three rounds.
- Record finding class, severity, and disposition separately. Minor implementation defects are fixed when low-risk and in scope or recorded as `accepted_residual`; `rejected_as_reviewer_error` needs orchestrator rationale.
- Create a new selection record for each fixer/re-review and record every fallback or escalation.
- Inspect the final diff directly and run or equivalently reuse the canonical fixed-point gate under the validation policy.

## Lifecycle and commit

- For repository-managed lifecycle artifacts, run exit reconciliation and inspect landing preview before transactional landing; skip that lifecycle for local-only artifacts.
- Repeat only gates whose inputs lifecycle landing changed.
- Stage explicit item paths; inspect index name-status, diff, statistics, and whitespace.
- Create exactly one neutral landing commit with a Conventional Commit header and a body under 50 words; do not count an explicitly authorized prerequisite checkpoint as the item's landing commit.
- Inspect the complete message and trailers; reject any agent, AI, model, automation, generated-by, or agent `Co-authored-by` attribution.

## Integration and cleanup

- Confirm landing branch has not moved from the recorded item start commit.
- Fast-forward only; verify merged HEAD and integration-sensitive gates.
- Retain recovery state on any failure.
- Classify parent and nested-submodule tracked, untracked, ignored, and generated residue; retain recovery state for anything undeclared. Snapshot and compare landing submodule config/status before and after cleanup; do not deinitialize shared configuration. Remove only the recorded owned worktree, with one bounded force only when the lifecycle assertions prove no unapproved residue remains. Delete only its fully merged branch.
- Start the next item from the newly landed HEAD only after cleanup succeeds.

## Sequence completion

- Run or equivalently reuse one repository-wide gate on the landing branch, with the fixed-point evidence identity recorded.
- Confirm no intended change remains active and no owned temporary state remains.
- Report any prerequisite checkpoint separately, then item landing commit order, model-selection records, review findings, exact evidence, residual risk, and preserved unrelated material.
