# Adapter: OpenCode

Skills CLI id: `opencode`  
Install path (project): `.agents/skills/`  
Global often: `~/.config/opencode/skills/`

## Detect

- `opencode` CLI or OpenCode project config
- Paths: `~/.config/opencode/`, `.agents/skills/` without Claude/Cursor-only tools

## User matrix

OpenCode is multi-provider: show only the model ids configured for this project, never invented slugs.

| Tier | Model | Effort | Best for | Cost |
| --- | --- | --- | --- | --- |
| S | smallest / fastest configured model | `low` if the provider exposes it | rename, typo, quick question | $ |
| M | default project coding model | `medium` | local bug, CRUD, tests | $$ |
| L | stronger configured model | `high` | multi-file feature, API design, races | $$$ |
| XL | best frontier model configured | highest level offered | security, architecture, long-horizon | $$$$ |

If the provider has no reasoning/effort setting, the model choice alone sets the tier.

## Auto-apply (after the user says yes)

1. **Subagent (automatic, only if configured):** if the project defines subagents with their own `model`, delegate the task to the one on the chosen tier.
2. **Otherwise manual:** say so in the question and give the steps: pick the configured model at session start (or set `model` in the project config).

## Orchestration

- Run workers as separate OpenCode sessions/tasks with full prompts.
- Keep write paths disjoint for fan-out.
- Use repo skills under `.agents/skills/` so OpenCode discovers this skill natively.

## Example

```text
Card: Tier S · low · solo → user keeps the fast configured model
→ Apply rename + run unit test for that package
```
