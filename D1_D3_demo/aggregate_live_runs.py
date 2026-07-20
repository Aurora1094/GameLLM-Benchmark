from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any, Sequence


DEMO_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = DEMO_ROOT / "report_config.json"
DEFAULT_OUTPUT = DEMO_ROOT / "results" / "live"
GENERATED_DIR = DEMO_ROOT / "results" / "generated"
INDICATORS = (
    "maintainability",
    "reliability",
    "security",
    "efficiency",
    "conformance",
    "llm_review",
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate audited, report-eligible D3-v2 live runs without calling any API."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tex_escape(value: Any) -> str:
    text = str(value)
    for old, new in {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }.items():
        text = text.replace(old, new)
    return text


def verify_manifest(run_dir: Path, manifest: dict[str, Any]) -> None:
    indexed_paths: set[str] = set()
    for artifact in manifest.get("artifact_index", []):
        relative = artifact["path"]
        indexed_paths.add(relative)
        path = (run_dir / relative).resolve()
        if not path.is_relative_to(run_dir.resolve()) or not path.is_file():
            raise ValueError(f"Missing or unsafe artifact path: {relative}")
        if path.stat().st_size != artifact["size_bytes"] or sha256_file(path) != artifact["sha256"]:
            raise ValueError(f"Artifact integrity failure: {path}")
    required = {
        "summary.json",
        "scores/d1.json",
        "scores/d3.json",
        "scores/d3_tools.json",
        "prompts/d3_judge.txt",
    }
    if not required.issubset(indexed_paths):
        raise ValueError(f"Manifest omits required artifacts: {sorted(required - indexed_paths)}")
    sidecar = run_dir / "manifest.sha256"
    if not sidecar.is_file() or sidecar.read_text(encoding="ascii").split()[0] != sha256_file(run_dir / "manifest.json"):
        raise ValueError(f"Manifest SHA256 sidecar is missing or invalid: {run_dir.name}")


def verify_run(
    run_dir: Path,
    expected_candidate: str,
    expected_judges: list[str],
    expected_tools: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    summary_path = run_dir / "summary.json"
    manifest_path = run_dir / "manifest.json"
    d3_path = run_dir / "scores" / "d3.json"
    if not summary_path.is_file() or not manifest_path.is_file() or not d3_path.is_file():
        raise ValueError(f"Run lacks summary, manifest, or D3 result: {run_dir}")
    summary = read_json(summary_path)
    manifest = read_json(manifest_path)
    d3 = read_json(d3_path)
    generation = summary.get("generation", {})
    if summary.get("status") != "completed" or summary.get("format_version") != 2:
        raise ValueError(f"Run is not a completed Demo-v2 run: {run_dir.name}")
    if generation.get("origin") != "llm_api" or generation.get("requested_origin") != "llm_api":
        raise ValueError(f"Only origin=llm_api is report-eligible: {run_dir.name}")
    if not generation.get("model_call_attempted") or not generation.get("model_call_succeeded"):
        raise ValueError(f"Candidate generation call did not succeed: {run_dir.name}")
    if generation.get("model") != expected_candidate:
        raise ValueError(f"Candidate model mismatch in {run_dir.name}")
    if d3.get("schema_version") != 2 or d3.get("status") not in {"completed", "panel_degraded"}:
        raise ValueError(f"D3 schema/status is not report-eligible: {run_dir.name}")
    tools = d3.get("tools", {})
    if tools.get("status") != "completed" or tools.get("tool_versions") != expected_tools:
        raise ValueError(f"D3 tooling is incomplete or version-mismatched: {run_dir.name}")
    panel = d3.get("judge_panel", {})
    valid = [item for item in panel.get("judge_results", []) if item.get("status") == "completed"]
    if len(valid) < 2 or panel.get("valid_judge_count", 0) < 2:
        raise ValueError(f"Fewer than two valid judges: {run_dir.name}")
    if {item.get("model") for item in panel.get("judge_results", [])} != set(expected_judges):
        raise ValueError(f"Judge panel differs from report_config.json: {run_dir.name}")
    verify_manifest(run_dir, manifest)
    if manifest.get("generation_origin") != "llm_api" or manifest.get("format_version") != 2:
        raise ValueError(f"Manifest is not a live Demo-v2 manifest: {run_dir.name}")
    return summary, manifest, d3


def make_row(run_id: str, summary: dict[str, Any], d3: dict[str, Any]) -> dict[str, Any]:
    d1 = summary["scores"]["d1"]
    gated = summary["scores"].get("d1_gated_final", {})
    scores = d3["indicator_scores"]
    panel = d3["judge_panel"]
    row: dict[str, Any] = {
        "run_id": run_id,
        "candidate_model": summary["generation"]["model"],
        "prompt_sha256": summary["prompt"]["rendered_sha256"],
        "code_sha256": summary["code"]["sha256"],
        "d1_steps": int(d1["pipeline_steps_passed"]),
        "d1_gate": bool(d1["gate_pass"]),
        "d3_status": d3["status"],
        "d3_score": float(d3["score"]),
        "d1_gated_final_score": float(
            gated.get("score", d3["score"] if d1["gate_pass"] else 0.0)
        ),
        "raw_score_before_cap": float(d3.get("raw_score_before_cap", d3["score"])),
        "security_cap_applied": bool(d3.get("security_cap_applied", False)),
        "judge_valid_count": int(panel["valid_judge_count"]),
        "judge_std": float(panel.get("score_std", 0)),
        "judge_range": float(panel.get("score_range", 0)),
        "high_disagreement": bool(panel.get("high_disagreement", False)),
    }
    for indicator in INDICATORS:
        row[indicator] = float(scores[indicator])
    judge_totals = {
        item["model"]: float(item["total"])
        for item in panel["judge_results"]
        if item.get("status") == "completed"
    }
    row["judge_scores"] = judge_totals
    if row["candidate_model"] in judge_totals:
        other = [score for model, score in judge_totals.items() if model != row["candidate_model"]]
        row["same_family_self_difference"] = (
            round(judge_totals[row["candidate_model"]] - statistics.mean(other), 3) if other else None
        )
    else:
        row["same_family_self_difference"] = None
    return row


def issue_counts(d3: dict[str, Any]) -> dict[str, int]:
    details = d3["tools"].get("details", {})
    return {
        "maintainability": len(details.get("maintainability", {}).get("structural_findings", [])),
        "reliability": len(details.get("reliability", {}).get("ruff_findings", [])),
        "security": len(details.get("security", {}).get("bandit_findings", []))
        + len(details.get("security", {}).get("forbidden_calls", [])),
        "efficiency": len(details.get("efficiency", {}).get("ruff_perf_findings", []))
        + len(details.get("efficiency", {}).get("hot_loop_calls", [])),
        "conformance": len(details.get("conformance", {}).get("findings", [])),
    }


def write_live_table(
    rows: list[dict[str, Any]],
    issue_rows: list[dict[str, Any]],
    tool_versions: dict[str, str],
    path: Path,
) -> None:
    score_lines = []
    for row in rows:
        score_lines.append(
            f"{tex_escape(row['candidate_model'])} & {row['d1_steps']}/6 & {row['maintainability']:.1f} & "
            f"{row['reliability']:.1f} & {row['security']:.1f} & {row['efficiency']:.1f} & "
            f"{row['conformance']:.1f} & {row['llm_review']:.1f} & {row['d3_score']:.1f} & "
            f"{row['d1_gated_final_score']:.1f} \\\\"
        )
    tools = "\n".join(f"{tex_escape(name)} & {tex_escape(version)} \\\\" for name, version in tool_versions.items())
    issues = "\n".join(
        f"{tex_escape(item['run_id'])} & {item['maintainability']} & {item['reliability']} & {item['security']} & {item['efficiency']} & {item['conformance']} \\\\"
        for item in issue_rows
    )
    disagreements = "\n".join(
        f"{tex_escape(row['run_id'])} & {row['judge_valid_count']} & {row['llm_review']:.1f} & {row['judge_std']:.2f} & {row['judge_range']:.1f} & {tex_escape(row['high_disagreement'])} & {tex_escape(row['same_family_self_difference'])} \\\\"
        for row in rows
    )
    text = (
        "\\begin{table}[htbp]\n\\centering\n\\caption{D3-v2 真实候选模型结果}\n\\small\n\\setlength{\\tabcolsep}{2.5pt}\n"
        "\\begin{tabular}{lrrrrrrrrr}\n\\toprule\n模型 & D1 & 维护 & 可靠 & 安全 & 效率 & 规范 & Judge & D3诊断 & 门控总分 \\\\ \\midrule\n"
        + "\n".join(score_lines)
        + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
        + "\\paragraph{固定工具版本。}\n\\begin{tabular}{ll}\n工具 & 版本 \\\\ \\hline\n"
        + tools
        + "\n\\end{tabular}\n"
        + "\\paragraph{静态问题分类。}\n\\begin{longtable}{lrrrrr}\nRun & 维护 & 可靠 & 安全 & 效率 & 规范 \\\\ \\hline\n"
        + issues
        + "\n\\end{longtable}\n"
        + "\\paragraph{Judge 分歧与同家族自评差异。}\n{\\footnotesize\n\\setlength{\\tabcolsep}{3pt}\n\\begin{longtable}{lrrrrrr}\nRun & 有效数 & 均值 & 标准差 & 极差 & 高分歧 & 自评差 \\\\ \\hline\n"
        + disagreements
        + "\n\\end{longtable}\n}\n"
        + "高危安全样例的安全子项归零，且 D3 总分封顶为 50/100。\n"
    )
    path.write_text(text, encoding="utf-8")


def write_live_metrics(aggregate: dict[str, Any], path: Path) -> None:
    macros = {
        "LiveRunCount": aggregate["run_count"],
        "LiveModelCallSuccessCount": aggregate["run_count"],
        "LiveUniqueCodeCount": aggregate["unique_code_count"],
        "LiveDOnePassCount": aggregate["d1_gate_pass_count"],
        "LiveDThreeEvaluatedCount": aggregate["run_count"],
        "LiveDThreeMean": f"{aggregate['d3_mean']:.2f}",
        "LiveDThreeStd": f"{aggregate['d3_sample_std']:.2f}",
        "LiveDThreeMin": f"{aggregate['d3_min']:.1f}",
        "LiveDThreeMax": f"{aggregate['d3_max']:.1f}",
        "LiveGatedFinalMean": f"{aggregate['d1_gated_final_mean']:.2f}",
        "LiveDOneZeroedCount": aggregate["d1_gate_zeroed_count"],
    }
    path.write_text(
        "\n".join(f"\\newcommand{{\\{key}}}{{{value}}}" for key, value in macros.items()) + "\n",
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = args.config.resolve()
    config = read_json(config_path)
    if config.get("schema_version") != 2:
        raise ValueError("report_config.json schema_version must be 2")
    candidates = config.get("candidates", [])
    expected_judges = config.get("judge_models", [])
    expected_tools = config.get("required_tools", {})
    if len(expected_judges) != 3 or not candidates:
        raise ValueError("Report config requires candidates and exactly three judge models")

    rows: list[dict[str, Any]] = []
    source_runs: list[dict[str, Any]] = []
    all_issue_rows: list[dict[str, Any]] = []
    generated_times: list[str] = []
    for candidate in candidates:
        model = candidate.get("model")
        run_ids = candidate.get("run_ids", [])
        if not model or not isinstance(run_ids, list):
            raise ValueError("Each candidate requires model and run_ids")
        for run_id in run_ids:
            run_dir = (DEMO_ROOT / "runs" / run_id).resolve()
            if not run_dir.is_relative_to((DEMO_ROOT / "runs").resolve()):
                raise ValueError(f"Unsafe run id: {run_id}")
            summary, manifest, d3 = verify_run(
                run_dir, model, expected_judges, expected_tools
            )
            row = make_row(run_id, summary, d3)
            rows.append(row)
            all_issue_rows.append({"run_id": run_id, **issue_counts(d3)})
            generated_times.append(summary["generated_at_utc"])
            source_runs.append(
                {
                    "run_id": run_id,
                    "candidate_model": model,
                    "summary_sha256": sha256_file(run_dir / "summary.json"),
                    "manifest_sha256": sha256_file(run_dir / "manifest.json"),
                    "artifact_count": len(manifest["artifact_index"]),
                }
            )
    if not rows:
        raise ValueError("No report-eligible run_ids are configured")
    prompt_hashes = {row["prompt_sha256"] for row in rows}
    if len(prompt_hashes) != 1:
        raise ValueError("Report candidates were not generated from the same rendered prompt")
    scores = [row["d3_score"] for row in rows]
    gated_scores = [row["d1_gated_final_score"] for row in rows]
    aggregate = {
        "run_count": len(rows),
        "model_call_success_count": len(rows),
        "candidate_model_count": len({row["candidate_model"] for row in rows}),
        "unique_code_count": len({row["code_sha256"] for row in rows}),
        "d1_gate_pass_count": sum(row["d1_gate"] for row in rows),
        "d3_mean": statistics.mean(scores),
        "d3_sample_std": statistics.stdev(scores) if len(scores) > 1 else 0.0,
        "d3_min": min(scores),
        "d3_max": max(scores),
        "d1_gated_final_mean": statistics.mean(gated_scores),
        "d1_gate_zeroed_count": sum(not row["d1_gate"] for row in rows),
        "high_disagreement_count": sum(row["high_disagreement"] for row in rows),
        "security_cap_count": sum(row["security_cap_applied"] for row in rows),
        "indicator_means": {
            key: statistics.mean(row[key] for row in rows) for key in INDICATORS
        },
    }
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "format_version": 2,
        "d3_schema_version": 2,
        "generated_at_utc": max(generated_times),
        "config": config,
        "config_sha256": sha256_file(config_path),
        "same_prompt_across_runs": True,
        "rendered_prompt_sha256": next(iter(prompt_hashes)),
        "rows": rows,
        "static_issue_counts": all_issue_rows,
        "aggregate": aggregate,
        "source_runs": source_runs,
    }
    (output_dir / "live_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    csv_rows = [{key: value for key, value in row.items() if key != "judge_scores"} for row in rows]
    with (output_dir / "live_results.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)
    write_live_table(rows, all_issue_rows, expected_tools, GENERATED_DIR / "live_table.tex")
    write_live_metrics(aggregate, GENERATED_DIR / "live_metrics.tex")
    print(f"Aggregated {len(rows)} audited D3-v2 live runs into {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
