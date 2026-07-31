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

Read the accepted artifact from that reference, using the start-commit path for a tracked artifact or the supplied path and verifiable content hash for local-only context. Read repository instructions from the item worktree. The supplied pointers are the stable evidence contract; any supplied diff is context only and is never the source of truth.

Accepted requirements and exclusions:
Derive these from [ACCEPTED_ARTIFACT_REFERENCE]. Orchestrator scope rulings:
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

Report findings first, ordered Critical, Important, then Minor, with file and line references. For each finding, state the violated requirement or concrete impact and the evidence.

Then report two explicit verdicts:
- Requirement compliance: PASS or FAIL
- Code quality: PASS or FAIL

Finally report checks run, exact results, and residual risks. If no findings exist, say so explicitly.
```

An item advances only when both verdicts pass and no Critical or Important finding remains. The orchestrator resolves findings that conflict with the accepted change.

## Scoped re-review dispatch

Use this same template for every re-review, with `Review scope: re-review round <n>`. It must receive the current item worktree, original start commit, immutable accepted-artifact reference, protected paths, the open findings and rulings, and pointers to the fixer commands, evidence manifests, exit statuses, and logs. It derives the current diff and repository state locally; a fix diff may identify the area to inspect but is context only. Report the same separate `Requirement compliance` and `Code quality` verdicts, explicitly stating whether each open finding is resolved.
