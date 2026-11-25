#!/usr/bin/env python3
"""Project profile for model-orchestrate-agent: size, structure, growth alerts.

Stdlib only. Read-only unless --save, which writes <root>/.model-orchestrate.json
as the baseline that later scans compare against to detect growth.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any

SNAPSHOT = ".model-orchestrate.json"
PREFS = ".model-orchestrate.prefs.json"
PREF_KEYS = {
    "always_accept": bool,  # aplica as escolhas sem perguntar (exceto nível acima do modelo atual)
    "never_switch_session": bool,  # nunca propor trocar o modelo da própria sessão
    "optimize_for": str,  # cost | balanced | quality
}
PREF_OPTIMIZE = ("cost", "balanced", "quality")
OUTCOMES = ".model-orchestrate.outcomes.jsonl"
OUTCOME_RESULTS = ("ok", "escalated", "overkill")  # ok = o nível bastou; escalated = faltou; overkill = sobrou
OUTCOME_WINDOW = 5  # só os últimos N resultados do mesmo tipo e nível contam
OUTCOME_MIN = 3  # abaixo disso não há evidência para calibrar
SIZE_ORDER = ("small", "medium", "large")
MAX_FILES = 50_000
# Reading files dominates scan time, so lines are counted exactly only for files up
# to MAX_EXACT bytes and READ_BUDGET bytes in total; the rest is estimated from size.
MAX_EXACT = 512_000
READ_BUDGET = 16_000_000
DEFAULT_BYTES_PER_LINE = 40
MINIFIED = (".min.js", ".min.css", ".min.mjs", ".bundle.js")

SKIP_DIRS = {
    "node_modules", "venv", "env", "__pycache__", "dist", "build", "out", "target",
    "vendor", "coverage", "site-packages", "bin", "obj", "Pods",
}
SOURCE_EXT = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".java", ".kt", ".kts", ".go",
    ".rs", ".rb", ".php", ".cs", ".cpp", ".cc", ".c", ".h", ".hpp", ".m", ".mm", ".swift",
    ".scala", ".dart", ".lua", ".sh", ".ps1", ".sql", ".vue", ".svelte", ".html", ".css",
    ".scss", ".sass", ".less", ".ex", ".exs", ".erl", ".clj", ".hs", ".ml", ".r", ".jl",
    ".zig", ".sol",
}
MANIFESTS = {
    "package.json", "pyproject.toml", "setup.py", "go.mod", "Cargo.toml", "pom.xml",
    "build.gradle", "build.gradle.kts", "composer.json", "Gemfile", "pubspec.yaml", "mix.exs",
}
TEST_DIRS = {"test", "tests", "__tests__", "spec", "specs"}
TEST_SUFFIXES = (
    "_test.py", "_test.go", ".test.ts", ".test.tsx", ".test.js", ".test.jsx",
    ".spec.ts", ".spec.tsx", ".spec.js", ".spec.jsx", "test.java", "tests.cs", "_spec.rb",
)
CI_PATHS = (
    ".github/workflows", ".gitlab-ci.yml", "azure-pipelines.yml", "Jenkinsfile",
    ".circleci", "bitbucket-pipelines.yml",
)
MEMORY_PATHS = ("CLAUDE.md", "AGENTS.md", ".cursor/rules", ".cursorrules", ".github/copilot-instructions.md")
# Where each host reads persistent project context from.
MEMORY_FOR_ADAPTER = {
    "claude-code": "CLAUDE.md",
    "claude-ai": "Project instructions (Claude Projects)",
    "codex": "AGENTS.md",
    "opencode": "AGENTS.md",
    "cursor": ".cursor/rules",
    "github-copilot": ".github/copilot-instructions.md",
}


def _is_test(rel: Path) -> bool:
    name = rel.name.lower()
    return (
        bool({p.lower() for p in rel.parts[:-1]} & TEST_DIRS)
        or name.startswith("test_")
        or name.endswith(TEST_SUFFIXES)
    )


def _count_lines(path: Path) -> int:
    try:
        with path.open("rb") as fh:
            return sum(chunk.count(b"\n") for chunk in iter(lambda: fh.read(1 << 16), b""))
    except OSError:
        return 0


def size_class(source_files: int, loc: int) -> str:
    if source_files >= 500 or loc >= 50_000:
        return "large"
    if source_files >= 50 or loc >= 5_000:
        return "medium"
    return "small"


def scan(root: str | Path) -> dict[str, Any]:
    root = Path(root).resolve()
    if not root.is_dir():
        raise SystemExit(f"error: not a directory: {root}")

    files = source_files = 0
    read_bytes = counted_lines = estimated_bytes = 0
    languages: dict[str, int] = {}
    package_dirs: set[str] = set()
    has_tests = truncated = False
    for dirpath, dirnames, filenames in os.walk(root):
        # Hidden dirs (.git, .venv, .next, ...) and build output are not project code.
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        rel_dir = Path(dirpath).relative_to(root)
        for name in filenames:
            files += 1
            if files > MAX_FILES:
                truncated = True
                break
            if name in MANIFESTS or name.endswith(".csproj"):
                package_dirs.add(rel_dir.as_posix())
            ext = os.path.splitext(name)[1].lower()
            if ext not in SOURCE_EXT or name.lower().endswith(MINIFIED):
                continue
            source_files += 1
            languages[ext] = languages.get(ext, 0) + 1
            has_tests = has_tests or _is_test(rel_dir / name)
            path = Path(dirpath, name)
            try:
                size = path.stat().st_size
            except OSError:
                continue
            if size <= MAX_EXACT and read_bytes + size <= READ_BUDGET:
                read_bytes += size
                counted_lines += _count_lines(path)
            else:
                estimated_bytes += size
        if truncated:
            break

    # Big files tend to have long lines; never estimate denser than the default.
    bytes_per_line = max(read_bytes / counted_lines if counted_lines else 0, DEFAULT_BYTES_PER_LINE)
    loc = counted_lines + round(estimated_bytes / bytes_per_line)
    memory = next((p for p in MEMORY_PATHS if (root / p).exists()), None)
    return {
        "name": root.name,
        "scanned": datetime.date.today().isoformat(),
        "size": size_class(source_files, loc),
        "files": min(files, MAX_FILES),
        "source_files": source_files,
        "loc": loc,
        "loc_estimated": estimated_bytes > 0,
        "languages": [ext.lstrip(".") for ext, _ in sorted(languages.items(), key=lambda kv: -kv[1])[:5]],
        "packages": len(package_dirs),
        "monorepo": len(package_dirs) >= 3,
        "has_tests": has_tests,
        "has_ci": any((root / p).exists() for p in CI_PATHS),
        "memory_file": memory,
        "truncated": truncated,
    }


def load_baseline(root: str | Path) -> dict[str, Any] | None:
    path = Path(root).resolve() / SNAPSHOT
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def save_baseline(root: str | Path, profile: dict[str, Any]) -> Path:
    path = Path(root).resolve() / SNAPSHOT
    path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    return path


def load_prefs(root: str | Path) -> dict[str, Any]:
    """Preferências do usuário para o projeto; arquivo ausente ou ilegível = vazio. Só chaves e tipos conhecidos."""
    path = Path(root).resolve() / PREFS
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    clean: dict[str, Any] = {}
    for key, kind in PREF_KEYS.items():
        value = data.get(key)
        if isinstance(value, kind) and (key != "optimize_for" or value in PREF_OPTIMIZE):
            clean[key] = value
    return clean


def parse_pref(assignment: str) -> tuple[str, Any]:
    """'chave=valor' -> (chave, valor tipado). Erro claro para chave ou valor inválido."""
    key, sep, raw = assignment.partition("=")
    key = key.strip()
    raw = raw.strip().lower()
    if not sep or key not in PREF_KEYS:
        raise SystemExit(f"error: use chave=valor com chave em {sorted(PREF_KEYS)}")
    if PREF_KEYS[key] is bool:
        if raw not in ("true", "false"):
            raise SystemExit(f"error: {key} aceita true ou false")
        return key, raw == "true"
    if raw not in PREF_OPTIMIZE:
        raise SystemExit(f"error: {key} aceita {', '.join(PREF_OPTIMIZE)}")
    return key, raw


def save_prefs(root: str | Path, updates: dict[str, Any]) -> Path:
    path = Path(root).resolve() / PREFS
    current = load_prefs(root)
    current.update(updates)
    path.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load_outcomes(root: str | Path) -> list[dict[str, Any]]:
    """Resultados registrados (um JSON por linha); linhas ilegíveis são ignoradas."""
    path = Path(root).resolve() / OUTCOMES
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    rows: list[dict[str, Any]] = []
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if (
            isinstance(row, dict)
            and row.get("tier") in ("S", "M", "L", "XL")
            and row.get("result") in OUTCOME_RESULTS
            and isinstance(row.get("type"), str)
        ):
            rows.append(row)
    return rows


def parse_outcome(assignment: str) -> dict[str, Any]:
    """'tipo:nível:resultado' -> linha do registro. Ex.: bugfix:M:ok."""
    parts = [p.strip() for p in assignment.split(":")]
    if (
        len(parts) != 3
        or not parts[0]
        or parts[1].upper() not in ("S", "M", "L", "XL")
        or parts[2].lower() not in OUTCOME_RESULTS
    ):
        raise SystemExit(f"error: use tipo:nível:resultado, resultado em {', '.join(OUTCOME_RESULTS)}")
    return {"type": parts[0].lower(), "tier": parts[1].upper(), "result": parts[2].lower()}


def log_outcome(root: str | Path, row: dict[str, Any]) -> Path:
    path = Path(root).resolve() / OUTCOMES
    row = dict(row, at=datetime.date.today().isoformat())
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def calibration_for(outcomes: list[dict[str, Any]], task_type: str, tier: str) -> tuple[str, str] | None:
    """('up'|'down', motivo) quando os últimos resultados do mesmo tipo e nível pedem ajuste; senão None."""
    recent = [o for o in outcomes if o["type"] == task_type and o["tier"] == tier][-OUTCOME_WINDOW:]
    n = len(recent)
    if n < OUTCOME_MIN:
        return None
    escalated = sum(o["result"] == "escalated" for o in recent)
    overkill = sum(o["result"] == "overkill" for o in recent)
    if escalated * 2 > n:
        return "up", f"{escalated} de {n} tarefas '{task_type}' no nível {tier} precisaram subir"
    if overkill * 2 > n:
        return "down", f"{overkill} de {n} tarefas '{task_type}' no nível {tier} sobraram capacidade"
    return None


def alerts_for(profile: dict[str, Any], baseline: dict[str, Any] | None, adapter: str = "generic") -> list[str]:
    alerts: list[str] = []
    size = profile["size"]
    if baseline is None:
        alerts.append(
            f"baseline: no {SNAPSHOT} yet; offer to save one (project-scan.py --save) so growth can be tracked"
        )
    else:
        since = baseline.get("scanned", "the last baseline")
        old_size = baseline.get("size")
        if old_size in SIZE_ORDER and SIZE_ORDER.index(size) > SIZE_ORDER.index(old_size):
            alerts.append(
                f"growth: project grew {old_size} -> {size} since {since}; review default tiers "
                "(features M, cross-module L) and save a new baseline"
            )
        old_loc = baseline.get("loc")
        if isinstance(old_loc, int) and old_loc > 0 and profile["loc"] >= old_loc * 1.5:
            pct = round((profile["loc"] - old_loc) * 100 / old_loc)
            approx = "~" if profile.get("loc_estimated") or baseline.get("loc_estimated") else ""
            alerts.append(
                f"growth: code grew {pct}% since {since} ({approx}{old_loc} -> {approx}{profile['loc']} lines)"
            )
        old_pkgs = baseline.get("packages")
        if isinstance(old_pkgs, int) and profile["packages"] > old_pkgs:
            alerts.append(
                f"structure: packages {old_pkgs} -> {profile['packages']}; cross-package tasks classify as L, "
                "scope each task to one package to stay on M"
            )
    if size != "small":
        if not profile["has_tests"]:
            alerts.append(
                "verification: no tests found; add tests before risky edits (cheaper than escalating tiers)"
            )
        if not profile["memory_file"]:
            target = MEMORY_FOR_ADAPTER.get(adapter, "AGENTS.md")
            alerts.append(
                f"context: no agent memory file; add {target} with build/test commands and layout "
                "so each session re-explores less"
            )
    if size == "large":
        alerts.append(
            "scope: large repo; name files or modules in each task to stay on M, "
            "and send discovery to an S explore worker"
        )
    if profile["monorepo"] and not any(a.startswith("structure:") for a in alerts):
        alerts.append(
            f"structure: {profile['packages']} packages; scope each task to one package to stay on M"
        )
    if profile["truncated"]:
        alerts.append(f"scan: stopped at {MAX_FILES} files; numbers are lower bounds")
    return alerts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Profile a project and report growth alerts.")
    parser.add_argument("path", nargs="?", default=".", help="Project root (default: .)")
    parser.add_argument(
        "--adapter",
        default="generic",
        help="Host adapter id, used to name the right memory file in alerts.",
    )
    parser.add_argument("--save", action="store_true", help=f"Write {SNAPSHOT} as the new baseline.")
    parser.add_argument(
        "--set-pref",
        action="append",
        default=[],
        metavar="CHAVE=VALOR",
        help=f"Grava uma preferência do projeto em {PREFS} (always_accept, never_switch_session, optimize_for). "
        "Só depois de o usuário pedir.",
    )
    parser.add_argument(
        "--log-outcome",
        action="append",
        default=[],
        metavar="TIPO:NIVEL:RESULTADO",
        help=f"Registra em {OUTCOMES} como o nível foi (ok | escalated | overkill); calibra as próximas "
        "recomendações. Só com o aval do usuário.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")

    profile = scan(args.path)
    baseline = load_baseline(args.path)
    alerts = alerts_for(profile, baseline, args.adapter)
    result: dict[str, Any] = {
        "project": profile,
        "baseline": baseline.get("scanned") if baseline else None,
        "alerts": alerts,
        "preferences": load_prefs(args.path),
    }
    if args.set_pref:
        updates = dict(parse_pref(item) for item in args.set_pref)
        result["preferences_saved"] = str(save_prefs(args.path, updates))
        result["preferences"] = load_prefs(args.path)
    if args.log_outcome:
        for row in [parse_outcome(item) for item in args.log_outcome]:
            result["outcome_logged"] = str(log_outcome(args.path, row))
        result["outcomes_total"] = len(load_outcomes(args.path))
    if args.save:
        result["saved"] = str(save_baseline(args.path, profile))
        result["alerts"] = [a for a in alerts if not a.startswith("baseline:")]
    json.dump(result, sys.stdout, indent=2 if args.pretty else None, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
