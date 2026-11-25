#!/usr/bin/env python3
"""Heuristic task classifier for model-orchestrate-agent.

Stdlib only. Emits a plan JSON (valid for emit-plan.py --stdin) with axes,
suggested tier, effort, signals, mode, and adapter. Keywords cover English
and Brazilian Portuguese.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable

TIER_ORDER = ("S", "M", "L", "XL")
EFFORT = {"S": "low", "M": "medium", "L": "high", "XL": "max"}
# Keep in sync with VALID_ADAPTER in emit-plan.py and assets/plan.schema.json.
ADAPTERS = (
    "claude-code",
    "claude-ai",
    "github-copilot",
    "codex",
    "cursor",
    "opencode",
    "generic",
)
# Env var prefixes a host sets in the shell it runs tools from (best effort).
ADAPTER_ENV_PREFIXES = (
    ("claude-code", ("CLAUDECODE", "CLAUDE_CODE_")),
    ("codex", ("CODEX_",)),
    ("cursor", ("CURSOR_",)),
    ("opencode", ("OPENCODE",)),
)

# auth, authn, authz, authenticate(d), authentication, authorize, authorization —
# but not "author" / "authors".
AUTH = r"\bauth(n|z|enticat\w*|ori[sz]\w*)?\b"

DOWNSHIFT = (
    r"\btypo\b",
    r"\brename\b",
    r"\bone file\b",
    r"\bsingle file\b",
    r"\bjust explain\b",
    r"\bexplain only\b",
    r"\blint\b",
    r"\bformatting\b",
    r"\bcomments?\b",
    r"\bdocs?\b",
    r"\breadme\b",
    # pt-BR
    r"\berros? de digita[çc][ãa]o\b",
    r"\brenome\w*",
    r"\b(um|[úu]nico) arquivo\b",
    r"\barquivo [úu]nico\b",
    r"\b(s[óo]|apenas) expli\w*",
    r"\bcoment[áa]rios?\b",
    r"\bdocumenta[çc][ãa]o\b",
    r"\bformata[çc][ãa]o\b",
)

UPSHIFT = (
    r"\bsecur(e|ity)\b",
    AUTH,
    r"\bmigrations?\b",
    r"\brace\b",
    r"\bdeadlocks?\b",
    r"\bdon'?t break\b",
    r"\barchitecture\b",
    r"\bmulti[- ]?(package|repo|service)s?\b",
    r"\badversarial\b",
    r"\boauth",
    r"\binjection\b",
    r"\bflaky\b",
    r"\bproduction\b",
    r"\bencrypt\w*|\bcrypto\w*",
    # pt-BR
    r"\bseguran[çc]a\b",
    r"\bautentica[çc][ãa]o\b",
    r"\bautoriza[çc][ãa]o\b",
    r"\bmigra[çc](ão|ões|ao|oes)\b",
    r"\bcondi[çc](ão|ões|ao|oes) de corrida\b",
    r"\bn[ãa]o (pode |deve )?quebr\w*",
    r"\barquitetura\b",
    r"\binje[çc][ãa]o\b",
    r"\bintermitente\b",
    r"\bprodu[çc][ãa]o\b",
    r"\bcriptograf\w*",
)

TYPE_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    (
        "security",
        (
            r"\bsecur", r"\bseguran[çc]a", AUTH, r"\bautentica", r"\bautoriza",
            r"\boauth", r"\binjection", r"\binje[çc][ãa]o", r"\bxss\b", r"\bcsrf\b",
            r"\bvulnerab", r"\bcve\b", r"\bencrypt", r"\bdecrypt", r"\bcrypto",
            r"\bcriptograf", r"\bsecrets?\b", r"\bsegredos?\b", r"\bcredentials?\b",
            r"\bcredenci", r"\bpermissions?\b", r"\bpermiss[õo]es\b",
        ),
    ),
    ("ui", (r"\bui\b", r"\bcss\b", r"\blayout\b", r"\bvisual\b", r"\bdesign system\b", r"\btelas?\b", r"\bresponsiv")),
    ("design", (r"\barchitect", r"\barquitet", r"\bapi design\b", r"\bdesign de api\b", r"\bmodule shape\b")),
    ("research", (r"\bresearch\b", r"\bpesquis", r"\bexplor", r"\binvestig", r"\bsurvey\b")),
    (
        "bug",
        (
            r"\bbugs?\b", r"\bfix\b", r"\bcorrig", r"\bconsert", r"\berros?\b", r"\bfalha",
            r"\bnull pointer\b", r"\bcrash", r"\btrava", r"\bregress", r"\bleak", r"\bvazamento\b",
        ),
    ),
    ("feature", (r"\badd\b", r"\badicion", r"\bimplement", r"\bfeature\b", r"\bfuncionalidade\b", r"\bendpoints?\b", r"\bcri(ar|e)\b")),
    ("mechanical", (r"\brename\b", r"\brenome", r"\btypo\b", r"\bformat(ting|ar)?\b", r"\bboilerplate\b")),
]

QA_PATTERNS = (
    r"\bexplain\b", r"\bwhere is\b", r"\bwhat does\b", r"\bhow does\b",
    r"\bexpli(que|car|ca)\b", r"\bonde (fica|est[áa])\b", r"\bo que (faz|[ée])\b", r"\bcomo funciona\b",
)
# Any of these means the task changes code, so it is not a read-only question.
EDIT_VERBS = (
    r"\b(fix|add|implement\w*|change|update|refactor|write|create|remove|delete|rename|migrate|bump|patch)\b",
    r"\b(corrig\w*|adicion\w*|alter\w*|atualiz\w*|refator\w*|escrev\w*|cri(ar|e)|remov\w*|renome\w*|migr\w*)\b",
)


def _matches(patterns: Iterable[str], text: str) -> list[str]:
    hits: list[str] = []
    for pat in patterns:
        if re.search(pat, text, flags=re.IGNORECASE):
            hits.append(pat)
    return hits


def _detect_type(text: str) -> str:
    if _matches(QA_PATTERNS, text) and not _matches(EDIT_VERBS, text):
        return "qa"
    for label, pats in TYPE_PATTERNS:
        if _matches(pats, text):
            return label
    return "feature"


def _score_axes(text: str, task_type: str) -> dict[str, str]:
    words = len(re.findall(r"\w+", text))
    multi = bool(
        re.search(
            r"\b(multi[- ]?files?|across|several files|many files|multiple files|packages"
            r"|repo[- ]wide|codebase[- ]wide|v[áa]rios arquivos|m[úu]ltiplos arquivos"
            r"|todo o (projeto|reposit[óo]rio|c[óo]digo))\b",
            text,
            re.I,
        )
    )
    one_file = bool(
        re.search(r"\b(one|single)\s+file\b|\b(um|[úu]nico)\s+arquivo\b|\barquivo\s+[úu]nico\b", text, re.I)
    )
    ambiguous = bool(
        re.search(
            r"\b(maybe|figure out|unclear|explor\w*|investig\w*|tbd"
            r"|talvez|descobrir|n[ãa]o (est[áa] )?claro|indefinido)\b",
            text,
            re.I,
        )
    )
    high_risk = task_type == "security" or bool(
        re.search(
            r"\b(migrations?|production|prod|auth|secrets?|credentials?|payments?|billing"
            r"|migra[çc]\w*|produ[çc][ãa]o|segredos?|credenci\w*|pagamentos?|cobran[çc]a)\b",
            text,
            re.I,
        )
    )
    verifiable = bool(re.search(r"\b(tests?|testes?|lint|typecheck|ci)\b", text, re.I))
    long_horizon = bool(
        re.search(
            r"\b(end[- ]to[- ]end|multi[- ]step|long[- ]running|overhaul"
            r"|ponta a ponta|v[áa]rias etapas|longa dura[çc][ãa]o)\b",
            text,
            re.I,
        )
    ) or words > 120

    breadth = "high" if multi and not one_file else ("low" if one_file else "medium")
    if words < 12 and not multi:
        breadth = "low"

    return {
        "type": task_type,
        "breadth": breadth,
        "ambiguity": "high" if ambiguous else "low",
        "risk": "high" if high_risk else "low",
        "verifiability": "high" if verifiable else "medium",
        "horizon": "high" if long_horizon else "low",
    }


def _base_tier(axes: dict[str, str], down: list[str], up: list[str]) -> str:
    if axes["type"] == "qa":
        # Read-only questions never need L/XL; escalate if the answer falls short.
        return "S" if axes["breadth"] == "low" and axes["risk"] == "low" else "M"
    if axes["type"] == "security" or (axes["risk"] == "high" and axes["ambiguity"] == "high"):
        return "XL"
    if axes["type"] in {"design", "research"} and axes["breadth"] != "low":
        return "L"
    if axes["type"] == "ui" and axes["breadth"] != "low":
        return "L"
    if up and not down:
        return "L"
    if axes["type"] == "mechanical" or (down and axes["risk"] == "low"):
        return "S"
    if axes["type"] == "bug" and axes["breadth"] == "low":
        return "M"
    if axes["breadth"] == "high" or axes["horizon"] == "high":
        return "L"
    return "M"


def _apply_optimize(tier: str, optimize_for: str, axes: dict[str, str]) -> str:
    idx = TIER_ORDER.index(tier)
    if optimize_for == "cost" and idx > 0 and axes["risk"] != "high":
        # Borderline downshift one step except security/high risk
        if axes["ambiguity"] != "high":
            return TIER_ORDER[idx - 1] if tier in {"L", "XL"} and axes["breadth"] != "high" else tier
    if optimize_for == "quality" and idx < len(TIER_ORDER) - 1 and axes["type"] != "qa":
        if axes["ambiguity"] == "high" or axes["risk"] == "high" or axes["type"] in {
            "security",
            "design",
            "ui",
        }:
            return TIER_ORDER[idx + 1]
    return tier


def _suggest_mode(tier: str, axes: dict[str, str], optimize_for: str) -> str:
    if tier in {"S", "M"} and axes["breadth"] != "high":
        return "solo"
    if optimize_for == "cost":
        # Fan-out multiplies context; under cost bias keep one isolated worker.
        return "single-worker"
    if axes["type"] == "security" or (tier == "XL" and axes["breadth"] == "high"):
        return "fan-out"
    return "single-worker"


def detect_adapter(environ: dict[str, str] | None = None) -> str:
    env = os.environ if environ is None else environ
    for adapter, prefixes in ADAPTER_ENV_PREFIXES:
        if any(key.upper().startswith(prefixes) for key in env):
            return adapter
    return "generic"


def escalation_for(tier: str) -> str:
    if tier == "XL":
        return "top tier: if quality fails, re-plan with the failure evidence or ask the user"
    return f"if quality fails -> {TIER_ORDER[TIER_ORDER.index(tier) + 1]}"


def load_scanner():
    sys.dont_write_bytecode = True  # não deixar __pycache__ dentro da skill instalada
    spec = importlib.util.spec_from_file_location(
        "project_scan", Path(__file__).resolve().parent / "project-scan.py"
    )
    scanner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scanner)
    return scanner


def _worker_pays_off(axes: dict[str, str], tier: str, session_tier: str | None) -> tuple[bool, str]:
    """Um worker relê o contexto inteiro: só compensa com trabalho grande ou diferença de preço grande."""
    if session_tier is None or TIER_ORDER.index(tier) >= TIER_ORDER.index(session_tier):
        return True, ""
    gap = TIER_ORDER.index(session_tier) - TIER_ORDER.index(tier)
    if axes["breadth"] == "high" or axes["horizon"] == "high" or gap >= 2:
        return True, ""
    return False, "worker não compensa: tarefa curta e a economia de um nível não paga a releitura do contexto"


def decide_ask(tier: str, mode: str, session_tier: str | None, always_accept: bool) -> tuple[str, str]:
    """Quando perguntar (decision-card.md, "When to ask"). Devolve (decisão, motivo).

    inline = uma linha e segue; ask = cartão e espera; auto = o usuário já pediu "sempre aceitar".
    """
    idx = TIER_ORDER.index(tier)
    workers = mode != "solo"
    if session_tier is not None:
        current = TIER_ORDER.index(session_tier)
        if idx > current:
            return "ask", "acima do modelo atual: risco de qualidade, precisa de sim"
        if always_accept:
            return "auto", "usuário pediu sempre aceitar (abaixo ou no nível da sessão)"
        if idx == current and not workers:
            return "inline", "nível igual ao da sessão, sem worker: uma linha e segue"
        if idx < current and idx >= TIER_ORDER.index("M"):
            return "ask", "abaixo do modelo atual em trabalho não trivial: economia real"
        if idx < current:
            return "inline", "tarefa S abaixo da sessão: uma linha e segue"
        return "ask", "há worker: confirmar antes de criar"
    if always_accept:
        return "auto", "usuário pediu sempre aceitar (nível da sessão desconhecido: só vale até o nível atual)"
    return ("ask" if workers or idx >= TIER_ORDER.index("L") else "inline"), "nível da sessão desconhecido"


def project_context(path: str, adapter: str) -> tuple[dict[str, Any], list[str]]:
    """Profile the project with project-scan.py (read-only) and return its alerts."""
    scanner = load_scanner()
    profile = scanner.scan(path)
    return profile, scanner.alerts_for(profile, scanner.load_baseline(path), adapter)


def classify(
    task: str,
    optimize_for: str | None = None,
    adapter: str = "auto",
    project: str | None = None,
    session_tier: str | None = None,
) -> dict:
    text = task.strip()
    if not text:
        raise SystemExit("error: empty task")
    if adapter == "auto":
        adapter = detect_adapter()
    if adapter not in ADAPTERS:
        raise SystemExit(f"error: invalid adapter {adapter!r}")
    if session_tier is not None and session_tier not in TIER_ORDER:
        raise SystemExit(f"error: invalid session tier {session_tier!r}")
    scanner = load_scanner() if project is not None else None
    prefs = scanner.load_prefs(project) if scanner else {}
    if optimize_for is None:  # sem --optimize-for explícito: preferência do projeto, depois balanced
        optimize_for = prefs.get("optimize_for", "balanced")

    task_type = _detect_type(text)
    down = _matches(DOWNSHIFT, text)
    up = _matches(UPSHIFT, text)
    axes = _score_axes(text, task_type)
    tier = _base_tier(axes, down, up)
    tier = _apply_optimize(tier, optimize_for, axes)
    calibration = None
    if scanner is not None and task_type != "security" and axes["risk"] != "high":
        verdict = scanner.calibration_for(scanner.load_outcomes(project), task_type, tier)
        if verdict is not None:
            direction, reason = verdict
            idx = TIER_ORDER.index(tier) + (1 if direction == "up" else -1)
            if 0 <= idx < len(TIER_ORDER):
                calibration = {"from": tier, "to": TIER_ORDER[idx], "reason": reason}
                tier = TIER_ORDER[idx]
    # Floor for security
    if task_type == "security" and TIER_ORDER.index(tier) < TIER_ORDER.index("L"):
        tier = "L"
    if task_type == "security" and (axes["ambiguity"] == "high" or "oauth" in text.lower()):
        tier = "XL"

    signals: list[str] = []
    if down:
        signals.append("downshift_keywords")
    if up:
        signals.append("upshift_keywords")
    for key, val in axes.items():
        if key != "type" and val == "high":
            signals.append(f"high_{key}")

    plan = {
        "task": text,
        "optimize_for": optimize_for,
        "axes": axes,
        "tier": tier,
        "effort": EFFORT[tier],
        "mode": _suggest_mode(tier, axes, optimize_for),
        "signals": signals,
        "adapter": adapter,
        "escalation": escalation_for(tier),
        "why": (
            f"type={axes['type']}, breadth={axes['breadth']}, "
            f"risk={axes['risk']}, ambiguity={axes['ambiguity']}"
        ),
    }
    if calibration is not None:
        went_up = TIER_ORDER.index(calibration["to"]) > TIER_ORDER.index(calibration["from"])
        plan["calibration"] = calibration
        plan["signals"].append("calibrated_up" if went_up else "calibrated_down")
    pays, why_not = _worker_pays_off(axes, tier, session_tier)
    if plan["mode"] == "single-worker" and not pays:
        plan["mode"] = "solo"
        plan["mode_reason"] = why_not
    plan["decision"], plan["decision_reason"] = decide_ask(
        tier, plan["mode"], session_tier, bool(prefs.get("always_accept"))
    )
    if session_tier is not None:
        plan["session_tier"] = session_tier
    if prefs:
        plan["preferences"] = prefs
    if project is not None:
        plan["project"], plan["alerts"] = project_context(project, adapter)
    return plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Classify a coding task into model/effort tiers (S/M/L/XL)."
    )
    parser.add_argument(
        "--task",
        "-t",
        help="Task text. If omitted, read stdin.",
    )
    parser.add_argument(
        "--optimize-for",
        choices=("cost", "balanced", "quality"),
        default=None,
        help="Bias tier selection (default: preference of the project, else balanced).",
    )
    parser.add_argument(
        "--session-tier",
        choices=TIER_ORDER,
        default=None,
        help="Tier of the model the session is on now; decides whether to ask or just continue.",
    )
    parser.add_argument(
        "--adapter",
        choices=("auto",) + ADAPTERS,
        default="auto",
        help="Host adapter id written to the plan (default: auto-detect from env, else generic).",
    )
    parser.add_argument(
        "--project",
        metavar="PATH",
        help="Project root: add size/structure profile and growth alerts (read-only).",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON.",
    )
    args = parser.parse_args(argv)

    # Windows pipes default to the ANSI codepage (cp1252), which crashes on many
    # non-ASCII task texts; utf-8-sig also drops the BOM PowerShell adds when piping.
    sys.stdin.reconfigure(encoding="utf-8-sig")
    sys.stdout.reconfigure(encoding="utf-8")

    task = args.task
    if task is None:
        task = sys.stdin.read()
    result = classify(
        task,
        optimize_for=args.optimize_for,
        adapter=args.adapter,
        project=args.project,
        session_tier=args.session_tier,
    )
    indent = 2 if args.pretty else None
    json.dump(result, sys.stdout, indent=indent, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
