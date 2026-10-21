---
id: delegated-worktree-cwd
persistence: ephemeral
status: landed
depends_on:
files_owned:
  - docs/changes/delegated-worktree-cwd/change.md
  - SKILL.md
  - references/worktree-lifecycle.md
  - references/implementer-prompt.md
  - references/reviewer-prompt.md
  - references/fixer-prompt.md
  - references/pre-implementation-review-prompt.md
  - references/orchestrator-checklist.md
  - evals/evals.json
  - docs/roadmap.md
accepted_at: 2026-10-21
started_at: 2026-10-21
landed_at: 2026-10-21
archive_path: docs/changes/archive/2026-10-21-delegated-worktree-cwd
---
# Launch delegated roles in the item worktree (delegated working directory)

Status: Landed · 2026-10-21

**Upstream dependencies:** None. Independent of the `review-record-tooling` change, which
landed on 2026-10-21 at `7916dbe` before this item began: the only shared surface is
`docs/roadmap.md`, and file overlap is reconciliation against the latest landed HEAD, not a
dependency edge. No landed or deferred artifact is
consumed; nothing in `docs/spec/deferred-work.md` covers dispatch working directories.
**Dependents:** None.

**Files owned:** `references/worktree-lifecycle.md` (canonical owner of the delegated
working-directory contract: rule, audit-pointer status, fallback) ·
`references/implementer-prompt.md`, `references/reviewer-prompt.md`,
`references/fixer-prompt.md`, `references/pre-implementation-review-prompt.md` (prompt
text: working-directory fact + prohibition, audit pointer, fallback block) · `SKILL.md`
(dispatch interface statements in §5–§7) · `references/orchestrator-checklist.md`
(checklist lines and per-dispatch fallback record) · `evals/evals.json` (one new eval) ·
`docs/roadmap.md` (status line + DAG on land). `references/validation-policy.md`,
`references/model-routing.md`, `references/review-record-contract.md`,
`references/accepted-work-envelope-contract.md`, `scripts/`, and `tests/` are deliberately
untouched (rationale under Δ UNCHANGED).

## Why

Every delegated dispatch currently hands the absolute item-worktree path as the child's
only operating address. The contract text establishes that handover and nothing more — it
never states where the child process actually starts. In the externally observed session
below, the child's process working directory was the repository of record, not the item
worktree, which is what made the handover the child's only *address*. The contract lines:

- `references/worktree-lifecycle.md:7` — "Delegated agents receive an absolute worktree
  path but no branch, integration, or cleanup authority."
- All four role templates put the absolute path on the operating-address line:
  `references/implementer-prompt.md:12` "Work only in this item worktree:
  [ABSOLUTE_WORKTREE_PATH]"; `references/fixer-prompt.md:12` (same sentence);
  `references/reviewer-prompt.md:12` and `references/pre-implementation-review-prompt.md:12`
  "Item worktree: [ABSOLUTE_WORKTREE_PATH]".
- `SKILL.md:95` — instantiate the implementer prompt "with that record, the absolute
  item-worktree path, and the execution map"; `SKILL.md:104` gives the reviewer "the item
  start commit and absolute worktree path"; `references/orchestrator-checklist.md:32` —
  "Give the implementer an absolute worktree path and no Git/lifecycle authority."

Externally observed evidence (session artifacts held in a different repository's records,
outside this repo; 16-child orchestration session on 2026-10-20): every child's first
command was `cd <absolute worktree> && ...`, and each child's recorded working directory
was the repository of record, not the item worktree. On one model lane carrying a
Windows-host harness prior, the model rewrote the POSIX path into that host's mount
namespace (`/var/home/kai/worktrees/...` became `C:\workspace\files\var\home\kai\worktrees\...`,
also `C:/workspace/files/...`), then spent 3–5 turns probing (`pwd`, `ls`, `find`,
`command -v cygpath`, degraded retries) before recovering via `$HOME/worktrees/...`:
6 of 9 runs on that lane, 0 of 7 on the other lanes. All failures were fail-closed — no
wrong write occurred — but turns and context were spent. Variant shapes beyond a leading
`cd`: `git -C '<mount-path>'` as the first tool call, bare path arguments to `ls`/`cat`,
and shell-variable assignments of the rewritten path. This repo's contract text contains
no `cd` instruction that could cause this: over the contract surfaces only, the
reproducing query `grep -rnE '(^|[^[:alnum:]_/-])cd[[:space:]]' SKILL.md references/`
returns zero matches (exit 1). Scope matters — the identical query also matches this
change file's own quotations of the failure
(`docs/changes/delegated-worktree-cwd/change.md:62`, `:90`), so an unscoped run over
`docs/changes/` is not zero-match. The absolute `cd` is therefore structural, induced by
the dispatch design —
and that is the trigger this change removes for this workflow entirely: if a dispatched
child starts in its item worktree, no `cd` is needed and the mount-rewrite incentive
disappears.

Harness feasibility is verified, not assumed. The subagent-harness vendor documentation
vendored outside this repo (its `docs/tool-reference.md`, dispatch-parameter table) states:

> `cwd` | string | runtime cwd | Override working directory. With `machine`, the directory on that machine.

The same page states that a workflow's *host command steps* have "no per-step `cwd`" and
directs the operator to "[s]et `cwd` on the outer `subagent({...})` request instead, or put
a trusted directory change in the command (for example, `cd /path/to/worktree && npm
test`)" (`tool-reference.md:13`). That `cd` workaround belongs to host command steps,
**not** to a delegated agent, so it is not a sanctioned substitute for setting a child's
working directory — the per-child `cwd` override is the mechanism for a dispatched agent.
Whether any *other* host supports per-child cwd is host-specific and
must be probed per host; the contract below therefore mandates a documented fallback
instead of assuming capability everywhere.

This change is contract-only. This repo ships Markdown contracts, evals, and some Python
tooling; the dispatch mechanics live in the host harness, not here. No code change is
proposed.

## What changes

### Δ ADDED — Delegated working-directory contract (`references/worktree-lifecycle.md` — canonical owner)

Reword the opening sentence (`worktree-lifecycle.md:7`) from "Delegated agents receive an
absolute worktree path but no branch, integration, or cleanup authority" to state that
delegated agents *start in* the item worktree and still receive no branch, integration, or
cleanup authority. Add a `## Delegated working directory` section owning three rules:

1. **Primary rule.** Every pre-implementation reviewer, implementer, reviewer, fixer, and
   re-review dispatch is launched with the child's process working directory set to the
   item worktree root, wherever the host harness supports per-child working directories.
   The child is already at the worktree root when its first command runs; the recorded
   child working directory must equal the item worktree root. Consequently every child
   command's recorded *relative* working directory is relative to the item worktree root,
   never to the landing checkout.
2. **Audit pointer, not operating address.** The absolute worktree path stays in the
   execution map and in each prompt as an identifier only. This reconciles the templates
   with `references/validation-policy.md`, which already requires "the exact command,
   relative working directory, and recorded absolute working-directory audit pointer"
   (`validation-policy.md:36`) and states "Recorded absolute paths are audit pointers
   only" (`validation-policy.md:42`). The prompt states the working directory as a fact,
   prohibits a `cd` before the first command, requires worktree-relative paths, and marks
   the absolute path as an audit identifier — never as an instruction to travel there.
3. **Documented fallback.** When the host harness cannot set a child's working directory,
   the dispatch keeps the current absolute-path handover but must state the path as
   POSIX-only and instruct the child to confirm with `pwd` before its first command. The
   fallback must not silently become the norm: the orchestrator records, per dispatch,
   which mode was used, and reports a host that needed only the fallback at sequence
   completion.

### Δ MODIFIED — Role prompt templates (`implementer-prompt.md`, `reviewer-prompt.md`, `fixer-prompt.md`, `pre-implementation-review-prompt.md`)

In each template, replace the single operating-address line (line 12 in each) with two
parts:

```text
Working directory: you are already at the item worktree root. Do not `cd` before your
first command; use worktree-relative paths for all tool arguments.
Absolute worktree path (audit identifier only, not an operating instruction):
[ABSOLUTE_WORKTREE_PATH]
```

plus a fenced fallback block: "If your harness did not start you in the worktree, the
absolute path above is a POSIX path; confirm with `pwd` before your first command and do
not rewrite it into any other host's path form." All authority prose is preserved
verbatim: read-only constraints, no staging/commit/merge/landing authority, submodule
boundaries, and the "commands run ... relative working directory plus recorded absolute
audit pointer" reporting line each template already contains. In `fixer-prompt.md`, align
the trailing re-review paragraph (`fixer-prompt.md:49`, "send a read-only scoped re-review
the current item-worktree path, ...") to launch the re-review in the item worktree under
the same contract, and align the parallel `## Scoped re-review dispatch` section in
`references/reviewer-prompt.md:66-68` ("It must receive the current item worktree, original
start commit, ...") the same way — neither template keeps the old operating-address
framing. The templates keep the `[ABSOLUTE_WORKTREE_PATH]` token — exactly one occurrence
each, always on the audit-identifier line.

### Δ MODIFIED — `SKILL.md` (interface statements only)

- §5: "instantiate `references/implementer-prompt.md` with that record, the absolute
  item-worktree path, and the execution map" becomes "with that record, the delegated
  working directory under `references/worktree-lifecycle.md`, and the execution map".
- §6 reviewer pointer list: "the item start commit and absolute worktree path" becomes
  "the item start commit and the item worktree as the reviewer's working directory
  (absolute path as audit pointer)". The §6 evidence bullet ("recorded absolute
  working-directory audit pointers") and the `## Complete the sequence` wording at
  `SKILL.md:165` ("absolute paths
  and Git provenance remain audit pointers") already match and stay unchanged.
- §7 re-review dispatch: launched under the same delegated working directory.
- Section references in this change use the `### N.` headings under `## Run one item`:
  §5 "Delegate implementation" (`SKILL.md:93`), §6 "Obtain independent review" (`:99`),
  §7 "Fix and re-review" (`:114`). The sequence-completion wording above lives under
  `## Complete the sequence` (`SKILL.md:161`), not §8 ("Reach the final fixed point",
  `:127`).

### Δ MODIFIED — `references/orchestrator-checklist.md`

- Replace "Give the implementer an absolute worktree path and no Git/lifecycle authority."
  with: launch every delegated role with its working directory at the item worktree root
  when the host supports per-child cwd; otherwise use the documented POSIX-only fallback
  with `pwd` confirmation, per `references/worktree-lifecycle.md`; no Git/lifecycle
  authority either way.
- Add a checklist line: record per dispatch which working-directory mode was used, and
  report a host that used only the fallback — mechanics, recording, and reporting owned by
  `references/worktree-lifecycle.md`, cited rather than restated here (`AGENTS.md:33`: a
  fact must have one canonical owner).

### Δ ADDED — `evals/evals.json` (one eval, id 19)

No existing eval encodes the current absolute-path-plus-`cd` dispatch behavior (checked:
the only absolute-path mentions are evals 9 and 14, both asserting absolute paths are
audit pointers for evidence reuse — this change strengthens that, so both stay passing).
Add one eval whose assertions pin: every delegated dispatch launches with the child's
working directory at the item worktree root when the harness supports it; the prompt
states the working directory as a fact and forbids a `cd` before the first command; the
absolute path appears only as an audit identifier; a harness without per-child cwd gets
the explicit POSIX-only fallback with `pwd` confirmation, recorded per dispatch and
reported rather than normalized away; and all existing isolation, read-only, and authority
invariants are unchanged.

### Δ UNCHANGED (deliberate)

- `references/validation-policy.md` — already the canonical owner of the audit-pointer
  semantics (`validation-policy.md:36`, `:42`); duplicating them here would violate the
  one-canonical-owner rule. The child starting at the worktree root only makes its
  "relative working directory" records uniformly worktree-relative.
- `references/model-routing.md` — model selection, not dispatch mechanics.
- `references/review-record-contract.md` and `references/accepted-work-envelope-contract.md`
  — envelope and identity semantics are untouched by dispatch location. The former was
  landed with `review-record-tooling`; this change must not touch it.
- `docs/roadmap.md` listing — deferred to acceptance and land, deliberately. An earlier
  sibling proposal-time line would have entangled two unaccepted changes in one dirty hunk;
  that sibling (`review-record-tooling`) has since landed and its line is committed, so this
  change adds its own listing once at acceptance and then lets `doc-contract` own the status
  token and the generated DAG.
  Front matter is canonical (`AGENTS.md`), so the rendered-view absence is drift, not order
  corruption.
- No code or schema change: contract-only, as stated in Why.

## Tasks

1. `references/worktree-lifecycle.md`: reword the opening sentence; add the
   `## Delegated working directory` section with the primary rule, audit-pointer rule, and
   documented fallback, including the per-dispatch record requirement.
2. The four role prompt templates: replace the operating-address line with the
   working-directory fact, prohibition, and audit-identifier line; add the fallback block;
   align the fixer template's re-review paragraph.
3. `SKILL.md`: update the §5, §6, and §7 dispatch statements as listed above.
4. `references/orchestrator-checklist.md`: update the implementer line and add the
   fallback-record line.
5. `evals/evals.json`: add eval 19 per Δ ADDED.
6. Verify per the section below.
7. On land: update `docs/roadmap.md` status line + DAG (via `doc-contract update`), archive
   this folder per the repository contract.

## Verify

Reviewer-executable without live dispatch:

- `grep -c 'ABSOLUTE_WORKTREE_PATH' references/implementer-prompt.md
  references/reviewer-prompt.md references/fixer-prompt.md
  references/pre-implementation-review-prompt.md` — exactly one occurrence per file, each
  on the audit-identifier line (never the line stating the working directory).
- Each of the four templates contains a no-`cd` prohibition, a worktree-relative-paths
  requirement, and the POSIX-only fallback block; `grep -n "already at the item worktree"
  references/*-prompt.md` finds all four.
- `references/worktree-lifecycle.md` contains the `## Delegated working directory` section
  and its opening sentence no longer says delegated agents "receive an absolute worktree
  path" as their operating address; the no-branch/no-integration/no-cleanup authority
  clause is still present in that sentence.
- `references/validation-policy.md` and `references/review-record-contract.md` carry no
  hunk owned by this item: `git diff <this item's begin commit> --
  references/validation-policy.md references/review-record-contract.md` is empty. The
  sibling `review-record-tooling` landed before this item began, so both files are clean at
  the begin commit and any hunk here would belong to this item.
- `python3 -m json.tool evals/evals.json >/dev/null`; the new eval's assertions match
  Δ ADDED; evals 9 and 14 are textually unchanged and remain satisfied by the new wording.
  A behavioural *pass* needs a model run and is not claimed here; the file holds 18 evals,
  so 19 is the next free id.
- `doc-contract check --repo-root . --offline` and `doc-contract check --repo-root .`
  report 0 errors and no new warnings; `git diff --check` clean.

Requires live dispatch (operator-gated evidence, recorded per the live-verification modes
in `references/validation-policy.md` — do not claim these from desk-checking):

- On a harness with per-child cwd: a dispatched child's first command is worktree-relative
  (no leading absolute `cd`), and its recorded working directory equals the item worktree
  root. Success criterion for the original problem: zero first-command absolute `cd`
  occurrences across a multi-child session.
- On the previously affected lane (the one carrying the Windows-host harness prior):
  zero mount-path rewrites (`C:\workspace\...` / `C:/workspace/...` forms) of the worktree
  path, measured over the same run count that previously showed 6/9 failures.
- On a harness without per-child cwd: the fallback fires explicitly, `pwd` is the child's
  first command, and the fallback usage is recorded and reported.
