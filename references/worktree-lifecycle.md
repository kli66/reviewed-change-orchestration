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

If the host already placed the session in an isolated workspace, do not create a nested worktree blindly. Prefer the host's native isolation mechanism when it can create an item workspace and provides clear ownership/cleanup. Otherwise use the configured worktree root, defaulting to `~/worktrees`, while leaving the host-managed workspace untouched. Never designate an externally managed workspace as owned cleanup material.

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

## Enforce submodule boundaries

Record initialized submodules recursively before implementation and after each delegated command:

```bash
git submodule status --recursive
git submodule foreach --recursive 'git rev-parse HEAD && git status --short --untracked-files=all'
```

Build, test, compile, and explicitly declared artifact-generation commands may create or update their expected filesystem outputs inside a submodule. They do not authorize repository-state changes. Require the user's explicit approval for the exact submodule path and operation before allowing a commit or amend, checkout or switch, reset, rebase, merge, cherry-pick, index update, checked-out commit change, or superproject gitlink change. A blanket approval is insufficient.

Treat any unapproved tracked change, undeclared untracked residue, changed submodule `HEAD`, or changed superproject gitlink as a stop condition. Do not stage or land submodule changes under the item unless the approved scope explicitly includes that exact operation. Preserve the worktree and branch for recovery when the boundary is crossed.

## Select a location

Use this order after the host-managed-workspace check:

1. `[worktree].root` in `<target-repo>/.reviewed-change-orchestration.toml`.
2. `~/worktrees`.

Expand `~` using the invoking user's home directory and require an absolute root outside the canonical target repository and its existing managed worktrees. Canonicalize the configured root with physical-path resolution. Before creating any directory, inspect every existing ancestor through the configured root for a symlink, non-directory, inaccessible component, or repository/common-Git-directory/registered-worktree collision. Then inspect every existing generated descendant at or below the canonical root; reject a symlink, non-directory, inaccessible component, or physical path outside that root. Missing components are not evidence of safety: create only the deterministic repository bucket and item bucket, one component at a time, after rechecking each newly created component by physical path and containment beneath the canonical root. Do not modify `.git/info/exclude` or `.gitignore` to make the root acceptable.

Generate a deterministic, sanitized path as `<worktree-root>/<repo-slug>-<repo-id>/<item-slug>-<short-start-commit>`, where `repo-id` is a short stable identifier derived from the canonical Git common directory. Use `rco/<item-slug>-<short-start-commit>` for the temporary branch. Check the branch name before creating anything: an existing local or remote-tracking name is an ownership collision and stops the item; never choose a suffix or another identity. If the exact generated path already exists, including a dangling symlink or non-directory, treat it as a recovery or ownership collision and stop; never overwrite it or silently select another path. Record the canonical root, canonical created path, branch, start commit, root source, ancestor checks, and creation mechanism. This record defines what the workflow owns.

## Create and establish a baseline

Create the branch and worktree from the exact landing HEAD:

```bash
git worktree add -b <temporary-branch> <absolute-worktree-path> <item-start-commit>
```

If an accepted change artifact is intentionally untracked or ignored and repository policy treats it as local-only orchestration context, copy only that named artifact into the item worktree after creation. Record it as protected local material, keep it outside the index, and do not run repository document lifecycle operations merely to make it trackable.

Inside the new worktree:

1. Confirm `HEAD` equals the recorded item start commit and the temporary branch is checked out.
2. Confirm tracked status is clean.
3. Confirm the recorded submodule baseline and run only repository-declared setup needed for this checkout; do not mutate tracked dependency or lock files or submodule repository state incidentally.
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

1. Confirm the recorded canonical worktree path is still registered to the recorded temporary branch, and recheck every existing ancestor for the containment contract before acting on it.
2. Confirm the item commit is reachable from the landing branch. Classify all parent-worktree and recursive-submodule residue before removal: tracked changes, staged changes, untracked files, ignored files, generated artifacts, and nested-submodule state. Only an absent path or an explicitly declared item-owned generated artifact under its bounded owned path is disposable. Any other residue, including an undeclared file in the parent worktree or a nested submodule, retains the worktree and branch for recovery.
3. Snapshot the landing checkout before cleanup: `git status --short --untracked-files=all`, `git config --local --get-regexp '^submodule\.'` (record no-match explicitly), `git submodule status --recursive`, and recursive submodule `HEAD`/status. Cleanup must leave this snapshot byte-for-byte equivalent for the landing checkout's configuration and semantically equivalent for its status and submodule commits.
4. Do not run `git submodule deinit` in a linked worktree when its configuration can be shared with the landing checkout. Prefer removal without deinitialization. Deinitialization is permitted only after proving the target submodule configuration is worktree-local, recording its exact config scope, and verifying the landing snapshot remains unchanged afterward. Never use `--force` deinitialization.
5. From outside the worktree, run `git worktree remove <absolute-worktree-path>`. When Git requires force solely because the worktree contains an initialized submodule, use one `git worktree remove --force` only after steps 1-4 prove all residue is absent or declared disposable; never use force to discard unapproved material or bypass a lock.
6. Repeat the landing snapshot and compare it before deleting the branch. Stop and preserve recovery state if landing configuration, landing status, submodule commits, or nested-submodule state changed.
7. Confirm the item commit is reachable from the landing branch, then run `git branch -d <temporary-branch>`.
8. Confirm both the registration and branch are gone.

Never use `git branch -D`, force deinitialization, or forced removal when any assertion is ambiguous. A cleanup probe must cover initialized and uninitialized submodules, dirty state, declared generated artifacts, nested submodules, and shared configuration in a two-worktree fixture; it must prove the landing checkout configuration and status stay unchanged. Never prune or remove unrelated or externally managed worktrees. On any failed assertion, preserve the branch and worktree and report their exact recovery coordinates.
