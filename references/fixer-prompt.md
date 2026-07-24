# Fixer prompt template

Use the original implementer when it remains effective; otherwise dispatch a fresh or more capable fixer. Give it findings verbatim and keep the reviewer read-only.

```text
Fix the adjudicated review findings for accepted change [CHANGE_REFERENCE].

Work only in this item worktree: [ABSOLUTE_WORKTREE_PATH]
Start commit: [ITEM_START_COMMIT]
Fix round: [ROUND] of 3

Model selection record:
[MODEL_SELECTION_RECORD]

Accepted requirements and exclusions:
[REQUIREMENTS_AND_EXCLUSIONS]

Open findings and orchestrator rulings:
[OPEN_FINDINGS_AND_RULINGS]

Read the current implementation and tests before editing. Make the smallest changes that resolve the findings without expanding accepted scope. Add or improve regression coverage where the harness supports it.

Do not stage, commit, merge, land, archive, create/delete branches or worktrees, edit the landing checkout, or alter unrelated material.

Run affected focused validation:
[FOCUSED_VALIDATION]

Report:
- finding-by-finding disposition;
- files changed;
- commands run with exact pass/fail results;
- any finding still open or requiring a product/architecture decision.
```

After every fix dispatch, send only the fix diff and open findings to a read-only scoped re-review. Do not accept the fixer's own clearance as closure.
