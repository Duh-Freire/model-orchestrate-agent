# Market hosts (v0.1)

First-class adapters follow workplace adoption of AI coding tools from the
JetBrains Developer Ecosystem Survey 2026 (field period May–July 2026):

| Rank | Host | Adoption at work | Skills CLI agent id |
| --- | --- | --- | --- |
| 1 | Claude Code | 39% | `claude-code` |
| 2 | GitHub Copilot | 21% | `github-copilot` |
| 3 | OpenAI Codex | 16% | `codex` |
| 4 | Cursor | 12% | `cursor` |
| 5 | OpenCode | 7% | `opencode` |

Source: [AI Coding Agents: Adoption Trends](https://blog.jetbrains.com/research/2026/08/ai-coding-agent-adoption-2026/).

## Nearby (generic adapter)

| Host | Approx. adoption | Notes |
| --- | --- | --- |
| JetBrains AI / Junie | ~9% | Often hosts other agents; use generic or the nested agent's adapter |
| Google Antigravity | ~6% | Use [generic.md](adapters/generic.md); Gemini CLI-related surfaces similar |

## Detection hints

| Host | Signals |
| --- | --- |
| Claude Code | `CLAUDECODE` / `CLAUDE_CODE_*` env, `.claude/`, Agent/Task tool with `effort` |
| Claude apps (`claude-ai`) | Uploaded skill in a chat, code-execution sandbox, no Agent/Task tool |
| GitHub Copilot | Copilot Chat / agent session, `.github/`, `~/.copilot/` |
| Codex | `CODEX*` / `.codex/`, Codex CLI or IDE extension |
| Cursor | Cursor agent UI, `.cursor/`, Task tool with model slugs |
| OpenCode | `opencode` CLI, `~/.config/opencode/` |

If unsure → [generic.md](adapters/generic.md).

Revisit this ranking when publishing major versions; update adapters if the market shifts.
