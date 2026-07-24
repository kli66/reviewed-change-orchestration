# Model routing

Choose capability tiers against models the host actually exposes. Optimize total cost, including retries and extra turns, rather than token price alone.

| Work | Capability tier |
|---|---|
| Complete specification, mechanical edit, roughly one or two files | Economical implementer |
| Multi-file integration, debugging, or prose-heavy requirements | Standard implementer |
| Architecture, security, concurrency, migrations, or broad judgment | Strongest suitable implementer |
| Initial review | At least the judgment tier warranted by diff size and risk |
| Scoped re-review of explicit fixes | Economical or standard when the risk is narrow |

Map these tiers to named models available in the current host; do not bake versioned model IDs into this skill.

Increase capability after two materially unsuccessful fix attempts, when a dispatched agent reports that the task exceeds its reasoning capacity, or when newly discovered risk moves the task into a higher tier. Change the context or task framing as well when missing information caused the failure. Repeating an unchanged cheap dispatch usually costs more.

Keep reviewer independence more important than uniform model choice. A small reviewer can validate a mechanical diff; a subtle security or concurrency diff needs strong judgment even when its line count is small.
