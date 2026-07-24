# Orchestrator checklist

## Sequence setup

- Confirm accepted status and implementation/landing/commit authority.
- Record landing branch HEAD, repository instructions, dirty paths, and existing worktrees.
- Order items by user instruction or real dependency edges; keep one active.
- Build validation and model-routing decisions for every item.

## Item isolation and entry

- Create one recorded owned worktree and temporary branch from current landing HEAD.
- Prove the worktree location is safe and the baseline is understood.
- Run repository-native entry reconciliation inside that worktree, never beforehand in the landing checkout; stop on contradiction or scope choice.
- Give the implementer an absolute worktree path and no Git/lifecycle authority.

## Review fixed point

- Inspect status, changed/untracked files, diff, and implementer test evidence.
- Give a fresh read-only reviewer requirements, diff, changed files, and raw evidence.
- Require separate compliance and quality verdicts.
- Send actionable findings to a fixer, then scoped re-review; cap at three rounds.
- Inspect the final diff directly and run the canonical fixed-point gate.

## Lifecycle and commit

- Run exit reconciliation and inspect landing preview before transactional landing.
- Repeat only gates whose inputs lifecycle landing changed.
- Stage explicit item paths; inspect index name-status, diff, statistics, and whitespace.
- Create exactly one neutral commit with a Conventional Commit header and a body under 50 words.
- Inspect the complete message and trailers; reject any agent, AI, model, automation, generated-by, or agent `Co-authored-by` attribution.

## Integration and cleanup

- Confirm landing branch has not moved from the recorded item start commit.
- Fast-forward only; verify merged HEAD and integration-sensitive gates.
- Retain recovery state on any failure.
- Remove only the recorded owned worktree, then delete only its fully merged branch.
- Start the next item from the newly landed HEAD only after cleanup succeeds.

## Sequence completion

- Run one repository-wide gate on the landing branch.
- Confirm no intended change remains active and no owned temporary state remains.
- Report commit order, review findings, exact evidence, residual risk, and preserved unrelated material.
