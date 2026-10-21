---
persistence: living
---

# Fixer prompt template

Use the original implementer when it remains effective; otherwise dispatch a fresh or more capable fixer. Give it findings verbatim and keep the reviewer read-only.

````text
Fix the adjudicated review findings for accepted change [CHANGE_REFERENCE].

Working directory: you are already at the item worktree root. Do not `cd` before your first command; use worktree-relative paths for all tool arguments.
Absolute worktree path (audit identifier only, not an operating instruction): [ABSOLUTE_WORKTREE_PATH]

```text
If your harness did not start you in the worktree, the absolute path above is a POSIX path; confirm with `pwd` before your first command and do not rewrite it into any other host's path form.
```

Start commit: [ITEM_START_COMMIT]
Fix round: [ROUND] of 3

Model selection record:
[MODEL_SELECTION_RECORD]

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

Open findings and orchestrator rulings:
[OPEN_FINDINGS_AND_RULINGS]

Read the current implementation and tests before editing. Make the smallest changes that resolve the stable finding IDs without expanding accepted scope or changing frozen matrix bytes. An accepted-artifact gap, new scope, or contradiction is `user_ruling_required`, not a fixer task. Add or improve regression coverage where the harness supports it.

Do not stage, commit, merge, land, archive, create/delete branches or worktrees, edit the landing checkout, or alter unrelated material. In submodules, build, test, compile, and explicitly declared artifact-generation commands are allowed, but do not commit, amend, checkout, switch, reset, rebase, merge, cherry-pick, update the index, change the checked-out commit, or update a superproject gitlink without exact user approval. Stop and report any unapproved submodule repository-state change.

Run affected focused validation:
[FOCUSED_VALIDATION]

Report:
- finding-by-finding disposition against stable IDs;
- files changed;
- commands run with exact pass/fail results, covered-bytes manifests/fingerprints, exact command, relative working directory plus recorded absolute audit pointer, normalized execution context, dependency and mutable-external-input identity, and log paths;
- any finding still open or requiring a product/architecture decision.
````

After every fix dispatch, launch a read-only scoped re-review in the item worktree under the delegated working-directory contract in `references/worktree-lifecycle.md`, and provide the original start commit, immutable accepted-artifact reference, and the full review-record identity tuple: envelope path, `envelope_id`, `matrix_hash`, current envelope revision/hash, namespace, and predecessor identity. Also provide protected paths, open findings/rulings, and fixer command/evidence/exit-status/log pointers. A fix diff may be supplied only as context; the reviewer derives the current state locally and separately reports compliance and quality verdicts. Do not accept the fixer's own clearance as closure.
