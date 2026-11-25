#!/usr/bin/env python3
"""Emit or validate an orchestration plan for model-orchestrate-agent.

Stdlib only. Validates against assets/plan.schema.json (subset checker).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
SCHEMA_PATH = SKILL_ROOT / "assets" / "plan.schema.json"

TIER_EFFORT = {"S": "low", "M": "medium", "L": "high", "XL": "max"}
VALID_TIERS = frozenset(TIER_EFFORT)
VALID_EFFORT = frozenset(TIER_EFFORT.values())  # low | medium | high | max
VALID_MODE = frozenset({"solo", "single-worker", "fan-out"})
VALID_OPT = frozenset({"cost", "balanced", "quality"})
VALID_ADAPTER = frozenset(
    {
        "claude-code",
        "claude-ai",
        "github-copilot",
        "codex",
        "cursor",
        "opencode",
        "generic",
    }
)
WORKER_KEYS = frozenset({"role", "goal", "tier", "write_paths"})


def _load_schema() -> dict[str, Any]:
    with SCHEMA_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def validate_plan(plan: dict[str, Any]) -> list[str]:
    """Lightweight validation mirroring plan.schema.json required fields/enums."""
    errors: list[str] = []
    required = (
        "tier",
        "effort",
        "mode",
        "optimize_for",
        "why",
        "adapter",
        "escalation",
    )
    for key in required:
        if key not in plan:
            errors.append(f"missing required field: {key}")

    if "tier" in plan and plan["tier"] not in VALID_TIERS:
        errors.append(f"invalid tier: {plan['tier']!r}")
    if "effort" in plan and plan["effort"] not in VALID_EFFORT:
        errors.append(f"invalid effort: {plan['effort']!r}")
    if "mode" in plan and plan["mode"] not in VALID_MODE:
        errors.append(f"invalid mode: {plan['mode']!r}")
    if "optimize_for" in plan and plan["optimize_for"] not in VALID_OPT:
        errors.append(f"invalid optimize_for: {plan['optimize_for']!r}")
    if "adapter" in plan and plan["adapter"] not in VALID_ADAPTER:
        errors.append(f"invalid adapter: {plan['adapter']!r}")
    if "why" in plan and (not isinstance(plan["why"], str) or not plan["why"].strip()):
        errors.append("why must be a non-empty string")
    if "escalation" in plan and not isinstance(plan.get("escalation"), str):
        errors.append("escalation must be a string")
    if "task" in plan and not isinstance(plan["task"], str):
        errors.append("task must be a string")

    signals = plan.get("signals")
    if signals is not None and (
        not isinstance(signals, list) or not all(isinstance(s, str) for s in signals)
    ):
        errors.append("signals must be an array of strings")

    axes = plan.get("axes")
    if axes is not None and (
        not isinstance(axes, dict) or not all(isinstance(v, str) for v in axes.values())
    ):
        errors.append("axes must be an object of string values")

    if "decision" in plan and plan["decision"] not in ("inline", "ask", "auto"):
        errors.append(f"invalid decision: {plan['decision']!r}")
    if "session_tier" in plan and plan["session_tier"] not in VALID_TIERS:
        errors.append(f"invalid session_tier: {plan['session_tier']!r}")
    if "preferences" in plan and not isinstance(plan["preferences"], dict):
        errors.append("preferences must be an object")
    cal = plan.get("calibration")
    if cal is not None and (
        not isinstance(cal, dict)
        or cal.get("from") not in VALID_TIERS
        or cal.get("to") not in VALID_TIERS
        or not isinstance(cal.get("reason"), str)
    ):
        errors.append("calibration must be {from, to, reason} with valid tiers")
    if "mode_reason" in plan and not isinstance(plan["mode_reason"], str):
        errors.append("mode_reason must be a string")
    if "project" in plan and not isinstance(plan["project"], dict):
        errors.append("project must be an object")
    alerts = plan.get("alerts")
    if alerts is not None and (
        not isinstance(alerts, list) or not all(isinstance(a, str) for a in alerts)
    ):
        errors.append("alerts must be an array of strings")

    workers = plan.get("workers")
    if workers is not None:
        if not isinstance(workers, list):
            errors.append("workers must be an array")
        else:
            for i, w in enumerate(workers):
                if not isinstance(w, dict):
                    errors.append(f"workers[{i}] must be an object")
                    continue
                if "role" not in w or "goal" not in w:
                    errors.append(f"workers[{i}] requires role and goal")
                for key in ("role", "goal"):
                    if key in w and not isinstance(w[key], str):
                        errors.append(f"workers[{i}].{key} must be a string")
                if "tier" in w and w["tier"] not in VALID_TIERS:
                    errors.append(f"workers[{i}].tier invalid: {w['tier']!r}")
                paths = w.get("write_paths")
                if paths is not None and (
                    not isinstance(paths, list) or not all(isinstance(p, str) for p in paths)
                ):
                    errors.append(f"workers[{i}].write_paths must be an array of strings")
                for key in w:
                    if key not in WORKER_KEYS:
                        errors.append(f"workers[{i}] unknown field: {key}")

    # Reject unknown top-level keys beyond schema properties
    allowed = {
        "task",
        "tier",
        "effort",
        "mode",
        "optimize_for",
        "why",
        "adapter",
        "escalation",
        "workers",
        "signals",
        "axes",
        "project",
        "alerts",
        "decision",
        "decision_reason",
        "session_tier",
        "preferences",
        "calibration",
        "mode_reason",
    }
    for key in plan:
        if key not in allowed:
            errors.append(f"unknown field: {key}")

    return errors


def build_plan(
    *,
    task: str,
    tier: str,
    adapter: str,
    optimize_for: str,
    mode: str | None,
    why: str | None,
    effort: str | None,
    escalation: str | None,
) -> dict[str, Any]:
    if tier not in VALID_TIERS:
        raise SystemExit(f"error: invalid --tier {tier!r}")
    if adapter not in VALID_ADAPTER:
        raise SystemExit(f"error: invalid --adapter {adapter!r}")
    if optimize_for not in VALID_OPT:
        raise SystemExit(f"error: invalid --optimize-for {optimize_for!r}")

    resolved_effort = effort or TIER_EFFORT[tier]
    if resolved_effort not in VALID_EFFORT:
        raise SystemExit(f"error: invalid --effort {resolved_effort!r}")

    if mode is None:
        mode = "solo" if tier in {"S", "M"} else "single-worker"
    if mode not in VALID_MODE:
        raise SystemExit(f"error: invalid --mode {mode!r}")

    order = ("S", "M", "L", "XL")
    default_escalation = (
        "top tier: if quality fails, re-plan with the failure evidence or ask the user"
        if tier == "XL"
        else f"if quality fails -> {order[order.index(tier) + 1]}"
    )
    plan: dict[str, Any] = {
        "task": task,
        "tier": tier,
        "effort": resolved_effort,
        "mode": mode,
        "optimize_for": optimize_for,
        "why": why or f"tier {tier} for task",
        "adapter": adapter,
        "escalation": escalation or default_escalation,
    }
    return plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Emit or validate a model-orchestrate-agent plan JSON."
    )
    parser.add_argument("--task", "-t", help="Task summary for a new plan.")
    parser.add_argument(
        "--tier",
        choices=sorted(VALID_TIERS),
        help="Capability tier (required unless --stdin / --validate-only).",
    )
    parser.add_argument(
        "--adapter",
        default="generic",
        choices=sorted(VALID_ADAPTER),
        help="Host adapter id (default: generic).",
    )
    parser.add_argument(
        "--optimize-for",
        default="balanced",
        choices=sorted(VALID_OPT),
        help="Optimization bias (default: balanced).",
    )
    parser.add_argument(
        "--mode",
        choices=sorted(VALID_MODE),
        help="Execution mode (default from tier).",
    )
    parser.add_argument("--effort", choices=sorted(VALID_EFFORT), help="Override effort.")
    parser.add_argument("--why", help="One-line rationale.")
    parser.add_argument("--escalation", help="Escalation rule string.")
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read an existing plan JSON from stdin and validate it.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Alias for --stdin (validate stdin plan).",
    )
    parser.add_argument(
        "--schema",
        action="store_true",
        help="Print the path to plan.schema.json and exit.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    args = parser.parse_args(argv)

    # Windows pipes default to the ANSI codepage (cp1252), which crashes on many
    # non-ASCII task texts; utf-8-sig also drops the BOM PowerShell adds when piping.
    sys.stdin.reconfigure(encoding="utf-8-sig")
    sys.stdout.reconfigure(encoding="utf-8")

    if args.schema:
        print(SCHEMA_PATH)
        # Touch-load to ensure file exists
        _load_schema()
        return 0

    if args.stdin or args.validate_only:
        raw = sys.stdin.read()
        try:
            plan = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"error: invalid JSON: {exc}", file=sys.stderr)
            return 2
        if not isinstance(plan, dict):
            print("error: plan must be a JSON object", file=sys.stderr)
            return 2
        errors = validate_plan(plan)
        if errors:
            for err in errors:
                print(f"error: {err}", file=sys.stderr)
            return 1
        indent = 2 if args.pretty else None
        json.dump(plan, sys.stdout, indent=indent, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0

    if not args.task or not args.tier:
        parser.error("--task and --tier are required unless --stdin / --schema")

    plan = build_plan(
        task=args.task,
        tier=args.tier,
        adapter=args.adapter,
        optimize_for=args.optimize_for,
        mode=args.mode,
        why=args.why,
        effort=args.effort,
        escalation=args.escalation,
    )
    errors = validate_plan(plan)
    if errors:
        for err in errors:
            print(f"error: {err}", file=sys.stderr)
        return 1

    indent = 2 if args.pretty else None
    json.dump(plan, sys.stdout, indent=indent, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
