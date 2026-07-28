# Model routing

Choose capability tiers against models the host actually exposes. Optimize total cost, including retries and extra turns, rather than token price alone.

| Work | Policy tier |
|---|---|
| Complete specification, mechanical edit, roughly one or two files | `economical` |
| Multi-file integration, debugging, or prose-heavy requirements | `standard` |
| Architecture, security, concurrency, migrations, or broad judgment | `strongest` |
| Initial review | At least the judgment tier warranted by diff size and risk |
| Scoped re-review of explicit fixes | `economical` or `standard` when the risk is narrow |

Map tiers to models available in the current host. Do not bake versioned model IDs into this skill.

## Resolve overrides

Look for `.reviewed-change-orchestration.toml` at the target repository root before building the execution map. The file is optional; do not create or modify it unless the user asks. See `routing-config.example.toml` for the supported routing and worktree schema.

Apply routing inputs in this order:

1. Derive the policy tier from the task, diff, and risk.
2. Apply a valid repository config mapping or role override.
3. Apply an explicit user instruction from the current request.
4. Resolve the effective tier to a model and effort level the host actually exposes.

A config override may raise capability. It may request a lower tier, but it cannot silently weaken the policy floor: record the conflict and keep the policy tier. A role-specific `model` or `effort` requires an explicit non-`auto` role tier so its capability can be compared with the floor. An explicit user request to accept the lower tier governs after the orchestrator states the concrete risk. Reviewer independence and risk floors matter more than uniform model choice.

Reject the config before dispatch when TOML is invalid, `schema_version` is not `1`, a tier/role/effort value is unsupported, a worktree root is invalid, or an unknown key could hide a typo. If a configured model is unavailable, select a same-or-higher-tier available model and record the fallback; stop if no adequate model exists.

The optional `[worktree].root` setting is resolved by the lifecycle policy, with `~/worktrees` as the default. Expand `~` using the invoking user's home directory, require an absolute path outside the target repository, and reject inaccessible, repository-local, symlinked, or canonically ambiguous roots before creating a worktree. The lifecycle policy also validates every existing generated-path ancestor and branch identity.

## Record every selection

Before each implementer, initial reviewer, fixer, or re-review dispatch, add a model-selection record to the execution map and include it in the role prompt. Record:

- change item and dispatch role, including fix round when applicable;
- task and risk signals used for classification;
- policy tier;
- config override and explicit user override, including source or `none`;
- effective tier;
- resolved model and effort;
- concise rationale;
- fallback or escalation from the prior selection, including reason or `none`.

Use this compact record shape:

```text
item=<change>; role=<implementer|reviewer|fixer|re_review>; round=<n|none>
signals=<task/diff/risk signals>; policy_tier=<tier>
config_override=<value and path|none>; user_override=<value|none>
effective_tier=<tier>; model=<host model>; effort=<host effort>
rationale=<why>; fallback_or_escalation=<change and reason|none>
```

Update the record before dispatch when the diff or risk changes. Report records in dispatch order at sequence completion. This is orchestration evidence, not a new repository ledger; do not create a tracked record file unless the repository explicitly requires one.

## Escalate deliberately

Increase capability after two materially unsuccessful fix attempts, when an agent reports that the task exceeds its reasoning capacity, or when newly discovered risk raises the policy tier. Change context or task framing when missing information caused the failure. Repeating an unchanged cheap dispatch usually costs more.

A small reviewer can validate a mechanical diff; a subtle security or concurrency diff needs strong judgment even when its line count is small.
