import argparse
import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent
SCORES_DIR = ROOT_DIR / "data" / "scores"


def find_latest_run() -> Path | None:
    runs = sorted([d for d in SCORES_DIR.iterdir() if d.is_dir()])
    return runs[-1] if runs else None


def resolve_summary_path(run: str | None, summary: str | None) -> Path:
    if summary:
        summary_path = Path(summary)
        if not summary_path.is_absolute():
            summary_path = ROOT_DIR / summary_path
        return summary_path

    if run:
        run_dir = Path(run)
        if not run_dir.is_absolute():
            run_dir = SCORES_DIR / run
        return run_dir / "summary.json"

    latest = find_latest_run()
    if latest is None:
        raise FileNotFoundError("未找到任何评分结果目录")
    return latest / "summary.json"


def load_results(summary_path: Path) -> list[dict[str, Any]]:
    if not summary_path.exists():
        raise FileNotFoundError(f"结果文件不存在: {summary_path}")
    with open(summary_path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_dimension_data(scores: dict[str, Any], key: str) -> dict[str, Any]:
    data = dict(scores.get(key, {}))
    weights = scores.get("weights", {})

    if key == "d1_executability":
        details = data.get("details", {})
        if not isinstance(details, dict):
            details = {}
        indicators = details.get("indicators", {})
        data.setdefault("raw_score", float(sum(indicators.values())))
        data.setdefault("max_score", float(len(indicators)))
        data.setdefault(
            "weighted_contribution",
            float(data.get("score", 0.0)) * float(weights.get("executability", 0.0)),
        )
        data.setdefault(
            "indicators",
            [{"name": name, "score": float(score), "max_score": 1.0} for name, score in indicators.items()],
        )

    elif key == "d2_functionality":
        details = data.get("details", {})
        if not isinstance(details, dict):
            details = {}
        criteria_scores = details.get("criteria_scores", {})
        if "passed" in details:
            data.setdefault("raw_score", float(details["passed"]))
        if "total" in details:
            data.setdefault("max_score", float(details["total"]))
        data.setdefault(
            "weighted_contribution",
            float(data.get("score", 0.0)) * float(weights.get("functionality", 0.0)),
        )
        data.setdefault(
            "indicators",
            [{"name": name, "score": float(score), "max_score": 2.0} for name, score in criteria_scores.items()],
        )

    elif key == "d3_code_quality":
        details = data.get("details", {})
        if not isinstance(details, dict):
            details = {}
        indicator_scores = details.get("indicator_scores", {})
        data.setdefault("raw_score", float(details.get("score", 0.0)))
        data.setdefault("max_score", 100.0 if details else 0.0)
        data.setdefault(
            "weighted_contribution",
            float(data.get("score", 0.0)) * float(weights.get("code_quality", 0.0)),
        )
        data.setdefault(
            "indicators",
            [
                {"name": name, "score": float(score), "max_score": float(max_score)}
                for name, score, max_score in [
                    ("modularity", indicator_scores.get("modularity", 0.0), 20.0),
                    ("reuse", indicator_scores.get("reuse", 0.0), 20.0),
                    ("naming", indicator_scores.get("naming", 0.0), 15.0),
                    ("comments", indicator_scores.get("comments", 0.0), 15.0),
                    ("constants", indicator_scores.get("constants", 0.0), 15.0),
                    ("complexity", indicator_scores.get("complexity", 0.0), 15.0),
                ]
                if name in indicator_scores
            ],
        )

    elif key == "d4_ux":
        details = data.get("details", {})
        if not isinstance(details, dict):
            details = {}
        data.setdefault("raw_score", float(details.get("score", 0.0)))
        data.setdefault("max_score", 100.0 if details else 0.0)
        data.setdefault(
            "weighted_contribution",
            float(data.get("score", 0.0)) * float(weights.get("ux", 0.0)),
        )
        if "indicators" not in data and details:
            sections = []
            for section_name in ("visual", "smoothness", "balance", "audio_animation"):
                section = details.get(section_name)
                if not isinstance(section, dict):
                    continue
                sections.append(
                    {
                        "name": section_name,
                        "score": float(section.get("score", 0.0)),
                        "max_score": float(section.get("max_score", 0.0)),
                        "sub_indicators": [
                            {"name": sub_name, "score": float(sub_score), "max_score": 1.0}
                            for sub_name, sub_score in section.get("indicators", {}).items()
                        ],
                    }
                )
            data["indicators"] = sections

    return data


def print_indicator_lines(indicators: list[dict[str, Any]], indent: str = "    ") -> None:
    for item in indicators:
        line = f"{indent}- {item['name']}: {float(item.get('score', 0.0)):.3f}"
        if "max_score" in item:
            line += f" / {float(item['max_score']):.3f}"
        print(line)

        for sub in item.get("sub_indicators", []):
            sub_line = f"{indent}    * {sub['name']}: {float(sub.get('score', 0.0)):.3f}"
            if "max_score" in sub:
                sub_line += f" / {float(sub['max_score']):.3f}"
            print(sub_line)


def print_dimension_block(title: str, data: dict[str, Any]) -> None:
    print(
        f"{title}: score={float(data.get('score', 0.0)):.3f}, "
        f"raw={float(data.get('raw_score', 0.0)):.3f}/{float(data.get('max_score', 0.0)):.3f}, "
        f"weighted={float(data.get('weighted_contribution', 0.0)):.3f}"
    )
    print_indicator_lines(data.get("indicators", []), indent="  ")


def print_result_entry(item: dict[str, Any]) -> None:
    scores = item["scores"]
    d1 = normalize_dimension_data(scores, "d1_executability")
    d2 = normalize_dimension_data(scores, "d2_functionality")
    d3 = normalize_dimension_data(scores, "d3_code_quality")
    d4 = normalize_dimension_data(scores, "d4_ux")

    print("=" * 100)
    print(f"Game: {item.get('game', '-')}")
    print(f"Difficulty: {item.get('difficulty', '-')}")
    print(f"Model: {item.get('model', '-')}")
    print(f"Provider: {item.get('provider', '-')}")
    print(f"Timestamp: {item.get('timestamp', '-')}")
    print(f"Code Path: {item.get('code_path', '-')}")
    print(f"Final Score: {float(scores.get('total_score', 0.0)):.3f}")
    print(
        "Formula: "
        + scores.get(
            "final_score_formula",
            "Final Score = 0.2 * Dimension1 + 0.5 * Dimension2 + 0.15 * Dimension3 + 0.15 * Dimension4",
        )
    )
    print("-" * 100)
    print_dimension_block("Dimension1", d1)
    print_dimension_block("Dimension2", d2)
    print_dimension_block("Dimension3", d3)
    print_dimension_block("Dimension4", d4)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="打印完整测评结果")
    parser.add_argument("--run", help="指定 data/scores 下的某次 run 目录名，例如 20260416_233830")
    parser.add_argument("--summary", help="直接指定 summary.json 路径")
    parser.add_argument("--game", help="只打印指定游戏")
    parser.add_argument("--model", help="只打印指定模型")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary_path = resolve_summary_path(args.run, args.summary)
    results = load_results(summary_path)

    if args.game:
        results = [item for item in results if item.get("game") == args.game]
    if args.model:
        results = [item for item in results if item.get("model") == args.model]

    print(f"Summary File: {summary_path}")
    print(f"Result Count: {len(results)}")
    if not results:
        print("没有匹配到结果")
        return

    for item in sorted(results, key=lambda x: (x.get("game", ""), x.get("model", ""))):
        print_result_entry(item)


if __name__ == "__main__":
    main()
