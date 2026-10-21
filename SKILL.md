---
name: reviewed-change-orchestration
description: Land one or more accepted, non-trivial repository change items with orchestrator-owned worktree isolation, cost-aware implementer/fixer delegation, independent read-only review, repository-native lifecycle handling, validation, fast-forward integration, cleanup, and exactly one neutral landing commit per item, separate from any explicitly authorized prerequisite baseline checkpoint. Use when the user asks to implement and commit accepted changes with independent agent review, to land a sequence of accepted doc-contract changes, or to run a high-assurance implement-review-fix workflow. Do not use for proposals awaiting acceptance, review-only work, ordinary small fixes, or requests that do not authorize commits.
persistence: living
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
- `references/model-routing.md` before every pre-implementation reviewer, implementer, reviewer, fixer, or re-review dispatch. It defines selection records and optional `.reviewed-change-orchestration.toml` routing/worktree overrides.
- `references/validation-policy.md` while building the execution map and before claiming a boundary is complete.
- `references/orchestrator-checklist.md` throughout each item.
- `references/review-record-contract.md` before every item enters implementation, and `references/pre-implementation-review-prompt.md` before dispatching a triggered pre-implementation review.
- The applicable role prompt before delegating implementation, review, or fixes.

## Build the execution map

For each item, record:

- accepted requirements, exclusions, and lifecycle state;
- landing branch, preflight HEAD, and exact item start commit after any authorized prerequisite checkpoint;
- accepted-artifact policy: repository-managed lifecycle state or named local-only context;
- owned files, expected durable-document mutations, and later overlaps;
- the explicit pre-implementation risk decision, including a source-backed rationale for every signal when the decision is `none`;
- immutable accepted-artifact and applicable durable-contract references pinned to the item start commit;
- the orchestrator-owned, non-indexed review-record envelope path and ID; its current revision/hash; its immutable requirement matrix hash; requirement/finding namespace; predecessor identity when any; and any failure-domain work packages;
- focused checks, canonical repository gate, and any live verification;
- validation evidence records: covered-bytes manifest and fingerprint; exact command; relative working directory plus recorded absolute working-directory audit pointer; normalized repository/worktree execution context; dependency and mutable-external-input identity; exit status; and log path;
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

Before `git worktree add`, enforce the lifecycle containment contract: canonicalize the configured root and every existing generated-path ancestor, reject symlink traversal and exact path or branch collisions, and create missing deterministic buckets safely. Run a suitable clean-baseline check inside the item worktree. A clean Git status proves only isolation, not baseline correctness. Stop for an ambiguous or failing validation baseline unless the failure is understood and the user authorizes proceeding. Record the exact baseline evidence.

If the accepted artifact is named local-only orchestration context, copy only that artifact into the item worktree when needed and keep it untracked or ignored according to repository policy. Do not stage or land it.

### 3. Reconcile entry

If the repository manages the accepted artifact through `doc-contract`, invoke `/doc-contract reconcile <change-folder> entry` inside the already-created item worktree. Never reconcile entry in the landing checkout and then create the worktree: its mutations and evidence belong to the isolated item state. Let that skill own acceptance, roadmap, ADR, dependency, ownership, and drift semantics.

Stop on missing acceptance, a live contradiction, or a material scope choice. Fix factual lifecycle drift only when the repository contract permits it and include those mutations in this item's eventual commit.

For repositories without `doc-contract`, or when an intentionally untracked or ignored artifact is not repository-managed lifecycle state, perform only the applicable repository entry check without inventing a new document lifecycle or requiring the artifact to become tracked.

### 4. Establish the pre-implementation review contract

Inspect the immutable accepted artifact, start-commit repository instructions and durable contracts, and execution map for credentials or secrets, fail-closed behavior, evidence or identity binding, mutable external inputs, live integrations, import or source provenance, destructive behavior, concurrency, and security-sensitive parsing. Trigger pre-implementation review when any signal is present or cannot be ruled out. A skipped review records `none` plus a source-backed rationale for every signal; silence is not a negative decision.

Every accepted item receives a frozen requirement matrix before implementation. For a `none` risk decision, the orchestrator derives accepted obligations and applicable start-commit invariants directly, allocates IDs, freezes the matrix, and proceeds without a pre-implementation reviewer. For a triggered item, resolve and record an independent pre-implementation reviewer selection, instantiate `references/pre-implementation-review-prompt.md`, and give that fresh-context role the item worktree, immutable accepted-artifact reference, start-commit durable-contract references, execution map, protected paths, and the available envelope path, `envelope_id`, `matrix_hash`, current envelope revision/hash, namespace, and predecessor identity (using explicit pending values before the matrix exists). It is read-only, reports proposed rows in discovery order without stable IDs, and must not rely on the implementer's narrative.

The orchestrator adjudicates direct derivation or the pre-review report into the immutable requirement matrix and append-only findings ledger specified by `references/review-record-contract.md`. Allocate IDs and pin the matrix before implementation. Only a matrix containing accepted obligations may proceed automatically. An accepted-artifact gap, new scope, or contradiction receives `user_ruling_required` and stops without fixer dispatch; resolve a reviewer concern into another class or return it to the user. A resumption requires a revised and reaccepted accepted artifact, or an equivalently authoritative replacement for named local-only context. Retain the prior envelope unchanged as superseded lineage, then create a fresh envelope/path and namespace bound to its final identity; restart entry reconciliation and pre-review for the new matrix revision. A chat ruling alone cannot alter a frozen matrix.

When an item has more than one failure domain, or owned file/test groups have different side-effect cutoffs or evidence dependencies, split its execution map into failure-domain work packages. A package names its requirement IDs, invariants, owned files, side-effect cutoff, focused tests, and evidence dependencies. Freeze packages inside the matrix bytes, so `matrix_hash` covers them. Packages do not create lifecycle folders, commits, concurrent items, or delegated mutation authority.

### 5. Delegate implementation

Resolve and record the implementer model selection using `references/model-routing.md`, then instantiate `references/implementer-prompt.md` with that record, the delegated working directory under `references/worktree-lifecycle.md`, and the execution map. The implementer may edit only the item worktree and runs focused validation. It may not stage, commit, merge, land, archive, create or delete branches/worktrees, or edit the landing checkout.

Inspect the resulting status, changed files, diff, and test evidence yourself. An agent report never proves the worktree state.

### 6. Obtain independent review

Resolve and record an independent reviewer selection, then instantiate `references/reviewer-prompt.md` for a fresh-context, read-only reviewer. Dispatch once and wait for completion or a meaningful reviewer message; do not repeatedly resend an unchanged prompt. Give it pointers to:

- the accepted-artifact pointer from which requirements and exclusions are derived;
- the item start commit and the item worktree as the reviewer's working directory (absolute path as audit pointer), under `references/worktree-lifecycle.md`;
- the accepted artifact and its immutable reference (the start-commit path for tracked artifacts, or a path and content hash for local-only context);
- the review-record envelope path and ID, immutable matrix hash, current envelope revision/hash, namespace, predecessor identity when any, and applicable frozen work packages;
- protected unrelated paths;
- implementer exact commands, covered-bytes manifests/fingerprints, relative working directories, recorded absolute working-directory audit pointers, normalized contexts, dependency and mutable-external-input identities, exit statuses, and log paths.

The reviewer derives current status, the start-to-current diff, changed and untracked files, implementation, and tests locally. Do not paste the full diff or raw command output into the prompt.

Require separate requirement-compliance and code-quality verdicts. The reviewer verifies the accepted artifact and frozen matrix together rather than recreating uncited requirements from scratch, recomputes the matrix and current envelope identities, and reports existing stable finding IDs plus newly discovered findings in provisional discovery order. The reviewer may inspect and run non-destructive checks, but may not edit files or perform lifecycle or Git mutations.

### 7. Fix and re-review

Critical or Important implementation defects or failed compliance caused by implementation enter a bounded loop:

1. Resolve every reviewer concern into another finding class or return it to the user. An accepted-artifact gap, new scope, or contradiction stops for `user_ruling_required`; do not silently redesign the item or send it to a fixer.
2. Instantiate `references/fixer-prompt.md` for the original implementer or a separate fixer.
3. Run affected focused checks.
4. Launch a scoped read-only re-review under the same delegated working directory in `references/worktree-lifecycle.md`, with the original start commit, immutable accepted-artifact reference, full review-record identity tuple (envelope path, `envelope_id`, `matrix_hash`, current envelope revision/hash, namespace, and predecessor identity), protected paths, open findings, and fixer command/evidence/exit-status/log pointers. A supplied fix diff is context only, never its source of truth.

Create a fresh selection record for every fixer and re-review dispatch. Use at most three fix rounds. After two materially unsuccessful attempts, increase model capability or change the task framing instead of repeating the same dispatch, and record the escalation. If a load-bearing finding remains after the third round, retain the worktree and branch and stop for user direction.

Record Minor implementation defects explicitly; fix them when low-risk and in scope, otherwise record them as `accepted_residual`. A `rejected_as_reviewer_error` disposition is orchestrator-owned and requires rationale. The orchestrator assigns stable IDs to initial-review findings when appending them; fixers and re-reviewers report dispositions against those stable IDs. The ledger may advance revision/hash but never changes matrix bytes or `matrix_hash`.

### 8. Reach the final fixed point

The orchestrator inspects all source, tests, public documentation, untracked additions, and lifecycle mutations. Run the canonical repository gate now, after the final code change. Record fresh evidence for this exact worktree state using the validation evidence format; `HEAD` and dirty status are provenance, not the reusable state identity.

For a reproducible defect, add a regression test first when the repository has a useful seam and prove it fails without the fix. Do not impose test-first work where no meaningful harness exists.

### 9. Reconcile exit and land lifecycle state

When the accepted artifact is repository-managed through `doc-contract`, invoke `/doc-contract reconcile <change-folder> exit`, then run `doc-contract land <change-folder> --repo-root <item-worktree> --dry-run`. Inspect its complete write/move plan and diff before running the same command without `--dry-run`. Use the repository's vendored equivalent when required. Do not hand-roll status, roadmap, archive, graph, or fingerprint mutations.

For named local-only artifacts, skip reconciliation and landing. Keep them outside the index and preserve their repository-policy status.

Run the canonical gate again only when exit reconciliation or landing changed inputs that the gate covers. Otherwise retain the fresh final-fixed-point evidence and run the relevant lifecycle check.

### 10. Create the item commit

Only the orchestrator stages and commits:

1. Stage explicit item-owned implementation and lifecycle paths.
2. Inspect staged name-status, statistics, full diff as risk warrants, and whitespace errors.
3. Confirm unrelated paths remain outside the index.
4. Create exactly one neutral landing commit for the item. An explicitly authorized prerequisite baseline checkpoint is separate and does not count as the item's landing commit. Use a Conventional Commit header such as `fix(parser): reject truncated input`; omit the scope when it adds no value.
5. Keep the commit body under 50 words. Omit the body entirely when the header is sufficient.
6. Include no agent, AI, model, automation, or generated-by attribution in the header, body, or trailers. Do not add `Co-authored-by` for an agent.
7. Inspect the complete resulting commit message and diff, then confirm the item worktree has no unintended tracked changes.

Do not push, create a PR, deploy, or mutate remote branches without separate authorization.

### 11. Integrate, verify, and clean up

Follow `references/worktree-lifecycle.md`. Confirm the landing branch has not moved from the item's recorded start commit, then fast-forward it to the item commit. Never resolve divergence by force, reset, or an implicit merge commit. Before cleanup, classify all parent and nested-submodule residue and snapshot landing-checkout submodule configuration/status; linked-worktree cleanup must not deinitialize shared landing configuration.

Verify the merged state before cleanup. Preserve the item worktree and branch on any integration or verification failure. Remove only the worktree this workflow created, then delete its fully merged temporary branch. Cleanup success is the gate that permits the next item to start.

## Complete the sequence

After the final item:

1. Run one repository-wide canonical gate on the landing branch, or reuse final fixed-point evidence only when the validation policy proves equivalent covered bytes, command, relative working directory, normalized execution context, dependency identity, and mutable external inputs after fast-forward; absolute paths and Git provenance remain audit pointers.
2. Confirm all intended lifecycle items landed and no owned worktree or temporary branch remains.
3. Report any prerequisite checkpoint separately, then item landing commits in order, review-found defects, exact validation evidence, residual findings, and unrelated material left untouched.
4. Report model-selection records in dispatch order, including overrides, fallbacks, and escalations.

Never describe focused checks as the full gate, a reviewed diff as committed, or an item commit as landed before merged-state verification succeeds.

## Failure rule

On any unresolved failure, keep the owned worktree and temporary branch recoverable, report their exact paths/names and last proven state, and stop. Never clean unrelated worktrees or delete unmerged branches.
