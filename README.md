# Model Orchestrate Agent — a Claude Code skill for model routing

**Model Orchestrate Agent** is a smart skill that analyzes every coding task before it runs. It automatically recommends the cheapest AI model and the ideal effort level to get the job done.

Sometimes we use a cannon to shoot a sparrow, or hire a crane to carry a shoebox. The bill at the end of the month feels the weight.

Under the hood, `model-orchestrate-agent` is an [Agent Skill](https://code.claude.com/docs/en/skills) for Claude Code (and other AI coding agents) that classifies every new coding task, recommends a model tier and reasoning effort, and — once you approve — applies the choice automatically by spawning a subagent or a new session on the right model. It saves tokens on easy work and escalates to frontier models only when the task really needs it.

[![skills.sh](https://skills.sh/b/Duh-Freire/model-orchestrate-agent)](https://skills.sh/Duh-Freire/model-orchestrate-agent)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.txt)
![Claude Code](https://img.shields.io/badge/Claude_Code-skill-D97757)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)

---

## Why

Running every task on the strongest model burns tokens; running everything on the cheapest one burns your time. This skill makes the trade-off explicit, task by task:

- **Task-aware routing** — scores type, breadth, ambiguity, risk, verifiability and horizon, then maps the task to a tier: **S / M / L / XL**.
- **Human in the loop** — nothing switches until you say yes. After that, the switch is automatic.
- **Cache-friendly** — never changes the current session's model mid-thread; uses subagents or new sessions at task boundaries.
- **Multi-agent orchestration** — chooses between solo, single-worker, or fan-out + verify for large or risky work.
- **Escalation and calibration** — goes one tier up on quality failure, logs outcomes, and recalibrates tiers per project over time.
- **Project growth alerts** — profiles the repository and warns when it grows enough to rethink default tiers.
- **Multi-host** — adapters for Claude Code, Claude.ai, GitHub Copilot, OpenAI Codex, Cursor, OpenCode, and a generic fallback. It only ever shows the current app's own models.
- **Bilingual triggers** — understands English and Brazilian Portuguese requests.

## Tiers

| Tier | Capability | Effort | Typical task | Claude Code model |
| --- | --- | --- | --- | --- |
| **S** | Fast / cheap coder | `low` | Rename, typo, quick question | Haiku |
| **M** | Balanced coder | `medium` | Local bug, CRUD, tests, small refactor | Sonnet |
| **L** | Strong coder | `high` | Multi-file feature, API design, races | Sonnet, or Opus when judgment-heavy |
| **XL** | Frontier + deep reasoning | `max` | Security, architecture, long-horizon work | Opus (security) · Fable (long or ambiguous) |

Bias the choice per project with `optimize_for`: `cost`, `balanced` (default) or `quality`.

## Installation

### Quick install (any agent, via [skills.sh](https://skills.sh))

```bash
npx skills add Duh-Freire/model-orchestrate-agent
```

The [skills CLI](https://github.com/vercel-labs/skills) detects your agents (Claude Code, Codex, Cursor, Copilot, OpenCode, ...) and installs the skill where each one expects it.

### Claude Code (manual)

Personal (available in every project):

```bash
git clone https://github.com/Duh-Freire/model-orchestrate-agent.git ~/.claude/skills/model-orchestrate-agent
```

Project-only (shared with your team through the repo):

```bash
git clone https://github.com/Duh-Freire/model-orchestrate-agent.git .claude/skills/model-orchestrate-agent
```

On Windows (PowerShell):

```powershell
git clone https://github.com/Duh-Freire/model-orchestrate-agent.git "$env:USERPROFILE\.claude\skills\model-orchestrate-agent"
```

Restart Claude Code; the skill shows up as `/model-orchestrate-agent`.

### Claude.ai / Claude desktop

Download `model-orchestrate-agent.skill` from the [latest release](https://github.com/Duh-Freire/model-orchestrate-agent/releases/latest) and upload it under **Settings → Capabilities → Skills**.

### Other agents (Codex, Cursor, Copilot, OpenCode)

Copy the folder into the host's skills directory, or point the agent at `SKILL.md`. The matching adapter in [`references/adapters/`](references/adapters) lists that host's models and how a switch is applied.

**Requirements:** Python 3.8+ for the optional helper scripts (standard library only). Without Python, the skill still works: the model classifies in its head using `SKILL.md`.

## Usage

The skill triggers on its own at the start of each new coding task, or when you ask things like *"which model should I use?"*, *"how do I save tokens?"*, or *"should I delegate this to subagents?"*. You can also call it explicitly:

```text
/model-orchestrate-agent Fix the null pointer when the cart is empty
```

### Example: trivial task — one line, no question

```markdown
Tier S — mechanical rename in one module; doing it on the current model.
```

### Example: local bug while the session is on Opus — asks first

```markdown
Recommendation: Tier M · Sonnet · effort medium · single-worker
Why: localized bug, verifiable with the existing test
Escalation: if a race across services shows up → L

Apply ▶ M now (Sonnet · medium as a subagent)? Yes / another row / keep current / always accept
```

Answer **yes** and the skill runs `Agent(model="sonnet", effort="medium", ...)` right away.

### Example: security review — fan-out with verification

```markdown
Recommendation: Tier XL · Opus · effort max · fan-out
Why: security, high cost of error
Workers: (1) threat scan read-only, (2) patch critical issues, (3) verify with tests + checklist
```

More in [`references/examples.md`](references/examples.md).

### Helper scripts

```bash
# Classify a task and emit a validated plan (JSON)
python scripts/classify.py --task "Add rate limiting middleware with tests" --project . --session-tier L \
  | python scripts/emit-plan.py --stdin

# Profile the repo, save a growth baseline, set preferences, log outcomes
python scripts/project-scan.py . --save
python scripts/project-scan.py . --set-pref optimize_for=cost
python scripts/project-scan.py . --log-outcome bugfix:M:ok
```

Project preferences live in `.model-orchestrate.prefs.json` (`always_accept`, `never_switch_session`, `optimize_for`) and are written only when you ask.

## How it works

1. **Project check** — profile the repo and compare with the saved baseline.
2. **Classify** — score the task and map it to a tier ([taxonomy](references/taxonomy.md), [tiers](references/tiers.md)).
3. **Mode** — solo, single-worker, or fan-out + verify ([orchestration](references/orchestration.md)).
4. **Adapt** — load the host adapter for the current app.
5. **Recommend** — show a decision card with the host's model matrix.
6. **Apply** — on your yes, spawn the subagent or session automatically.
7. **Escalate** — one tier up on quality failure ([escalation](references/escalation.md)).
8. **Calibrate** — log the outcome; after 3+ results the tier for that task type adjusts itself.

## Repository layout

```text
SKILL.md                 Skill entry point (frontmatter + protocol)
assets/                  Decision card template and plan JSON schema
references/              Taxonomy, tiers, orchestration, escalation, examples
references/adapters/     One file per host app (Claude Code, Codex, Cursor, ...)
scripts/                 classify.py, emit-plan.py, project-scan.py (stdlib only)
```

## Contributing

Issues and pull requests are welcome — especially new host adapters and updated model lists as vendors ship new models.

## License

[MIT](LICENSE.txt)
