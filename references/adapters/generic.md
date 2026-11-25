# Adapter: generic

Use when the host is unknown, or for hosts without a dedicated adapter
(JetBrains AI/Junie, Google Antigravity, Gemini CLI, Cline, Windsurf/Devin Desktop, etc.).

## Detect

- No clear Claude / Copilot / Codex / Cursor / OpenCode signals
- Or user named a host that is not in the adapter set

## User matrix

Describe roles; if you know the host's model menu, use its real names and effort labels instead.

| Tier | Model | Effort | Best for | Cost |
| --- | --- | --- | --- | --- |
| S | fastest / cheapest coding model | low reasoning | rename, typo, quick question | $ |
| M | default coding model | medium reasoning | local bug, CRUD, tests | $$ |
| L | strong coding model | high reasoning | multi-file feature, API design, races | $$$ |
| XL | best frontier model available | max reasoning | security, architecture, long-horizon | $$$$ |

## Auto-apply (after the user says yes)

1. **Subagent (automatic, only if exposed):** if the host has a subagent / task tool that accepts a model, run the task there with the chosen model and effort.
2. **Otherwise manual:** say so in the question and give the steps: the host's model selector, ideally in a new chat or session for the new task. Never claim a model switch occurred.

## Orchestration

- Prefer solo for S/M.
- Single-worker / fan-out: separate chats or sessions per worker with self-contained prompts if the product has no Task API.

## Example

```text
Card: Tier M · medium · solo
Matrix row ▶ M: default coding model, medium reasoning
→ "Recommended: tier M. Keep your default model, or pick another row."
```
