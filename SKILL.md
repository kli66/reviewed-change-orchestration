---
name: reviewed-change-orchestration
description: Land one or more accepted, non-trivial repository change items with orchestrator-owned worktree isolation, cost-aware implementer/fixer delegation, independent read-only review, repository-native lifecycle handling, validation, fast-forward integration, cleanup, and exactly one neutral landing commit per item, separate from any explicitly authorized prerequisite baseline checkpoint. Use when the user asks to implement and commit accepted changes with independent agent review, to land a sequence of accepted doc-contract changes, or to run a high-assurance implement-review-fix workflow. Do not use for proposals awaiting acceptance, review-only work, ordinary small fixes, or requests that do not authorize commits.
---

# Reviewed change orchestration

Land accepted change items without giving delegated agents repository mutation authority. Process multiple items strictly sequentially so every item starts from the state actually landed before it.

## Establish authority and sequence

Before changing the repository:

1. Confirm the user authorized implementation, local landing, and commits. Treat `Proposed (not accepted)` as a hard stop.
2. Read applicable repository instructions and each accepted change artifact completely.
3. Record the landing branch, its current HEAD, staged and unstaged tracked changes, untracked paths, existing worktrees, repository-native gates, and the requested or dependency-valid item order.
4. Classify each accepted change artifact as repository-managed lifecycle state or named local-only orchestration context. Do not require an intentionally untracked or ignored artifact to become tracked.
5. Preserve unrelated tracked, untracked, ignored, generated, and externally managed worktree material.
6. Keep exactly one item active. File overlap requires reconciliation against the latest landed HEAD; it is not automatically a dependency edge.

Use this workflow only when independent review and isolation justify their cost. Route a typo or similarly local low-risk edit through the repository's ordinary workflow.

## Load the operating references

Read these files before the corresponding phase:

- `references/worktree-lifecycle.md` before creating, integrating, or removing an item worktree.
- `references/model-routing.md` before every implementer, reviewer, fixer, or re-review dispatch. It defines selection records and optional `.reviewed-change-orchestration.toml` routing/worktree overrides.
- `references/validation-policy.md` while building the execution map and before claiming a boundary is complete.
- `references/orchestrator-checklist.md` throughout each item.
- The applicable role prompt before delegating implementation, review, or fixes.

## Build the execution map

For each item, record:

- accepted requirements, exclusions, and lifecycle state;
- landing branch, preflight HEAD, and exact item start commit after any authorized prerequisite checkpoint;
- accepted-artifact policy: repository-managed lifecycle state or named local-only context;
- owned files, expected durable-document mutations, and later overlaps;
- focused checks, canonical repository gate, and any live verification;
- validation evidence records: covered-input fingerprint, command, working directory, relevant environment/toolchain identity, exit status, and log path;
- worktree and temporary branch names;
- one model-selection record per planned dispatch, updated before any retry or escalation;
- Conventional Commit header (`type(scope): description`, omitting scope when unnecessary) and a body under 50 words for any authorized prerequisite checkpoint and for the item landing commit;
- protected unrelated paths.

Do not start the next item until the current item is integrated, verified, and cleaned up.

## Run one item

### 1. Resolve tracked landing-checkout changes

Follow the tracked-baseline preflight in `references/worktree-lifecycle.md` before creating an item worktree. Inspect staged and unstaged changes to tracked files separately from untracked and ignored material.

If tracked files are modified or deleted, stop before worktree creation. Show the exact tracked status and combined diffstat, including deletions, and request explicit permission to create a separate prerequisite checkpoint commit containing all current tracked modifications and deletions. Permission to implement and commit the accepted item does not authorize this checkpoint.

When permission is granted, stage tracked changes only with the scope of `git add -u`, inspect the staged paths and diff, and create the checkpoint under the normal commit-message and no-attribution rules. Confirm tracked status is then clean without staging, stashing, copying, deleting, or otherwise disturbing untracked or ignored material. Record the checkpoint as the new item start commit.

If permission is denied, preserve the landing checkout exactly and ask the user to resolve it or authorize another bounded approach. Never silently transfer dirty tracked state into the item worktree.

### 2. Create an owned worktree

Follow `references/worktree-lifecycle.md`. Create the item branch from the current landing HEAD, not the sequence's original baseline. Prefer a host-managed isolation mechanism when it exposes ownership and cleanup; otherwise resolve the configured worktree root, defaulting to `~/worktrees`.

Run a suitable clean-baseline check inside the item worktree. A clean Git status proves only isolation, not baseline correctness. Stop for an ambiguous or failing validation baseline unless the failure is understood and the user authorizes proceeding. Record the exact baseline evidence.

If the accepted artifact is named local-only orchestration context, copy only that artifact into the item worktree when needed and keep it untracked or ignored according to repository policy. Do not stage or land it.

### 3. Reconcile entry

If the repository manages the accepted artifact through `doc-contract`, invoke `/doc-contract reconcile <change-folder> entry` inside the already-created item worktree. Never reconcile entry in the landing checkout and then create the worktree: its mutations and evidence belong to the isolated item state. Let that skill own acceptance, roadmap, ADR, dependency, ownership, and drift semantics.

Stop on missing acceptance, a live contradiction, or a material scope choice. Fix factual lifecycle drift only when the repository contract permits it and include those mutations in this item's eventual commit.

For repositories without `doc-contract`, or when an intentionally untracked or ignored artifact is not repository-managed lifecycle state, perform only the applicable repository entry check without inventing a new document lifecycle or requiring the artifact to become tracked.

### 4. Delegate implementation

Resolve and record the implementer model selection using `references/model-routing.md`, then instantiate `references/implementer-prompt.md` with that record, the absolute item-worktree path, and the execution map. The implementer may edit only the item worktree and runs focused validation. It may not stage, commit, merge, land, archive, create or delete branches/worktrees, or edit the landing checkout.

Inspect the resulting status, changed files, diff, and test evidence yourself. An agent report never proves the worktree state.

### 5. Obtain independent review

Resolve and record an independent reviewer selection, then instantiate `references/reviewer-prompt.md` for a fresh-context, read-only reviewer. Dispatch once and wait for completion or a meaningful reviewer message; do not repeatedly resend an unchanged prompt. Give it pointers to:

- the accepted-artifact pointer from which requirements and exclusions are derived;
- the item start commit and absolute worktree path;
- the accepted artifact and its immutable reference (the start-commit path for tracked artifacts, or a path and content hash for local-only context);
- protected unrelated paths;
- implementer command lines, exit statuses, covered-input fingerprints, and log paths.

The reviewer derives current status, the start-to-current diff, changed and untracked files, implementation, and tests locally. Do not paste the full diff or raw command output into the prompt.

Require separate requirement-compliance and code-quality verdicts. The reviewer may inspect and run non-destructive checks, but may not edit files or perform lifecycle or Git mutations.

### 6. Fix and re-review

Critical or Important findings, failed compliance, or a confirmed acceptance gap enter a bounded loop:

1. Adjudicate any finding that conflicts with accepted scope. Do not silently redesign the item.
2. Instantiate `references/fixer-prompt.md` for the original implementer or a separate fixer.
3. Run affected focused checks.
4. Dispatch a scoped read-only re-review of the fixes and open findings.

Create a fresh selection record for every fixer and re-review dispatch. Use at most three fix rounds. After two materially unsuccessful attempts, increase model capability or change the task framing instead of repeating the same dispatch, and record the escalation. If a load-bearing finding remains after the third round, retain the worktree and branch and stop for user direction.

Record Minor findings explicitly; fix them when low-risk and in scope, otherwise report them as residual risk.

### 7. Reach the final fixed point

The orchestrator inspects all source, tests, public documentation, untracked additions, and lifecycle mutations. Run the canonical repository gate now, after the final code change. Record fresh evidence for this exact worktree state using the validation evidence format; `HEAD` and dirty status are provenance, not the reusable state identity.

For a reproducible defect, add a regression test first when the repository has a useful seam and prove it fails without the fix. Do not impose test-first work where no meaningful harness exists.

### 8. Reconcile exit and land lifecycle state

When the accepted artifact is repository-managed through `doc-contract`, invoke `/doc-contract reconcile <change-folder> exit`, then run `doc-contract land <change-folder> --repo-root <item-worktree> --dry-run`. Inspect its complete write/move plan and diff before running the same command without `--dry-run`. Use the repository's vendored equivalent when required. Do not hand-roll status, roadmap, archive, graph, or fingerprint mutations.

For named local-only artifacts, skip reconciliation and landing. Keep them outside the index and preserve their repository-policy status.

Run the canonical gate again only when exit reconciliation or landing changed inputs that the gate covers. Otherwise retain the fresh final-fixed-point evidence and run the relevant lifecycle check.

### 9. Create the item commit

Only the orchestrator stages and commits:

1. Stage explicit item-owned implementation and lifecycle paths.
2. Inspect staged name-status, statistics, full diff as risk warrants, and whitespace errors.
3. Confirm unrelated paths remain outside the index.
4. Create exactly one neutral landing commit for the item. An explicitly authorized prerequisite baseline checkpoint is separate and does not count as the item's landing commit. Use a Conventional Commit header such as `fix(parser): reject truncated input`; omit the scope when it adds no value.
5. Keep the commit body under 50 words. Omit the body entirely when the header is sufficient.
6. Include no agent, AI, model, automation, or generated-by attribution in the header, body, or trailers. Do not add `Co-authored-by` for an agent.
7. Inspect the complete resulting commit message and diff, then confirm the item worktree has no unintended tracked changes.

Do not push, create a PR, deploy, or mutate remote branches without separate authorization.

### 10. Integrate, verify, and clean up

Follow `references/worktree-lifecycle.md`. Confirm the landing branch has not moved from the item's recorded start commit, then fast-forward it to the item commit. Never resolve divergence by force, reset, or an implicit merge commit.

Verify the merged state before cleanup. Preserve the item worktree and branch on any integration or verification failure. Remove only the worktree this workflow created, then delete its fully merged temporary branch. Cleanup success is the gate that permits the next item to start.

## Complete the sequence

After the final item:

1. Run one repository-wide canonical gate on the landing branch, or reuse the final fixed-point evidence only when the validation policy proves covered-input and execution-context equivalence after fast-forward.
2. Confirm all intended lifecycle items landed and no owned worktree or temporary branch remains.
3. Report any prerequisite checkpoint separately, then item landing commits in order, review-found defects, exact validation evidence, residual findings, and unrelated material left untouched.
4. Report model-selection records in dispatch order, including overrides, fallbacks, and escalations.

Never describe focused checks as the full gate, a reviewed diff as committed, or an item commit as landed before merged-state verification succeeds.

## Failure rule

On any unresolved failure, keep the owned worktree and temporary branch recoverable, report their exact paths/names and last proven state, and stop. Never clean unrelated worktrees or delete unmerged branches.
