# Orchestration

Choose an execution mode after the tier is set.

## Modes

| Mode | Use when |
| --- | --- |
| **solo** | Narrow scope; lead can finish without isolation; tier S/M |
| **single-worker** | Isolated implement or explore; keep lead context small |
| **fan-out** | Parallel independent subtasks (e.g. explore + implement paths that do not share writes) |

## Fan-out pattern

1. Split into workers with **non-overlapping write sets** when possible.
2. Each worker gets a **self-contained** prompt (goal, constraints, files, done definition).
3. Run a **verify** step on the merged result with tier ≥ worker tier, or rely on automated checks (tests, lint, typecheck).

## Lead vs workers

- Lead may stay on a cheaper tier when it only classifies and merges.
- Workers run at the planned tier for their slice.
- Verifier should not be weaker than the implementer for judgment-heavy work.

## Parallelism rules

- Parallelize read-only explore freely.
- Do not parallelize two writers on the same file without a merge plan.
- Cap fan-out: prefer 2–4 workers unless the host documents higher limits.
- Under `optimize_for: cost`, use single-worker instead of fan-out: every worker re-reads context.

## When a worker does not pay off

A worker re-reads the whole context. With `--session-tier`, `classify.py` keeps the task `solo` on the session model when the pick is below it but the work is short: no high breadth, no long horizon and a gap of one tier only. Workers stay for broad or long work, for a gap of two tiers or more, and for isolation (explore, verify). The plan says why in `mode_reason`.

## Plan / execute split

For ambiguous L/XL work under `optimize_for: cost` or `balanced`:

1. Short **plan** at L (or XL if security/architecture).
2. **Execute** at M or L once the plan is concrete.

Under `optimize_for: quality`, plan and execute may stay at the higher tier.
