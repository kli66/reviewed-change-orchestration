---
name: reviewed-change-orchestration
description: Land one or more accepted, non-trivial repository change items with orchestrator-owned worktree isolation, cost-aware implementer/fixer delegation, independent read-only review, repository-native lifecycle handling, validation, fast-forward integration, cleanup, and exactly one neutral commit per item. Use when the user asks to implement and commit accepted changes with independent agent review, to land a sequence of accepted doc-contract changes, or to run a high-assurance implement-review-fix workflow. Do not use for proposals awaiting acceptance, review-only work, ordinary small fixes, or requests that do not authorize commits.
---

# Reviewed change orchestration

Land accepted change items without giving delegated agents repository mutation authority. Process multiple items strictly sequentially so every item starts from the state actually landed before it.

## Establish authority and sequence

Before changing the repository:

1. Confirm the user authorized implementation, local landing, and commits. Treat `Proposed (not accepted)` as a hard stop.
2. Read applicable repository instructions and each accepted change artifact completely.
3. Record the landing branch, its current HEAD, dirty paths, existing worktrees, repository-native gates, and the requested or dependency-valid item order.
4. Preserve unrelated tracked, untracked, ignored, generated, and externally managed worktree material.
5. Keep exactly one item active. File overlap requires reconciliation against the latest landed HEAD; it is not automatically a dependency edge.

Use this workflow only when independent review and isolation justify their cost. Route a typo or similarly local low-risk edit through the repository's ordinary workflow.

## Load the operating references

Read these files before the corresponding phase:

- `references/worktree-lifecycle.md` before creating, integrating, or removing an item worktree.
- `references/model-routing.md` before every implementer, reviewer, fixer, or re-review dispatch. It defines selection records and optional `.reviewed-change-orchestration.toml` overrides.
- `references/validation-policy.md` while building the execution map and before claiming a boundary is complete.
- `references/orchestrator-checklist.md` throughout each item.
- The applicable role prompt before delegating implementation, review, or fixes.

## Build the execution map

For each item, record:

- accepted requirements, exclusions, and lifecycle state;
- landing branch and exact start commit;
- owned files, expected durable-document mutations, and later overlaps;
- focused checks, canonical repository gate, and any live verification;
- worktree and temporary branch names;
- one model-selection record per planned dispatch, updated before any retry or escalation;
- Conventional Commit header (`type(scope): description`, omitting scope when unnecessary) and a body under 50 words;
- protected unrelated paths.

Do not start the next item until the current item is integrated, verified, and cleaned up.

## Run one item

### 1. Create an owned worktree

Follow `references/worktree-lifecycle.md`. Create the item branch from the current landing HEAD, not the sequence's original baseline. Prefer a host-native isolation mechanism when it exposes ownership and cleanup; otherwise use an ignored repository-local worktree directory.

Run a suitable clean-baseline check inside the item worktree. Stop for an ambiguous or failing baseline unless the failure is understood and the user authorizes proceeding. Record the exact baseline evidence.

### 2. Reconcile entry

If the repository uses `doc-contract`, invoke `/doc-contract reconcile <change-folder> entry` inside the already-created item worktree. Never reconcile entry in the landing checkout and then create the worktree: its mutations and evidence belong to the isolated item state. Let that skill own acceptance, roadmap, ADR, dependency, ownership, and drift semantics.

Stop on missing acceptance, a live contradiction, or a material scope choice. Fix factual lifecycle drift only when the repository contract permits it and include those mutations in this item's eventual commit.

For repositories without `doc-contract`, perform the repository's equivalent entry check without inventing a new document lifecycle.

### 3. Delegate implementation

Resolve and record the implementer model selection using `references/model-routing.md`, then instantiate `references/implementer-prompt.md` with that record, the absolute item-worktree path, and the execution map. The implementer may edit only the item worktree and runs focused validation. It may not stage, commit, merge, land, archive, create or delete branches/worktrees, or edit the landing checkout.

Inspect the resulting status, changed files, diff, and test evidence yourself. An agent report never proves the worktree state.

### 4. Obtain independent review

Resolve and record an independent reviewer selection, then instantiate `references/reviewer-prompt.md` for a fresh-context, read-only reviewer. Give it:

- the accepted requirements and exclusions;
- the item start commit and absolute worktree path;
- current status, changed-file list, actual diff, and untracked-file paths;
- implementer test commands and raw results, without the implementer's confidence narrative.

Require separate requirement-compliance and code-quality verdicts. The reviewer may inspect and run non-destructive checks, but may not edit files or perform lifecycle or Git mutations.

### 5. Fix and re-review

Critical or Important findings, failed compliance, or a confirmed acceptance gap enter a bounded loop:

1. Adjudicate any finding that conflicts with accepted scope. Do not silently redesign the item.
2. Instantiate `references/fixer-prompt.md` for the original implementer or a separate fixer.
3. Run affected focused checks.
4. Dispatch a scoped read-only re-review of the fixes and open findings.

Create a fresh selection record for every fixer and re-review dispatch. Use at most three fix rounds. After two materially unsuccessful attempts, increase model capability or change the task framing instead of repeating the same dispatch, and record the escalation. If a load-bearing finding remains after the third round, retain the worktree and branch and stop for user direction.

Record Minor findings explicitly; fix them when low-risk and in scope, otherwise report them as residual risk.

### 6. Reach the final fixed point

The orchestrator inspects all source, tests, public documentation, untracked additions, and lifecycle mutations. Run the canonical repository gate now, after the final code change. Fresh evidence must describe this exact worktree state.

For a reproducible defect, add a regression test first when the repository has a useful seam and prove it fails without the fix. Do not impose test-first work where no meaningful harness exists.

### 7. Reconcile exit and land lifecycle state

For `doc-contract`, invoke `/doc-contract reconcile <change-folder> exit`, then run `doc-contract land <change-folder> --repo-root <item-worktree> --dry-run`. Inspect its complete write/move plan and diff before running the same command without `--dry-run`. Use the repository's vendored equivalent when required. Do not hand-roll status, roadmap, archive, graph, or fingerprint mutations.

Run the canonical gate again only when exit reconciliation or landing changed inputs that the gate covers. Otherwise retain the fresh final-fixed-point evidence and run the relevant lifecycle check.

### 8. Create the item commit

Only the orchestrator stages and commits:

1. Stage explicit item-owned implementation and lifecycle paths.
2. Inspect staged name-status, statistics, full diff as risk warrants, and whitespace errors.
3. Confirm unrelated paths remain outside the index.
4. Create exactly one neutral commit for the item. Use a Conventional Commit header such as `fix(parser): reject truncated input`; omit the scope when it adds no value.
5. Keep the commit body under 50 words. Omit the body entirely when the header is sufficient.
6. Include no agent, AI, model, automation, or generated-by attribution in the header, body, or trailers. Do not add `Co-authored-by` for an agent.
7. Inspect the complete resulting commit message and diff, then confirm the item worktree has no unintended tracked changes.

Do not push, create a PR, deploy, or mutate remote branches without separate authorization.

### 9. Integrate, verify, and clean up

Follow `references/worktree-lifecycle.md`. Confirm the landing branch has not moved from the item's recorded start commit, then fast-forward it to the item commit. Never resolve divergence by force, reset, or an implicit merge commit.

Verify the merged state before cleanup. Preserve the item worktree and branch on any integration or verification failure. Remove only the worktree this workflow created, then delete its fully merged temporary branch. Cleanup success is the gate that permits the next item to start.

## Complete the sequence

After the final item:

1. Run one repository-wide canonical gate on the landing branch.
2. Confirm all intended lifecycle items landed and no owned worktree or temporary branch remains.
3. Report commits in landing order, review-found defects, exact validation evidence, residual findings, and unrelated material left untouched.
4. Report model-selection records in dispatch order, including overrides, fallbacks, and escalations.

Never describe focused checks as the full gate, a reviewed diff as committed, or an item commit as landed before merged-state verification succeeds.

## Failure rule

On any unresolved failure, keep the owned worktree and temporary branch recoverable, report their exact paths/names and last proven state, and stop. Never clean unrelated worktrees or delete unmerged branches.
