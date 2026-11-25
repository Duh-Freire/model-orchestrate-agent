---
name: model-orchestrate-agent
description: >-
  Recommends the cheapest sufficient model and effort for each coding task in
  the host app's own terms (Claude, Codex, Cursor, Copilot, OpenCode) and warns
  when the project grows. After the user approves, it applies the choice
  automatically (subagent or new session) wherever the host allows. Use
  proactively at the start of every new coding task (feature, bug, refactor,
  review, migration), when scope or project structure changes, or when the user
  asks which model or effort to use, how to save tokens, or whether to delegate
  to subagents. Also for Portuguese requests such as qual modelo usar, nível de
  esforço, economizar tokens or delegar para subagentes.
license: MIT
metadata:
  author: duphl-wq
  version: "0.7.0"
  tags: routing orchestration model effort cost tokens subagents
---

# Model orchestrate agent

Recommend the lowest tier that still delivers, in the current app's models; the user validates, then the switch is automatic.

- **Run:** every new coding task or scope change · first task in a project and after it grows · questions about model, effort or tokens.
- **Skip:** follow-ups inside the same task · model and effort locked by the user · chat with no coding.
- **Task boundary:** a new deliverable asked by the user is a new task; classify it, but show the card only when `decision` is `ask` (see [decision-card](assets/decision-card.md)). Corrections, "continue", questions and fixes of the task just done are the same task. A batch of related requests in a row ("do A", "now B") is classified once per request and costs one line each when the tier does not change.

## Protocol

0. **Preferences:** with `--project`, `classify.py` reads `.model-orchestrate.prefs.json` (`always_accept`, `never_switch_session`, `optimize_for`) and the explicit `--optimize-for` still wins. Save one only when the user says so (`project-scan.py --set-pref key=value`).
1. **Project check** (first task per session, or after new packages / many new files): profile the repo, compare with the saved baseline, collect **alerts**.
2. **Classify → tier** — score type, breadth, ambiguity, risk, verifiability, horizon ([taxonomy](references/taxonomy.md)); map to S / M / L / XL ([tiers](references/tiers.md)), biased by `optimize_for`: `cost` | `balanced` (default) | `quality`. Obvious tasks: classify in your head, no script.
3. **Mode** — solo | single-worker | fan-out + verify ([orchestration](references/orchestration.md)). A worker re-reads the context: with `--session-tier`, a short task one tier below the session stays `solo` (`mode_reason` says why).
4. **Adapt** — load one `references/adapters/<id>.md`: `claude-code` (Agent tool present) · `claude-ai` (Claude chat, no Agent tool) · `github-copilot` · `codex` · `cursor` · `opencode` · `generic` (see [market-hosts](references/market-hosts.md)).
5. **Recommend** — card + the adapter's **User matrix** (▶ on the pick) + alerts, per [assets/decision-card.md](assets/decision-card.md). Ask only when the choice matters; otherwise one line and continue.
6. **Apply automatically** once the user says yes, following the adapter's **Auto-apply** order: worker on the chosen model/effort → new session with them (if the host has a session tool) → exact manual steps when the host allows nothing else. A solo task on a different tier runs as a single worker.
7. **Escalate** — on quality failure, recommend one tier up; on yes, apply the same way ([escalation](references/escalation.md)).
8. **Calibrate** — when the task ends, offer to log how the tier fared (`ok` | `escalated` | `overkill`); with the user's yes, `project-scan.py --log-outcome type:tier:result`. After 3+ results for the same type and tier, `classify.py --project` moves the tier one step and says so in `calibration`. Security and high-risk tasks are never lowered.

Scripts (stdlib; English + pt-BR keywords; output is a valid [plan](assets/plan.schema.json)):

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/classify.py" --task "..." --project . --session-tier M | python3 "${CLAUDE_SKILL_DIR}/scripts/emit-plan.py" --stdin
python3 "${CLAUDE_SKILL_DIR}/scripts/project-scan.py" . [--save] [--set-pref always_accept=true] [--log-outcome bugfix:M:ok]
```

`--session-tier` is the tier of the model the session is on (Haiku S, Sonnet M, Opus L, Fable XL as a guide): it makes the plan carry `decision` = `inline` | `ask` | `auto`. `--project` adds the repo profile, preferences and alerts (read-only); `--save` records the growth baseline (`.model-orchestrate.json`) only after the user agrees. `--adapter` defaults to `auto`. Claude chat: run from this skill's folder as `scripts/...`. Windows: `python`.

## If only this file is available

Some Claude surfaces sync only `SKILL.md` (no `references/`, `scripts/`). Then classify in your head and use:

- **Matrix (Claude):** S Haiku · low · M Sonnet · medium · L Sonnet, or Opus if judgment-heavy · high · XL Opus for security, Fable for long or ambiguous work · max. Other apps: their fast / default / strong / frontier models.
- **Auto-apply:** `Agent` tool present → on yes, `Agent(model=<alias>, effort=<level>)` with a self-contained prompt; no such tool → give the manual steps (model menu / `/model` + `/effort`).

## Hard rules

- **The user validates, then it is automatic:** never switch model, change effort or spawn a worker on another tier before their yes; after it, apply without further steps. If the user says "always accept", auto-apply for the rest of the session but still ask before any tier above the current model.
- **Never switch this session's own model** (a deliberate choice, no opt-in: it discards the cache and the desktop app refuses it): hosts refuse it and it breaks the cache. Use a worker or a new session; if the user insists, give the manual steps.
- **Only this app's options:** show the loaded adapter's models and effort labels; never mix vendors.
- **Switch only at task boundaries:** new session, `/clear`, or a subagent spawn. Mid-thread switches invalidate the prompt cache and re-read the whole context.
- Model names live in adapters (plus the Claude fallback above); never invent ids.
- Never claim the parent session model changed unless the adapter documents a supported mechanism.
- Escalate one tier, once; no S → XL jump without new risk evidence. XL is the top: re-plan or ask.
- Effort is linear, one level per tier: `low` (S) · `medium` (M) · `high` (L) · `max` (XL).
