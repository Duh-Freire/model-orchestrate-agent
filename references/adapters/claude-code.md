# Adapter: Claude Code

Skills CLI id: `claude-code` (also any Claude surface, e.g. Cowork, that exposes an `Agent` tool)  
Install path (project): `.claude/skills/` · personal: `~/.claude/skills/`

## Detect

- Tools named `Agent` or `Task` with `model` / `effort` / `subagent_type`
- Config under `.claude/` or `~/.claude/`
- Env hints: `CLAUDECODE`, `CLAUDE_CODE_*` (`classify.py --adapter auto` checks these)

## User matrix

Show only Claude models and Claude Code effort levels:

| Tier | Model | Effort | Best for | Cost |
| --- | --- | --- | --- | --- |
| S | Haiku (`haiku`) | `low` | rename, typo, quick question | $ |
| M | Sonnet (`sonnet`) | `medium` | local bug, CRUD, tests | $$ |
| L | Sonnet, or Opus (`opus`) when judgment-heavy | `high` | multi-file feature, API design, races | $$$ |
| XL | Opus for security · Fable (`fable`) for long or ambiguous work, if your plan has it | `max` | security, architecture, long-horizon | $$$$ |

Current Claude 5 family (check the host's model list before relying on an id):

| Alias | Model | Id |
| --- | --- | --- |
| `haiku` | Haiku 5.5 | `claude-haiku-5-5` |
| `sonnet` | Sonnet 5.5 | `claude-sonnet-5-5` |
| `opus` | Opus 5.5 | `claude-opus-5-5` |
| `fable` | Fable 5.1 | `claude-fable-5-1` |

Prefer the alias in `Agent(model=...)`; ids are for logs and docs. If the plan has no Fable, XL falls back to Opus · `max` and the card says so.

Fable may hand security-heavy requests to another model, so keep security on Opus.
Effort availability depends on the model; if `max` is missing, use the highest level offered.

## Auto-apply (after the user says yes)

1. **Subagent (default, automatic):** `Agent(model="<alias>", effort="<level>", prompt="<self-contained task>")`. Works for cheaper and stronger tiers and keeps this session's cache; the lead only merges and verifies. A solo task on a different tier becomes single-worker.
2. **New session (automatic, Claude desktop app):** when the user wants the task in its own session, start it with the app's session tool (`start_session` with `model` / `effort`). It accepts only the same model family or cheaper and effort at or below the current one; a stronger tier falls back to 1.
3. **This session's own model: never automatic.** The desktop app refuses it ("a session must not silently re-price its own turns") and it would discard the cache. If the user insists: `/clear`, then `/model <alias>` and `/effort <level>`; or a new terminal session with `claude --model <alias> --effort <level>`.

If `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` is set, step 1 cannot set the model: say so and use step 2 or the manual steps.

## Orchestration

- Workers get self-contained prompts (goal, files, constraints, done-definition); pass `model` and `effort` per call (`Task` is an alias of `Agent`).
- Custom subagents (`.claude/agents/*.md`) may set `model` and `effort` in frontmatter; the per-call `model` wins.
- Do **not** put Claude-only frontmatter (`model`, `effort`, `context: fork`) into the shared `SKILL.md`.

## Example

```text
Card: Tier M · Sonnet · medium; session on Opus
"Apply ▶ M now (Sonnet · medium as a subagent)?" → user: yes
→ Agent(prompt="<implement bugfix + run test>", model="sonnet", effort="medium")
→ "Subagent started: Sonnet · medium" → lead merges and runs tests
```
