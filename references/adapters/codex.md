# Adapter: OpenAI Codex

Skills CLI id: `codex`  
Install path (project): `.agents/skills/`

## Detect

- Codex CLI, IDE extension, or Codex app
- Paths: `.codex/`, `~/.codex/`; env hints `CODEX_*`
- Skills invoked with `$skill` / `/skills`

## User matrix

Show only models from the user's `/model` picker and Codex reasoning-effort levels. Model lists change by account and build; fill **Model** with the live names.

| Tier | Model | Reasoning effort | Best for | Cost |
| --- | --- | --- | --- | --- |
| S | fastest / mini coding model | `low` (`minimal` if offered) | rename, typo, quick question | $ |
| M | default coding model | `medium` | local bug, CRUD, tests | $$ |
| L | strongest coding model | `high` | multi-file feature, API design, races | $$$ |
| XL | top model on the account | highest level offered | security, architecture, long-horizon | $$$$ |

## Auto-apply (after the user says yes)

1. **Subagent (automatic, only if this build exposes one):** if the session has a sub-agent / task tool that accepts a model and reasoning effort, run the task there with the chosen values.
2. **Otherwise manual** (Codex has no documented way for the agent to switch its own model). Say so in the question and give the steps, at the start of a new thread:
   - `/model` → pick model and effort (Codex sets both in one step).
   - One run: `codex -m <model> -c model_reasoning_effort=<level>`.
   - Default: `model` and `model_reasoning_effort` in `~/.codex/config.toml`.

## Orchestration

- Delegate heavy slices as separate Codex threads/tasks with full prompts (goal, constraints, paths, verify steps).
- Tier changes go into a new thread (cache-friendly boundary); avoid mid-thread model flips.
- Keep the skill in `.agents/skills/model-orchestrate-agent` for repo discovery.

## Example

```text
Card: Tier M · medium · single-worker → user accepts
→ New thread with the default coding model at medium
→ Prompt includes failing test path and acceptance criteria; lead verifies
```
