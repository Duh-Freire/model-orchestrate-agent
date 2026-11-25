# Adapter: GitHub Copilot

Skills CLI id: `github-copilot`  
Install path (project): `.agents/skills/` (also seen under Copilot skill roots)

## Detect

- Copilot Chat / Agent mode in VS Code, JetBrains, or github.com
- Paths: `~/.copilot/`, `.github/` agent config
- User is in a Copilot agent session rather than Claude/Cursor-specific tools

## User matrix

Show only models from the user's Copilot model picker (catalog depends on the plan) and Copilot's **Thinking Effort** levels:

| Tier | Model | Thinking Effort | Best for | Cost |
| --- | --- | --- | --- | --- |
| S | fast / light model, or Auto | None or Low | rename, typo, quick question | $ |
| M | default coding model, or Auto | Medium | local bug, CRUD, tests | $$ |
| L | stronger reasoning model | High | multi-file feature, API design, races | $$$ |
| XL | top reasoning model on the plan | highest level offered | security, architecture, long-horizon | $$$$ |

Non-reasoning models have no Thinking Effort menu; then the model choice alone sets the tier. Higher effort spends more AI credits.

## Auto-apply (after the user says yes)

1. **Subagent (automatic, only if exposed):** if the agent session has a subagent tool that accepts a model, run the task there on the chosen model.
2. **Otherwise manual** (the model is chosen in the Copilot UI). Say so in the question and give the steps: model picker in the chat input → select the model → `>` next to it → **Thinking Effort**. The level persists per model. For a cloud agent task, pick model and reasoning level in the task form.

## Orchestration

- Prefer **Agent mode** for multi-step work; Ask/Chat for S questions.
- Fan-out: separate agent sessions only when the UI supports isolated tasks; otherwise ordered workers with clear write boundaries.
- Put done-definition and test commands in the worker prompt.

## Example

```text
Card: Tier L · High · solo → user selects a stronger reasoning model at High
→ Implement rate limit + tests in one agent run
→ Recommend XL only if authz edge cases appear
```
