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

## Resolve tracked landing-checkout changes

Before selecting or creating an item worktree, distinguish staged and unstaged tracked changes from untracked and ignored material:

```bash
git status --short --untracked-files=no
git diff --name-status
git diff --cached --name-status
git diff --stat
git diff --cached --stat
git diff HEAD --stat
```

The status and name-status views are the complete tracked/index evidence; the modified and deleted tracked paths define the checkpoint scope, and the three diffstats show the unstaged, staged, and combined results. Treat any staged addition as protected non-checkpoint material. Also record untracked paths and any named ignored change artifact as protected local material, but do not propose adding them to the checkpoint.

If tracked modifications or deletions are present, stop before `git worktree add`. Show the user the tracked status and combined diffstat, state that existing implementation/commit authority does not cover these pre-existing changes, and ask for explicit permission to create a separate prerequisite checkpoint commit containing every current tracked modification and deletion. If a staged addition is present, also stop and ask the user to resolve it or authorize separate bounded index handling before any checkpoint.

If permission is granted:

1. Check the staged name-status for additions or other non-checkpoint material. Because `git add -u` does not remove an already staged addition, stop for user resolution or separately authorized bounded index handling if one is present.
2. Run `git add -u` from the repository root. Do not use `git add -A`, path globs, or any command that can add untracked or ignored files.
3. Inspect `git diff --cached --name-status`, `git diff --cached --stat`, `git diff --cached --check`, and the full staged diff as risk warrants.
4. Confirm the index contains all and only the previously reported tracked modifications and deletions.
5. Commit with a Conventional Commit header, a body under 50 words or no body, and no agent, AI, model, automation, generated-by, or agent `Co-authored-by` attribution.
6. Confirm `git status --short --untracked-files=no` is empty and that recorded untracked and ignored material remains unstaged and otherwise untouched.
7. Record the checkpoint commit as the item's new start commit.

This prerequisite checkpoint is not the accepted item's landing commit. The item still receives exactly one landing commit after implementation and review.

If permission is denied, retain the landing checkout unchanged and ask the user to resolve the tracked changes or explicitly authorize another bounded approach. Do not stash, discard, copy into an item worktree, or commit them implicitly.

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

If an accepted change artifact is intentionally untracked or ignored and repository policy treats it as local-only orchestration context, copy only that named artifact into the item worktree after creation. Record it as protected local material, keep it outside the index, and do not run repository document lifecycle operations merely to make it trackable.

Inside the new worktree:

1. Confirm `HEAD` equals the recorded item start commit and the temporary branch is checked out.
2. Confirm tracked status is clean.
3. Run only repository-declared setup needed for this checkout; do not mutate tracked dependency or lock files incidentally.
4. Run the cheapest meaningful clean-baseline gate.

A clean tracked status is not a passing validation baseline. If setup or baseline validation fails, retain the worktree and branch. Investigate or ask whether to proceed with a known baseline failure; do not erase the evidence.

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
