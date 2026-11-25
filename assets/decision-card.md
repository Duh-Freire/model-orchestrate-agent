# Recommendation template

Render in the user's language. Nothing switches until the user answers; after a yes, the switch is automatic.

```markdown
Recommendation: Tier <S|M|L|XL> · <model from adapter> · effort <level> · <solo|single-worker|fan-out>
Why: <one line>
Escalation: if <signal> → <next tier>
Workers: <optional list>
Alerts: <project alerts, one per line; omit when none>
```

Then the **User matrix** from the loaded adapter (only that app's models and effort labels):

- Copy the adapter's table; translate the column headers.
- Mark the recommended row with ▶ and bold it; if the current model sits on another row, tag it "(current)".
- Last line, the decision, naming what "yes" will do (from the adapter's **Auto-apply**):
  "Apply ▶ M now (Sonnet · medium as a subagent)? Yes / another row / keep current / always accept"
  When the host has no auto-apply, say so: "Switch in the model menu (Sonnet · Medium), then reply."

## When to ask

Ask only when the answer changes something:

- the pick is **above** the current model (quality risk), or
- the pick is **below** it on non-trivial work (tier M+ or workers: real savings), or
- the plan spawns workers.

Otherwise, one line and continue, e.g. "Tier S — doing it on the current model." Use the host's question tool when it has one.

`classify.py --session-tier <S|M|L|XL>` applies exactly these rules and returns `decision`:

- `inline`: same tier as the session and no worker (or a tier S task below it): one line, no card, no question.
- `ask`: pick above the session, pick below it on tier M+, or any worker: show the card and wait.
- `auto`: the user chose "always accept"; apply without asking (a pick above the session still returns `ask`).

Pass the session tier whenever it is known (the host shows the current model); without it the script cannot tell, and returns a conservative answer.

## After the answer

- **Yes / another row:** apply it right away with the adapter's Auto-apply order, then report in one line what ran ("Subagent started: Sonnet · medium").
- **Keep current:** continue on the current model; do not ask again for this task.
- **Always accept:** auto-apply later picks this session without asking, except a tier above the current model, which still needs a yes. Offer to keep it for the project: with the user's yes, `project-scan.py --set-pref always_accept=true` writes `.model-orchestrate.prefs.json`, which later sessions read through `classify.py --project`. Same for `never_switch_session` and `optimize_for`. Never write preferences without a yes.
- **End of task:** one line asking to log the outcome (`ok` / `escalated` / `overkill`); with a yes, `project-scan.py --log-outcome type:tier:result` (see [escalation](../references/escalation.md)). A `calibration` in the plan goes on the card: "Tier L instead of M: 3 of 4 'refactor' tasks at M had to go up".
- If the mechanism fails (tool refused, model not offered), say why and give the manual steps; never claim a switch that did not happen.

## Alerts

From `classify.py --project` or `project-scan.py`. Show them once per session, or again when they change. Saving a baseline (`project-scan.py --save`) writes `.model-orchestrate.json` in the repo: only when the user agrees.
