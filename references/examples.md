# Examples

Model names come from the loaded adapter; Claude Code shown here.

## S — rename (one line, no question)

**Task:** Rename `getUser` to `fetchUser` in one module. Session already on Sonnet.

```markdown
Tier S — mechanical rename in one module; doing it on the current model.
```

## M — local bug (asks: current model is higher)

**Task:** Fix null pointer when cart is empty; test exists. Session on Opus.

```markdown
Recommendation: Tier M · Sonnet · effort medium · single-worker
Why: localized bug, verifiable with the existing test
Escalation: if a race across services shows up → L
```

Then the Claude Code user matrix with ▶ on M and "(current)" on the Opus row, ending with:
"Apply ▶ M now (Sonnet · medium as a subagent)? Yes / another row / keep current / always accept"

User: yes → `Agent(model="sonnet", effort="medium", prompt=...)` runs at once → "Subagent started: Sonnet · medium".

## L — multi-file feature, growing project

**Task:** Add rate limiting middleware and wire config + tests (`--project .`).

```markdown
Recommendation: Tier L · Sonnet · effort high · single-worker
Why: multi-file API surface, moderate risk
Escalation: if authz interaction is unclear → XL
Alerts:
- growth: project grew small -> medium since 2026-09-01; review default tiers and save a new baseline
- context: no agent memory file; add CLAUDE.md with build/test commands and layout
```

## XL — security review (fan-out)

**Task:** Audit new OAuth callback for token leakage and open redirects.

```markdown
Recommendation: Tier XL · Opus · effort max · fan-out
Why: security, high cost of error
Escalation: top tier: re-plan with failure evidence or ask the user
Workers: (1) threat scan read-only, (2) patch critical issues, (3) verify with tests + checklist
```
