---
persistence: living
---
# Research: Agent Skill/Task Scheduling & Orchestration — Canonicalization, State Consumption, Persistence, Parallel Merge-Back


Date: 2026-09-17 (research run). Primary sources only (official docs, repo source, specs, first-party APIs); unverifiable claims are flagged explicitly. Also written to the configured output path.

**Context mapping:** (a) structural identity vs text-normalization → §1; (b) machine-readable lifecycle state for downstream agents → §2; (c) SQLite vs multi-file state → §3; (d) parallel merge-back with priority → §4; adoptable projects → §5.

---

## 1. Document Canonicalization / Identity ("doorstop style")

### 1.1 Agent-skills front matter: a discovery contract, never an identity contract

- **anthropics/skills** defines a skill as "a folder with a `SKILL.md` file containing YAML frontmatter and instructions"; required fields are `name` (lowercase-hyphen) and `description`; `compatibility` optional. Many skills Apache 2.0; bundled docx/pdf/pptx/xlsx skills "source-available, not open source." [README.md](https://github.com/anthropics/skills/blob/HEAD/README.md); [skill-creator/SKILL.md](https://github.com/anthropics/skills/blob/1ed29a03dc852d30fa6ef2ca53a67dc2c2c2c563/skills/skill-creator/SKILL.md)
- The **Agent Skills open standard** (agentskills.io) fully specifies `SKILL.md` front matter: `name` (required, 1–64 chars, lowercase-alphanumeric+hyphens, must match directory name), `description` (required, ≤1024 chars), `license`, `compatibility`, `metadata` (string map), `allowed-tools` (experimental). It specifies **no hashing, signing, or canonicalization** of front matter or body. [specification.mdx](https://raw.githubusercontent.com/agentskills/agentskills/refs/heads/main/docs/specification.mdx)
- **Claude Code** uses front matter for load/trigger behavior ("the `description` helps Claude decide when to load the skill automatically"; `allowed-tools` goes through the normal permission flow). No identity hash. [custom-skills](https://code.claude.com/docs/en/custom-skills); [skills.md](https://code.claude.com/docs/en/skills.md)

**Finding:** front-matter-vs-body canonicalization is essentially unaddressed in the skills ecosystem. Our doc-contracts `self_hash` has no analogue there — the real precedents are Doorstop and git.

### 1.2 tasks.md / tasks.json

- **tasksmd/tasks.md** (TASKS.md spec v1.0, MIT): `## P0`–`## P3` priority headings, `- [ ]` checkbox tasks, bold-label metadata (`ID`, `Tags`, `Details`, `Files`, `Acceptance`, `Plan`, `Blocked by`, `Blocked`, `Parent`), `<!-- policy: -->` comments. Deliberately "not machine-strict": "LLMs read Markdown natively, so the format doesn't need to be machine-strict." **No hashing — git is the audit trail**; deterministic discovery via lexicographic path sort. [spec.md](https://github.com/tasksmd/tasks.md/blob/main/spec.md); [LICENSE](https://raw.githubusercontent.com/tasksmd/tasks.md/main/LICENSE)
- **Task Master** (eyaltoledano/claude-task-master): canonical store is `tasks.json` (`id`, `title`, `description`, `status`∈pending/done/deferred, `dependencies`, `priority`, `details`, `testStrategy`, `subtasks`, `metadata`); per-task files use `# Task ID:`/`# Title:`/`# Status:` comment headers — **not YAML front matter**. [task-structure.md](https://github.com/eyaltoledano/claude-task-master/blob/main/docs/task-structure.md); [docs](https://docs.task-master.dev/capabilities/task-structure)
- **Flagged unverified:** the prompt's "taskmaster-ai … hashing" claim — no content hashing of tasks is documented anywhere in Task Master's primary docs/source I read.

### 1.3 Spec-driven development repos

- **github/spec-kit**: SDD phases (constitution → specify → plan → tasks → implement → converge); artifacts are Markdown — bug reports "live in `.specify/bugs/login-crash/`"; verdicts are strings (`verified`/`partial`/`failed`). No content hashing documented. [README](https://github.com/github/spec-kit/); [Agentic SDD](https://github.github.io/spec-kit/reference/agentic-sdd.html)
- **spec-kit-canon**: "canon-driven (baseline-driven)" behavior — canonicalization as *authoritative Markdown content*, not hashing. [repo](https://github.com/maximiliamus/spec-kit-canon)
- **OpenAI Symphony** (Apache 2.0): "Symphony is technically just a `SPEC.md` file — a definition of the problem and the intended solution … giving agents high-level steering." [announcement](https://openai.com/index/open-source-codex-orchestration-symphony/); [repo README](https://github.com/openai/symphony)
- **OpenAI PLANS.md** cookbook: living design documents to steer long Codex tasks. [cookbook](https://developers.openai.com/cookbook/articles/codex_exec_plans)

### 1.4 Structural / semantic identity: what projects actually hash

- **Doorstop** — the namesake "doorstop style": items are YAML files; `item.stamp()` hashes "the item's key content" = `[uid, text, ref, references, links, extended_reviewed attributes]` — **semantic parsed fields, not raw bytes**. The `reviewed:` attribute stores the fingerprint at last review; drift = comparing current stamp vs stored stamp; links carry parent fingerprints so child items go "suspect" when a parent changes. LGPL-3.0-only (SPDX in source). [v2.2 item reference](https://doorstop.readthedocs.io/en/v2.2/reference/item/); [v1.5 items doc](https://doorstop.readthedocs.io/en/v1.5/reference/items/); [stamp() in item.py](https://github.com/doorstop-dev/doorstop/blob/develop/doorstop/core/item.py)
- **RFC 8785 JCS** — the standard for structural identity of parsed objects: canonical serialization (sorted keys by Unicode code point, IEEE-754 doubles, normalized escapes) so "cryptographic operations performed on the canonicalized counterpart … generate consistent results." This is the parse→canonical-bytes→hash approach — a direct answer to (a) for rco's canonical-JSON envelopes and for canonicalizing parsed YAML front matter. [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html)
- **Git object hashing** — byte-exact baseline: `hash-object` hashes `"blob " + size + "\0" + content` (type+size header + content → SHA-1); no normalization, so whitespace-only edits change identity. [Git Internals — Git Objects](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects)
- **OpenClaw** hashes memory-index sources: `memory_index_sources(path, source, hash, mtime)`. [openclaw-agent-schema.sql](https://github.com/openclaw/openclaw/blob/8d535fb0/src/state/openclaw-agent-schema.sql)
- **LangGraph checkpoints** use pointer identity (UUID-ish `checkpoint_id` + `ts`), state as opaque msgpack — no content hash. [checkpoint-sqlite source](https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-sqlite/langgraph/checkpoint/sqlite/__init__.py)

**§1 bottom line:** no agent-skill project hashes front matter/body for drift detection. The two mature content-identity patterns are Doorstop's semantic-field stamp (parsed fields, stored-review comparison) and RFC 8785 JCS (canonical serialization of parsed objects) — both directly borrowable. Structural identity over parsed fields is strictly more robust than text-normalization heuristics, and Doorstop is the working precedent.

---

## 2. Downstream Implementation-Agent Consumption (JSON/API vs Markdown)

- **LangGraph**: typed `State` (TypedDict + reducers) exposed programmatically via `graph.get_state(config)` keyed by `thread_id` — fully machine-readable. [Checkpointers docs](https://docs.langchain.com/oss/python/langgraph/checkpointers); [state.py](https://github.com/langchain-ai/langgraph/blob/d27d4b2d9895a4aa83170b4aaa135878f99c7fd6/libs/langgraph/langgraph/graph/state.py)
- **CrewAI**: `Task` is a Pydantic model (description, expected_output, agent, async_execution, callback, output_file); `TaskOutput` supports multiple formats incl. JSON; outputs persist to SQLite as JSON columns. [tasks docs](https://docs.crewai.com/edge/en/concepts/tasks); [storage source](https://github.com/crewAIInc/crewAI/blob/e21c5062/lib/crewai/src/crewai/memory/storage/kickoff_task_outputs_storage.py)
- **AG2**: `KnowledgeStore` Protocol (read/write/list/append/read_range/exists/on_change) with Memory/Sqlite/Disk/Redis/Locked backends; `EventLogWriter` → JSONL; `DefaultBootstrap` writes a `SKILL.md` explaining each store directory "to an LLM reader." [Knowledge Store docs](https://docs.ag2.ai/docs/user-guide/advanced/knowledge_store/)
- **OpenHands SDK**: append-only typed (Pydantic) event log = "the agent's memory and the integration point for auxiliary services"; conversation state saved/restored (messages, agent config, execution status). [event_store.py](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/conversation/event_store.py); [convo-persistence](https://docs.openhands.dev/sdk/guides/convo-persistence)
- **SWE-agent**: per-instance `.traj` JSON files with `(thought, action, observation)` turns + `state` (working_dir, open_file). [trajectories docs](https://swe-agent.com/latest/usage/trajectories/)
- **Claude Code hooks**: every event (PreToolUse, PostToolUse, Stop, SessionStart…) delivers JSON on stdin with `session_id`, `transcript_path`, `cwd`, `hook_event_name`, plus `agent_id`/`agent_type` inside subagents and `last_assistant_message` on Stop/SubagentStop. [hooks.md](https://code.claude.com/docs/en/hooks.md)
- **GitHub Copilot coding agent (cloud agent)**: first-party **REST task API** — `POST /agents/repos/{owner}/{repo}/tasks` plus list/status; works in an ephemeral GitHub Actions environment; lands changes on a branch/PR. [use-cloud-agent-via-the-api](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-via-the-api); [about-cloud-agent](https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent)
- **Copilot CLI**: dual-format — full session files in `~/.copilot/session-state/` **plus** a structured subset in "a local SQLite database, referred to as the session store," optionally synced to GitHub. [chronicle](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/chronicle)
- **Taskwarrior**: interchange via JSON — `task export` emits one JSON object per line (all fields optional, `status`∈P/C/D/R); hooks receive JSON on stdin. [task RFC](https://github.com/GothenburgBitFactory/taskwarrior/blob/develop/doc/devel/rfcs/task.md); [export](https://taskwarrior.org/docs/commands/export/); [hooks](https://taskwarrior.org/docs/hooks/)
- **tasks.md**: the opposite pole — Markdown-first by design (see §1.2). [spec.md](https://github.com/tasksmd/tasks.md/blob/main/spec.md)
- **VS Code agents**: file-based memory scopes (user/repo/session); Plan agent persists plans to `plan.md`. [Memory in VS Code agents](https://code.visualstudio.com/docs/agents/run/memory)
- **Symphony**: issue tracker (Linear) is the control plane; agents pull open, unblocked tasks; "objectives instead of strict transitions." [announcement](https://openai.com/index/open-source-codex-orchestration-symphony/)

**§2 bottom line for (b):** ecosystem splits into fully-structured consumers (LangGraph/CrewAI/AG2/SWE-agent/Copilot REST API) vs deliberately Markdown-first consumers (tasks.md, PLANS.md, VS Code memory). No project ships both a human-Markdown lifecycle artifact **and** a machine-readable projection — except Copilot CLI's files+SQLite-subset model, which is the strongest precedent for exposing rco/doc-contract lifecycle state to implementing agents.

---

## 3. Task Status & Content Persistence (SQLite vs file)

### 3.1 SQLite: schemas and concurrency

- **LangGraph checkpoint-sqlite** (MIT): `checkpoints(thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id, type, checkpoint BLOB, metadata BLOB, PK(thread_id,ns,id))` + `writes(...)`; `PRAGMA journal_mode=WAL`; `threading.Lock`; sync saver documented as "does not scale to multiple threads" (async variant on aiosqlite); msgpack strict-mode serde against untrusted DBs. [source](https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-sqlite/langgraph/checkpoint/sqlite/__init__.py); [README](https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-sqlite/README.md). Postgres saver for "durable, long-running workflows." [checkpoint-postgres README](https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-postgres/README.md)
- **CrewAI** (MIT): `latest_kickoff_task_outputs(task_id TEXT PK, task_key, expected_output, output JSON, task_index, inputs JSON, was_replayed BOOLEAN, timestamp)`; WAL; every write under `store_lock(...)` named lock with `connect(timeout=30)`; `INSERT OR REPLACE`. `SQLiteFlowPersistence` adds `flow_states` + `pending_feedback` tables. [kickoff storage source](https://github.com/crewAIInc/crewAI/blob/e21c5062/lib/crewai/src/crewai/memory/storage/kickoff_task_outputs_storage.py); [flow sqlite.py](https://github.com/crewAIInc/crewAI/blob/c0fa66d1/lib/crewai/src/crewai/flow/persistence/sqlite.py)
- **Taskwarrior 3 / TaskChampion** (MIT project): text `.data` files → `taskchampion.sqlite3`; brand-new sync with a server model (cloud backends aws/gcp/local, encrypted, snapshots, undo) — SQLite locally + sync server for cross-machine. [upgrade-3](https://taskwarrior.org/docs/upgrade-3/); [taskchampion repo](https://github.com/GothenburgBitFactory/taskchampion); [PR #3094](https://github.com/GothenburgBitFactory/taskwarrior/pull/3094)
- **OpenClaw** (license not verified): two-level SQLite (global `openclaw.sqlite` + per-agent DB); `schema_meta(schema_version, app_version, …)`; "Schema migrations run forward when a database opens. Older OpenClaw builds refuse databases written by a newer schema." Cold transcripts as `<sha256>.jsonl.zst`. [layout docs](https://docs.openclaw.ai/reference/database-schemas/layout); [schema source](https://github.com/openclaw/openclaw/blob/8d535fb0/src/state/openclaw-agent-schema.sql)
- **AG2**: `SqliteKnowledgeStore` = "single-process durability on disk — the pragmatic default"; Redis for "multi-process or cross-host"; `LockedKnowledgeStore` "wraps another store to serialize concurrent writers"; WAL-style `append`/`read_range` byte offsets. [docs](https://docs.ag2.ai/docs/user-guide/advanced/knowledge_store/)
- **task-master SQLite backend (PR #1619)** — the clearest documented SQLite-vs-file tradeoff in agent-task tooling: "SQLite as local working database … JSONL as git-synced export format (line-based diffs); Self-healing: rebuild SQLite from JSONL on startup." WAL, migration runner, atomic writes (temp+rename), DB files gitignored while `tasks.jsonl` is tracked. [PR #1619](https://github.com/eyaltoledano/claude-task-master/pull/1619)

### 3.2 File-based state (the fragility baseline)

- **Claude Code `~/.claude`**: plaintext JSONL transcripts, `file-history/<session>/` snapshots for checkpoint restore ("Holds snapshots for the 100 most recent checkpoints"), `sessions/` files "used to detect concurrent sessions and crashes," auto memory, `agent-memory/`, `~/.claude.json` with rotating backups; no encryption at rest; 30-day sweep. [claude-directory](https://code.claude.com/docs/en/claude-directory); [sessions](https://code.claude.com/docs/en/sessions)
- **OpenHands SDK**: file-based event log with locking "for thread-safe and process-safe event storage"; explicitly warns "file locking via flock() does NOT work reliably on NFS mounts or network filesystems." [event_store.py](https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/conversation/event_store.py)
- **SWE-agent**: plain `.json` trajectory files, no DB. [trajectories docs](https://swe-agent.com/latest/usage/trajectories/)
- **Copilot CLI**: full-fidelity files + SQLite subset (hybrid). [chronicle](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/chronicle)

**§3 bottom line for (c):** SQLite is the dominant local store, always with WAL + in-process lock (LangGraph, CrewAI) or a wrapper (AG2 `LockedKnowledgeStore`); cross-machine = sync server (TaskChampion) or non-SQLite backend (Redis). Multi-process writers on one SQLite file are uniformly avoided. The recurring best-practice shape for git-centric agent state is task-master PR #1619's **SQLite + JSONL dual-store with rebuild-from-JSONL self-healing** — directly applicable to rco.

---

## 4. Parallel Multi-Agent Merge-Back & Priority

- **Claude Code worktrees** (first-party): `claude --worktree <name>` → isolated worktree under `.claude/worktrees/<name>/` on `worktree-<name>`; while isolated, Claude Code blocks edits/wd-changes/git-redirects targeting the main checkout (four checks, enforced for spawned subagents); worktrees are locked, stale locks swept later; exit prompts keep/remove; resume re-enters the worktree. `/batch` "splits one large change into 5 to 30 worktree-isolated subagents that each open a pull request." Agent teams are **not** worktree-isolated — "partition the work so each teammate owns a different set of files." [worktrees](https://code.claude.com/docs/en/worktrees); [agents](https://code.claude.com/docs/en/agents)
- **GitHub merge queue** (first-party): "pull requests … are merged in a first-in-first-out order where the required checks are always satisfied." Temporary integration branches (`gh-readonly-queue/{base_branch}` for third-party CI; `merge_group` events for Actions), grouping, `Build concurrency` (1–100), `Merge limits` (min/max batch + wait timeout), `Only merge non-failing` toggle. **No priority ordering** — vendor FAQ (secondary) confirms FIFO-only; Mergify adds priority rules. [Managing a merge queue](https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue); [Mergify FAQ (vendor, flagged)](https://articles.mergify.com/github-pull-request-merge-queue-faq/)
- **Symphony** (Apache 2.0): "Agents only start working on tasks that aren't blocked, so execution unfolds naturally and optimally in parallel for this DAG"; orchestrator "watches CI, rebases when needed, resolves conflicts, retries flaky checks." Priority = unblockedness (dependency order). [announcement](https://openai.com/index/open-source-codex-orchestration-symphony/)
- **Task Master** `next`: deterministic selection order — "Prioritizes tasks by priority level, dependency count, and task ID." [task-structure docs](https://docs.task-master.dev/capabilities/task-structure)
- **LangGraph**: Pregel-style super-steps; `Send` API for map-reduce fan-out; reducers merge parallel writes — parallelism inside one run, not N repo merges. [use-graph-api](https://docs.langchain.com/oss/python/langgraph/use-graph-api); [state.py](https://github.com/langchain-ai/langgraph/blob/d27d4b2d9895a4aa83170b4aaa135878f99c7fd6/libs/langgraph/langgraph/graph/state.py)
- **CrewAI**: sequential vs hierarchical (manager agent) processes; per-task `async_execution`. [processes docs](https://docs.crewai.com/edge/en/concepts/processes)
- **AG2 / AutoGen**: `GroupChat` + `GroupChatManager` (manager selects next speaker, broadcasts); classic framework is now AG2 Classic. [GroupChat docs](https://docs.ag2.ai/latest/docs/user-guide/advanced-concepts/groupchat/groupchat/); [AG2 repo](https://github.com/ag2ai/ag2)
- **Conflict prediction via file overlap** (concrete tools, primary repos):
  - **mergesage** (MIT — verified via GitHub license API): predicts conflicting branches before merge using `git merge-tree` simulation, read-only. [repo](https://github.com/jay-tank/mergesage); [LICENSE](https://raw.githubusercontent.com/jay-tank/mergesage/main/LICENSE)
  - **git-overlap**: detects files edited in your branch that are also edited in open PRs/remote branches. **No license file (GitHub API 404)** — pattern only. [repo](https://github.com/marcoganassin96/git-overlap)
  - **grove** (license not verified): "cross-worktree conflict intelligence … file, hunk, symbol, dependency, and schema overlaps." [repo](https://github.com/NathanDrake2406/grove/)
  - **claude-pre-merge-conflict-predictor**: Claude Code skill comparing branch vs open PRs on the same base. [repo](https://github.com/ritesh31/claude-pre-merge-conflict-predictor)

**§4 bottom line for (d):** the industry pattern is isolation-first + serialized integration: per-agent worktrees (Claude Code), FIFO merge queue with batched temporary integration branches (GitHub), blocked-by dependency ordering for parallelism (Symphony, tasks.md, Task Master). Explicit priority-sorting of *concurrent merge attempts* has no first-party precedent beyond FIFO+batching; deterministic *selection* priority exists (Task Master). Pre-merge conflict prediction via file-overlap / `git merge-tree` is an active micro-tool niche mapping directly onto rco's merge-ordering problem.

---

## 5. Borrow / Adopt Candidates

| Project | Area | License | Verdict |
|---|---|---|---|
| [doorstop-dev/doorstop](https://github.com/doorstop-dev/doorstop) | 1 canonicalization | LGPL-3.0-only (SPDX in source) | **Borrow concept wholesale**: semantic-field stamp + stored-review hash = the exact pattern doc-contracts generalizes; reimplement, don't vendor LGPL. |
| [RFC 8785 JCS](https://www.rfc-editor.org/rfc/rfc8785.html) | 1 canonicalization | IETF standard | **Adopt wholesale**: canonical-JSON identity for rco and canonicalized parsed front matter. |
| [github/spec-kit](https://github.com/github/spec-kit) | 1 spec-driven process | Not verified this run | Borrow `.specify/<slug>/` artifact layout + verdict states; not adoptable (Python 3.11+/uv/agent integrations). |
| [tasksmd/tasks.md](https://github.com/tasksmd/tasks.md) | 2 consumption | MIT | **Adopt wholesale** as the Markdown lifecycle surface (P0–P3, Blocked by, Files, Acceptance), paired with a JSON projection. |
| [Copilot CLI chronicle model](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/chronicle) | 2+3 consumption/persistence | Proprietary (pattern) | **Borrow the dual-format pattern**: full-fidelity files + SQLite query subset. |
| [Taskwarrior JSON RFC](https://github.com/GothenburgBitFactory/taskwarrior/blob/develop/doc/devel/rfcs/task.md) | 2 consumption | MIT project | **Adopt the interchange shape**: JSONL, one object/line, all-optional fields. |
| [task-master PR #1619](https://github.com/eyaltoledano/claude-task-master/pull/1619) | 3 persistence | Not verified this run | **Adopt the architecture wholesale** for (c): SQLite working store + git-friendly JSONL + rebuild self-healing. |
| [langgraph checkpoint-sqlite](https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-sqlite/langgraph/checkpoint/sqlite/__init__.py) | 3 persistence | MIT | **Borrow schema + WAL/lock discipline** (thread/checkpoint/parent chain, writes table); too heavy to adopt. |
| [AG2 KnowledgeStore](https://docs.ag2.ai/docs/user-guide/advanced/knowledge_store/) | 3 persistence | Apache-2.0 (per repo; verify LICENSE) | **Borrow the Protocol + LockedKnowledgeStore** backend-swap idea. |
| [CrewAI storage](https://github.com/crewAIInc/crewAI/blob/e21c5062/lib/crewai/src/crewai/memory/storage/kickoff_task_outputs_storage.py) | 3 persistence | MIT (per repo; verify) | **Borrow JSON-column task-output table** (INSERT OR REPLACE, replay flag). |
| [GothenburgBitFactory/taskchampion](https://github.com/GothenburgBitFactory/taskchampion) | 3 persistence | MIT project (LICENSE present; content not fetched) | **Borrow replica+sync model** if cross-machine ever needed; overkill for offline stdlib-only. |
| [openclaw/openclaw](https://docs.openclaw.ai/reference/database-schemas/layout) | 3 persistence | Not verified this run | **Borrow versioned `schema_meta` migrations** (forward-only, refuse-newer-DB). |
| [Claude Code worktrees](https://code.claude.com/docs/en/worktrees) | 4 merge-back | Proprietary (pattern) | **Adopt the pattern**: locks, stale-sweep, main-checkout guardrails on top of rco's existing worktrees. |
| [GitHub merge queue](https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue) | 4 merge-back | Proprietary (semantics) | **Adopt semantics**: FIFO + batch grouping + rebase-onto-latest-queued integration branches. |
| [openai/symphony](https://github.com/openai/symphony) | 4 merge-back | Apache 2.0 | **Borrow blocked-by DAG scheduling philosophy** (unblocked-pull parallelism, CI shepherding); Elixir impl not adoptable. |
| [jay-tank/mergesage](https://github.com/jay-tank/mergesage) | 4 conflict prediction | MIT (verified via GitHub API) | **Adopt approach wholesale**: read-only `git merge-tree` simulation is core-git, fits stdlib-only/offline. |
| [marcoganassin96/git-overlap](https://github.com/marcoganassin96/git-overlap) | 4 conflict prediction | None (404 via GitHub API) | Borrow pattern only; blocked from adoption by missing license. |

---

## Summary Table of Borrowable Candidates

| Project | Area | License | Verdict |
|---|---|---|---|
| doorstop-dev/doorstop | 1 | LGPL-3.0-only | Borrow concept (semantic stamp + review hash) |
| RFC 8785 JCS | 1 | IETF standard | Adopt wholesale (canonical-JSON identity) |
| tasksmd/tasks.md | 2 | MIT | Adopt wholesale (Markdown task surface) |
| Copilot CLI chronicle | 2+3 | Proprietary pattern | Borrow dual-format (files + SQLite subset) |
| Taskwarrior JSON RFC | 2 | MIT | Adopt JSONL interchange shape |
| task-master PR #1619 | 3 | Unverified | Adopt SQLite+JSONL+rebuild architecture |
| langgraph checkpoint-sqlite | 3 | MIT | Borrow schema + WAL/lock discipline |
| AG2 KnowledgeStore | 3 | Apache-2.0 (unverified) | Borrow Protocol + Locked wrapper |
| CrewAI storage | 3 | MIT (unverified) | Borrow JSON-column task-output table |
| taskchampion | 3 | MIT (unverified) | Borrow replica+sync model (optional) |
| OpenClaw schema_meta | 3 | Unverified | Borrow versioned-migration discipline |
| Claude Code worktrees | 4 | Proprietary pattern | Adopt pattern (locks, guards, cleanup) |
| GitHub merge queue | 4 | Proprietary semantics | Adopt FIFO + batches + integration branches |
| openai/symphony | 4 | Apache 2.0 | Borrow blocked-by DAG scheduling philosophy |
| mergesage | 4 | MIT | Adopt `git merge-tree` read-only prediction |
| git-overlap | 4 | None (404) | Borrow pattern only |

---

## Gaps / Unverified Claims

1. **No hashing in agent-skills front matter** — confirmed absence per docs (anthropics/skills, agentskills.io spec, Claude Code skills); deep source audit of each CLI's skill loader was out of scope.
2. **"taskmaster-ai hashing"** from the prompt could not be verified — Task Master documents tasks.json + task files with status/priority, no content hash.
3. **Multi-process SQLite concurrency**: no first-party project claims safe multi-process writes to one agent-state SQLite file; documented answers are single-process+WAL (LangGraph "does not scale to multiple threads", CrewAI named lock), Redis (AG2), or Postgres (LangGraph).
4. **Priority-sorted concurrent merges**: no first-party implementation found; GitHub merge queue is explicitly FIFO; Task Master's `next` ordering governs selection, not merging.
5. **Licenses not verified this run** (verify before adoption): spec-kit, task-master, taskchampion LICENSE contents, AG2, crewAI, grove, claude-pre-merge-conflict-predictor, OpenClaw.
6. **Mergify FAQ** is a vendor (secondary) source for "GitHub merge queue is FIFO-only"; the FIFO statement itself is backed by GitHub's first-party docs.
7. Doorstop fingerprint hash algorithm (MD5 vs SHA) is not stated in the primary docs read (examples show 32-hex stamps); the stamp *field composition* is verified from source (`item.py`).
