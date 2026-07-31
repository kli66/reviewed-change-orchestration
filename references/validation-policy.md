---
persistence: living
---

# Validation policy

Match evidence to the state transition it proves. A green command proves only the exact tree on which it ran.

## Clean baseline

Run the cheapest meaningful repository-native check before implementation. It should distinguish pre-existing failure from item regressions without paying for the entire suite when a focused smoke or test subset is sufficient.

Record known baseline failures explicitly. Proceed only when they are understood and do not mask the changed surface.

## Implementer evidence

Run focused tests and changed-surface formatting, lint, or type checks. Add a direct behavioral spot-check when the test harness does not expose the boundary.

For a reproducible defect with a useful seam, prove regression coverage by observing the test fail without the fix and pass with it. Do not require test-first work for document-only changes or code without a meaningful harness.

## Pre-implementation review evidence

For every accepted item, record the explicit risk decision, immutable accepted-artifact reference, start-commit durable-contract references, and the full review-record identity tuple: envelope path, `envelope_id`, frozen `matrix_hash`, current envelope revision/hash, namespace, and predecessor identity when any. Also record applicable work packages before implementation. A `none` decision skips only the pre-implementation reviewer: the orchestrator derives and freezes accepted obligations and applicable invariants directly. A triggered item incorporates the independent pre-review report before freezing. A credential-bearing, fail-closed, identity-bound, mutable, live, provenance-sensitive, destructive, concurrent, or security-sensitive boundary needs an acquisition point, required re-observation, rejection point before side effects, and value-free diagnostic obligation in its matrix row.

Live verification is `not_required`, `automated`, or `operator_gated`. An operator-gated check is not claimed as automated coverage: record its required authority, credential boundary, and result separately. If credentials, infrastructure, or authority are unavailable, report that live verification as not run. Do not persist credential values, credential-bearing URIs, or raw unbounded secret-bearing output in evidence, diagnostics, logs, the envelope, or eval results.

## Reviewer evidence

The read-only reviewer receives and inspects the full review-record identity tuple: envelope path, `envelope_id`, `matrix_hash`, current envelope revision/hash, namespace, and predecessor identity. It also inspects the accepted artifact, frozen requirement matrix, actual diff, changed and untracked files, tests, and implementer results. It may run focused reproductions or non-destructive checks, especially for risky failure paths. It recomputes the matrix and current envelope identities, verifies cited requirements rather than recreating uncited scope, reports existing stable finding IDs and new findings in provisional discovery order, and keeps requirement-compliance and code-quality verdicts separate. Its primary independent value is judgment, not ceremonial repetition of an unchanged full suite.

## Evidence identity and reuse

Record each validation command with:

- a covered-bytes manifest and fingerprint for tracked changes, index state, and untracked files the command can read; include ignored or generated inputs when they are part of that command's scope;
- the exact command, relative working directory, and recorded absolute working-directory audit pointer;
- normalized execution context: canonical repository identity from the common Git directory, relative working directory, command argv, relevant environment keys/values, platform, and toolchain identity, not the absolute item or landing worktree path;
- dependency identity (lockfiles plus resolved dependency/tool versions) and every mutable external input read by the command, or an explicit declaration that no mutable external input is read;
- exit status and an external log path; and
- Git provenance (`HEAD`, branch, and dirty-status summary) for reporting.

Git provenance is not the reusable state identity: the same bytes can be dirty before a commit and clean after a fast-forward. Recorded absolute paths are audit pointers only. Reuse evidence only when the command, covered bytes, relative working directory, normalized execution context, dependency identity, and mutable external inputs are equivalent. A difference reruns the affected gate; unknown external or mutable input makes evidence non-reusable. A reviewer reproduction is independent evidence and should not be skipped merely because an implementer command has a reusable record.

## Final fixed-point gate

After the last fix, the orchestrator runs the canonical repository test, lint, type, build, and lifecycle commands required for the changed surface. This is the pre-commit code-state gate. Read complete output and record a complete evidence record; do not infer success from a sub-agent report.

If exit reconciliation or transactional landing mutates inputs covered by that gate, rerun the affected canonical commands after landing. If it changes only lifecycle state covered by a separate resolver, run that resolver rather than repeating an unrelated expensive suite.

## Merged-state verification

After fast-forward integration and before cleanup, prove:

- landing `HEAD` is the item commit;
- the temporary branch is an ancestor of the landing branch;
- lifecycle/document checks still pass;
- integration-sensitive tests pass when the landing checkout, generated state, hooks, or environment can differ from the item worktree.

Do not automatically rerun an unchanged expensive suite solely because the commit moved by fast-forward. Run the checks whose evidence could have changed at integration.

After all items, run one repository-wide canonical gate on the landing branch unless final fixed-point evidence has equivalent covered bytes, command, relative working directory, normalized execution context, dependency identity, and mutable external inputs after landing. In that case, reuse the evidence and still run merged-state and lifecycle checks whose inputs can differ at integration.

## Report boundaries honestly

Report focused tests, full tests, lint/type/build checks, lifecycle gates, and live external smoke tests separately. Name anything skipped because infrastructure, credentials, or authority was unavailable. Never collapse partial evidence into “all checks passed.”
