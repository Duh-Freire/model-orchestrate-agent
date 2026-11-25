# Adapter: Claude apps (claude.ai, desktop, mobile chat)

Adapter id: `claude-ai`
Install: zip the `model-orchestrate-agent/` folder and upload it in **Customize > Skills**.

## Detect

- Skill was uploaded to Claude, and the session is a chat (not Claude Code)
- Scripts run in the code-execution sandbox; no `Agent` / `Task` tool to spawn workers
- If an `Agent` / `Task` tool **is** available (Claude Code, Cowork), use [claude-code.md](claude-code.md) instead

## User matrix

Show only Claude models and the app's Effort labels. Use names exactly as the user's model menu lists them.

| Tier | Model | Effort | Best for | Cost |
| --- | --- | --- | --- | --- |
| S | Haiku | Low | rename, typo, quick question | $ |
| M | Sonnet | Medium | local bug, CRUD, tests | $$ |
| L | Sonnet, or Opus when judgment-heavy | High | multi-file feature, API design, races | $$$ |
| XL | Opus for security · Fable for long or ambiguous work, if listed | Max | security, architecture, long-horizon | $$$$ |

The menu also has Extra high between High and Max; this skill uses four levels. Current Haiku, Opus and Fable models always think, so there is no thinking toggle to set. Enterprise admins may hide some models or levels.

## Auto-apply (after the user says yes)

**Not available here:** in chat, Claude cannot change its own model or open other chats. Say so in the question ("Switch in the model menu, then reply") and give the steps: model menu next to the send button → pick the model → **Effort** → pick the level. It applies from the next response; for a new task, start a new chat so the old conversation is not re-read on the new model. Never claim a switch happened.

For automatic switching, use the skill in Claude Code or the desktop app's Code tab ([claude-code.md](claude-code.md)).

## Orchestration

- Solo is the default: chat has no worker API.
- Single-worker / fan-out → separate chats, one per worker, each with a self-contained prompt (goal, files, constraints, done-definition). Put shared context in a Project so it is not re-pasted.
- Run the classifier from this skill's folder: `python3 scripts/classify.py --task "..." --adapter claude-ai`.

## Example

```text
Card: Tier S · Low · solo; current chat is on Opus
→ Task is one rename: do it here (switching costs more than it saves),
  and recommend Haiku · Low in a new chat for the next batch of similar edits.
```
