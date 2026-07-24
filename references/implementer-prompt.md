# Implementer prompt template

Replace every bracketed field. Keep the requirements in the accepted artifact rather than retelling the orchestration history.

```text
Implement accepted change [CHANGE_REFERENCE].

Work only in this item worktree: [ABSOLUTE_WORKTREE_PATH]
Start commit: [ITEM_START_COMMIT]

Read the complete accepted change artifact and repository instructions first.

Accepted requirements and exclusions:
[REQUIREMENTS_AND_EXCLUSIONS]

Current baseline, earlier landed interfaces, and reconciled drift:
[BASELINE_AND_DRIFT]

Protected unrelated paths:
[DO_NOT_TOUCH]

Implement the accepted behavior at its real contract boundary. Preserve behavior outside scope. Add focused acceptance coverage. When fixing a reproducible defect and the harness supports it, demonstrate that the regression test fails without the fix and passes with it.

You may edit only in-scope code, tests, and documentation inside the named worktree. Do not stage, commit, merge, land, archive, create/delete branches or worktrees, edit the landing checkout, or alter unrelated material.

Run focused validation:
[FOCUSED_VALIDATION]

Report:
- status: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED;
- files changed;
- implementation or API decisions;
- deviations, ambiguities, or descoped criteria;
- commands run with exact pass/fail results;
- validation that could not be performed.
```

Do not let an implementer turn ambiguity into scope expansion. Provide missing context, increase capability, or return the decision to the user.
