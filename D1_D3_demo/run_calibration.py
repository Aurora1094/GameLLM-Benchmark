from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


DEMO_ROOT = Path(__file__).resolve().parent
REPO_ROOT = DEMO_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from d3_v2 import evaluate_d3_tools, run_judge_panel
from d3_v2.evaluator import CONFIG_PATH as DEFAULT_D3_CONFIG
from evaluator.dimension1.dimension1_executable import INDICATOR_ORDER, evaluate_dimension1


D1_STEP_ORDER = [key for key, _ in INDICATOR_ORDER]
TOOL_INDICATORS = (
    "maintainability",
    "reliability",
    "security",
    "efficiency",
    "conformance",
)
ALL_INDICATORS = (*TOOL_INDICATORS, "llm_review")
D3_LABELS = {
    "maintainability": "可维护性与结构",
    "reliability": "可靠性与缺陷风险",
    "security": "安全与任务约束",
    "efficiency": "效率与资源纪律",
    "conformance": "Python 规范与可读性",
    "llm_review": "三模型语义评审",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calibrate the Demo-local D1 and D3-v2 contracts.")
    parser.add_argument("--check", action="store_true", help="Exit non-zero on any assertion failure.")
    parser.add_argument("--repeat", type=int, default=3, help="Repeated deterministic tool runs.")
    parser.add_argument("--runtime-sec", type=int, default=3, help="D1 runtime probe duration.")
    parser.add_argument("--output", type=Path, default=DEMO_ROOT / "results")
    parser.add_argument("--expectations", type=Path, default=DEMO_ROOT / "expectations.json")
    parser.add_argument("--d3-config", type=Path, default=DEFAULT_D3_CONFIG)
    parser.add_argument("--include-judges", action="store_true", help="Run paid three-model calibration.")
    parser.add_argument("--region", default="us-east-1")
    return parser.parse_args(argv)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def value_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def reset_generated_dir(path: Path, output_dir: Path) -> None:
    target = path.resolve()
    root = output_dir.resolve()
    if target == root or not target.is_relative_to(root):
        raise ValueError(f"Refusing to reset directory outside calibration output: {target}")
    if target.exists():
        shutil.rmtree(target)


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not_installed"


def git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        timeout=10,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unavailable"


def fixture_path(section: str, filename: str) -> Path:
    root = (DEMO_ROOT / "fixtures" / section).resolve()
    path = (root / filename).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"Fixture escapes {root}: {filename}")
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def load_expectations(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema_version") != 3:
        raise ValueError("expectations.json schema_version must be 3")
    if value.get("calibration_method") != "known_groups":
        raise ValueError("calibration_method must be known_groups")
    if value.get("d1", {}).get("step_order") != D1_STEP_ORDER:
        raise ValueError("D1 step order differs from the production D1 evaluator")
    d1_cases = value.get("d1", {}).get("cases", [])
    if [case.get("expected_pipeline_steps") for case in d1_cases] != list(range(7)):
        raise ValueError("D1 cases must preregister the unchanged 0..6 staircase")
    d3_cases = value.get("d3", {}).get("cases", [])
    ids = [case.get("id") for case in d3_cases]
    if len(ids) != len(set(ids)) or value.get("d3", {}).get("baseline") not in ids:
        raise ValueError("D3 cases require unique ids and one baseline")
    for case in d1_cases:
        fixture_path("d1", case["file"])
    for case in d3_cases:
        fixture_path("d3", case["file"])
        target = case.get("target_indicator")
        if target is not None and target not in ALL_INDICATORS:
            raise ValueError(f"Unknown target indicator: {target}")
    return value


def compact_d1(raw: dict[str, Any]) -> dict[str, Any]:
    runtime = raw.get("runtime", {})
    return {
        "pipeline_steps_passed": int(raw.get("pipeline_steps_passed", 0)),
        "raw_pass_count": int(raw.get("raw_pass_count", 0)),
        "gate_pass": bool(raw.get("gate_pass", False)),
        "diagnosis": runtime.get("diagnosis", "not_run"),
        "indicators": raw.get("indicators", {}),
        "reason": raw.get("reason", ""),
    }


def run_d1_cases(expectations: dict[str, Any], runtime_sec: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for case in expectations["d1"]["cases"]:
        path = fixture_path("d1", case["file"])
        actual = compact_d1(evaluate_dimension1(path, runtime_sec=runtime_sec))
        expected_vector = dict(zip(D1_STEP_ORDER, case["expected_indicators"], strict=True))
        passed = (
            actual["pipeline_steps_passed"] == case["expected_pipeline_steps"]
            and actual["diagnosis"] == case["expected_diagnosis"]
            and actual["indicators"] == expected_vector
        )
        records.append(
            {
                "id": case["id"],
                "file": case["file"],
                "expected_pipeline_steps": case["expected_pipeline_steps"],
                "expected_diagnosis": case["expected_diagnosis"],
                "expected_indicators": expected_vector,
                "actual": actual,
                "pass": passed,
                "fixture_sha256": file_sha256(path),
            }
        )
    return records


def evaluate_d3_fixture_gate(path: Path, runtime_sec: int) -> dict[str, Any]:
    """Confirm the D1 prerequisite while retaining transient probe evidence."""
    attempts: list[dict[str, Any]] = []
    selected: dict[str, Any] | None = None
    for _ in range(3):
        current = compact_d1(evaluate_dimension1(path, runtime_sec=runtime_sec))
        attempts.append(current)
        selected = current
        if current["gate_pass"]:
            break
    assert selected is not None
    return {**selected, "attempt_count": len(attempts), "attempts": attempts}


def run_d3_cases(
    expectations: dict[str, Any],
    repeat: int,
    runtime_sec: int,
    config_path: Path,
    output_dir: Path,
    include_judges: bool,
    region: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for case in expectations["d3"]["cases"]:
        path = fixture_path("d3", case["file"])
        d1 = evaluate_d3_fixture_gate(path, runtime_sec=runtime_sec)
        repeated = [evaluate_d3_tools(path, config_path=config_path) for _ in range(repeat)]
        hashes = [value_sha256(item) for item in repeated]
        first = repeated[0]
        case_dir = output_dir / "cases" / "d3" / case["id"]
        reset_generated_dir(case_dir, output_dir)
        write_json(case_dir / "d1_gate.json", d1)
        write_json(case_dir / "d3_tools.json", first)
        judge_panel: dict[str, Any] = {"status": "not_run"}
        if include_judges and first.get("status") == "completed" and d1["gate_pass"]:
            judge_panel = run_judge_panel(path, case_dir, region=region, config_path=config_path)
            write_json(case_dir / "judge_panel.json", judge_panel)
        records.append(
            {
                "id": case["id"],
                "file": case["file"],
                "target_indicator": case.get("target_indicator"),
                "intervention": case.get("intervention", ""),
                "d1_gate": d1,
                "tool_result": first,
                "repeat_hashes": hashes,
                "deterministic": len(set(hashes)) == 1,
                "judge_panel": judge_panel,
                "fixture_sha256": file_sha256(path),
            }
        )
    return records


def build_derived_checks(
    baseline_path: Path,
    config_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    derived = output_dir / "derived_fixtures"
    reset_generated_dir(derived, output_dir)
    source = baseline_path.read_text(encoding="utf-8")

    comments_many = derived / "comments_many.py"
    comments_few = derived / "comments_few.py"
    comments_many.parent.mkdir(parents=True, exist_ok=True)
    comments_many.write_text(source + "\n" + "\n".join(f"# explanatory note {n}" for n in range(80)) + "\n", encoding="utf-8")
    comments_few.write_text(source + "\n# one explanatory note\n", encoding="utf-8")
    many_result = evaluate_d3_tools(comments_many, config_path=config_path)
    few_result = evaluate_d3_tools(comments_few, config_path=config_path)

    numbers_path = derived / "ordinary_numbers.py"
    numbers_path.write_text(
        source
        + "\n\ndef ordinary_numbers_probe(value: int) -> tuple[int, ...]:\n"
        + "    return (value + 7, value + 11, value + 13, value + 17)\n",
        encoding="utf-8",
    )
    baseline_result = evaluate_d3_tools(baseline_path, config_path=config_path)
    numbers_result = evaluate_d3_tools(numbers_path, config_path=config_path)

    base_config = json.loads(config_path.read_text(encoding="utf-8"))
    changed_config = copy.deepcopy(base_config)
    changed_config["judge"]["high_disagreement_range"] = 4.5
    changed_path = derived / "changed_config.json"
    write_json(changed_path, changed_config)
    changed_result = evaluate_d3_tools(baseline_path, config_path=changed_path)

    version_config = copy.deepcopy(base_config)
    version_config["required_tools"]["ruff"] = "0.0.0-calibration"
    version_path = derived / "changed_tool_version.json"
    write_json(version_path, version_config)
    version_result = evaluate_d3_tools(baseline_path, config_path=version_path)

    checks = {
        "comment_quantity_no_cliff": {
            "pass": many_result.get("indicator_scores") == few_result.get("indicator_scores"),
            "many": many_result.get("indicator_scores"),
            "few": few_result.get("indicator_scores"),
        },
        "ordinary_numbers_no_cliff": {
            "pass": all(
                float(numbers_result.get("indicator_scores", {}).get(key, -999))
                >= float(baseline_result.get("indicator_scores", {}).get(key, 0)) - 1.0
                for key in TOOL_INDICATORS
            ),
            "baseline": baseline_result.get("indicator_scores"),
            "ordinary_numbers": numbers_result.get("indicator_scores"),
        },
        "config_change_changes_hash": {
            "pass": baseline_result.get("config_sha256") != changed_result.get("config_sha256"),
            "baseline_hash": baseline_result.get("config_sha256"),
            "changed_hash": changed_result.get("config_sha256"),
        },
        "tool_version_change_changes_hash_and_stops": {
            "pass": (
                baseline_result.get("config_sha256") != version_result.get("config_sha256")
                and version_result.get("status") == "incomplete_tooling"
            ),
            "baseline_hash": baseline_result.get("config_sha256"),
            "changed_hash": version_result.get("config_sha256"),
            "changed_status": version_result.get("status"),
        },
    }
    for name, result in {
        "comments_many": many_result,
        "comments_few": few_result,
        "ordinary_numbers": numbers_result,
        "changed_config": changed_result,
        "changed_tool_version": version_result,
    }.items():
        write_json(derived / f"{name}_result.json", result)
    return checks


def analyze_d3(
    records: list[dict[str, Any]],
    baseline_id: str,
    include_judges: bool,
    derived_checks: dict[str, Any],
) -> dict[str, Any]:
    by_id = {record["id"]: record for record in records}
    baseline = by_id[baseline_id]
    baseline_scores = dict(baseline["tool_result"].get("indicator_scores", {}))
    if include_judges and baseline["judge_panel"].get("score") is not None:
        baseline_scores["llm_review"] = baseline["judge_panel"]["score"]
    sensitivity: list[dict[str, Any]] = []
    assertions: list[dict[str, Any]] = []

    for record in records:
        assertions.append(
            {
                "id": f"{record['id']}:d1_gate",
                "pass": record["d1_gate"]["gate_pass"],
                "detail": f"D1={record['d1_gate']['pipeline_steps_passed']}/6",
            }
        )
        assertions.append(
            {
                "id": f"{record['id']}:tool_complete",
                "pass": record["tool_result"].get("status") == "completed",
                "detail": record["tool_result"].get("status"),
            }
        )
        assertions.append(
            {
                "id": f"{record['id']}:deterministic",
                "pass": record["deterministic"],
                "detail": record["repeat_hashes"],
            }
        )
        target = record["target_indicator"]
        if target is None:
            continue
        current_scores = dict(record["tool_result"].get("indicator_scores", {}))
        if include_judges and record["judge_panel"].get("score") is not None:
            current_scores["llm_review"] = record["judge_panel"]["score"]
        compared = ALL_INDICATORS if include_judges else TOOL_INDICATORS
        drops = {
            key: round(float(baseline_scores.get(key, 0)) - float(current_scores.get(key, 0)), 3)
            for key in compared
        }
        target_drop = drops.get(target)
        evaluable = target in drops
        largest_drop = max(drops.values(), default=0.0)
        target_is_largest = bool(evaluable and target_drop is not None and target_drop > 0 and target_drop >= largest_drop)
        non_target_changes = {
            key: value for key, value in drops.items() if key != target and abs(value) > 0.001
        }
        sensitivity.append(
            {
                "id": record["id"],
                "target_indicator": target,
                "drops": drops,
                "target_drop": target_drop,
                "target_is_largest_drop": target_is_largest if evaluable else None,
                "non_target_changes": non_target_changes,
            }
        )
        if evaluable:
            assertions.append(
                {
                    "id": f"{record['id']}:target_largest_drop",
                    "pass": target_is_largest,
                    "detail": drops,
                }
            )

    security = by_id.get("security_risks", {}).get("tool_result", {})
    security_capped_total = min(
        float(security.get("score") or 0) + 15.0,
        float(security.get("critical_total_cap") or 50),
    )
    assertions.extend(
        [
            {
                "id": "security_risks:security_zero",
                "pass": security.get("indicator_scores", {}).get("security") == 0,
                "detail": security.get("indicator_scores", {}).get("security"),
            },
            {
                "id": "security_risks:critical_cap",
                "pass": bool(security.get("critical_security_risk")) and security_capped_total <= 50,
                "detail": security_capped_total,
            },
        ]
    )
    for key, item in derived_checks.items():
        assertions.append({"id": key, "pass": bool(item["pass"]), "detail": item})

    judge_matrix: list[dict[str, Any]] = []
    fixture_statistics: list[dict[str, Any]] = []
    if include_judges:
        for record in records:
            panel = record["judge_panel"]
            fixture_statistics.append(
                {
                    "fixture": record["id"],
                    "mean": panel.get("score"),
                    "standard_deviation": panel.get("score_std"),
                    "range": panel.get("score_range"),
                    "high_disagreement": panel.get("high_disagreement"),
                }
            )
            assertions.append(
                {
                    "id": f"{record['id']}:judge_panel",
                    "pass": panel.get("status") in {"completed", "panel_degraded"},
                    "detail": panel.get("status"),
                }
            )
            for judge in panel.get("judge_results", []):
                judge_matrix.append(
                    {
                        "fixture": record["id"],
                        "judge_model": judge["model"],
                        "status": judge["status"],
                        "score": judge.get("total"),
                    }
                )
    judge_statistics = []
    for model in sorted({item["judge_model"] for item in judge_matrix}):
        scores = [
            float(item["score"])
            for item in judge_matrix
            if item["judge_model"] == model and item["score"] is not None
        ]
        judge_statistics.append(
            {
                "judge_model": model,
                "valid_fixture_count": len(scores),
                "mean": round(statistics.mean(scores), 3) if scores else None,
                "standard_deviation": (
                    round(statistics.stdev(scores), 3) if len(scores) > 1 else 0.0 if scores else None
                ),
                "range": round(max(scores) - min(scores), 3) if scores else None,
            }
        )
    all_pass = all(item["pass"] for item in assertions)
    return {
        "pass": all_pass,
        "assertions": assertions,
        "sensitivity": sensitivity,
        "derived_checks": derived_checks,
        "security_best_case_total_after_cap": security_capped_total,
        "judge_calibration": {
            "included": include_judges,
            "matrix": judge_matrix,
            "fixture_statistics": fixture_statistics,
            "judge_statistics": judge_statistics,
            "same_family_self_evaluation": "not_applicable_to_anonymous_fixtures",
        },
    }


def latex_escape(value: Any) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def write_csv_outputs(output_dir: Path, d1: list[dict[str, Any]], d3: list[dict[str, Any]]) -> None:
    with (output_dir / "d1_results.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["case", "expected_level", "actual_level", "diagnosis", "pass"])
        for row in d1:
            writer.writerow(
                [row["id"], row["expected_pipeline_steps"], row["actual"]["pipeline_steps_passed"], row["actual"]["diagnosis"], row["pass"]]
            )
    with (output_dir / "d3_results.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["case", *TOOL_INDICATORS, "tools_total", "judge", "status"])
        for row in d3:
            result = row["tool_result"]
            scores = result.get("indicator_scores", {})
            writer.writerow(
                [row["id"], *(scores.get(key) for key in TOOL_INDICATORS), result.get("score"), row["judge_panel"].get("score"), result.get("status")]
            )


def write_tex_outputs(
    output_dir: Path,
    d1: list[dict[str, Any]],
    d3: list[dict[str, Any]],
    analysis: dict[str, Any],
) -> None:
    generated = output_dir / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    target_drops = [
        item["target_drop"]
        for item in analysis["sensitivity"]
        if isinstance(item.get("target_drop"), (int, float))
    ]
    target_mean = statistics.mean(target_drops) if target_drops else 0.0
    (generated / "calibration_metrics.tex").write_text(
        "\n".join(
            [
                f"\\newcommand{{\\DThreeTargetMean}}{{{target_mean:.2f}}}",
                f"\\newcommand{{\\DThreeSchemaVersion}}{{2}}",
                f"\\newcommand{{\\DThreeToolRepeatCount}}{{{len(d3[0]['repeat_hashes']) if d3 else 0}}}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    d1_rows = [
        f"{latex_escape(row['id'])} & {row['expected_pipeline_steps']} & {row['actual']['pipeline_steps_passed']} & {latex_escape(row['actual']['diagnosis'])} & {'通过' if row['pass'] else '失败'} \\\\"
        for row in d1
    ]
    (generated / "d1_table.tex").write_text(
        "\\begin{longtable}{lrrrr}\n案例 & 预期级别 & 实际级别 & 诊断 & 结论 \\\\ \\hline\n"
        + "\n".join(d1_rows)
        + "\n\\end{longtable}\n",
        encoding="utf-8",
    )

    design_rows = [
        f"{latex_escape(row['id'])} & {latex_escape(D3_LABELS.get(row['target_indicator'], '基线'))} & {latex_escape(row['intervention'])} \\\\"
        for row in d3
    ]
    (generated / "d3_design_table.tex").write_text(
        "\\begin{longtable}{p{0.20\\linewidth}p{0.22\\linewidth}p{0.48\\linewidth}}\n案例 & 定向子项 & 干预 \\\\ \\hline\n"
        + "\n".join(design_rows)
        + "\n\\end{longtable}\n",
        encoding="utf-8",
    )

    score_rows = []
    for row in d3:
        score = row["tool_result"].get("indicator_scores", {})
        judge = row["judge_panel"].get("score")
        score_rows.append(
            f"{latex_escape(row['id'])} & "
            + " & ".join(f"{float(score.get(key, 0)):.1f}" for key in TOOL_INDICATORS)
            + f" & {float(row['tool_result'].get('score') or 0):.1f} & {float(judge):.1f}" if judge is not None else
            f"{latex_escape(row['id'])} & "
            + " & ".join(f"{float(score.get(key, 0)):.1f}" for key in TOOL_INDICATORS)
            + f" & {float(row['tool_result'].get('score') or 0):.1f} & --"
        )
        score_rows[-1] += " \\\\"
    (generated / "d3_table.tex").write_text(
        "\\begin{longtable}{lrrrrrrr}\n案例 & 维护 & 可靠 & 安全 & 效率 & 规范 & 工具/85 & Judge/15 \\\\ \\hline\n"
        + "\n".join(score_rows)
        + "\n\\end{longtable}\n",
        encoding="utf-8",
    )

    delta_rows = []
    short_labels = {
        "maintainability": "维护",
        "reliability": "可靠",
        "security": "安全",
        "efficiency": "效率",
        "conformance": "规范",
        "llm_review": "Judge",
    }
    for row in analysis["sensitivity"]:
        target_drop = row.get("target_drop")
        target_drop_text = "--" if target_drop is None else f"{float(target_drop):.1f}"
        largest_text = "--" if row.get("target_is_largest_drop") is None else (
            "是" if row["target_is_largest_drop"] else "否"
        )
        non_target = row.get("non_target_changes", {})
        non_target_text = "无" if not non_target else "，".join(
            f"{short_labels.get(key, key)} {float(value):+.1f}"
            for key, value in non_target.items()
        )
        delta_rows.append(
            f"{latex_escape(row['id'])} & {latex_escape(short_labels.get(row['target_indicator'], row['target_indicator']))} & "
            f"{target_drop_text} & {largest_text} & {latex_escape(non_target_text)} \\\\"
        )
    (generated / "d3_delta_table.tex").write_text(
        "\\begin{longtable}{p{0.22\\linewidth}p{0.14\\linewidth}ccp{0.30\\linewidth}}\n案例 & 目标 & 目标降分 & 是否最大 & 非目标变化（公开） \\\\ \\hline\n"
        + "\n".join(delta_rows)
        + "\n\\end{longtable}\n",
        encoding="utf-8",
    )

    first_tools = d3[0]["tool_result"] if d3 else {}
    tool_rows = [
        f"{latex_escape(name)} & {latex_escape(version)} \\\\"
        for name, version in first_tools.get("tool_versions", {}).items()
    ]
    issue_rows = []
    for row in d3:
        details = row["tool_result"].get("details", {})
        counts = {
            "维护": len(details.get("maintainability", {}).get("structural_findings", [])),
            "可靠": len(details.get("reliability", {}).get("ruff_findings", [])),
            "安全": len(details.get("security", {}).get("bandit_findings", []))
            + len(details.get("security", {}).get("forbidden_calls", [])),
            "效率": len(details.get("efficiency", {}).get("hot_loop_calls", [])),
            "规范": len(details.get("conformance", {}).get("findings", [])),
        }
        issue_rows.append(
            f"{latex_escape(row['id'])} & " + " & ".join(str(value) for value in counts.values()) + " \\\\"
        )
    judge_rows = []
    for row in d3:
        panel = row["judge_panel"]
        judge_rows.append(
            f"{latex_escape(row['id'])} & {latex_escape(panel.get('status'))} & {latex_escape(panel.get('score', '--'))} & {latex_escape(panel.get('score_std', '--'))} & {latex_escape(panel.get('score_range', '--'))} & {latex_escape(panel.get('high_disagreement', '--'))} \\\\"
        )
    audit = (
        "\\paragraph{固定工具版本。}\n\\begin{tabular}{ll}\n工具 & 版本 \\\\ \\hline\n"
        + "\n".join(tool_rows)
        + "\n\\end{tabular}\n"
        + "\\paragraph{静态问题分类计数。}\n\\begin{longtable}{lrrrrr}\n案例 & 维护 & 可靠 & 安全 & 效率 & 规范 \\\\ \\hline\n"
        + "\n".join(issue_rows)
        + "\n\\end{longtable}\n"
        + "\\paragraph{Judge 分歧。}\n\\begin{longtable}{lrrrrr}\n案例 & 状态 & 均值 & 标准差 & 极差 & 高分歧 \\\\ \\hline\n"
        + "\n".join(judge_rows)
        + "\n\\end{longtable}\n"
        + f"\\paragraph{{安全封顶。}}高危样例按最佳 Judge 得分计算后为 {analysis['security_best_case_total_after_cap']:.1f}/100，且不得超过 50 分。\n"
    )
    (generated / "audit_table.tex").write_text(audit, encoding="utf-8")


def write_markdown_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# D1 / D3-v2 校准报告",
        "",
        f"- 总体结论：{'通过' if summary['overall_pass'] else '失败'}",
        f"- D3 schema：{summary['d3_schema_version']}",
        f"- 工具重复轮数：{summary['repeat']}",
        f"- Judge 校准：{'已运行' if summary['include_judges'] else '未运行（默认无 API 费用）'}",
        "",
        "## 断言",
        "",
    ]
    for item in summary["d3_analysis"]["assertions"]:
        lines.append(f"- [{'x' if item['pass'] else ' '}] `{item['id']}`")
    lines.extend(
        [
            "",
            "## 边界",
            "",
            "D3-v2 仅用于 Demo 方法验证；不得与正式流水线旧 D3 混排。Radon MI 仅记录，不计分。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_artifact_index(output_dir: Path) -> list[dict[str, Any]]:
    return [
        {
            "path": path.relative_to(output_dir).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": file_sha256(path),
        }
        for path in sorted(output_dir.rglob("*"))
        if path.is_file() and path.name not in {"manifest.json", "manifest.sha256"}
    ]


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.repeat < 1:
        raise ValueError("--repeat must be positive")
    if args.runtime_sec < 3:
        raise ValueError("--runtime-sec must be at least 3")
    if args.include_judges and not (
        os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")
    ):
        print(
            "Judge calibration not started: AWS_ACCESS_KEY_ID and "
            "AWS_SECRET_ACCESS_KEY must be set in this process.",
            file=sys.stderr,
        )
        print("Existing calibration artifacts were left unchanged.", file=sys.stderr)
        return 2
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    reset_generated_dir(output_dir / "cases" / "d3", output_dir)
    expectations = load_expectations(args.expectations.resolve())
    d1 = run_d1_cases(expectations, args.runtime_sec)
    d3 = run_d3_cases(
        expectations,
        args.repeat,
        args.runtime_sec,
        args.d3_config.resolve(),
        output_dir,
        args.include_judges,
        args.region,
    )
    baseline_case = next(case for case in expectations["d3"]["cases"] if case["id"] == expectations["d3"]["baseline"])
    derived_checks = build_derived_checks(
        fixture_path("d3", baseline_case["file"]),
        args.d3_config.resolve(),
        output_dir,
    )
    d3_analysis = analyze_d3(d3, expectations["d3"]["baseline"], args.include_judges, derived_checks)
    d1_pass = all(item["pass"] for item in d1)
    overall_pass = d1_pass and d3_analysis["pass"]
    summary = {
        "schema_version": 3,
        "d3_schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "overall_pass": overall_pass,
        "check_requested": args.check,
        "repeat": args.repeat,
        "include_judges": args.include_judges,
        "d1_pass": d1_pass,
        "d1": d1,
        "d3": d3,
        "d3_analysis": d3_analysis,
        "provenance": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "git_commit": git_commit(),
            "expectations_sha256": file_sha256(args.expectations.resolve()),
            "d3_config_sha256": file_sha256(args.d3_config.resolve()),
            "packages": {name: package_version(name) for name in ("pygame", "ruff", "radon", "bandit")},
        },
    }
    write_json(output_dir / "summary.json", summary)
    write_csv_outputs(output_dir, d1, d3)
    write_tex_outputs(output_dir, d1, d3, d3_analysis)
    write_markdown_report(output_dir / "report.md", summary)
    manifest = {
        "format_version": 2,
        "overall_pass": overall_pass,
        "d3_schema_version": 2,
        "generated_at_utc": summary["generated_at_utc"],
        "artifact_index": build_artifact_index(output_dir),
    }
    manifest_path = output_dir / "manifest.json"
    write_json(manifest_path, manifest)
    (output_dir / "manifest.sha256").write_text(file_sha256(manifest_path) + "  manifest.json\n", encoding="ascii")
    print(f"D1 staircase: {'PASS' if d1_pass else 'FAIL'}")
    print(f"D3-v2 deterministic calibration: {'PASS' if d3_analysis['pass'] else 'FAIL'}")
    print(f"Judge API calls: {'enabled' if args.include_judges else 'disabled'}")
    print(f"Summary: {output_dir / 'summary.json'}")
    if args.check and not overall_pass:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
