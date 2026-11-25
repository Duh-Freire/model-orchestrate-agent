# Adapter: Cursor

Skills CLI id: `cursor`  
Install path (project): `.agents/skills/` (global often `~/.cursor/skills/`)

## Detect

- Cursor Agent / Cloud Agent session; env hints `CURSOR_*`
- Task tool that accepts a `model` slug
- Paths: `.cursor/`, `~/.cursor/`

## User matrix

Show only models from the user's Cursor model picker (list live slugs when the environment exposes them):

| Tier | Model | Effort | Best for | Cost |
| --- | --- | --- | --- | --- |
| S | Auto (Optimize For: Cost) or a fast model | non-thinking / `-fast` / `-low` | rename, typo, quick question | $ |
| M | Auto (Balance) or the default coder | default / `-medium` | local bug, CRUD, tests | $$ |
| L | strong thinking model | thinking / `-high` | multi-file feature, API design, races | $$$ |
| XL | frontier thinking model | `-max` or the strongest suffix listed | security, architecture, long-horizon | $$$$ |

Max mode (large context) only when the task truly needs a wide slice of the repo; it is wasteful for small jobs. Map skill `optimize_for` to Auto: `cost`→Cost, `balanced`→Balance, `quality`→the most capable option.

## Auto-apply (after the user says yes)

1. **Subagent (default, automatic):** run the task through the **Task** tool with an explicit `model` slug for the chosen tier (effort lives in the slug suffix). A solo task on a different tier becomes single-worker.
2. **Parent chat model: manual.** The agent cannot change the picker; if the user wants the whole chat on that tier, give the steps: model picker in the chat / agent input, in a new chat for a new task.

## Orchestration

- Default worker `model` to `inherit` only when the parent already matches the tier.
- Explore-type subagents for read-only fan-out; general-purpose for implementation.
- Never claim the skill changed the parent model picker.

## Example

```text
Card: Tier L · high · fan-out → user accepts
→ Task(explore): map call sites (fast model)
→ Task(implement): apply patch (L / -high slug)
→ Lead runs tests; recommend XL only if logic still fails
```
