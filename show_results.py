# -*- coding: utf-8 -*-
"""读取并展示最新评分结果。"""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SCORES_DIR = ROOT_DIR / "data" / "scores"


def find_latest_run():
    runs = sorted([d for d in SCORES_DIR.iterdir() if d.is_dir()])
    return runs[-1] if runs else None


def load_summary(run_dir):
    summary_file = run_dir / "summary.json"
    if not summary_file.exists():
        return []
    with open(summary_file, encoding="utf-8") as f:
        return json.load(f)


def _avg(values):
    return sum(values) / len(values) if values else 0.0


def _normalize_dimension_data(scores, key):
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

    if key == "d2_functionality":
        details = data.get("details", {})
        if not isinstance(details, dict):
            details = {}
        criteria_scores = details.get("criteria_scores", {})
        passed = details.get("passed")
        total = details.get("total")
        if passed is not None:
            data.setdefault("raw_score", float(passed))
        if total is not None:
            data.setdefault("max_score", float(total))
        data.setdefault(
            "weighted_contribution",
            float(data.get("score", 0.0)) * float(weights.get("functionality", 0.0)),
        )
        data.setdefault(
            "indicators",
            [{"name": name, "score": float(score), "max_score": 2.0} for name, score in criteria_scores.items()],
        )

    if key == "d3_code_quality":
        details = data.get("details", {})
        if not isinstance(details, dict):
            details = {}
        indicator_scores = details.get("indicator_scores", {})
        data.setdefault("raw_score", float(details.get("score", 0.0)))
        data.setdefault("max_score", 100.0 if indicator_scores or details else 0.0)
        data.setdefault(
            "weighted_contribution",
            float(data.get("score", 0.0)) * float(weights.get("code_quality", 0.0)),
        )
        data.setdefault(
            "indicators",
            [{"name": name, "score": float(score)} for name, score in indicator_scores.items()],
        )

    if key == "d4_ux":
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


def _print_indicator_lines(indicators, indent="    "):
    for item in indicators:
        line = f"{indent}- {item['name']}: {item['score']:.3f}"
        if "max_score" in item:
            line += f" / {item['max_score']:.3f}"
        print(line)

        sub_indicators = item.get("sub_indicators", [])
        for sub in sub_indicators:
            sub_line = f"{indent}    * {sub['name']}: {sub['score']:.3f}"
            if "max_score" in sub:
                sub_line += f" / {sub['max_score']:.3f}"
            print(sub_line)


def _print_dimension_block(title, dimension_data):
    print(
        f"  {title}: score={dimension_data['score']:.3f}, "
        f"raw={dimension_data.get('raw_score', 0):.3f}/{dimension_data.get('max_score', 0):.3f}, "
        f"weighted={dimension_data.get('weighted_contribution', 0):.3f}"
    )
    _print_indicator_lines(dimension_data.get("indicators", []), indent="    ")


def print_results(results):
    if not results:
        print("没有找到评分结果")
        return

    model_stats = {}
    for r in results:
        model = r["model"]
        scores = r["scores"]
        if model not in model_stats:
            model_stats[model] = {"total": [], "d1": [], "d2": [], "d3": [], "d4": []}

        model_stats[model]["total"].append(scores["total_score"])
        model_stats[model]["d1"].append(scores["d1_executability"]["score"])
        model_stats[model]["d2"].append(scores["d2_functionality"]["score"])
        model_stats[model]["d3"].append(scores["d3_code_quality"]["score"])
        model_stats[model]["d4"].append(scores["d4_ux"]["score"])

    print("\n" + "=" * 100)
    print("GameLLM-Benchmark 评分结果")
    print("=" * 100)

    print(f"\n{'游戏':<20} {'模型':<35} {'最终分':>8} {'D1':>8} {'D2':>8} {'D3':>8} {'D4':>8}")
    print("-" * 100)
    for r in sorted(results, key=lambda x: (x["game"], x["model"])):
        scores = r["scores"]
        print(
            f"{r['game']:<20} {r['model']:<35} "
            f"{scores['total_score']:>8.3f} "
            f"{scores['d1_executability']['score']:>8.3f} "
            f"{scores['d2_functionality']['score']:>8.3f} "
            f"{scores['d3_code_quality']['score']:>8.3f} "
            f"{scores['d4_ux']['score']:>8.3f}"
        )

    print("\n" + "=" * 100)
    print("模型平均分")
    print("=" * 100)
    print(f"\n{'模型':<35} {'平均最终分':>12} {'D1':>8} {'D2':>8} {'D3':>8} {'D4':>8}")
    print("-" * 100)
    for model, stats in sorted(model_stats.items(), key=lambda x: -_avg(x[1]["total"])):
        print(
            f"{model:<35} "
            f"{_avg(stats['total']):>12.3f} "
            f"{_avg(stats['d1']):>8.3f} "
            f"{_avg(stats['d2']):>8.3f} "
            f"{_avg(stats['d3']):>8.3f} "
            f"{_avg(stats['d4']):>8.3f}"
        )

    print("\n" + "=" * 100)
    print("逐条详细评分")
    print("=" * 100)
    for r in sorted(results, key=lambda x: (x["game"], x["model"])):
        scores = r["scores"]
        d1 = _normalize_dimension_data(scores, "d1_executability")
        d2 = _normalize_dimension_data(scores, "d2_functionality")
        d3 = _normalize_dimension_data(scores, "d3_code_quality")
        d4 = _normalize_dimension_data(scores, "d4_ux")
        print(f"\n游戏: {r['game']}")
        print(f"模型: {r['model']}")
        print(f"代码: {r['code_path']}")
        print(f"最终得分: {scores['total_score']:.3f}")
        print(f"公式: {scores.get('final_score_formula', 'Final Score = 0.2*D1 + 0.5*D2 + 0.15*D3 + 0.15*D4')}")
        _print_dimension_block("Dimension1 可执行性", d1)
        _print_dimension_block("Dimension2 功能正确性", d2)
        _print_dimension_block("Dimension3 代码质量", d3)
        _print_dimension_block("Dimension4 用户体验", d4)

    games = sorted(set(r["game"] for r in results))
    models = sorted(set(r["model"] for r in results))
    print(f"\n共 {len(results)} 条记录，{len(models)} 个模型，{len(games)} 个游戏")
    print("=" * 100)


if __name__ == "__main__":
    latest = find_latest_run()
    if not latest:
        print("未找到任何评分结果，请先运行 run_pipeline.py")
    else:
        print(f"读取结果: {latest.name}")
        results = load_summary(latest)
        print_results(results)
