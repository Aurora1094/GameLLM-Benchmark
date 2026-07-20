from __future__ import annotations

import ast
import hashlib
import importlib.metadata
import json
import math
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PACKAGE_ROOT / "config.json"

RUFF_SELECT = "E,W,F,I,N,UP,SIM,B,BLE,PERF,C90,PLR,PLE,PLW,RUF,TRY"
STRUCTURAL_CODES = {
    "C901",
    "PLR0904",
    "PLR0911",
    "PLR0912",
    "PLR0913",
    "PLR0914",
    "PLR0915",
    "PLR0916",
    "PLR0917",
}
RELIABILITY_SEVERE = {"F821", "F822", "F823", "B012"}
RELIABILITY_MODERATE = {
    "B006",
    "B008",
    "B023",
    "BLE001",
    "E722",
    "TRY201",
    "TRY203",
}
CONFORMANCE_PREFIXES = ("E", "W", "I", "N", "UP", "SIM")
CONFORMANCE_EXTRA = {"F401", "F841"}
HOT_LOOP_CALLS = {
    "open",
    "pygame.font.Font",
    "pygame.font.SysFont",
    "pygame.image.load",
    "pygame.mixer.Sound",
    "pygame.mixer.music.load",
}


def _json_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_d3_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema_version") != 2:
        raise ValueError("D3-v2 config schema_version must be 2")
    weights = value.get("weights", {})
    if sum(float(item) for item in weights.values()) != 100:
        raise ValueError("D3-v2 weights must sum to 100")
    return value


def _tool_versions(required: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    versions: dict[str, str] = {}
    errors: list[str] = []
    for package, expected in required.items():
        try:
            actual = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            actual = "not_installed"
        versions[package] = actual
        if actual != expected:
            errors.append(f"{package}: expected {expected}, found {actual}")
    return versions, errors


def _run_json_command(command: list[str], allowed_codes: set[int]) -> Any:
    env = dict(os.environ)
    env.setdefault("PYTHONUTF8", "1")
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        env=env,
    )
    if completed.returncode not in allowed_codes:
        raise RuntimeError(
            f"Command failed ({completed.returncode}): {' '.join(command)}\n"
            f"{completed.stderr[-1000:]}"
        )
    text = completed.stdout.strip()
    return json.loads(text) if text else []


def _ruff_findings(code_path: Path) -> list[dict[str, Any]]:
    raw = _run_json_command(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            str(code_path),
            "--output-format",
            "json",
            "--no-cache",
            "--isolated",
            "--select",
            RUFF_SELECT,
        ],
        {0, 1},
    )
    findings = []
    for item in raw:
        location = item.get("location", {})
        findings.append(
            {
                "code": item.get("code", ""),
                "message": item.get("message", ""),
                "line": location.get("row"),
                "column": location.get("column"),
                "url": item.get("url"),
            }
        )
    return findings


def _bandit_findings(code_path: Path) -> list[dict[str, Any]]:
    raw = _run_json_command(
        [sys.executable, "-m", "bandit", "-q", "-f", "json", str(code_path)],
        {0, 1},
    )
    findings = []
    for item in raw.get("results", []):
        findings.append(
            {
                "test_id": item.get("test_id"),
                "test_name": item.get("test_name"),
                "severity": str(item.get("issue_severity", "LOW")).upper(),
                "confidence": str(item.get("issue_confidence", "LOW")).upper(),
                "message": item.get("issue_text", ""),
                "line": item.get("line_number"),
            }
        )
    return findings


def _radon_metrics(source: str) -> dict[str, Any]:
    from radon.complexity import cc_rank, cc_visit
    from radon.metrics import mi_visit
    from radon.raw import analyze

    blocks = cc_visit(source)
    complexities = [int(block.complexity) for block in blocks]
    ranks = [cc_rank(value) for value in complexities]
    raw = analyze(source)
    return {
        "complexities": complexities,
        "ranks": ranks,
        "max_complexity": max(complexities, default=1),
        "mean_complexity": mean(complexities) if complexities else 1.0,
        "maintainability_index": float(mi_visit(source, multi=True)),
        "raw": {
            "loc": raw.loc,
            "lloc": raw.lloc,
            "sloc": raw.sloc,
            "comments": raw.comments,
            "blank": raw.blank,
        },
    }


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def _top_level_executable_count(tree: ast.Module) -> int:
    passive = (
        ast.Import,
        ast.ImportFrom,
        ast.Assign,
        ast.AnnAssign,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.ClassDef,
    )
    count = 0
    for node in tree.body:
        if isinstance(node, passive):
            continue
        if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
            rendered = ast.dump(node.test, include_attributes=False)
            if "__name__" in rendered and "__main__" in rendered:
                continue
        count += 1
    return count


def _has_main_guard(tree: ast.Module) -> bool:
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        rendered = ast.dump(node.test, include_attributes=False)
        if "__name__" in rendered and "__main__" in rendered:
            return True
    return False


def _import_safety_probe(code_path: Path) -> dict[str, Any]:
    wrapper = """
import importlib.util, os, sys
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
spec = importlib.util.spec_from_file_location('d3_v2_candidate', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print('__IMPORT_COMPLETED__', flush=True)
"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", wrapper, str(code_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=3,
            env={**os.environ, "SDL_VIDEODRIVER": "dummy", "PYGAME_HIDE_SUPPORT_PROMPT": "1"},
        )
        return {
            "safe": result.returncode == 0 and "__IMPORT_COMPLETED__" in result.stdout,
            "timed_out": False,
            "returncode": result.returncode,
            "stderr_tail": result.stderr[-500:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "safe": False,
            "timed_out": True,
            "returncode": None,
            "stderr_tail": (exc.stderr or "")[-500:] if isinstance(exc.stderr, str) else "",
        }


def _normalized_statement(node: ast.stmt) -> str:
    cloned = ast.dump(node, annotate_fields=True, include_attributes=False)
    return cloned


def _clone_metrics(tree: ast.Module) -> dict[str, Any]:
    windows: list[tuple[str, ...]] = []
    window_size = 6
    bodies: list[list[ast.stmt]] = [tree.body]
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bodies.append(node.body)
    for body in bodies:
        statements = [_normalized_statement(node) for node in body]
        for index in range(max(0, len(statements) - window_size + 1)):
            windows.append(tuple(statements[index : index + window_size]))
    counts = Counter(windows)
    groups = [count for count in counts.values() if count > 1]
    extra_occurrences = sum(count - 1 for count in groups)
    return {
        "method": "normalized_ast_statement_windows",
        "window_size": window_size,
        "window_count": len(windows),
        "clone_group_count": len(groups),
        "extra_occurrences": extra_occurrences,
    }


def _scan_policy_and_hot_loops(tree: ast.Module, config: dict[str, Any]) -> dict[str, Any]:
    forbidden_prefixes = tuple(config["security"]["forbidden_call_prefixes"])
    calls: list[dict[str, Any]] = []
    hot_loop_calls: list[dict[str, Any]] = []
    external_imports: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root != "pygame" and root not in sys.stdlib_module_names:
                    external_imports.append({"name": alias.name, "line": node.lineno})
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".", 1)[0]
            if root != "pygame" and root not in sys.stdlib_module_names:
                external_imports.append({"name": node.module, "line": node.lineno})
        elif isinstance(node, ast.Call):
            name = _call_name(node.func) or ""
            if any(name == prefix or name.startswith(prefix + ".") for prefix in forbidden_prefixes):
                calls.append({"name": name, "line": getattr(node, "lineno", None)})

    for loop in [node for node in ast.walk(tree) if isinstance(node, (ast.While, ast.For))]:
        for node in ast.walk(loop):
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node.func) or ""
            if name in HOT_LOOP_CALLS or any(
                name == prefix or name.startswith(prefix + ".") for prefix in forbidden_prefixes
            ):
                hot_loop_calls.append({"name": name, "line": getattr(node, "lineno", None)})

    unique_hot = list({(item["name"], item["line"]): item for item in hot_loop_calls}.values())
    return {
        "forbidden_calls": calls,
        "external_imports": external_imports,
        "hot_loop_calls": unique_hot,
    }


def _cc_factor(rank: str) -> float:
    return {"A": 1.0, "B": 0.8, "C": 0.5, "D": 0.25, "E": 0.0, "F": 0.0}[rank]


def _maintainability_score(
    radon: dict[str, Any],
    ruff: list[dict[str, Any]],
    clones: dict[str, Any],
    tree: ast.Module,
    import_probe: dict[str, Any],
) -> tuple[float, dict[str, Any]]:
    factors = [_cc_factor(rank) for rank in radon["ranks"]] or [1.0]
    # A single deeply complex routine can dominate the change risk of a small
    # game even when many trivial helpers keep the mean low.  Preserve a small
    # distribution component while weighting the worst observed rank.
    cc_score = 12 * (0.1 * mean(factors) + 0.9 * min(factors))
    structural = [item for item in ruff if item["code"] in STRUCTURAL_CODES]
    structural_score = max(0.0, 8.0 - 1.5 * len(structural))
    clone_score = max(0.0, 5.0 - clones["extra_occurrences"])
    main_guard = _has_main_guard(tree)
    top_level = _top_level_executable_count(tree)
    testability_score = (
        (2.0 if main_guard else 0.0)
        + (2.0 if import_probe["safe"] else 0.0)
        + (1.0 if top_level <= 3 else 0.0)
    )
    score = round(cc_score + structural_score + clone_score + testability_score, 3)
    return score, {
        "cyclomatic_score": round(cc_score, 3),
        "structural_score": structural_score,
        "clone_score": clone_score,
        "testability_score": testability_score,
        "structural_findings": structural,
        "has_main_guard": main_guard,
        "top_level_executable_count": top_level,
        "import_probe": import_probe,
        "clone_metrics": clones,
        "radon": radon,
    }


def _reliability_score(ruff: list[dict[str, Any]], tree: ast.Module) -> tuple[float, dict[str, Any]]:
    relevant: list[dict[str, Any]] = []
    deduction = 0.0
    for item in ruff:
        code = item["code"]
        points = 0.0
        if code in RELIABILITY_SEVERE:
            points = 5.0
        elif code in RELIABILITY_MODERATE:
            points = 2.0
        elif code.startswith(("B", "BLE", "PLE", "PLW", "TRY")):
            points = 1.0
        if points:
            relevant.append({**item, "deduction": points})
            deduction += points

    broad_handlers = 0
    swallowed_handlers = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if node.type is None or (
            isinstance(node.type, ast.Name) and node.type.id in {"Exception", "BaseException"}
        ):
            broad_handlers += 1
            if len(node.body) == 1 and isinstance(node.body[0], (ast.Pass, ast.Continue)):
                swallowed_handlers += 1
    ast_deduction = min(4.0, broad_handlers + swallowed_handlers * 2.0)
    score = max(0.0, 20.0 - deduction - ast_deduction)
    return round(score, 3), {
        "ruff_findings": relevant,
        "ruff_deduction": deduction,
        "broad_exception_handlers": broad_handlers,
        "swallowed_exception_handlers": swallowed_handlers,
        "ast_deduction": ast_deduction,
    }


def _security_score(
    bandit: list[dict[str, Any]], policy: dict[str, Any]
) -> tuple[float, bool, dict[str, Any]]:
    severity_weight = {"HIGH": 6.0, "MEDIUM": 3.0, "LOW": 1.0}
    confidence_factor = {"HIGH": 1.0, "MEDIUM": 0.75, "LOW": 0.5}
    weighted: list[dict[str, Any]] = []
    deduction = 0.0
    critical = bool(policy["forbidden_calls"] or policy["external_imports"])
    for item in bandit:
        points = severity_weight[item["severity"]] * confidence_factor[item["confidence"]]
        weighted.append({**item, "deduction": points})
        deduction += points
        if item["severity"] == "HIGH" and item["confidence"] == "HIGH":
            critical = True
    if policy["forbidden_calls"]:
        deduction += 15.0
    if policy["external_imports"]:
        deduction += 15.0
    score = max(0.0, 15.0 - deduction)
    return round(score, 3), critical, {
        "bandit_findings": weighted,
        "bandit_deduction": round(sum(item["deduction"] for item in weighted), 3),
        "forbidden_calls": policy["forbidden_calls"],
        "external_imports": policy["external_imports"],
        "critical_risk": critical,
    }


def _efficiency_score(
    ruff: list[dict[str, Any]], policy: dict[str, Any]
) -> tuple[float, dict[str, Any]]:
    perf = [item for item in ruff if item["code"].startswith("PERF")]
    perf_deduction = min(4.0, float(len(perf)))
    hot_deduction = min(6.0, 2.0 * len(policy["hot_loop_calls"]))
    score = max(0.0, 10.0 - perf_deduction - hot_deduction)
    return round(score, 3), {
        "ruff_perf_findings": perf,
        "ruff_deduction": perf_deduction,
        "hot_loop_calls": policy["hot_loop_calls"],
        "hot_loop_deduction": hot_deduction,
    }


def _conformance_score(
    ruff: list[dict[str, Any]], logical_lines: int
) -> tuple[float, dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    weighted_count = 0.0
    for item in ruff:
        code = item["code"]
        if code in CONFORMANCE_EXTRA or code.startswith(CONFORMANCE_PREFIXES):
            weight = 0.5 if code.startswith(("I", "UP", "SIM")) else 1.0
            findings.append({**item, "weight": weight})
            weighted_count += weight
    density = weighted_count * 100.0 / max(1, logical_lines)
    score = 10.0 * max(0.0, 1.0 - density / 10.0)
    return round(score, 3), {
        "findings": findings,
        "weighted_finding_count": weighted_count,
        "logical_lines": logical_lines,
        "weighted_findings_per_100_lloc": round(density, 3),
    }


def _incomplete_result(
    versions: dict[str, str], errors: list[str], config: dict[str, Any]
) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "status": "incomplete_tooling",
        "score": None,
        "score_normalized": None,
        "max_score": 85,
        "indicator_scores": {},
        "reason": "Required D3-v2 tools are missing or version-mismatched.",
        "tool_versions": versions,
        "tool_errors": errors,
        "config_sha256": _json_hash(config),
    }


def evaluate_d3_tools(
    code_path: Path | str,
    config_path: Path = CONFIG_PATH,
) -> dict[str, Any]:
    target = Path(code_path).resolve()
    config = load_d3_config(config_path)
    versions, errors = _tool_versions(config["required_tools"])
    if errors:
        return _incomplete_result(versions, errors, config)
    if not target.is_file():
        return {
            **_incomplete_result(versions, [f"Code file not found: {target}"], config),
            "status": "invalid_input",
        }

    source = target.read_text(encoding="utf-8-sig", errors="replace").lstrip("\ufeff")
    try:
        tree = ast.parse(source, filename=str(target))
    except SyntaxError as exc:
        return {
            **_incomplete_result(versions, [f"SyntaxError: {exc}"], config),
            "status": "invalid_input",
        }

    try:
        ruff = _ruff_findings(target)
        bandit = _bandit_findings(target)
        radon = _radon_metrics(source)
        clones = _clone_metrics(tree)
        import_probe = _import_safety_probe(target)
        policy = _scan_policy_and_hot_loops(tree, config)
    except Exception as exc:
        return _incomplete_result(versions, [f"{type(exc).__name__}: {exc}"], config)

    maintainability, maintainability_details = _maintainability_score(
        radon, ruff, clones, tree, import_probe
    )
    reliability, reliability_details = _reliability_score(ruff, tree)
    security, critical_risk, security_details = _security_score(bandit, policy)
    efficiency, efficiency_details = _efficiency_score(ruff, policy)
    conformance, conformance_details = _conformance_score(ruff, radon["raw"]["lloc"])
    indicators = {
        "maintainability": maintainability,
        "reliability": reliability,
        "security": security,
        "efficiency": efficiency,
        "conformance": conformance,
    }
    score = round(sum(indicators.values()), 3)
    return {
        "schema_version": 2,
        "status": "completed",
        "method": config["method"],
        "score": score,
        "score_normalized": score / 85.0,
        "max_score": 85,
        "indicator_scores": indicators,
        "critical_security_risk": critical_risk,
        "critical_total_cap": config["security"]["critical_total_cap"],
        "reason": "D3-v2 deterministic tool evaluation completed.",
        "tool_versions": versions,
        "config_sha256": _json_hash(config),
        "details": {
            "maintainability": maintainability_details,
            "reliability": reliability_details,
            "security": security_details,
            "efficiency": efficiency_details,
            "conformance": conformance_details,
            "ruff_all_findings": ruff,
        },
    }
