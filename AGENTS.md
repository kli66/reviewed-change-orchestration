---
persistence: living
---

# AGENTS.md — how to work in this repo

This is the durable operating contract for agents working on `reviewed-change-orchestration`. The installed `doc-contract` CLI reads `.doc-contract.toml`; no vendored runtime is required.

## Document taxonomy

```
AGENTS.md                     operating contract and change protocol
SKILL.md                      living consumer contract for orchestration behavior
references/*.md              living phase and role contracts
references/*.example.toml    non-managed configuration examples
docs/roadmap.md               living cross-change order and generated DAG
docs/changes/<name>/          ephemeral substantial work
docs/changes/archive/<date>-<name>/  landed change lineage
HANDOFF-*.md                  local-only ephemeral scaffolding, never durable state
```

Every managed Markdown document carries a `persistence:` header and is a node in the resolver. Documents outside `docs/changes/`, `docs/adr/`, and `docs/spec/` are enumerated in `.doc-contract.toml` under `root_nodes`. The same discovery result bounds value-free secret scanning; source, examples that are not managed nodes, generated output, and dependency trees remain outside this scan unless explicitly enrolled.

## Persistence model

Each managed document has one canonical question, one owner, one persistence class, and one forcing function:

- `frozen`: append-only decisions or archives, protected by `self_hash`.
- `living`: current contracts kept true by repository checks or change reconciliation.
- `ephemeral`: active change material disposed into archive on landing.
- `deferred`: trigger-gated backlog material promoted into a change when its trigger fires.

Minimize the living set. A fact must have one canonical owner; do not maintain the same contract independently in `SKILL.md`, a reference, a change, and a handoff. The skill defines the orchestration interface, references define phase-specific detail, and changes define accepted deltas.

## Change weight

- Trivial edits need no change folder; update the roadmap when they affect planned work.
- Substantial work uses one `docs/changes/<name>/change.md` by default with `Why`, `What changes`, `Tasks`, and `Verify` sections.
- Split proposal, design, and tasks only when each document is independently substantial.

## Change and handoff protocol

Substantial open work lives in `docs/changes/<name>/`, not in a root handoff. A `HANDOFF-*.md` is local-only scaffolding unless Kai explicitly says otherwise. When a handoff is consumed, first capture its durable content into the applicable change, roadmap, ADR, specification, or project memory; make those artifacts self-contained; then remove the consumed handoff and create a fresh handoff only for remaining work.

Before touching an active change:

1. Run `doc-contract reconcile mechanical <change> --phase entry --format json --repo-root .`, adding `--include-untracked` only for explicitly provisional work.
2. Compare the change against the roadmap, applicable durable contracts, and current repository state. Mechanical readiness does not replace semantic reconciliation.
3. Stop on a contradiction, missing acceptance authority, or a material scope choice. Only explicit user or reviewer authority permits `doc-contract accept`.
4. Run `doc-contract begin` only after acceptance and entry reconciliation; it refuses proposed, blocked, and landed changes.

Before handing off or landing:

1. Run `doc-contract reconcile mechanical <change> --phase exit --format json --repo-root .` and repair semantic drift.
2. Run `doc-contract land <change> --repo-root . --dry-run`; add `--diff` when line-level inspection is warranted.
3. Inspect the complete plan, then run the same command without `--dry-run`. Do not hand-edit status, roadmap, fingerprint, journal, or archive transitions.
4. Preserve durable findings before the change moves to `docs/changes/archive/<date>-<name>/`.

## Dependency and hashing rules

Every change declares its upstream `depends_on` edges and `files_owned` in YAML front matter. Declare only upstream dependencies; dependents are computed. Front matter is the canonical source of order, while the generated Mermaid block in `docs/roadmap.md` is a rendered view.

Dependency topology is mandatory. With `edge_fingerprints = "advisory"`, missing fingerprints are accepted while explicit empty, pending, malformed, or stale fingerprints warn. Frozen `self_hash` validation remains strict. Hashes normalize front matter, line endings, trailing whitespace, and boundary blank lines, but prose and Markdown changes remain significant.

## Repository-specific invariants

- Use this orchestration workflow only for accepted, non-trivial changes whose implementation, local landing, and commit are explicitly authorized.
- Keep exactly one repository change active at a time; never parallelize item integration.
- The orchestrator alone owns worktrees, branches, staging, commits, fast-forward integration, landing, and cleanup. Delegated roles work only inside the named item worktree and never mutate Git lifecycle state.
- Preserve unrelated tracked, untracked, ignored, generated, submodule, and external worktree material.
- Obtain independent fresh-context read-only review; do not treat implementer confidence as review evidence.
- Run final-fixed-point validation against the exact tree being landed, stage only owned paths, and create exactly one neutral Conventional Commit per item. A separately authorized tracked-baseline or acceptance checkpoint is distinct.
- Never push, create a pull request, deploy, or mutate remote branches without separate authorization.
- Treat `Proposed (not accepted)` and `blocked` as hard stops for execution.

## Validation

Run the documentation contract and repository-native checks from the repository root:

```bash
doc-contract check --repo-root . --offline
doc-contract check --repo-root .
python3 -m json.tool evals/evals.json >/dev/null
git diff --check
```

The capability subprocess checks that `evals/evals.json` remains valid JSON. It does not substitute for semantic review of `SKILL.md`, references, change requirements, or eval assertions.
