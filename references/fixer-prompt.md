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

Do not stage, commit, merge, land, archive, create/delete branches or worktrees, edit the landing checkout, or alter unrelated material. In submodules, build, test, compile, and explicitly declared artifact-generation commands are allowed, but do not commit, amend, checkout, switch, reset, rebase, merge, cherry-pick, update the index, change the checked-out commit, or update a superproject gitlink without exact user approval. Stop and report any unapproved submodule repository-state change.

Run affected focused validation:
[FOCUSED_VALIDATION]

Report:
- finding-by-finding disposition;
- files changed;
- commands run with exact pass/fail results, covered-bytes manifests/fingerprints, exact command, relative working directory plus recorded absolute audit pointer, normalized execution context, dependency and mutable-external-input identity, and log paths;
- any finding still open or requiring a product/architecture decision.
```

After every fix dispatch, send a read-only scoped re-review the current item-worktree path, original start commit, immutable accepted-artifact reference, protected paths, open findings/rulings, and fixer command/evidence/exit-status/log pointers. A fix diff may be supplied only as context; the reviewer derives the current state locally and separately reports compliance and quality verdicts. Do not accept the fixer's own clearance as closure.
