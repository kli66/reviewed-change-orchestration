# Validation policy

Match evidence to the state transition it proves. A green command proves only the exact tree on which it ran.

## Clean baseline

Run the cheapest meaningful repository-native check before implementation. It should distinguish pre-existing failure from item regressions without paying for the entire suite when a focused smoke or test subset is sufficient.

Record known baseline failures explicitly. Proceed only when they are understood and do not mask the changed surface.

## Implementer evidence

Run focused tests and changed-surface formatting, lint, or type checks. Add a direct behavioral spot-check when the test harness does not expose the boundary.

For a reproducible defect with a useful seam, prove regression coverage by observing the test fail without the fix and pass with it. Do not require test-first work for document-only changes or code without a meaningful harness.

## Reviewer evidence

The read-only reviewer inspects requirements, actual diff, changed and untracked files, tests, and implementer results. It may run focused reproductions or non-destructive checks, especially for risky failure paths. Its primary independent value is judgment, not ceremonial repetition of an unchanged full suite.

## Final fixed-point gate

After the last fix, the orchestrator runs the canonical repository test, lint, type, build, and lifecycle commands required for the changed surface. This is the pre-commit code-state gate. Read complete output and record exit status; do not infer success from a sub-agent report.

If exit reconciliation or transactional landing mutates inputs covered by that gate, rerun the affected canonical commands after landing. If it changes only lifecycle state covered by a separate resolver, run that resolver rather than repeating an unrelated expensive suite.

## Merged-state verification

After fast-forward integration and before cleanup, prove:

- landing `HEAD` is the item commit;
- the temporary branch is an ancestor of the landing branch;
- lifecycle/document checks still pass;
- integration-sensitive tests pass when the landing checkout, generated state, hooks, or environment can differ from the item worktree.

Do not automatically rerun an unchanged expensive suite solely because the commit moved by fast-forward. Run the checks whose evidence could have changed at integration.

After all items, run one repository-wide canonical gate on the landing branch.

## Report boundaries honestly

Report focused tests, full tests, lint/type/build checks, lifecycle gates, and live external smoke tests separately. Name anything skipped because infrastructure, credentials, or authority was unavailable. Never collapse partial evidence into “all checks passed.”
