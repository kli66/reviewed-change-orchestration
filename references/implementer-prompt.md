---
persistence: living
---

# Implementer prompt template

Replace every bracketed field. Keep the requirements in the accepted artifact rather than retelling the orchestration history.

````text
Implement accepted change [CHANGE_REFERENCE].

Working directory: you are already at the item worktree root. Do not `cd` before your first command; use worktree-relative paths for all tool arguments.
Absolute worktree path (audit identifier only, not an operating instruction): [ABSOLUTE_WORKTREE_PATH]

```text
If your harness did not start you in the worktree, the absolute path above is a POSIX path; confirm with `pwd` before your first command and do not rewrite it into any other host's path form.
```

Start commit: [ITEM_START_COMMIT]

Model selection record:
[MODEL_SELECTION_RECORD]

Read the complete accepted change artifact and repository instructions first.

Accepted requirements and exclusions:
[REQUIREMENTS_AND_EXCLUSIONS]

Frozen review record:
envelope=[ENVELOPE_PATH]
envelope_id=[ENVELOPE_ID]
matrix_hash=[MATRIX_HASH]
current_revision_hash=[CURRENT_ENVELOPE_REVISION_HASH]
namespace=[REQUIREMENT_AND_FINDING_NAMESPACE]
predecessor=[PREDECESSOR_IDENTITY_OR_NULL]
Requirement matrix and applicable work packages:
[FROZEN_MATRIX_AND_WORK_PACKAGES]

Current baseline, earlier landed interfaces, and reconciled drift:
[BASELINE_AND_DRIFT]

Protected unrelated paths:
[DO_NOT_TOUCH]

Implement the frozen accepted obligations and applicable work packages at their real contract boundaries. Preserve behavior outside scope. Do not reinterpret an accepted-artifact gap, new scope, contradiction, or reviewer concern as implementation authority. Add focused acceptance coverage. When fixing a reproducible defect and the harness supports it, demonstrate that the regression test fails without the fix and passes with it.

You may edit only in-scope code, tests, and documentation inside the named worktree. Do not stage, commit, merge, land, archive, create/delete branches or worktrees, edit the landing checkout, or alter unrelated material. In submodules, build, test, compile, and explicitly declared artifact-generation commands are allowed, but do not commit, amend, checkout, switch, reset, rebase, merge, cherry-pick, update the index, change the checked-out commit, or update a superproject gitlink without exact user approval. Stop and report any unapproved submodule repository-state change.

Run focused validation:
[FOCUSED_VALIDATION]

Report:
- status: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED;
- files changed;
- implementation or API decisions;
- requirement IDs and work packages addressed;
- deviations, ambiguities, or descoped criteria;
- commands run with exact pass/fail results, covered-bytes manifests/fingerprints, exact command, relative working directory plus recorded absolute audit pointer, normalized execution context, dependency and mutable-external-input identity, and log paths;
- validation that could not be performed.
````

Do not let an implementer turn ambiguity into scope expansion. Provide missing context, increase capability, or return the decision to the user.
