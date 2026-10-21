---
persistence: living
---

# Roadmap

The living orchestration contract is `SKILL.md` plus its phase and role references. Active changes below are ordered by their front-matter dependencies; the generated diagram is authoritative only as a projection of those declarations.

## Active changes

- `docs/changes/archive/2026-07-31-converge-adversarial-review-contract/` (landed) — establish risk-triggered pre-implementation review and stable requirement and finding identities.
- `docs/changes/archive/2026-08-13-define-v0-accepted-work-envelopes/` (landed) — define the four versioned, strategy-neutral accepted-work envelopes and their offline owner validation seam.
- `docs/changes/archive/2026-08-16-defer-stale-owner-work/` (landed) — move two pre-coordination proposals into trigger-gated deferred work, correct landed status wording, and remove obsolete local recovery state.
- `docs/spec/deferred-work.md` (deferred register) — preserve validation-evidence and review-bound accept-and-execute options until their explicit promotion triggers fire.
- `docs/changes/archive/2026-10-21-review-record-tooling/` (landed) — offline stdlib tooling for the review-record envelope (matrix/ledger/envelope identity per review-record-contract v0.1.0): `matrix-hash`, `ledger-hash`, `init`, `freeze`, `append`, `verify` plus a 61-case test suite; editorial contract-doc section; no contract semantics change.
- `docs/changes/archive/2026-10-21-delegated-worktree-cwd/` (landed) — launch every delegated role with the child working directory at the item worktree root, keep the absolute path as an audit identifier only, and require a recorded POSIX-only `pwd`-confirmation fallback where a host cannot set a child working directory.

<!-- BEGIN GENERATED DAG (regenerate: doc-contract update --repo-root .) -->
```mermaid
flowchart TD
    converge_adversarial_review_contract["converge-adversarial-review-contract (landed)"]
    defer_stale_owner_work["defer-stale-owner-work (landed)"]
    define_v0_accepted_work_envelopes["define-v0-accepted-work-envelopes (landed)"]
    delegated_worktree_cwd["delegated-worktree-cwd (landed)"]
    review_record_tooling["review-record-tooling (landed)"]
    converge_adversarial_review_contract --> define_v0_accepted_work_envelopes
    define_v0_accepted_work_envelopes --> defer_stale_owner_work
```
<!-- END GENERATED DAG -->
