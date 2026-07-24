# Read-only reviewer prompt template

Use a fresh-context reviewer. Supply repository facts and evidence, not the implementer's confidence or design narrative.

```text
Independently review accepted change [CHANGE_REFERENCE]. Do not edit anything.

Item worktree: [ABSOLUTE_WORKTREE_PATH]
Start commit: [ITEM_START_COMMIT]

Model selection record:
[MODEL_SELECTION_RECORD]

Read the accepted artifact, repository instructions, current status, changed and untracked files, actual diff, implementation, and tests.

Accepted requirements and exclusions:
[REQUIREMENTS_AND_EXCLUSIONS]

Relevant invariants and current baseline:
[INVARIANTS_AND_BASELINE]

Changed-surface evidence:
[STATUS_DIFF_AND_CHANGED_FILES]

Implementer test evidence:
[COMMANDS_AND_RAW_RESULTS]

Protected unrelated paths:
[DO_NOT_TOUCH]

Review adversarially for requirement compliance and code quality. Check correctness, failure behavior, compatibility, security, atomicity or concurrency where relevant, diagnostics, test quality, public documentation, and scope control. Reproduce risky paths when useful.

You are read-only: do not edit source or tests; stage, commit, merge, land, or archive; create/delete branches or worktrees; or clean files. Test-created caches are acceptable only when repository-native and non-source.

Report findings first, ordered Critical, Important, then Minor, with file and line references. For each finding, state the violated requirement or concrete impact and the evidence.

Then report two explicit verdicts:
- Requirement compliance: PASS or FAIL
- Code quality: PASS or FAIL

Finally report checks run, exact results, and residual risks. If no findings exist, say so explicitly.
```

An item advances only when both verdicts pass and no Critical or Important finding remains. The orchestrator resolves findings that conflict with the accepted change.
