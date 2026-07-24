# Item worktree lifecycle

The orchestrator owns every operation in this file. Delegated agents receive an absolute worktree path but no branch, integration, or cleanup authority.

## Discover the host state

Record these facts before creating anything:

```bash
git rev-parse --show-toplevel
git rev-parse --git-dir
git rev-parse --git-common-dir
git rev-parse --show-superproject-working-tree
git branch --show-current
git rev-parse HEAD
git status --short
git worktree list --porcelain
```

Different Git and common directories normally indicate a linked worktree, but a submodule also has distinct metadata. Use `--show-superproject-working-tree` to distinguish them.

If the host already placed the session in an isolated workspace, do not create a nested worktree blindly. Prefer the host's native isolation mechanism when it can create an item workspace and provides clear ownership/cleanup. Otherwise create a sibling Git worktree from the common repository while leaving the host-managed workspace untouched. Never designate an externally managed workspace as owned cleanup material.

The landing branch must be named, locally available, and at the commit recorded in the execution map. Resolve detached HEAD or an ambiguous landing target before implementation.

## Select a location

Use this order:

1. An applicable repository or user instruction declaring a worktree location.
2. An existing project-local `.worktrees/` directory.
3. An existing project-local `worktrees/` directory.
4. A project-local `.worktrees/` directory.

For a project-local location, prove it is ignored with `git check-ignore`. Do not place a worktree there until the check succeeds. Do not slip a `.gitignore` edit into an accepted item's commit; establish the ignored location separately or stop for direction.

Choose collision-resistant temporary names, for example `rco/<item-slug>-<short-start-commit>` and `.worktrees/<item-slug>-<short-start-commit>`. Record the branch, absolute path, start commit, and creation mechanism. This record defines what the workflow owns.

## Create and establish a baseline

Create the branch and worktree from the exact landing HEAD:

```bash
git worktree add -b <temporary-branch> <absolute-worktree-path> <item-start-commit>
```

Inside the new worktree:

1. Confirm `HEAD` equals the recorded item start commit and the temporary branch is checked out.
2. Confirm tracked status is clean.
3. Run only repository-declared setup needed for this checkout; do not mutate tracked dependency or lock files incidentally.
4. Run the cheapest meaningful clean-baseline gate.

If setup or baseline fails, retain the worktree and branch. Investigate or ask whether to proceed with a known baseline failure; do not erase the evidence.

## Integrate safely

After the orchestrator creates the single item commit:

1. Confirm the item worktree has no unintended tracked modifications and record the item commit.
2. Confirm the landing branch still points to the recorded item start commit. A moved landing branch is reconciliation work: stop and reassess or replay the item in a newly based worktree; never force it back.
3. Confirm the landing checkout can accept the update without overwriting unrelated local changes.
4. From the landing checkout, fast-forward only:

```bash
git merge --ff-only <temporary-branch>
```

5. Confirm the landing branch `HEAD` equals the item commit and the temporary branch is an ancestor.
6. Run merged-state verification selected by `validation-policy.md`.

Do not use reset, force-update, an implicit merge commit, or conflict resolution to disguise landing-branch movement.

## Clean only proven owned state

Cleanup is allowed only after merged-state verification passes:

1. Confirm the recorded worktree path is still registered to the recorded temporary branch.
2. Confirm it has no tracked or untracked item residue that would be lost.
3. Run `git worktree remove <absolute-worktree-path>` from outside that worktree.
4. Confirm the item commit is reachable from the landing branch, then run `git branch -d <temporary-branch>`.
5. Confirm both the registration and branch are gone.

Do not use forced removal or `git branch -D` in this workflow. Never prune or remove unrelated or externally managed worktrees. On any failed assertion, preserve the branch and worktree and report their exact recovery coordinates.
