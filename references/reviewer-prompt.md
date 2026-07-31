---
persistence: living
---

# Read-only reviewer prompt template

Use a fresh-context reviewer. Supply repository facts and evidence, not the implementer's confidence or design narrative.

```text
Independently review accepted change [CHANGE_REFERENCE]. Do not edit anything.

Item worktree: [ABSOLUTE_WORKTREE_PATH]
Start commit: [ITEM_START_COMMIT]

Model selection record:
[MODEL_SELECTION_RECORD]

Accepted artifact reference:
[ACCEPTED_ARTIFACT_REFERENCE]

Frozen review record:
envelope=[ENVELOPE_PATH]
envelope_id=[ENVELOPE_ID]
matrix_hash=[MATRIX_HASH]
current_revision_hash=[CURRENT_ENVELOPE_REVISION_HASH]
namespace=[REQUIREMENT_AND_FINDING_NAMESPACE]
predecessor=[PREDECESSOR_IDENTITY_OR_NULL]
Requirement matrix and applicable work packages:
[FROZEN_MATRIX_AND_WORK_PACKAGES]

Read the accepted artifact from that reference, using the start-commit path for a tracked artifact or the supplied path and verifiable content hash for local-only context. Read repository instructions from the item worktree. Recompute `matrix_hash` from canonical frozen matrix bytes, validate the ordered ledger chain, verify the predecessor identity against its retained envelope when present, and recompute the current envelope revision/hash under `references/review-record-contract.md`; the ledger may advance without changing matrix bytes or `matrix_hash`. The supplied pointers are the stable evidence contract; any supplied diff is context only and is never the source of truth.

Accepted requirements and exclusions:
Verify these against [ACCEPTED_ARTIFACT_REFERENCE] and [FROZEN_MATRIX_AND_WORK_PACKAGES]; do not recreate uncited requirements. Orchestrator scope rulings:
[SCOPE_RULINGS]

Relevant invariants and current baseline:
[INVARIANTS_AND_BASELINE]

Evidence manifest:
[EVIDENCE_MANIFEST]

Command and log pointers:
[COMMANDS_EXIT_STATUSES_AND_LOG_PATHS]

Protected unrelated paths:
[DO_NOT_TOUCH]

Before judging the implementation, derive the current state locally. At minimum inspect `git status --short --untracked-files=all`, the tracked diff from `[ITEM_START_COMMIT]`, the untracked paths, the accepted artifact, all changed files, and the tests. If submodules are present, compare their current commits and status with the recorded baseline and do not change their Git state. Use the command and log pointers to verify implementer evidence; do not treat a pointer or an agent report as proof without inspecting the worktree.

Review adversarially for requirement compliance and code quality. Check correctness, failure behavior, compatibility, security, atomicity or concurrency where relevant, diagnostics, test quality, public documentation, and scope control. Reproduce risky paths when useful.

You are read-only: do not edit source or tests; stage, commit, merge, land, or archive; create/delete branches or worktrees; or clean files. Test-created caches are acceptable only when repository-native and non-source.

Report findings first, ordered Critical, Important, then Minor, with file and line references. For an existing ledger finding, state its stable finding ID, requirement IDs, class, severity, disposition, violated requirement or concrete impact, and evidence. Report each newly discovered finding with a provisional ordinal in discovery order, requirement IDs when applicable, class, severity, proposed disposition, impact, and evidence; the orchestrator alone assigns `F-*` IDs when appending. Do not reuse an existing ID; report split findings with `parent_id` and merged findings with a canonical ID plus `related_ids`.

Then report two explicit verdicts:
- Requirement compliance: PASS or FAIL
- Code quality: PASS or FAIL

Finally report checks run, exact results, and residual risks. If no findings exist, say so explicitly.
```

An item advances only when both verdicts pass and no Critical or Important implementation defect remains. An accepted-artifact gap, new scope, or contradiction is `user_ruling_required`, stops without fixer dispatch, and leaves the frozen matrix hash unchanged. The orchestrator resolves reviewer concerns into another class or returns them to the user.

## Scoped re-review dispatch

Use this same template for every re-review, with `Review scope: re-review round <n>`. It must receive the current item worktree, original start commit, immutable accepted-artifact reference, and the full review-record identity tuple: envelope path, `envelope_id`, `matrix_hash`, current envelope revision/hash, namespace, and predecessor identity. Also provide protected paths, open findings and rulings, and pointers to the fixer commands, evidence manifests, exit statuses, and logs. It derives the current diff and repository state locally; a fix diff may identify the area to inspect but is context only. Report the same separate `Requirement compliance` and `Code quality` verdicts, explicitly stating the disposition of each stable finding ID. A purported new requirement is a `new_scope` or `accepted_artifact_gap`, not a fixer task.
