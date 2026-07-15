from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any


DEMO_ROOT = Path(__file__).resolve().parent
REPO_ROOT = DEMO_ROOT.parent
DEFAULT_CONFIG = DEMO_ROOT / "report_config.json"
DEFAULT_OUTPUT = DEMO_ROOT / "results" / "live"
GENERATED_DIR = DEMO_ROOT / "results" / "generated"
INDICATORS = ("complexity", "reuse", "constants", "naming", "modularity", "comments")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate audited live LLM runs into report data and LaTeX tables."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_run(run_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    summary_path = run_dir / "summary.json"
    manifest_path = run_dir / "manifest.json"
    if not summary_path.is_file() or not manifest_path.is_file():
        raise ValueError(f"Run is missing summary or manifest: {run_dir}")

    summary = read_json(summary_path)
    manifest = read_json(manifest_path)
    generation = summary.get("generation", {})
    if summary.get("status") != "completed":
        raise ValueError(f"Run did not complete: {run_dir.name}")
    if generation.get("requested_origin") != "llm_api":
        raise ValueError(f"Run did not request a live model: {run_dir.name}")
    if generation.get("origin") != "llm_api":
        raise ValueError(f"Run is not a live model result: {run_dir.name}")
    if not generation.get("model_call_attempted") or not generation.get("model_call_succeeded"):
        raise ValueError(f"Run has no successful model call: {run_dir.name}")

    for artifact in manifest.get("artifact_index", []):
        artifact_path = run_dir / artifact["path"]
        if not artifact_path.is_file():
            raise ValueError(f"Missing run artifact: {artifact_path}")
        if artifact_path.stat().st_size != artifact["size_bytes"]:
            raise ValueError(f"Run artifact size mismatch: {artifact_path}")
        if sha256_file(artifact_path) != artifact["sha256"]:
            raise ValueError(f"Run artifact hash mismatch: {artifact_path}")

    if manifest.get("generation_origin") != "llm_api":
        raise ValueError(f"Manifest origin is not llm_api: {run_dir.name}")
    return summary, manifest


def optional_score(scores: dict[str, Any], key: str) -> int | None:
    value = scores.get(key)
    return int(value) if value is not None else None


def tex_value(value: int | None) -> str:
    return "--" if value is None else str(value)


def write_live_table(rows: list[dict[str, Any]], path: Path) -> None:
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{三次真实模型生成的 D1/D3 结果}",
        r"\label{tab:live-results}",
        r"\small",
        r"\setlength{\tabcolsep}{3.2pt}",
        r"\begin{tabularx}{\textwidth}{L{1.0cm} C{0.75cm} C{0.75cm} Y Y Y Y Y Y Y}",
        r"\toprule",
        r"样本 & D1 & 闸门 & 复杂度 & 复用 & 常量 & 命名 & 模块 & 注释 & D3 \\",
        r"\midrule",
    ]
    for index, row in enumerate(rows, start=1):
        gate = "通过" if row["d1_gate"] else "关闭"
        values = [tex_value(row[f"d3_{indicator}"]) for indicator in INDICATORS]
        lines.append(
            f"R{index} & {row['d1_steps']}/6 & {gate} & "
            + " & ".join(values)
            + f" & {tex_value(row['d3_score'])} \\\\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabularx}",
            r"\vspace{0.35em}",
            r"\begin{minipage}{0.97\textwidth}",
            r"\footnotesize 注：六项 D3 满分依次为 15、20、15、15、20、15；D3 仅在 D1 闸门打开后计算。",
            r"\end{minipage}",
            r"\end{table}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_live_metrics(aggregate: dict[str, Any], path: Path) -> None:
    macros = {
        "LiveRunCount": aggregate["run_count"],
        "LiveModelCallSuccessCount": aggregate["model_call_success_count"],
        "LiveUniqueCodeCount": aggregate["unique_code_count"],
        "LiveDOnePassCount": aggregate["d1_gate_pass_count"],
        "LiveDThreeEvaluatedCount": aggregate["d3_evaluated_count"],
        "LiveDThreeMean": f"{aggregate['d3_mean']:.2f}",
        "LiveDThreeStd": f"{aggregate['d3_sample_std']:.2f}",
        "LiveDThreeMin": aggregate["d3_min"],
        "LiveDThreeMax": aggregate["d3_max"],
    }
    path.write_text(
        "\n".join(f"\\newcommand{{\\{name}}}{{{value}}}" for name, value in macros.items())
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    config = read_json(args.config.resolve())
    run_ids = config.get("run_ids", [])
    if not run_ids:
        raise ValueError("report_config.json must contain at least one run_id")

    rows: list[dict[str, Any]] = []
    source_runs: list[dict[str, Any]] = []
    for run_id in run_ids:
        run_dir = DEMO_ROOT / "runs" / run_id
        summary, manifest = verify_run(run_dir)
        generation = summary["generation"]
        prompt = summary["prompt"]
        code = summary["code"]
        d1 = summary["scores"]["d1"]
        d3 = summary["scores"]["d3"]
        indicator_scores = d3.get("indicator_scores", {})
        row = {
            "run_id": run_id,
            "model": generation["model"],
            "provider": generation["provider"],
            "region": generation["region"],
            "generation_origin": generation["origin"],
            "generation_latency_seconds": generation.get("latency_seconds"),
            "request_id_present": bool(generation.get("request_id")),
            "prompt_sha256": prompt["rendered_sha256"],
            "code_sha256": code["sha256"],
            "code_syntax_valid": bool(code["syntax"]["valid"]),
            "actual_game_process_started": bool(d1.get("actual_game_process_started")),
            "d1_steps": int(d1["pipeline_steps_passed"]),
            "d1_gate": bool(d1["gate_pass"]),
            "d1_diagnosis": d1["diagnosis"],
            "d3_status": d3["status"],
            "d3_score": optional_score(d3, "score"),
        }
        for indicator in INDICATORS:
            row[f"d3_{indicator}"] = optional_score(indicator_scores, indicator)
        rows.append(row)
        source_runs.append(
            {
                "run_id": run_id,
                "generated_at_utc": summary["generated_at_utc"],
                "summary_sha256": sha256_file(run_dir / "summary.json"),
                "manifest_sha256": sha256_file(run_dir / "manifest.json"),
                "artifact_count": len(manifest["artifact_index"]),
            }
        )

    expected_model = config.get("model")
    models = {row["model"] for row in rows}
    if len(models) != 1 or expected_model not in models:
        raise ValueError(f"Live runs do not share expected model {expected_model}: {sorted(models)}")
    prompt_hashes = {row["prompt_sha256"] for row in rows}
    if len(prompt_hashes) != 1:
        raise ValueError("Live runs do not share the same rendered prompt")

    d3_scores = [row["d3_score"] for row in rows if row["d3_score"] is not None]
    if not d3_scores:
        raise ValueError("No live run reached D3")
    aggregate = {
        "run_count": len(rows),
        "model_call_success_count": sum(row["generation_origin"] == "llm_api" for row in rows),
        "unique_code_count": len({row["code_sha256"] for row in rows}),
        "d1_gate_pass_count": sum(row["d1_gate"] for row in rows),
        "d3_evaluated_count": len(d3_scores),
        "d3_mean": statistics.mean(d3_scores),
        "d3_sample_std": statistics.stdev(d3_scores) if len(d3_scores) > 1 else 0.0,
        "d3_min": min(d3_scores),
        "d3_max": max(d3_scores),
        "indicator_means": {
            indicator: statistics.mean(
                row[f"d3_{indicator}"]
                for row in rows
                if row[f"d3_{indicator}"] is not None
            )
            for indicator in INDICATORS
        },
    }

    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "format_version": 1,
        "generated_at_utc": max(run["generated_at_utc"] for run in source_runs),
        "config": config,
        "config_sha256": sha256_file(args.config.resolve()),
        "same_prompt_across_runs": True,
        "rendered_prompt_sha256": next(iter(prompt_hashes)),
        "rows": rows,
        "aggregate": aggregate,
        "source_runs": source_runs,
    }
    (output_dir / "live_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    with (output_dir / "live_results.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    write_live_table(rows, GENERATED_DIR / "live_table.tex")
    write_live_metrics(aggregate, GENERATED_DIR / "live_metrics.tex")
    print(f"Aggregated {len(rows)} audited live runs into {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
