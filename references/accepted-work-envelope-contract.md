---
persistence: living
---

# Accepted-work envelope contract

## Purpose and ownership

Version `0.1.0` defines one offline owner seam with exactly four public records: `AcceptedBundle`, `AttemptBinding`, `ReviewedItemHistory`, and `CandidateBundle`. The complete wire-shape authority is `schemas/accepted-work-envelopes-v0.1.0.schema.json`; `scripts/accepted_work_envelopes.py` evaluates that supported schema subset and then enforces canonical identity, graph, path, lineage, status, and observation invariants. Private authority, evidence, readiness, reconciliation, finding, assembly, and observation records are subordinate `$defs`, not additional envelopes.

Every envelope has exactly `schema_id`, `schema_version`, `kind`, `id`, and `body`. `schema_id` is `reviewed-change-orchestration.accepted-work-envelopes`; `schema_version` is exact `0.1.0`. Unknown IDs, versions, kinds, fields, or unsupported checked-in schema keywords fail closed.

## Canonical wire and parser limits

`id` is `sha256:` plus SHA-256 of canonical UTF-8 JSON containing `schema_id`, `schema_version`, `kind`, and `body`, excluding only `id`. `canonical_document_sha256` hashes the complete canonical envelope. Canonical JSON is `json.dumps(sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)` encoded as UTF-8 without a newline.

| Rule | Exact v0 behavior |
| --- | --- |
| Input size | Document and context are each at most 8 MiB, inclusive. |
| Depth | Root has depth 1; each nested object or array adds 1; depth 64 is allowed. |
| Containers | Each object or array may contain at most 10,000 entries, inclusive. |
| Strings | Strings are NFC and at most 1 MiB in UTF-8, inclusive. |
| Numbers | Numeric fields are finite integers; booleans never satisfy integer fields. |
| Object names | Duplicate JSON object names are rejected before structural validation. |
| Set-like arrays | Must already be sorted and unique; validation never silently normalizes them. |
| Ordered arrays | Commit, assembly, and other semantic sequences preserve caller order. |

Locators are exact `{scheme, value}` objects. `scheme` matches `^[a-z][a-z0-9.-]{0,63}$`. `value` is non-empty NFC, contains no control or whitespace, and is at most 2,048 UTF-8 bytes. Only `scheme = "uri"` invokes `urllib.parse.urlsplit`; it requires a valid absolute URI scheme and rejects username or password userinfo. Every other scheme remains opaque, including URI-looking relative or userinfo text.

Repository path grants are `{path, scope}` with `scope = file | tree`. Paths are POSIX repository-relative and reject empty values, absolute paths, backslashes, NUL, repeated separators, and `.` or `..` segments. Namespaced capability/action identifiers match `<namespace>:<name>`. Absence denies authority.

## Envelope fields and invariants

### `AcceptedBundle`

| Field | Meaning and invariant |
| --- | --- |
| `repository_id` | Exact repository identity for every item. |
| `repository_capabilities`, `repository_actions` | Sorted unique ceilings; item grants are subsets. |
| `items` | Sorted stable item identities with independent item authority, accepted-source reference, accepted outcomes, preserved behavior, exclusions, controls, paths, capability/action grants, verification obligations, and requirements. |
| `membership` | Sorted private assertions, each containing item ID plus authority and evidence independent of the corresponding item acceptance. The asserted ID set equals the item set exactly. |
| `dependencies` | Known, distinct item IDs; no duplicate/self edge; graph is acyclic. |

Authority and evidence references are required but are not trust proof. Duplicate item, authority, evidence, requirement, path, capability, action, membership, or edge identities fail. Two item path claims may overlap only when dependency reachability orders those items.

### `AttemptBinding`

| Field | Meaning and invariant |
| --- | --- |
| Upstream identity | Exact accepted-bundle, item, run, attempt, and repository identities. |
| Git/worktree identity | Exact base and candidate commit/tree, branch, and worktree identity or `not_applicable`. |
| `dependency_readiness` | `ready \| not_ready \| blocked \| ambiguous`; the exact required dependency-ID set equals the sorted observed set, and each observation names a `reviewed_success` history and current candidate tree. |
| `reconciliation` | `acceptance_preserving \| not_preserving \| blocked \| ambiguous`, rationale, and evidence. |
| `authorities` | Explicit nested authority references; presence is not trust proof. |
| `budgets` | Named units with non-negative integer `limit`, `consumed`, and `remaining`; `limit = consumed + remaining`. |
| `grant_ceiling` | Intrinsic accepted-item paths, capabilities, actions, and the subset classified as mutation actions. Selected grants and next actions must narrow this ceiling structurally. |
| Grants/actions | Selected paths, capabilities, actions, and next actions; contextual observations independently compare the intrinsic ceiling and selections. |
| `fencing_identity` | SHA-256 identity preimage containing the normal envelope identity fields with only `fencing_identity` omitted. |

Only next actions classified as mutation actions require `ready` plus `acceptance_preserving`; non-mutation observation/reporting actions remain representable while blocked. Contextual validation compares every binding identity, readiness/evidence fact, grant ceiling, selection, authority ID, and budget before a consumer may treat the binding as current.

### `ReviewedItemHistory`

| Field | Meaning and invariant |
| --- | --- |
| Upstream identity | Exact bundle, item, run, attempt binding, attempt, review, and history identities. |
| Git lineage | Candidate base, ticket branch, final tip, and ordered meaningful `implementation | review_fix` commits. Parent links are contiguous and final commit/tree equals final tip. |
| Accepted/review identity | Digest-bound accepted artifact plus exact review contract ID/version, review-envelope ID, matrix/envelope hashes, namespace, and optional predecessor tuple. |
| Requirements/findings | Full requirement coverage, stable findings, imported classes/severities/dispositions, and explicit residual finding IDs. |
| Verdicts | Independent compliance and quality wire verdicts are exactly `pass | fail`. |
| `validation_observations` | One or more obligation IDs with `pass \| fail \| unknown` and digest-bound evidence. |
| `outcome` | `reviewed_success \| incomplete \| failed \| blocked \| ambiguous`. |

`reviewed_success` requires at least one meaningful commit, complete commit requirement coverage, contiguous lineage, both verdicts passing, every validation observation passing, and only legal final `implementation_defect` dispositions. Critical/Important defects are `fixed` or `rejected_as_reviewer_error`; Minor defects may also be `accepted_residual`. Any current gap, new scope, contradiction, reviewer concern, open finding, unknown evidence, or illegal residual forbids success.

### `CandidateBundle`

| Field | Meaning and invariant |
| --- | --- |
| Upstream identity | Exact accepted-bundle ID, run ID, candidate base, and assembled tip/tree. |
| Coverage | Every accepted item appears exactly once as an embedded history or explicit `blocked \| skipped \| failed \| ambiguous \| partial` outcome. |
| Assembly | Opaque strategy ID and ordered steps binding input history IDs/trees plus before/after commit/tree. Steps form a contiguous chain from candidate base to assembled tip. |
| `aggregate_interactions` | One or more interaction obligations, each bound to the final assembled tree with `pass \| failed \| unknown` and evidence. |
| Packet/artifact | Digest-bound projections carrying exact accepted-bundle, run, and final-tree identities; opaque locators are not resolved. |
| Authority/status | `authority_ceiling = local_candidate_only`; status is `local_complete \| local_partial \| local_failed \| local_ambiguous`. |

Status precedence is deterministic: ambiguous or conflicting observation first, then failed item/interaction, then blocked/skipped/partial item, otherwise complete. `local_complete` requires every item to have reviewed success, a complete assembly chain, and all aggregate interactions passing. No status implies canonical integration, publication, deployment, production readiness, or authority for those effects.

## Contextual observations

Contextual validation requires exactly:

```text
context_schema_id      = reviewed-change-orchestration.accepted-work-envelope-context
context_schema_version = 0.1.0
kind                   = selected envelope kind
observations           = kind-specific private observation object
```

All kinds compare `envelope_id` and `canonical_document_sha256`. Categories are:

| Kind | Required observation categories |
| --- | --- |
| `AcceptedBundle` | repository identity, membership/dependencies, item authority/evidence records. |
| `AttemptBinding` | all binding/Git/worktree fields, readiness/reconciliation, grants/actions, authorities/budgets, and accepted-item ceilings. |
| `ReviewedItemHistory` | binding/Git lineage, current/predecessor review identities, commits/findings/outcome, accepted artifact, and validation evidence. |
| `CandidateBundle` | binding/status; history IDs, item IDs, and final trees; explicit outcomes; assembly before/after/input facts; aggregate evidence digests; and packet/artifact digests bound to the final tree. |

A contextual success means only that supplied observations equal the envelope and satisfy its narrowing/lineage rules. The module does not establish that the observation supplier is trustworthy.

## CLI and result protocol

```text
python3 scripts/accepted_work_envelopes.py validate \
  --kind <AcceptedBundle|AttemptBinding|ReviewedItemHistory|CandidateBundle> \
  --level <structural|contextual> --input <path|-> [--context <path>] [--out <path|->]
python3 scripts/accepted_work_envelopes.py canonicalize \
  --kind <AcceptedBundle|AttemptBinding|ReviewedItemHistory|CandidateBundle> \
  --input <path|-> [--out <path|->]
```

`validate` emits canonical JSON with result ID `reviewed-change-orchestration.accepted-work-envelope-validation-result`, version `0.1.0`, selected kind/level, structural/contextual flags, computed envelope/document identities when available, and sorted errors. Exit `0` means requested validation succeeded; exit `1` means invalid, incomplete, unknown, malformed, or mismatched input; exit `2` is invocation or I/O failure. `canonicalize` emits canonical envelope bytes only after structural success. File output uses a temporary sibling and atomic replacement.

Each error has only `code`, JSON Pointer `instance_path`, and sorted stable `related_ids`. It never includes accepted text, repository paths, locator values, evidence bytes, credentials, secrets, or command output. Errors sort by path, code, then related IDs. Parser failures such as duplicate names, invalid UTF-8/JSON, non-finite numbers, and size overflow use the same value-free result protocol for `validate`.

Validation results are outputs, never inputs to either operation. Consumers compare result ID/version exactly and reject unknown values before reading any validity field.

## Version and assurance boundary

Any change to the accepted instance set, canonical bytes, identity preimage, structural/contextual validity, or error meaning requires a new `0.x.0` schema and explicit compatibility decision. Editorial clarifications and implementation fixes that preserve those semantics retain `0.1.0`.

The module proves shape, canonical identity, set/subset relationships, DAG/path/lineage/status consistency, and equality with explicit observations. It does not prove human acceptance, trust anchors, reviewer independence, Git object existence, repository truth, evidence truth, process/effect completion, runtime sandbox enforcement, storage durability, integration, publication, deployment, or production readiness. It does not invoke Git/subprocesses, contact networks/providers, inspect credentials, or mutate repositories.
