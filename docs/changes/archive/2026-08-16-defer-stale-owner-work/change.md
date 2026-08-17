---
id: defer-stale-owner-work
persistence: ephemeral
status: landed
depends_on:
  - define-v0-accepted-work-envelopes
files_owned:
  - docs/changes/defer-stale-owner-work/change.md
  - docs/changes/archive/2026-08-13-define-v0-accepted-work-envelopes/change.md
  - docs/spec/deferred-work.md
  - docs/roadmap.md
accepted_at: 2026-08-16
started_at: 2026-08-16
landed_at: 2026-08-16
archive_path: docs/changes/archive/2026-08-16-defer-stale-owner-work
---
# Defer stale owner work

Status: Landed · 2026-08-16

**Upstream dependencies:** The landed `define-v0-accepted-work-envelopes` change establishes the current Track 1 owner seam and makes neither stale proposal a prerequisite for the first dogfood.
**Dependents:** None. A later trigger may promote either deferred entry into a newly reconciled proposal.
**Files owned:** The two stale active change artifacts, the new deferred register, the roadmap projection, the landed envelope archive's stale status sentence, and this change artifact. The explicitly authorized local recovery-branch deletion is a Git-ref cleanup rather than a repository file.

## Why

The two active proposals predate the reconciled cross-project sequence. `deepen-evidence-and-readiness` is not required by the landed envelope contract and conflicts with the repository's current Python baseline. `integrate-planned-accept-and-execute` remains blocked on an unaccepted provider capability and is outside the first dogfood critical path. Keeping either item active misstates current priority and creates avoidable ownership pressure.

The landed envelope archive also retains one stale sentence saying the change is in progress, and the local recovery branch points to an incomplete superseded implementation. The user explicitly authorized deferring both proposals, correcting the archive status wording, and deleting that recovery branch. This authority does not include a commit, push, publication, or other remote effect.

## What changes

**Delta ADDED** - One trigger-gated deferred-work register preserving the two future options and their promotion conditions.

**Delta MODIFIED** - The roadmap reports no active execution path for the deferred items, and the landed envelope archive consistently describes the item as landed.

**Delta REMOVED** - The two stale active change folders and the obsolete local recovery branch. Git history preserves their prior detailed proposals and recovery state.

## Acceptance feasibility

1. The independently reviewable outcome is one truthful owner-repository state: both stale proposals are parked behind explicit triggers, the landed archive is internally consistent, and the obsolete local recovery ref is absent.
2. Documentation topology, frozen-lineage wording, and local branch cleanup are distinct checks but share one truth boundary; leaving only part complete would retain misleading active or recovery state.
3. The artifact burden is bounded to one deferred register, roadmap/lifecycle projection, one sentence correction, transactional change archival, and local Git/doc-contract verification. No runtime toolchain or live service is required.
4. Only `reviewed-change-orchestration` changes. `harness-design`, `personal-pi`, and `doc-contract` remain read-only evidence. The user authorized the named local mutations but not commit, publication, or remote effects.
5. The register is written before the active proposals are removed, so their triggers remain durable. The recovery branch is deleted only after its superseded commit identity is rechecked. No intermediate state claims either proposal is accepted or executable.
6. **Keep atomic.** The bounded work packages are deferred-register creation, active-change removal and roadmap regeneration, archive wording correction, local branch cleanup, and verification. Splitting them would preserve contradictory current-state projections without creating an independently useful landing.

## Tasks

1. Add deferred entries for evidence/readiness and accept-and-execute work, each with an exact promotion trigger and current non-critical-path rationale.
2. Remove the two active proposal folders and regenerate the roadmap DAG so neither remains schedulable.
3. Correct the landed envelope archive's stale in-progress sentence without changing its implementation claims.
4. Delete `recovery/define-v0-accepted-work-envelopes` after confirming it still points to the superseded `9111174` commit and is not checked out.
5. Reconcile and land this cleanup through `doc-contract`, leaving the result uncommitted and unpublished.

## Verify

- `doc-contract check --repo-root . --offline` reports no errors or stale active-change warnings.
- `python3 -m unittest discover -s tests -p 'test_*.py'`, JSON parsing, and `git diff --check` pass.
- `git branch --list recovery/define-v0-accepted-work-envelopes` returns no branch.
- The deferred register contains one concrete `Trigger:` for each removed proposal, and the roadmap links the register.
- The final report states that no commit, fetch, push, or publication occurred.
