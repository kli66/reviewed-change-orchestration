---
id: deepen-evidence-and-readiness
persistence: ephemeral
status: proposed
depends_on:
  - converge-adversarial-review-contract
files_owned:
  - docs/changes/deepen-evidence-and-readiness/change.md
  - SKILL.md
  - references/orchestrator-checklist.md
  - references/validation-policy.md
  - references/worktree-lifecycle.md
  - references/implementer-prompt.md
  - references/reviewer-prompt.md
  - references/fixer-prompt.md
  - scripts/evidence.py
  - tests/test_evidence.py
  - evals/evals.json
fingerprints:
  converge-adversarial-review-contract: 076f7939d2d13c41
---
# Deepen validation evidence and environment readiness

Status: Proposed (not accepted) · Proposed 2026-07-31

**Upstream dependencies:** `docs/changes/converge-adversarial-review-contract/` must land first because focused fix evidence and final review records refer to its stable requirement and finding identities. Repository-native validation commands remain authoritative. Python 3.9 or newer is a required skill-host prerequisite for this change; a host without it is unsupported by this helper and must stop rather than select another unreviewed implementation substrate.
**Dependents:** `docs/changes/integrate-planned-accept-and-execute/` uses the resulting preflight and evidence-record interface for its separate acceptance checkpoint.
**Files owned:** `SKILL.md` · `references/orchestrator-checklist.md` · `references/validation-policy.md` · `references/worktree-lifecycle.md` · `references/implementer-prompt.md` · `references/reviewer-prompt.md` · `references/fixer-prompt.md` · `scripts/evidence.py` (new) · `tests/test_evidence.py` (new) · `evals/evals.json`

## Why

The workflow's evidence identity is intentionally strict, but callers must currently reproduce a long record shape manually in the execution map and every delegated prompt. That is a shallow interface: command execution, byte coverage, environment normalization, dependency identity, logging, residue classification, and reuse comparison are distributed across callers and are easy to record inconsistently.

Environment failures also arrive too late. Worktree-root restrictions, unavailable Git metadata mutation, unwritable default tool caches, missing toolchains, and unauthorized live inputs can invalidate implementation or validation after expensive dispatches. The workflow needs one bounded readiness record and one deep evidence module while retaining repository ownership of the actual gates.

## What changes

**Delta ADDED** - A small, standard-library evidence module that records declared validation commands and compares evidence identities; a two-phase environment preflight record; machine-readable evidence records and reasoned reuse decisions; executable fixture tests covering security, failure, residue, and equivalence behavior.

**Delta MODIFIED** - The execution map and role prompts pass evidence-record pointers rather than reproducing every field. Implementer and fixer boundaries record focused evidence, while the initial implementation boundary and final fixed point require complete records. Merged-state reuse is decided through the same module.

**Delta REMOVED** - Repeated prose-only construction and comparison of evidence manifests. No repository-native test, lint, type, build, lifecycle, or live gate is replaced, inferred, or hard-coded into the generic skill.

## Tasks

1. Design and version the external interface before implementation. Keep it to three operations: `preflight --phase <host|item> --spec <json> [--prior <host.json>] --out <json>`, `run --spec <json> --out <json> --log <path> -- <command>`, and `compare <left.json> <right.json>`. Define canonical JSON encoding, atomic record writes, schema compatibility, phase transition rules, error modes, and Python 3.9+ support.
2. Implement the helper as a Python 3.9+ standard-library-only module. Keep internal collection seams private; do not expose adapters without a production and test use.
3. Define the preflight spec as orchestrator declarations plus observable probes: prospective worktree root/path, required tools, setup command, baseline command, expected setup residue, live-input names and authorization, cache override variable names/defaults/bounded candidates, evidence-root candidates, ownership identity, and `sequence` or host-managed `retain` retention. The helper probes filesystem/tool state; it records but does not invent authority or live-input authorization.
4. Split readiness into two immutable phase records. Host phase inspects tracked-state prerequisites, prospective worktree containment and parent writability, declared tool presence, and declared live-input availability without Git metadata mutation. Item phase consumes the host record, selects and binds declared bounded cache and evidence roots before setup, runs the declared setup command, rejects residue outside its declaration, confirms tracked/index state, and runs the declared baseline command before expensive dispatches.
5. Select a per-item writable temporary or cache location only from caller-declared candidates and set only declared override variables. Record the selected environment explicitly, clean only proven item-owned temporary state, and do not hard-code UV, pytest, or another repository policy into the generic interface.
6. Require callers to declare covered paths, dependency inputs, mutable external inputs, relevant non-secret environment fields, expected generated residue, and a `coverage_basis` identifying the repository contract or execution-map ruling behind the declaration. Compute manifests, byte fingerprints, normalized repository and relative-working-directory identity, exact command argv, exit status, log location, and Git provenance from those declarations.
7. State the assurance limit explicitly: the helper validates declaration shape and proves equivalence only within the declared coverage universe. Evidence is reusable only when the orchestrator attests that the declaration covers the repository-native gate contract; omitted or uncertain coverage is `unknown` and non-reusable rather than inferred complete.
8. Make secret handling value-free for declared secret sources. Accept secret environment names and log policy, read values only in process memory for exact-value and credential-bearing-URI redaction, never persist values or digests, and reject recorded argv that embeds a declared secret. If secret-bearing output cannot be bounded, do not persist raw output and mark the evidence non-reusable with `secret_output_risk=unknown`.
9. Capture redacted stdout and stderr in an external evidence root selected by preflight, using a mode-0700 directory, mode-0600 files, and atomic writes. Keep pointers valid through sequence completion; record the retention policy and either clean sequence-scoped evidence after reporting or leave host-managed retained evidence untouched. A failed command still produces an inspectable non-passing record.
10. Permit reusable evidence only for commands executed by `run`. Record operator-gated or externally executed validation as `not_run` or non-reusable attestation with its reason; do not equate imported claims with helper-executed evidence.
11. Implement deterministic comparison that returns `reusable` or `not_reusable` plus field-level reasons. Require equivalence of command, covered bytes, relative working directory, normalized execution context, dependency identity, mutable external inputs, coverage basis, secret policy, and passing status; treat absolute paths and Git provenance as audit metadata only.
12. Define a complete phase evidence set as a manifest accounting for every gate ID selected in the execution map with a passing reusable record, policy-permitted authorized `not_run`, or explicit failure. Record aggregate disposition separately: completeness means every gate is accounted for and never authorizes progression; the existing validation policy permits progression only when every required gate passes or its named policy explicitly permits `not_run`.
13. Replace repeated field lists in the execution map and role prompts with stable record, evidence-set, and log pointers plus the declarations the receiving role must inspect. Preserve reviewer independence: an implementer record never suppresses a useful reviewer reproduction.
14. Record affected focused evidence and stable finding dispositions during fix rounds. Reuse unaffected records only after comparison succeeds. Require complete evidence sets at the initial implementation boundary and final fixed point, and preserve merged-state lifecycle and integration-sensitive checks.
15. Add temporary-repository fixture tests for schema/version handling, atomic writes, command success and failure, tracked/index/untracked/ignored byte coverage, equivalent bytes across worktree paths, dependency changes, mutable external changes, relative-working-directory changes, unknown coverage, declared-secret redaction, unknown secret output, generated residue, bounded cache fallback, log permissions/retention, and absence of unauthorized Git mutation.
16. Add eval scenarios showing early cache fallback, two fix rounds with selective evidence regeneration, complete final-fixed-point evidence, and an explicit non-reuse reason after an identity change.

## Verify

- `python3 -m unittest discover -s tests -p 'test_*.py'` passes on the declared Python 3.9+ support matrix using only the standard library.
- `python3 -m json.tool evals/evals.json` succeeds and `git diff --check` reports no errors.
- A fixture proves identical covered bytes and normalized context remain reusable across different absolute worktree paths and Git provenance.
- Fixtures prove changed dependencies, changed or unknown mutable inputs, changed commands or relative working directories, and incomplete declarations are non-reusable with explicit reasons.
- Declared secret values and credential-bearing URI userinfo never appear in records, persisted logs, diagnostics, or test failure output; unknown secret-output risk fails closed to non-reusable evidence without persisting raw output.
- Preflight selects a bounded writable cache only from declared candidates when a declared default is unavailable, records missing or unauthorized live inputs, and performs no Git metadata mutation.
- Existing fixed-point, independent-review, lifecycle, integration, and cleanup guarantees remain intact, while role prompts no longer require manual reconstruction of the full evidence schema.
