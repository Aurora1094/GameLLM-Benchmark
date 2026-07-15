from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEMO_ROOT = Path(__file__).resolve().parent
REPO_ROOT = DEMO_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluator.dimension1.dimension1_executable import INDICATOR_ORDER, evaluate_dimension1
from evaluator.dimension3.dimension3_code_quality import evaluate_dimension3_code_quality


D3_LABELS = {
    "complexity": "复杂度控制",
    "reuse": "代码复用",
    "constants": "常量使用",
    "naming": "命名规范",
    "modularity": "模块划分",
    "comments": "注释质量",
}
D1_STEP_ORDER = [key for key, _ in INDICATOR_ORDER]
D1_EVALUATOR = REPO_ROOT / "evaluator" / "dimension1" / "dimension1_executable.py"
D3_EVALUATOR = REPO_ROOT / "evaluator" / "dimension3" / "dimension3_code_quality.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the deterministic D1/D3 scoring contract.")
    parser.add_argument("--check", action="store_true", help="Exit non-zero when an expectation fails.")
    parser.add_argument("--repeat", type=int, default=1, help="Number of complete repeated evaluations.")
    parser.add_argument("--runtime-sec", type=int, default=3, help="D1 subprocess timeout per probe.")
    parser.add_argument("--output", type=Path, default=DEMO_ROOT / "results", help="Result directory.")
    return parser.parse_args()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def value_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def relative_path(path: Path, root: Path = REPO_ROOT) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


def git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        timeout=10,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def validate_case_ids(cases: list[dict[str, Any]], section: str) -> None:
    ids = [case.get("id") for case in cases]
    files = [case.get("file") for case in cases]
    if any(not isinstance(value, str) or not value for value in ids + files):
        raise ValueError(f"{section} cases require non-empty string id and file fields")
    if len(ids) != len(set(ids)):
        raise ValueError(f"{section} contains duplicate case ids")
    if len(files) != len(set(files)):
        raise ValueError(f"{section} contains duplicate fixture files")


def fixture_path(section: str, filename: str) -> Path:
    path = (DEMO_ROOT / "fixtures" / section / filename).resolve()
    fixture_root = (DEMO_ROOT / "fixtures" / section).resolve()
    if not path.is_relative_to(fixture_root):
        raise ValueError(f"Fixture escapes {fixture_root}: {filename}")
    if not path.is_file():
        raise FileNotFoundError(f"Missing fixture: {path}")
    return path


def load_expectations() -> dict[str, Any]:
    path = DEMO_ROOT / "expectations.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema_version") != 2:
        raise ValueError("expectations.json schema_version must be 2")
    if value.get("calibration_method") != "known_groups":
        raise ValueError("calibration_method must be known_groups")

    d1 = value.get("d1", {})
    d1_cases = d1.get("cases")
    if not isinstance(d1_cases, list) or not d1_cases:
        raise ValueError("d1.cases must be a non-empty list")
    validate_case_ids(d1_cases, "d1")
    if d1.get("step_order") != D1_STEP_ORDER:
        raise ValueError("D1 expectation order does not match the production evaluator")
    expected_levels = []
    for case in d1_cases:
        expected = case.get("expected_pipeline_steps")
        signature = case.get("expected_indicators")
        if not isinstance(expected, int) or not 0 <= expected <= len(D1_STEP_ORDER):
            raise ValueError(f"Invalid D1 expected level for {case['id']}")
        if not isinstance(signature, list) or len(signature) != len(D1_STEP_ORDER):
            raise ValueError(f"Invalid D1 indicator signature for {case['id']}")
        if any(value not in (0, 1) for value in signature):
            raise ValueError(f"D1 indicator signatures must be binary: {case['id']}")
        if not isinstance(case.get("expected_diagnosis"), str):
            raise ValueError(f"Missing D1 diagnosis for {case['id']}")
        fixture_path("d1", case["file"])
        expected_levels.append(expected)
    if expected_levels != list(range(len(D1_STEP_ORDER) + 1)):
        raise ValueError("D1 cases must preregister the ordered levels 0 through 6")

    d3 = value.get("d3", {})
    d3_cases = d3.get("cases")
    if not isinstance(d3_cases, list) or not d3_cases:
        raise ValueError("d3.cases must be a non-empty list")
    validate_case_ids(d3_cases, "d3")
    baseline_id = d3.get("baseline")
    by_id = {case["id"]: case for case in d3_cases}
    if baseline_id not in by_id or by_id[baseline_id].get("target_indicator") is not None:
        raise ValueError("D3 baseline must exist and have a null target_indicator")
    targets = []
    for case in d3_cases:
        target = case.get("target_indicator")
        if case["id"] != baseline_id:
            if target not in D3_LABELS:
                raise ValueError(f"Invalid D3 target for {case['id']}: {target}")
            targets.append(target)
        fixture_path("d3", case["file"])
    if set(targets) != set(D3_LABELS) or len(targets) != len(D3_LABELS):
        raise ValueError("D3 cases must contain exactly one targeted defect per indicator")
    return value


def preflight_pygame() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import pygame"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pygame preflight failed: {result.stderr.strip()}")


def compact_d1(result: dict[str, Any]) -> dict[str, Any]:
    runtime = result.get("runtime", {})
    stability = runtime.get("stability_probe") or {}
    quit_probe = runtime.get("quit_probe") or {}
    return {
        "score": result.get("score", 0.0),
        "raw_pass_count": result.get("raw_pass_count", 0),
        "pipeline_steps_passed": result.get("pipeline_steps_passed", 0),
        "gate_pass": bool(result.get("gate_pass", False)),
        "indicators": result.get("indicators", {}),
        "diagnosis": runtime.get("diagnosis", "not_run"),
        "reason": result.get("reason", ""),
        "evidence": {
            "pygame_import_ok": bool(runtime.get("pygame_import_ok", False)),
            "window_created": bool(stability.get("window_created", False)),
            "surface_returned": bool(stability.get("surface_returned", False)),
            "event_fetch_seen": bool(stability.get("event_fetch_seen", False)),
            "stability_timed_out": bool(stability.get("timed_out", False)),
            "quit_posted": bool(quit_probe.get("quit_posted", False)),
            "quit_returncode": quit_probe.get("returncode"),
            "quit_timed_out": bool(quit_probe.get("timed_out", False)),
        },
    }


def compact_d3(result: dict[str, Any]) -> dict[str, Any]:
    details = result.get("details", {})
    return {
        "score": result.get("score", 0),
        "score_normalized": result.get("score_normalized", 0.0),
        "reason": result.get("reason", ""),
        "indicator_scores": result.get("indicator_scores", {}),
        "category_scores": result.get("category_scores", {}),
        "evidence": {
            "complexity": details.get("indicator_1_complexity", {}),
            "reuse": details.get("indicator_2_reuse", {}),
            "constants": details.get("indicator_3_constants", {}),
            "naming": details.get("indicator_4_naming", {}),
            "modularity": details.get("indicator_5_modularity", {}),
            "comments": details.get("indicator_6_comments", {}),
        },
    }


def evaluate_once(runtime_sec: int, expectations: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, dict[str, Any]] = {"d1": {}, "d3": {}}
    raw: dict[str, dict[str, Any]] = {"d1": {}, "d3": {}}

    for case in expectations["d1"]["cases"]:
        result = evaluate_dimension1(fixture_path("d1", case["file"]), runtime_sec=runtime_sec)
        compact["d1"][case["id"]] = compact_d1(result)
        raw["d1"][case["id"]] = result

    for case in expectations["d3"]["cases"]:
        path = fixture_path("d3", case["file"])
        d1_result = evaluate_dimension1(path, runtime_sec=runtime_sec)
        d3_result = evaluate_dimension3_code_quality(path)
        compact["d3"][case["id"]] = {
            "d1": compact_d1(d1_result),
            "d3": compact_d3(d3_result),
        }
        raw["d3"][case["id"]] = {"d1": d1_result, "d3": d3_result}
    return {"compact": compact, "raw": raw}


def add_assertion(assertions: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    assertions.append({"name": name, "passed": bool(passed), "detail": detail})


def validate_results(
    first_run: dict[str, Any],
    compact_runs: list[dict[str, Any]],
    expectations: dict[str, Any],
    evaluator_hashes_before: dict[str, str],
    evaluator_hashes_after: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    assertions: list[dict[str, Any]] = []
    d1_cases = expectations["d1"]["cases"]

    for case in d1_cases:
        actual = first_run["d1"][case["id"]]
        expected_steps = case["expected_pipeline_steps"]
        expected_score = expected_steps / len(D1_STEP_ORDER)
        expected_gate = expected_steps == len(D1_STEP_ORDER)
        level_passed = (
            actual["pipeline_steps_passed"] == expected_steps
            and math.isclose(actual["score"], expected_score)
            and actual["gate_pass"] == expected_gate
        )
        add_assertion(
            assertions,
            f"D1 {case['id']} ordered level",
            level_passed,
            f"expected steps={expected_steps}, score={expected_score:.3f}, gate={expected_gate}; "
            f"actual steps={actual['pipeline_steps_passed']}, score={actual['score']:.3f}, gate={actual['gate_pass']}",
        )
        expected_indicators = dict(zip(D1_STEP_ORDER, case["expected_indicators"], strict=True))
        signature_passed = (
            actual["indicators"] == expected_indicators
            and actual["diagnosis"] == case["expected_diagnosis"]
        )
        add_assertion(
            assertions,
            f"D1 {case['id']} evidence signature",
            signature_passed,
            f"expected indicators={case['expected_indicators']}, diagnosis={case['expected_diagnosis']}; "
            f"actual indicators={[actual['indicators'][key] for key in D1_STEP_ORDER]}, diagnosis={actual['diagnosis']}",
        )

    d3_cases = expectations["d3"]["cases"]
    baseline_id = expectations["d3"]["baseline"]
    baseline = first_run["d3"][baseline_id]["d3"]
    baseline_scores = baseline["indicator_scores"]
    sensitivity: dict[str, Any] = {}
    target_drops: list[float] = []
    non_target_abs_drops: list[float] = []
    target_hits = 0

    for case in d3_cases:
        target = case["target_indicator"]
        if target is None:
            continue
        variant_result = first_run["d3"][case["id"]]
        scores = variant_result["d3"]["indicator_scores"]
        drops = {key: baseline_scores[key] - scores[key] for key in D3_LABELS}
        target_drop = drops[target]
        max_drop = max(drops.values())
        non_target = [abs(drop) for key, drop in drops.items() if key != target]
        total_drop = baseline["score"] - variant_result["d3"]["score"]
        passed = (
            variant_result["d1"]["gate_pass"]
            and target_drop > 0
            and total_drop > 0
            and target_drop == max_drop
        )
        if passed:
            target_hits += 1
        target_drops.append(target_drop)
        non_target_abs_drops.extend(non_target)
        sensitivity[case["id"]] = {
            "target": target,
            "target_drop": target_drop,
            "total_drop": total_drop,
            "indicator_drops": drops,
            "mean_non_target_absolute_drop": sum(non_target) / len(non_target),
            "target_to_non_target_ratio": (
                target_drop / (sum(non_target) / len(non_target)) if sum(non_target) else None
            ),
            "passed": passed,
        }
        add_assertion(
            assertions,
            f"D3 {case['id']} -> {target}",
            passed,
            f"D1 gate={variant_result['d1']['gate_pass']}; target drop={target_drop}; "
            f"max drop={max_drop}; total drop={total_drop}; non-target absolute drift={sum(non_target)}",
        )

    all_d3_gate = all(result["d1"]["gate_pass"] for result in first_run["d3"].values())
    add_assertion(assertions, "D3 fixtures preserve D1 gate", all_d3_gate, f"all_gate_pass={all_d3_gate}")

    d1_gate_count = sum(result["gate_pass"] for result in first_run["d1"].values())
    complete_case_id = next(
        case["id"]
        for case in d1_cases
        if case["expected_pipeline_steps"] == len(D1_STEP_ORDER)
    )
    add_assertion(
        assertions,
        "D1 gate opens only for the complete reference case",
        d1_gate_count == 1 and first_run["d1"][complete_case_id]["gate_pass"],
        f"gate_open_case_count={d1_gate_count}; expected_case={complete_case_id}",
    )

    defect_scores = [
        first_run["d3"][case["id"]]["d3"]["score"]
        for case in d3_cases
        if case["target_indicator"] is not None
    ]
    known_group_separation = bool(defect_scores) and baseline["score"] > max(defect_scores)
    add_assertion(
        assertions,
        "D3 baseline separates from all targeted defects",
        known_group_separation,
        f"baseline={baseline['score']}; highest_targeted_defect={max(defect_scores)}",
    )

    run_digests = [value_sha256(run) for run in compact_runs]
    deterministic = len(set(run_digests)) == 1
    add_assertion(
        assertions,
        "Repeated evaluations are deterministic",
        deterministic,
        f"repeat_count={len(compact_runs)}; full_compact_result_digests_identical={deterministic}",
    )

    evaluator_unchanged = evaluator_hashes_before == evaluator_hashes_after
    add_assertion(
        assertions,
        "Production evaluators remain unchanged during calibration",
        evaluator_unchanged,
        f"hashes_before={evaluator_hashes_before}; hashes_after={evaluator_hashes_after}",
    )

    target_mean = sum(target_drops) / len(target_drops)
    non_target_mean = sum(non_target_abs_drops) / len(non_target_abs_drops)
    discriminant_signal = target_mean > non_target_mean
    add_assertion(
        assertions,
        "D3 target signal exceeds non-target drift",
        discriminant_signal,
        f"mean_target_drop={target_mean:.3f}; mean_non_target_absolute_drop={non_target_mean:.3f}",
    )
    calibration = {
        "method": "known_groups",
        "d1_staircase_exact": all(
            first_run["d1"][case["id"]]["pipeline_steps_passed"] == case["expected_pipeline_steps"]
            for case in d1_cases
        ),
        "d1_gate_open_case_count": sum(result["gate_pass"] for result in first_run["d1"].values()),
        "d3_target_case_count": len(target_drops),
        "d3_target_hits": target_hits,
        "d3_target_hit_rate": target_hits / len(target_drops),
        "d3_baseline_score": baseline["score"],
        "d3_highest_defect_score": max(defect_scores),
        "d3_known_group_margin": baseline["score"] - max(defect_scores),
        "d3_mean_target_drop": target_mean,
        "d3_mean_non_target_absolute_drop": non_target_mean,
        "d3_target_to_non_target_signal_ratio": target_mean / non_target_mean if non_target_mean else None,
        "repeat_result_sha256": run_digests,
        "repeat_results_identical": deterministic,
    }
    return assertions, sensitivity, calibration


def build_provenance(expectations: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    evaluator_files = {"d1": D1_EVALUATOR, "d3": D3_EVALUATOR}
    fixture_files = {
        f"d1/{case['id']}": fixture_path("d1", case["file"])
        for case in expectations["d1"]["cases"]
    }
    fixture_files.update(
        {
            f"d3/{case['id']}": fixture_path("d3", case["file"])
            for case in expectations["d3"]["cases"]
        }
    )
    reference_name = expectations.get("reference", {}).get("archive", "")
    reference_path = REPO_ROOT / reference_name if reference_name else None
    reference = {
        "archive": reference_name,
        "exists": bool(reference_path and reference_path.is_file()),
        "sha256": file_sha256(reference_path) if reference_path and reference_path.is_file() else None,
        "size_bytes": reference_path.stat().st_size if reference_path and reference_path.is_file() else None,
        "adopted_patterns": expectations.get("reference", {}).get("adopted_patterns", []),
        "code_imported": bool(expectations.get("reference", {}).get("code_imported", False)),
    }
    return {
        "git_commit": git_commit(),
        "command": [sys.executable, *sys.argv],
        "environment": {
            "python": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "pygame": package_version("pygame"),
            "radon": package_version("radon"),
        },
        "configuration": {
            "repeat": args.repeat,
            "runtime_sec": args.runtime_sec,
            "sdl_video_driver": "dummy (set by D1 subprocess harness)",
        },
        "evaluator_files": {
            name: {"path": relative_path(path), "sha256": file_sha256(path)}
            for name, path in evaluator_files.items()
        },
        "fixture_files": {
            name: {"path": relative_path(path), "sha256": file_sha256(path)}
            for name, path in fixture_files.items()
        },
        "expectations": {
            "path": relative_path(DEMO_ROOT / "expectations.json"),
            "sha256": file_sha256(DEMO_ROOT / "expectations.json"),
            "schema_version": expectations["schema_version"],
        },
        "design_reference": reference,
        "llm": {"used": False, "model_calls": 0, "estimated_api_cost": 0},
    }


def write_case_evidence(
    output_dir: Path,
    expectations: dict[str, Any],
    compact: dict[str, Any],
    raw: dict[str, Any],
    provenance: dict[str, Any],
) -> list[str]:
    written: list[str] = []
    for section in ("d1", "d3"):
        case_dir = output_dir / "cases" / section
        case_dir.mkdir(parents=True, exist_ok=True)
        evaluator_key = section
        for case in expectations[section]["cases"]:
            path = fixture_path(section, case["file"])
            record = {
                "format_version": 1,
                "calibration_method": expectations["calibration_method"],
                "case": case,
                "fixture": {"path": relative_path(path), "sha256": file_sha256(path)},
                "evaluator": provenance["evaluator_files"][evaluator_key],
                "compact_result": compact[section][case["id"]],
                "raw_result": raw[section][case["id"]],
            }
            destination = case_dir / f"{case['id']}.json"
            destination.write_text(
                json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            written.append(destination.relative_to(output_dir).as_posix())
    return written


def write_d1_csv(path: Path, results: dict[str, Any], expectations: dict[str, Any]) -> None:
    fields = [
        "case_id",
        "fixture",
        "expected_steps",
        "actual_steps",
        "raw_pass_count",
        "score",
        "gate_pass",
        "diagnosis",
        "indicator_signature",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for case in expectations["d1"]["cases"]:
            result = results[case["id"]]
            writer.writerow(
                {
                    "case_id": case["id"],
                    "fixture": case["file"],
                    "expected_steps": case["expected_pipeline_steps"],
                    "actual_steps": result["pipeline_steps_passed"],
                    "raw_pass_count": result["raw_pass_count"],
                    "score": f"{result['score']:.6f}",
                    "gate_pass": result["gate_pass"],
                    "diagnosis": result["diagnosis"],
                    "indicator_signature": "".join(str(result["indicators"][key]) for key in D1_STEP_ORDER),
                }
            )


def write_d3_csv(
    path: Path,
    results: dict[str, Any],
    expectations: dict[str, Any],
    sensitivity: dict[str, Any],
) -> None:
    fields = [
        "case_id",
        "fixture",
        "target",
        "d1_steps",
        "d1_gate",
        "total",
        *D3_LABELS,
        "target_drop",
        "mean_non_target_absolute_drop",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for case in expectations["d3"]["cases"]:
            result = results[case["id"]]
            target = case["target_indicator"]
            row = {
                "case_id": case["id"],
                "fixture": case["file"],
                "target": target or "baseline",
                "d1_steps": result["d1"]["pipeline_steps_passed"],
                "d1_gate": result["d1"]["gate_pass"],
                "total": result["d3"]["score"],
                "target_drop": sensitivity.get(case["id"], {}).get("target_drop", ""),
                "mean_non_target_absolute_drop": sensitivity.get(case["id"], {}).get(
                    "mean_non_target_absolute_drop", ""
                ),
            }
            row.update(result["d3"]["indicator_scores"])
            writer.writerow(row)


def latex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "_": r"\_",
        "%": r"\%",
        "&": r"\&",
        "#": r"\#",
        "{": r"\{",
        "}": r"\}",
    }
    return "".join(replacements.get(char, char) for char in value)


def write_tex_tables(
    output_dir: Path,
    first_run: dict[str, Any],
    expectations: dict[str, Any],
    sensitivity: dict[str, Any],
    calibration: dict[str, Any],
    provenance: dict[str, Any],
) -> None:
    generated = output_dir / "generated"
    generated.mkdir(parents=True, exist_ok=True)

    ratio = calibration["d3_target_to_non_target_signal_ratio"]
    metric_commands = "\n".join(
        [
            rf"\newcommand{{\DThreeTargetMean}}{{{calibration['d3_mean_target_drop']:.3f}}}",
            rf"\newcommand{{\DThreeNonTargetMean}}{{{calibration['d3_mean_non_target_absolute_drop']:.3f}}}",
            rf"\newcommand{{\DThreeSignalRatio}}{{{ratio:.2f}}}",
            rf"\newcommand{{\DThreeBaselineScore}}{{{calibration['d3_baseline_score']:g}}}",
            rf"\newcommand{{\DThreeHighestDefectScore}}{{{calibration['d3_highest_defect_score']:g}}}",
            "",
        ]
    )
    (generated / "calibration_metrics.tex").write_text(metric_commands, encoding="utf-8")

    d1_lines = []
    for case in expectations["d1"]["cases"]:
        result = first_run["d1"][case["id"]]
        d1_lines.append(
            f"{latex_escape(case['file'])} & {case['expected_pipeline_steps']} & "
            f"{result['pipeline_steps_passed']} & {result['raw_pass_count']} & "
            f"{result['score']:.3f} & {'通过' if result['gate_pass'] else '关闭'} \\\\"
        )
    d1_table = "\n".join(
        [
            r"\begin{table}[htbp]",
            r"\centering",
            r"\caption{D1 0--6 级受控样例结果}",
            r"\small",
            r"\begin{tabular}{L{5.4cm} C{1.2cm} C{1.2cm} C{1.35cm} C{1.4cm} C{1.2cm}}",
            r"\toprule",
            r"样例 & 预期级 & 实际级 & 原始通过 & D1 分数 & 闸门 \\",
            r"\midrule",
            *d1_lines,
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
            "",
        ]
    )
    (generated / "d1_table.tex").write_text(d1_table, encoding="utf-8")

    design_lines = []
    for case in expectations["d3"]["cases"]:
        target = case["target_indicator"]
        design_lines.append(
            f"{latex_escape(case['id'])} & {latex_escape(D3_LABELS.get(target, '参考组'))} & "
            f"{latex_escape(case['intervention'])} \\\\"
        )
    design_table = "\n".join(
        [
            r"\begin{table}[htbp]",
            r"\centering",
            r"\caption{D3 known-groups 校准样例设计}",
            r"\small",
            r"\begin{tabularx}{\textwidth}{L{3.5cm} L{2.6cm} X}",
            r"\toprule",
            r"样例 & 预注册目标 & 受控干预 \\",
            r"\midrule",
            *design_lines,
            r"\bottomrule",
            r"\end{tabularx}",
            r"\end{table}",
            "",
        ]
    )
    (generated / "d3_design_table.tex").write_text(design_table, encoding="utf-8")

    d3_lines = []
    for case in expectations["d3"]["cases"]:
        result = first_run["d3"][case["id"]]
        scores = result["d3"]["indicator_scores"]
        target = case["target_indicator"]
        d3_lines.append(
            f"{latex_escape(case['id'])} & {latex_escape(D3_LABELS.get(target, '基线'))} & "
            f"{scores['complexity']} & {scores['reuse']} & {scores['constants']} & "
            f"{scores['naming']} & {scores['modularity']} & {scores['comments']} & "
            f"{result['d3']['score']} \\\\"
        )
    d3_table = "\n".join(
        [
            r"\begin{table}[htbp]",
            r"\centering",
            r"\caption{Pong 基线与六类受控退化的 D3 分数}",
            r"\scriptsize",
            r"\resizebox{\textwidth}{!}{%",
            r"\begin{tabular}{l l c c c c c c c}",
            r"\toprule",
            r"样例 & 目标 & 复杂度 & 复用 & 常量 & 命名 & 模块 & 注释 & 总分 \\",
            r"\midrule",
            *d3_lines,
            r"\bottomrule",
            r"\end{tabular}}",
            r"\end{table}",
            "",
        ]
    )
    (generated / "d3_table.tex").write_text(d3_table, encoding="utf-8")

    delta_lines = []
    for case in expectations["d3"]["cases"]:
        target = case["target_indicator"]
        if target is None:
            continue
        item = sensitivity[case["id"]]
        cells = []
        for indicator in D3_LABELS:
            value = item["indicator_drops"][indicator]
            rendered = f"{value:g}"
            cells.append(rf"\textbf{{{rendered}}}" if indicator == target else rendered)
        delta_lines.append(
            f"{latex_escape(case['id'])} & {latex_escape(D3_LABELS[target])} & "
            + " & ".join(cells)
            + f" & {item['mean_non_target_absolute_drop']:.2f} \\\\"
        )
    delta_table = "\n".join(
        [
            r"\begin{table}[htbp]",
            r"\centering",
            r"\caption{相对基线的 D3 降分矩阵（粗体为预注册目标）}",
            r"\scriptsize",
            r"\resizebox{\textwidth}{!}{%",
            r"\begin{tabular}{l l c c c c c c c}",
            r"\toprule",
            r"样例 & 目标 & 复杂度 & 复用 & 常量 & 命名 & 模块 & 注释 & 非目标均值 \\",
            r"\midrule",
            *delta_lines,
            r"\bottomrule",
            r"\end{tabular}}",
            r"\end{table}",
            "",
        ]
    )
    (generated / "d3_delta_table.tex").write_text(delta_table, encoding="utf-8")

    audit_table = "\n".join(
        [
            r"\begin{table}[htbp]",
            r"\centering",
            r"\caption{校准汇总与复现环境}",
            r"\small",
            r"\begin{tabularx}{\textwidth}{L{4.4cm} X}",
            r"\toprule",
            r"字段 & 记录值 \\",
            r"\midrule",
            r"校准方法 & known-groups calibration \\",
            f"D3 目标命中率 & {calibration['d3_target_hits']}/{calibration['d3_target_case_count']} "
            rf"({calibration['d3_target_hit_rate'] * 100:.1f}\%) \\",
            f"目标平均降分 / 非目标单元平均绝对漂移 & "
            f"{calibration['d3_mean_target_drop']:.3f} / "
            f"{calibration['d3_mean_non_target_absolute_drop']:.3f} \\\\ ",
            f"目标/非目标信号比 & {ratio:.2f} \\\\ ",
            f"Python / pygame / radon & {latex_escape(provenance['environment']['python'])} / "
            f"{latex_escape(provenance['environment']['pygame'])} / "
            f"{latex_escape(provenance['environment']['radon'])} \\\\ ",
            f"D1 / D3 evaluator SHA256（前 12 位） & "
            rf"\texttt{{{provenance['evaluator_files']['d1']['sha256'][:12]}}} / "
            rf"\texttt{{{provenance['evaluator_files']['d3']['sha256'][:12]}}} \\",
            f"D4 参考归档 SHA256（前 12 位） & "
            rf"\texttt{{{(provenance['design_reference']['sha256'] or 'not-found')[:12]}}} \\",
            r"LLM 调用 / API 成本 & 0 / 0 \\",
            r"\bottomrule",
            r"\end{tabularx}",
            r"\end{table}",
            "",
        ]
    )
    (generated / "audit_table.tex").write_text(audit_table, encoding="utf-8")


def write_markdown_report(
    path: Path,
    summary: dict[str, Any],
    expectations: dict[str, Any],
) -> None:
    first_run = summary["results"]
    calibration = summary["calibration"]
    lines = [
        "# GameBench D1/D3 校准实验总结",
        "",
        "本实验采用 known-groups calibration：D1 使用 0--6 级已知能力组，D3 使用一个参考 Pong 和六个单指标定向缺陷组。",
        "",
        f"- 总体状态：{'通过' if summary['overall_pass'] else '失败'}",
        f"- 重复次数：{summary['repeat_count']}",
        f"- 完整评分结果 SHA256 一致：{calibration['repeat_results_identical']}",
        f"- 实际墙钟时间：{summary['elapsed_seconds']:.3f} 秒",
        "- LLM 调用：0；API 成本：0",
        "",
        "## D1 阶梯结果",
        "",
        "| 样例 | 设计干预 | 预期级别 | 实际级别 | 原始通过数 | 指标签名 | D1 分数 | 闸门 |",
        "|---|---|---:|---:|---:|---|---:|---|",
    ]
    for case in expectations["d1"]["cases"]:
        result = first_run["d1"][case["id"]]
        signature = "".join(str(result["indicators"][key]) for key in D1_STEP_ORDER)
        lines.append(
            f"| `{case['file']}` | {case['intervention']} | {case['expected_pipeline_steps']} | "
            f"{result['pipeline_steps_passed']} | {result['raw_pass_count']} | `{signature}` | "
            f"{result['score']:.3f} | {'通过' if result['gate_pass'] else '关闭'} |"
        )

    lines.extend(
        [
            "",
            "## D3 受控退化结果",
            "",
            "| 样例 | 预注册目标 | D1 | 复杂度 | 复用 | 常量 | 命名 | 模块 | 注释 | 总分 |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for case in expectations["d3"]["cases"]:
        result = first_run["d3"][case["id"]]
        scores = result["d3"]["indicator_scores"]
        target = case["target_indicator"]
        lines.append(
            f"| `{case['id']}` | {D3_LABELS.get(target, '基线')} | "
            f"{result['d1']['pipeline_steps_passed']}/6 | {scores['complexity']} | {scores['reuse']} | "
            f"{scores['constants']} | {scores['naming']} | {scores['modularity']} | "
            f"{scores['comments']} | {result['d3']['score']} |"
        )

    lines.extend(
        [
            "",
            "## 缺陷识别能力",
            "",
            "| 缺陷组 | 目标 | 目标降分 | 非目标平均绝对漂移 | 总分降幅 |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for case in expectations["d3"]["cases"]:
        target = case["target_indicator"]
        if target is None:
            continue
        item = summary["sensitivity"][case["id"]]
        lines.append(
            f"| `{case['id']}` | {D3_LABELS[target]} | {item['target_drop']} | "
            f"{item['mean_non_target_absolute_drop']:.3f} | {item['total_drop']} |"
        )
    lines.extend(
        [
            "",
            f"目标指标命中率为 **{calibration['d3_target_hits']}/{calibration['d3_target_case_count']}**；"
            f"目标平均降分为 **{calibration['d3_mean_target_drop']:.3f}**，"
            f"非目标单元平均绝对漂移为 **{calibration['d3_mean_non_target_absolute_drop']:.3f}**，"
            f"信号比为 **{calibration['d3_target_to_non_target_signal_ratio']:.2f}**。",
            "参考组总分高于所有缺陷组，但不同干预强度并不等价，因此不能用降幅直接比较六个指标的重要性。",
            "",
            "## 自动断言",
            "",
        ]
    )
    for assertion in summary["assertions"]:
        mark = "PASS" if assertion["passed"] else "FAIL"
        lines.append(f"- **{mark}** `{assertion['name']}`：{assertion['detail']}")

    provenance = summary["provenance"]
    lines.extend(
        [
            "",
            "## 审计链",
            "",
            f"- 正式 D1 evaluator SHA256：`{provenance['evaluator_files']['d1']['sha256']}`",
            f"- 正式 D3 evaluator SHA256：`{provenance['evaluator_files']['d3']['sha256']}`",
            f"- D4 参考归档 SHA256：`{provenance['design_reference']['sha256']}`",
            "- 每个样例的预注册说明、fixture 哈希、完整原始输出和紧凑结果均位于 `results/cases/`。",
            "- `manifest.json` 汇总环境、配置、输入和产物哈希；报告表格不维护第二份手工分数。",
            "",
            "## 结论边界",
            "",
            "本报告支持评分器在这些受控样例上的内部一致性、已知组分离、方向敏感性和可复现性。",
            "它不证明 D3 与大规模人工评分的相关性，不证明阈值和权重唯一最优，也不证明对其他游戏类型或多文件工程具有外部有效性。",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def build_artifact_index(output_dir: Path) -> list[dict[str, Any]]:
    artifacts = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            artifacts.append(
                {
                    "path": path.relative_to(output_dir).as_posix(),
                    "size_bytes": path.stat().st_size,
                    "sha256": file_sha256(path),
                }
            )
    return artifacts


def main() -> int:
    args = parse_args()
    if args.repeat < 1:
        raise ValueError("--repeat must be at least 1")
    if args.runtime_sec < 3:
        raise ValueError("--runtime-sec must be at least 3 for the delayed QUIT probe")

    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    expectations = load_expectations()
    preflight_pygame()
    provenance = build_provenance(expectations, args)
    evaluator_hashes_before = {
        name: item["sha256"] for name, item in provenance["evaluator_files"].items()
    }

    started = time.perf_counter()
    evaluated_runs = [evaluate_once(args.runtime_sec, expectations) for _ in range(args.repeat)]
    elapsed_seconds = time.perf_counter() - started
    compact_runs = [run["compact"] for run in evaluated_runs]
    first_run = compact_runs[0]
    evaluator_hashes_after = {"d1": file_sha256(D1_EVALUATOR), "d3": file_sha256(D3_EVALUATOR)}
    assertions, sensitivity, calibration = validate_results(
        first_run,
        compact_runs,
        expectations,
        evaluator_hashes_before,
        evaluator_hashes_after,
    )
    overall_pass = all(item["passed"] for item in assertions)
    case_artifacts = write_case_evidence(
        output_dir,
        expectations,
        first_run,
        evaluated_runs[0]["raw"],
        provenance,
    )
    summary = {
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "overall_pass": overall_pass,
        "repeat_count": args.repeat,
        "runtime_sec": args.runtime_sec,
        "elapsed_seconds": round(elapsed_seconds, 6),
        "llm_used": False,
        "scoring_source": {
            "d1": "evaluator.dimension1.dimension1_executable.evaluate_dimension1",
            "d3": "evaluator.dimension3.dimension3_code_quality.evaluate_dimension3_code_quality",
        },
        "assertions": assertions,
        "calibration": calibration,
        "sensitivity": sensitivity,
        "provenance": provenance,
        "artifacts": {"manifest": "manifest.json", "case_evidence": case_artifacts},
        "results": first_run,
    }

    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_d1_csv(output_dir / "d1_results.csv", first_run["d1"], expectations)
    write_d3_csv(output_dir / "d3_results.csv", first_run["d3"], expectations, sensitivity)
    write_tex_tables(output_dir, first_run, expectations, sensitivity, calibration, provenance)
    write_markdown_report(output_dir / "report.md", summary, expectations)

    manifest = {
        "format_version": 1,
        "generated_at_utc": summary["generated_at_utc"],
        "calibration_method": expectations["calibration_method"],
        "overall_pass": overall_pass,
        "provenance": provenance,
        "artifact_index": build_artifact_index(output_dir),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"D1/D3 demo: {'PASS' if overall_pass else 'FAIL'}")
    print(
        f"Known-groups: D1 staircase={calibration['d1_staircase_exact']}; "
        f"D3 target hits={calibration['d3_target_hits']}/{calibration['d3_target_case_count']}"
    )
    print(f"Summary: {output_dir / 'summary.json'}")
    print(f"Manifest: {output_dir / 'manifest.json'}")
    if args.check and not overall_pass:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
