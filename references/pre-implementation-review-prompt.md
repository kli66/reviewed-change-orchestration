---
persistence: living
---

# Pre-implementation reviewer prompt template

Use a fresh-context reviewer before implementation only when the recorded risk decision triggers review. The reviewer is independent from the implementer and is read-only; every accepted item still receives an orchestrator-frozen matrix before implementation.

````text
Independently derive the pre-implementation execution contract for accepted change [CHANGE_REFERENCE]. Do not edit anything.

Working directory: you are already at the item worktree root. Do not `cd` before your first command; use worktree-relative paths for all tool arguments.
Absolute worktree path (audit identifier only, not an operating instruction): [ABSOLUTE_WORKTREE_PATH]

```text
If your harness did not start you in the worktree, the absolute path above is a POSIX path; confirm with `pwd` before your first command and do not rewrite it into any other host's path form.
```

Start commit: [ITEM_START_COMMIT]

Model selection record:
[MODEL_SELECTION_RECORD]

Immutable accepted-artifact reference:
[ACCEPTED_ARTIFACT_REFERENCE]

Pinned durable-contract references:
[START_COMMIT_DURABLE_CONTRACT_REFERENCES]

Execution map and risk decision:
[EXECUTION_MAP_AND_RISK_DECISION]

Review-record envelope:
path=[ENVELOPE_PATH]
envelope_id=[ENVELOPE_ID]
matrix_hash=[MATRIX_HASH_OR_PENDING]
current_revision_hash=[CURRENT_ENVELOPE_REVISION_HASH_OR_PENDING]
namespace=[REQUIREMENT_AND_FINDING_NAMESPACE]
predecessor=[PREDECESSOR_IDENTITY_OR_NULL]

Protected unrelated paths:
[DO_NOT_TOUCH]

Read the immutable accepted artifact from its reference, the named durable contracts at the item start commit, and repository instructions in the item worktree. When a predecessor is present, read its retained identity as lineage context without modifying it. Derive current repository state locally. Do not rely on an implementer report, create a matrix or ledger, or modify the envelope.

Apply this authority order: the accepted artifact controls accepted scope; repository-wide instructions and accepted ADR invariants apply when they explicitly govern every affected path; a requirement found only in another durable document is an `accepted_artifact_gap`; and any conflict with the accepted artifact is a `contradiction`. Do not infer authority from a document merely because it is durable.

For every accepted obligation and applicable invariant, report a proposed matrix row with a source reference, invariant or evidence field, authoritative acquisition point, required re-observation points, comparison or rejection point, side-effect cutoff, value-free diagnostic requirement, focused regression obligation, live-verification mode (`not_required`, `automated`, or `operator_gated`), and unresolved ambiguity. State `not_applicable` and why for each inapplicable field; do not invent blank obligations.

Identify failure domains. Propose work packages when there is more than one failure domain, or when owned file/test groups have different side-effect cutoffs or evidence dependencies. Use source references or provisional row ordinals, not requirement IDs. Each proposed package names invariants, owned files, side-effect cutoff, focused tests, and evidence dependencies. Do not create additional lifecycle items or commit boundaries.

Report proposed rows, package membership, and concerns in discovery order using source references or provisional ordinals. Do not allocate stable requirement or finding IDs. Identify accepted-artifact gaps, new-scope proposals, contradictions, and reviewer concerns separately from implementation defects. For each uncertainty, state whether implementation may proceed. Credentials, live systems, and diagnostics must be described value-free.

You are read-only: do not edit source or tests; do not write the review-record envelope; stage, commit, merge, land, archive; create/delete branches or worktrees; or clean files. Run only non-destructive inspection or focused checks if needed.
````

The orchestrator alone allocates stable IDs, adjudicates classes and dispositions, creates the immutable matrix, and appends the findings ledger under `references/review-record-contract.md`.
