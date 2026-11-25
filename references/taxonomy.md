# Task taxonomy

Score each axis before picking a tier. Prefer signals over prompt length alone.

## Axes

| Axis | Low | High |
| --- | --- | --- |
| **Type** | Q&A, rename, typo, format | Architecture, security, UI taste, long research |
| **Breadth** | One file / one symbol | Cross-cutting, many packages, repo-wide |
| **Ambiguity** | Spec clear, path known | Requirements fuzzy, discovery needed |
| **Risk** | Cosmetic, docs, tests only | Auth, data, migrations, prod config |
| **Verifiability** | Lint/tests catch mistakes | Judgment / taste / silent correctness |
| **Horizon** | One turn | Many steps, long-running agent |

## Type labels

Use one primary label:

- `qa` — explain or locate without edits
- `mechanical` — rename, import fix, formatting, boilerplate
- `bug` — localized defect with a repro or clear failure
- `feature` — new behavior with bounded scope
- `design` — API / module shape decisions
- `security` — auth, secrets, injection, permissions
- `ui` — visual / interaction quality
- `research` — explore codebase or options before changing

## Signal keywords (heuristic)

- **Downshift:** typo, rename, "one file", "just explain", lint fix, comment
- **Upshift:** security, migration, race, deadlock, "don't break", architecture, multi-package, adversarial review, flaky, production, encryption
- `classify.py` matches English and pt-BR equivalents (renomear, segurança, migração, produção, "não pode quebrar", …).
- Questions with no edit verb ("explain", "how does", "como funciona") are `qa` and cap at **M**, even on sensitive code.

## Anti-patterns

- Treating long prompts as hard (a long paste can still be S)
- Treating short prompts as easy (one sentence can be XL security)
- Counting files in the repo instead of files the task must touch
