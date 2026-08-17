---
id: define-v0-accepted-work-envelopes
persistence: ephemeral
status: landed
depends_on:
  - converge-adversarial-review-contract
files_owned:
  - docs/changes/define-v0-accepted-work-envelopes/change.md
  - .doc-contract.toml
  - pyproject.toml
  - uv.lock
  - references/accepted-work-envelope-contract.md
  - references/review-record-contract.md
  - schemas/accepted-work-envelopes-v0.1.0.schema.json
  - scripts/accepted_work_envelopes.py
  - tests/fixtures/accepted_work_envelopes_v0_1_0.json
  - tests/test_accepted_work_envelopes.py
fingerprints:
  converge-adversarial-review-contract: 076f7939d2d13c41
accepted_at: 2026-08-12
started_at: 2026-08-12
landed_at: 2026-08-13
archive_path: docs/changes/archive/2026-08-13-define-v0-accepted-work-envelopes
---
# Define the v0 accepted-work envelopes

Status: Landed · 2026-08-13

**Upstream dependencies:** The landed `docs/changes/archive/2026-07-31-converge-adversarial-review-contract/` supplies the stable requirement, finding, disposition, matrix, and review-envelope identities reused by `ReviewedItemHistory`. This change does not depend on the proposed `deepen-evidence-and-readiness` helper: v0 carries opaque, digest-bound evidence references and validates their lineage without adopting that helper's not-yet-accepted evidence-record interface. It is also independent of `integrate-planned-accept-and-execute`, whose provider-bound acceptance lifecycle does not own neutral accepted-work semantics.
**Dependents:** No active in-repository change depends on this proposal. The later accepted `personal-pi` controller change and the harness-design Track 3 dogfood consume the four envelopes without redefining them. A downstream consumer must pin this repository revision and invoke the owner CLI; it must not copy the schema or validation rules.
**Files owned:** `references/accepted-work-envelope-contract.md` (new canonical human contract) · `references/review-record-contract.md` (bind existing requirement/finding semantics to the v0 schema) · `schemas/accepted-work-envelopes-v0.1.0.schema.json` (new machine-readable schema) · `scripts/accepted_work_envelopes.py` (new standard-library contract module and CLI) · `tests/fixtures/accepted_work_envelopes_v0_1_0.json` (new deterministic fixture corpus) · `tests/test_accepted_work_envelopes.py` (new interface tests) · `pyproject.toml` and `uv.lock` (declarative Python 3.12+ test environment) · `.doc-contract.toml` (enroll the new human contract) · this change artifact. No active change owns these future source, schema, fixture, test, or environment paths. The only shared semantic surface is the already-landed review-record contract; no active change lists that file.

## Why

The first harness dogfood needs one semantic owner for exact accepted input, attempt fencing, reviewed item lineage, and local candidate output. Today this repository defines stable review-record identities and orchestration rules, but it has no versioned machine contract that a controller can validate without reinterpreting prose. Letting `personal-pi` invent those records would split authority between the semantic owner and the controller. Publishing only an accepted-item input would create the same split for reviewed histories and candidates.

The smallest useful seam is therefore one deep, standard-library contract module whose only cross-project record kinds are `AcceptedBundle`, `AttemptBinding`, `ReviewedItemHistory`, and `CandidateBundle`. The module owns structural validation, deterministic canonical encoding, content identity, lineage checks, and pure comparison with explicit caller observations. It does not own acceptance decisions, repository observation, Git mutation, evidence storage, orchestration, candidate assembly, packet rendering, or canonical integration.

The change is landed. It defines and validates an offline contract only; it does not accept real work, run a controller, or authorize any repository or external effect.

## What changes

**Delta ADDED** - One canonical human contract, one Draft 2020-12 JSON Schema artifact, one Python 3.12+ standard-library module with a two-operation CLI, one declarative `uv` environment, and one offline conformance corpus covering all four envelopes and their failure modes.

**Delta MODIFIED** - The review-record contract gains a versioned machine-reuse section so `ReviewedItemHistory` references its existing requirement, matrix, finding, severity, disposition, namespace, and envelope identities rather than defining a second review model. `.doc-contract.toml` enrolls the new human contract.

**Delta REMOVED** - None. No orchestration behavior, storage profile, provider adapter, Pi package, Git policy, or target-repository authority moves into this module.

### External seam

The complete executable interface is one script with two operations:

```text
python3 scripts/accepted_work_envelopes.py validate \
  --kind <AcceptedBundle|AttemptBinding|ReviewedItemHistory|CandidateBundle> \
  --level <structural|contextual> \
  --input <path|-> [--context <path>] [--out <path|->]

python3 scripts/accepted_work_envelopes.py canonicalize \
  --kind <AcceptedBundle|AttemptBinding|ReviewedItemHistory|CandidateBundle> \
  --input <path|-> [--out <path|->]
```

`structural` validates the selected envelope's schema and all intrinsic invariants. `contextual` additionally requires a caller-supplied observation context with `context_schema_id = "reviewed-change-orchestration.accepted-work-envelope-context"`, `context_schema_version = "0.1.0"`, the selected envelope kind, and its observations; any other context ID, version, kind, or field fails closed. It checks authority/evidence presence, exact upstream envelope identities, repository/Git observations, and lineage consistency before reporting success. The context is an operation-local observation wrapper under private schema definitions, not a fifth durable envelope. `canonicalize` performs structural validation and emits canonical bytes only for a valid envelope. There are no public classes for nested authority, event, storage, transition, snapshot, reconciliation, or observation records.

The CLI exits `0` only when the requested operation succeeds, `1` for a deterministic invalid, incomplete, unknown, or mismatched result, and `2` for invocation or I/O failure. `validate` emits a canonical result object with `result_schema_id = "reviewed-change-orchestration.accepted-work-envelope-validation-result"`, `result_schema_version = "0.1.0"`, selected kind and level, `structural_valid`, `contextual_valid` (`true`, `false`, or `null` when not requested), computed envelope identity, canonical document digest, and sorted value-free errors. Validation results are outputs, never inputs to either CLI operation. Consumers must compare the result ID and version exactly and reject an unknown value; the downstream-consumption fixture exercises that consumer obligation. Each error has a stable code, JSON Pointer instance path, related identity list, and no raw accepted text, evidence bytes, secret, credential-bearing locator, or unbounded command output. Errors sort by instance path, code, then related identities so equivalent invalid input produces byte-identical results.

### Wire and identity rules

Every envelope has exactly these top-level fields and no unknown properties:

```text
schema_id       = "reviewed-change-orchestration.accepted-work-envelopes"
schema_version  = "0.1.0"
kind            = one of the four envelope names
id              = "sha256:" plus 64 lowercase hexadecimal characters
body            = the kind-specific object
```

`id` is the SHA-256 digest of canonical UTF-8 JSON containing `schema_id`, `schema_version`, `kind`, and `body`, excluding only the self-referential `id` field. `canonical_document_sha256` is the digest of the complete canonical envelope including `id`. The validator recomputes both and rejects a missing or mismatched `id` before contextual checks. Envelope references always carry the exact upstream envelope `id`; callers do not substitute mutable names or paths for content identity.

Canonical JSON uses Python standard-library `json.dumps` with `sort_keys=True`, `separators=(',', ':')`, `ensure_ascii=False`, and `allow_nan=False`, encoded as UTF-8 with no trailing newline. The parser rejects duplicate object names, a document or context larger than 8 MiB, a container deeper than 64 where the root object has depth 1 and each nested object or array adds 1, any object or array with more than 10,000 entries, and any string larger than 1 MiB when UTF-8 encoded. Limits are inclusive: exactly 8 MiB, depth 64, 10,000 entries, and a 1 MiB string are eligible for all other validation, while the next byte, depth, or entry fails. Booleans are not accepted as integers, non-finite numbers are impossible, and v0 permits integer numeric fields only. Strings must be valid Unicode normalized to NFC. Arrays whose order is semantic preserve that order; set-like arrays must already be unique and sorted by their declared stable identity, otherwise validation fails instead of silently rewriting caller intent.

Stable evidence, authority, packet, and artifact locators use `{scheme, value}`. `scheme` matches `^[a-z][a-z0-9.-]{0,63}$`; `value` is a non-empty NFC string of at most 2,048 UTF-8 bytes with no control character or whitespace. The pair is otherwise opaque and is never resolved or normalized. Exactly `scheme = "uri"` selects URI validation: parse the complete `value` with Python 3.9 standard-library `urllib.parse.urlsplit(value, allow_fragments=True)`, require a non-empty parsed URI scheme matching the same scheme syntax, and reject any authority whose parsed `username` or `password` is not `None`. No other locator scheme receives URI parsing or credential inference. The contract therefore forbids syntactic URI userinfo deterministically but makes no general claim that opaque locator text is credential-free. Diagnostics identify only the instance path and error code, never the locator value.

Repository paths are POSIX repository-relative paths represented by `{path, scope}` where `scope` is `file` or `tree`. Empty paths, `.`, `..`, absolute paths, backslashes, NUL, repeated separators, non-normalized segments, and duplicate normalized claims are rejected. Two items may not own overlapping paths unless dependency reachability orders them. Capabilities and permitted actions are sorted unique namespaced identifiers declared by the accepted item; a later envelope may only select a subset. Absence denies authority. The contract validates subset and path containment but does not execute or enforce an effect.

The schema version is exact, not a compatibility range. `schema_version = "0.1.0"` is part of accepted bytes and identity. Any change to the accepted instance set, canonical encoding, identity preimage, intrinsic/contextual validity, or error meaning creates a new `0.x.0` schema and compatibility decision; the contract never guesses compatibility. Editorial annotations, implementation fixes, and fixture/test corrections that do not alter those semantics retain envelope `schema_version = "0.1.0"` and the existing artifact name rather than pretending a patch label can leave identity unchanged. The envelope schema, operation context, validation result, and review-record binding each start at exact version `0.1.0` under their distinct IDs. Unknown schema IDs, versions, envelope kinds, fields, capability identifiers that violate syntax, or context versions fail closed in the owner CLI. Validation results are not CLI inputs; a consumer must reject an unknown result ID/version before using any result field. Supporting `$defs` remain private to this schema and do not become independent contracts.

### `AcceptedBundle`

The body records one repository identity and explicit repository capability ceiling; a sorted item set; independently confirmed membership; and a dependency edge set. Every item has a stable item ID, its own authority reference and exact accepted-source evidence reference, accepted outcomes, preserved behavior, exclusions, controls, path grants, capability/action grants, verification obligations, and requirement references. Evidence references contain a stable locator, media type, byte length, and SHA-256 identity; authority references contain an opaque authority ID, authority scheme, subject, decision ID, and stable locator. The schema requires the references but does not claim that the authority is trusted or that a person genuinely accepted the item.

Membership must equal the item-ID set exactly and must be asserted independently from each item's acceptance reference. Dependency edges use known distinct item IDs, contain no duplicates or self-edges, and form an acyclic graph. Validation rejects duplicate item, requirement, evidence, authority, path, capability, action, or edge identities; unknown membership or dependencies; cycles; missing accepted-source or authority references; malformed or escaping paths; overlapping unordered ownership; and grants beyond the repository capability ceiling. Contextual validation can prove only that caller-supplied authority and evidence observations match the references. It reports authority as unverified when observations are absent and never promotes bundle membership into item acceptance.

### `AttemptBinding`

The body binds the exact accepted-bundle ID, item ID, run ID, attempt ID, repository ID, accepted base commit/tree, current candidate commit/tree, branch identity, and worktree identity or explicit `not_applicable`. It carries dependency-readiness and semantic-reconciliation outcomes with rationale/evidence references; authority references; finite budget entries with caller-selected unit, limit, consumed, and remaining non-negative integers; selected path/capability grants; next permitted action IDs; and a fencing identity. The fencing identity is `sha256:` plus the SHA-256 digest of canonical UTF-8 JSON containing the envelope `schema_id`, `schema_version`, `kind = "AttemptBinding"`, and `body` with only `fencing_identity` omitted. The outer envelope `id` is then computed normally over the complete body including that fence, avoiding self-reference while binding every other binding field.

Budgets must be finite and arithmetically consistent, but the module defines no project-wide values. Selected grants and next actions must be subsets of the accepted item. `ready` requires every dependency to identify a reviewed-success history on the current candidate lineage and reconciliation to be acceptance-preserving; `not_ready`, `blocked`, and `ambiguous` remain explicit and cannot permit mutation actions. Contextual validation recomputes the fence and compares every binding observation with an explicit current observation, including bundle/item/run/attempt, repository, base, candidate commit/tree, branch/worktree applicability, and grant ceiling. A missing, stale, or mismatched observation fails with field-level codes before a consumer may treat the binding as current. The module performs no Git query and grants no mutation authority itself.

### `ReviewedItemHistory`

The body records the accepted-bundle, item, run, attempt-binding, attempt, review, and history identities; exact candidate base commit/tree; ticket branch; final tip commit/tree; and the ordered meaningful commit range. Each commit is classified as `implementation` or `review_fix`, identifies its commit/tree and parent lineage, and references covered accepted requirements. High-frequency checkpoints are not part of this range.

Review semantics are imported from `references/review-record-contract.md` under `review_contract_id = "reviewed-change-orchestration.review-record"` and exact `review_contract_version = "0.1.0"`. A history carries those fields plus the exact accepted-artifact reference, `envelope_id`, `matrix_hash`, final `envelope_hash`, namespace, requirement IDs and coverage, stable finding IDs/classes/severities/dispositions, independent compliance and quality verdicts, repository-native validation evidence references, and explicit residuals. The schema and script reuse the contract's established enum values and identity rules; they do not create parallel requirement or finding concepts.

The outcome is exactly one of `reviewed_success`, `incomplete`, `failed`, `blocked`, or `ambiguous`. `reviewed_success` requires at least one meaningful commit, contiguous parent/tree lineage from candidate base to branch tip, complete accepted-requirement coverage, all required validation observations passing, and both independent review verdicts passing. Its referenced current review envelope may contain only final `implementation_defect` findings: Critical and Important defects must be `fixed` or `rejected_as_reviewer_error`, while Minor defects may additionally be `accepted_residual`; every rejection or residual retains the rationale required by the owner contract. A current-envelope `accepted_artifact_gap`, `new_scope`, `contradiction`, unresolved `reviewer_concern`, `open`, or `user_ruling_required` finding forbids success. A prior such finding may appear only in the retained superseded predecessor lineage after authoritative revision/reacceptance; `ReviewedItemHistory` binds the successful successor envelope and its predecessor identity. Any missing or conflicting review-record identity, illegal class/severity/disposition combination, failed validation, failed verdict, or ambiguous evidence also forbids `reviewed_success`. Contextual validation matches cited commits, trees, evidence, current and predecessor review-record hashes, and upstream binding identity against explicit observations; it does not query Git, run tests, or decide whether a reviewer was genuinely independent.

### `CandidateBundle`

The body records the accepted-bundle and run identities; exact local candidate base and assembled tip/tree; ordered embedded `ReviewedItemHistory` envelopes; explicit per-item outcomes whose non-success enum is exactly `blocked`, `skipped`, `failed`, `ambiguous`, or `partial`; an assembly receipt; aggregate verification evidence; and deterministic packet/artifact identities. An embedded history with outcome `incomplete` maps to item outcome `partial`; the other non-success history outcomes map by name. Embedding histories makes the candidate independently reconstructable while each embedded envelope retains its own content ID.

The assembly receipt identifies an opaque strategy ID, ordered assembly steps, input history IDs and trees, and before/after commit/tree identities. `merge_no_ff` is a permitted strategy ID for the first controller profile, not a required or canonical downstream policy. Aggregate evidence binds the final assembled tree and every accepted interaction obligation. Packet and artifact references contain stable locators, media types, byte lengths, and SHA-256 identities; the Markdown packet is a deterministic projection, never stronger authority than the exact envelope, Git objects, diff, and evidence.

Candidate status is exactly `local_complete`, `local_partial`, `local_failed`, or `local_ambiguous`, with an invariant `authority_ceiling = local_candidate_only`. Every accepted item must appear exactly once as a reviewed history or an explicit non-success item outcome; omission or duplication is structurally invalid, not an inferred partial result. Status follows deterministic precedence: `local_ambiguous` when any item outcome is `ambiguous` or any otherwise well-formed history, tree, receipt, aggregate evidence, packet, or artifact observation conflicts or remains unknown; otherwise `local_failed` when an item outcome or required aggregate verification is `failed`; otherwise `local_partial` when an item outcome is `blocked`, `skipped`, or `partial`; otherwise `local_complete` only when every item has one reviewed-success history, the assembly chain is complete, aggregate verification passes, and packet/artifact identities match. The validator rejects any status that differs from this precedence. No status or field may imply canonical integration, remote publication, deployment, production readiness, or permission for those effects.

### Consumption and assurance boundary

A later accepted `personal-pi` change may pin this repository as a reviewed Git submodule under its existing curation policy, expose no duplicate schema resource, and invoke `scripts/accepted_work_envelopes.py` from that pinned checkout with the Python version declared by `pyproject.toml`. Its private TypeScript adapter may translate process results into controller state, but it must persist the exact canonical envelope/result bytes and must not regenerate IDs, relax errors, copy `$defs`, or redefine success. If the pinned owner checkout or supported schema is absent, the controller fails closed. This change does not create that pin or controller change.

Structural and contextual validity have explicit limits. The module can prove shape, canonical identity, subset relationships, DAG/path/lineage consistency, and equality with supplied observations. It cannot establish human acceptance, trust anchors, reviewer independence, repository truth, Git-object existence, evidence truth, process completion, effect success, or authorization of a side effect without authoritative observations supplied by the owner of those facts. A successful contextual result means the supplied observations are internally consistent with the envelope; it is not a claim that the supplier was trustworthy.

## Tasks

1. Add `references/accepted-work-envelope-contract.md` as the canonical human-readable v0 contract and enroll it in `.doc-contract.toml`. Record the four-record external seam, field and invariant tables, structural/contextual assurance split, exact CLI behavior, canonicalization, error codes, version policy, and non-goals. Keep private support definitions subordinate to the four envelopes.
2. Amend `references/review-record-contract.md` with a machine-reuse section that assigns its current matrix/finding semantics `review_contract_id = "reviewed-change-orchestration.review-record"` and exact `review_contract_version = "0.1.0"`, then maps its canonical identity tuple, classifications, severities, dispositions, and verdicts into the `ReviewedItemHistory` schema. The envelope change imports these semantics rather than forking them.
3. Add `schemas/accepted-work-envelopes-v0.1.0.schema.json` as one Draft 2020-12 schema with four public envelope `$defs`, private nested `$defs`, `additionalProperties: false` throughout, exact version/kind constants, strict IDs and locators, integer-only quantities, NFC/path requirements documented through schema annotations, and no remote `$ref` or network resolution.
4. Implement `scripts/accepted_work_envelopes.py` using the Python 3.12+ standard library declared by `pyproject.toml`. Keep parsing, schema-subset evaluation, graph/path/lineage validation, observation comparison, canonical encoding, and atomic output helpers private. Reject unsupported schema keywords at module self-check instead of silently under-validating the checked-in schema.
5. Implement the exact `validate` and `canonicalize` operations, deterministic exit codes, canonical result/error format, content ID and complete-document digest computation, and fail-closed version behavior. Do not read Git, invoke subprocesses, contact a provider, inspect credentials, mutate a repository, or infer absent evidence.
6. Implement intrinsic validators for bundle membership and DAGs, ordered path overlap, grant/action subsets, finite budgets, binding fences, meaningful commit continuity, imported review-record identities and dispositions, candidate assembly/tree lineage, aggregate status, and packet/artifact consistency.
7. Implement contextual comparison against explicit operation-local observations. Require complete observations for contextual success; report absent authority/evidence/Git facts as unknown or missing, exact stale binding fields as mismatches, and untrusted real-world authority as outside the module's assurance rather than silently accepted.
8. Add one deterministic fixture corpus at `tests/fixtures/accepted_work_envelopes_v0_1_0.json`. It contains a valid synthetic same-repository `A -> B` bundle with independent `C`; valid derived instances of all four envelopes; matching and stale observations; meaningful implementation/review-fix commits; requirement coverage, validation, findings/dispositions, and residuals; a complete local candidate; and a partial/failed candidate. All commits, hashes, paths, authority IDs, and evidence locators are fake and explicitly non-authoritative.
9. Include invalid corpus cases for duplicate object names; document/context, depth, object/array-entry, string, and locator limits at the exact boundary and one unit over it; non-NFC text; booleans in integer fields; malformed locator schemes and control/whitespace; `scheme = "uri"` with a relative value, malformed URI scheme, username, or password; duplicate items; unknown dependencies; cycles; invalid membership; missing accepted-source/authority evidence; malformed or escaping ownership/capability grants; stale binding observations; illegal review finding class/severity/disposition combinations; incomplete or ambiguous reviewed success; inconsistent history/tree/assembly/aggregate/packet/artifact identity; false aggregate success; unknown envelope/context IDs or versions; and a downstream validation-result consumer receiving an unknown result ID or version. Include a valid negative-control locator whose scheme is not `uri` and whose value is URI-like relative or userinfo text; validation must preserve it as opaque and perform no URI parsing or credential inference.
10. Add `tests/test_accepted_work_envelopes.py` as black-box interface tests that invoke the CLI in temporary directories. Assert exact exit codes and canonical bytes; deterministic results across key order and absolute fixture location; equal identities for semantically identical inputs; distinct identities for changed accepted meaning; the root-depth-1 convention and every parser/locator limit exactly at and one unit beyond its inclusive boundary; rejection of malformed `uri` locators alongside acceptance and byte preservation of the non-`uri` opaque negative control; imported review finding legality; candidate-status precedence; and rejection of every invalid case before any simulated effect marker can be written.
11. Add a downstream-consumption fixture that invokes the CLI from a copied/pinned owner tree and proves a consumer can validate and retain exact owner bytes without importing or copying schema logic. Do not modify `personal-pi`; record its future pin, adapter, controller storage, and package/profile work as a separate accepted owner change.
12. Keep all tests offline and deterministic. They may read/write temporary files but must not run Git, mutate repository state, contact a provider, use credentials, access TKCS, start Milvus or Podman/Compose, or claim that fixture acceptance is real acceptance.

## Verify

- `uv run python -m unittest discover -s tests -p 'test_*.py'` passes using the locked Python 3.12+ declarative environment and no runtime dependencies outside the standard library.
- `python3 -m json.tool schemas/accepted-work-envelopes-v0.1.0.schema.json` and `python3 -m json.tool tests/fixtures/accepted_work_envelopes_v0_1_0.json` succeed.
- Repeated CLI runs over differently formatted copies of the valid `A -> B` plus independent `C` corpus emit byte-identical canonical envelopes, validation results, envelope IDs, and document digests.
- Invalid duplicate names, parser/locator bounds, Unicode/integer forms, membership, dependencies, cycles, authority/evidence references, path escape, capability expansion, stale observations, review finding combinations, lineage, aggregate success, envelope/context IDs or versions, and validation-result IDs or versions at the consumer each fail with stable value-free error codes and no repository or external effect. A non-`uri` locator containing URI-like relative or userinfo text remains valid, opaque, and byte-preserved.
- A matching `AttemptBinding` observation passes contextual comparison; each mismatched repository, bundle, item, run, attempt, base, candidate commit/tree, branch, worktree, grant, or fence field fails before mutation permission can be inferred.
- A reviewed-success fixture reuses the exact review-record identity tuple and enum semantics; an incomplete or ambiguous fixture cannot validate as reviewed success.
- A complete local candidate binds every accepted item and final tree; partial, failed, blocked, or ambiguous candidates remain reconstructable and cannot report aggregate success or imply canonical integration.
- `python3 -m json.tool evals/evals.json`, `doc-contract check --repo-root . --offline`, and `git diff --check` succeed. Baseline warnings for other proposed changes' not-yet-created owned files remain reported separately.

## Deferred and unresolved authority

This change requires typed references or bounded fields but deliberately does not choose authority-receipt trust anchors; exact pilot items or their acceptance; wall-time, turn, retry, or risk budget values; controller storage root; append-only JSONL/event reconstruction; process supervision; ticket branches; worker/reviewer/fixer dispatch; candidate assembly execution; Markdown rendering; canonical integration strategy or authority; remote publication; credentials; sandbox provider; TKCS infrastructure; production corpus; deployment; retention hardening; or production readiness. Those decisions remain with humans and the later accepted Track 2, Track 3, target-repository, sandbox-owner, and integration-owner changes.
