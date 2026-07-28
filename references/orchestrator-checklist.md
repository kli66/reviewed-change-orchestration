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
- Build validation decisions and a complete selection record for every planned dispatch.

## Item isolation and entry

- Create one recorded owned worktree and temporary branch from current landing HEAD under the configured root or the `~/worktrees` default.
- Prove the worktree location is safe and validate the baseline; clean tracked status alone is insufficient.
- Record initialized submodules recursively, including each checked-out commit and baseline status/index state.
- Allow declared build, test, compile, and generated-artifact commands in submodules; stop for any unapproved submodule commit, checkout/switch/reset/rebase/merge/cherry-pick, index update, checked-out commit change, or superproject gitlink change.
- Copy only a named local-only change artifact when needed, keep it outside the index, and preserve its ignored or untracked policy status.
- Run repository-native entry reconciliation inside that worktree only for repository-managed lifecycle artifacts, never beforehand in the landing checkout; stop on contradiction or scope choice.
- Give the implementer an absolute worktree path and no Git/lifecycle authority.
- Include the resolved implementer selection record in its prompt.

## Review fixed point

- Inspect status, changed/untracked files, diff, and implementer evidence manifest.
- Give a fresh read-only reviewer the accepted-artifact, worktree, diff, protected-path, and command/log pointers; let it derive status and the actual diff locally.
- Dispatch the reviewer once and wait for completion or a meaningful message; do not repeatedly resend an unchanged prompt.
- Record reviewer risk signals, overrides, effective tier, model, effort, and rationale before dispatch.
- Require separate compliance and quality verdicts.
- Send actionable findings to a fixer, then scoped re-review; cap at three rounds.
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
- Deinitialize only clean or declared-generated submodules, then remove only the recorded owned worktree; use one bounded force only when the lifecycle assertions prove no unapproved residue remains. Delete only its fully merged branch.
- Start the next item from the newly landed HEAD only after cleanup succeeds.

## Sequence completion

- Run or equivalently reuse one repository-wide gate on the landing branch, with the fixed-point evidence identity recorded.
- Confirm no intended change remains active and no owned temporary state remains.
- Report any prerequisite checkpoint separately, then item landing commit order, model-selection records, review findings, exact evidence, residual risk, and preserved unrelated material.
