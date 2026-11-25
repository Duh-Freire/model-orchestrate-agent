# Capability tiers

Abstract tiers only. Host adapters map these to concrete models and effort.

## Matrix

| Tier | Capability | Effort | When |
| --- | --- | --- | --- |
| **S** | Fast / cheap coder | `low` | Rename, typo, local Q&A, one obvious file |
| **M** | Balanced coder | `medium` | Local bug, CRUD, tests, small refactor |
| **L** | Strong coder | `high` | Multi-file, API design, races, moderate ambiguity |
| **XL** | Frontier + deep reason | `max` | Security, architecture, long-horizon, adversarial review |

## `optimize_for` bias

Default: `balanced`.

| Mode | Bias |
| --- | --- |
| `cost` | Prefer the lower tier when borderline; solo over fan-out; skip XL unless risk is high |
| `balanced` | Lowest tier that still meets the bar |
| `quality` | When borderline, pick the higher tier; prefer verify gate on L/XL work |

## Borderline rules

- Ambiguous **and** high risk → at least **L**, consider **XL**
- Clear mechanical edit across many files → **M** (breadth alone is not XL)
- Security or irreversible data → floor **L**, usually **XL**
- UI taste with brand constraints → at least **L**

## Effort labels

Portable effort vocabulary (one per tier, linear): `low` | `medium` | `high` | `max`.

If a host exposes a different scale, map at the adapter: `max` → strongest available; `low` → weakest / fast.
