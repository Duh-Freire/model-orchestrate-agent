# Escalation

Recommend more capacity only when evidence says the current tier failed. The user decides; show the failure evidence and the adapter's matrix row for the next tier.

## When to upgrade

- Worker output fails tests/lint for **logic** reasons (not env misconfig)
- Missed requirements after a clear checklist
- Conflicting edits that need stronger synthesis
- Security or data-risk discovered mid-task

## When not to upgrade

- Missing dependency / wrong cwd / flaky network
- User asked for a draft or sketch
- Failure is outside the task scope

## Policy

1. Recommend **exactly one** tier up (S→M, M→L, L→XL).
2. If the user accepts, apply it with the adapter's Auto-apply and retry **once** at the new tier with a prompt that includes the failure evidence.
3. Do not jump S→XL unless new information shows high risk (security, irreversible data).
4. Record the escalation on the decision card.
5. At XL there is no higher tier: re-plan with the failure evidence (smaller slices, more verification) or ask the user.

## Record the outcome

When the task ends, offer one line: "log this as ok / escalated / overkill?". With a yes: `project-scan.py --log-outcome <type>:<tier>:<result>` appends to `.model-orchestrate.outcomes.jsonl`. `escalated` = this policy ran; `overkill` = the tier was clearly more than needed; `ok` = it fit. After 3 results for the same type and tier within the last 5, a majority of `escalated` raises the next pick one tier and a majority of `overkill` lowers it (never for security or high risk). The plan shows `calibration`. Never log without a yes.

## Downgrade

If the task collapses to a mechanical leftover after planning, recommend finishing on a lower tier (save tokens on the tail).
