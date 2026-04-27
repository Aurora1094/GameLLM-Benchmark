import argparse
import json
import re
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


ROOT_DIR = Path(__file__).resolve().parents[1]
SCORES_DIR = ROOT_DIR / "data" / "scores"
FIGURES_DIR = ROOT_DIR / "analysis" / "figures"

DIMENSIONS = {
    "d1_executability": "Executability",
    "d2_functionality": "Functionality",
    "d3_code_quality": "Code Quality",
    "d4_ux": "UX",
}

WEIGHT_KEYS = {
    "d1_executability": "executability",
    "d2_functionality": "functionality",
    "d3_code_quality": "code_quality",
    "d4_ux": "ux",
}

DIFFICULTY_ORDER = ["easy", "medium", "hard"]


def find_latest_run() -> Path:
    runs = sorted(path for path in SCORES_DIR.iterdir() if path.is_dir())
    if not runs:
        raise FileNotFoundError(f"No score runs found under {SCORES_DIR}")
    return runs[-1]


def resolve_summary_path(run: str | None, summary: str | None) -> Path:
    if summary:
        path = Path(summary)
        return path if path.is_absolute() else ROOT_DIR / path

    if run:
        path = Path(run)
        run_dir = path if path.is_absolute() else SCORES_DIR / path
    else:
        run_dir = find_latest_run()

    return run_dir / "summary.json"


def load_results(summary_path: Path) -> list[dict[str, Any]]:
    if not summary_path.exists():
        raise FileNotFoundError(f"Summary file not found: {summary_path}")
    with open(summary_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected a list of result records in {summary_path}")
    return data


def short_model_name(model: str) -> str:
    aliases = {
        "amazon.nova-pro-v1:0": "Nova Pro",
        "deepseek.v3.2": "DeepSeek V3.2",
        "qwen.qwen3-coder-next": "Qwen Coder",
    }
    return aliases.get(model, model)


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")


def dimension_score(scores: dict[str, Any], key: str) -> float:
    return float(scores.get(key, {}).get("score", 0.0))


def dimension_weighted_contribution(scores: dict[str, Any], key: str) -> float:
    data = scores.get(key, {})
    if "weighted_contribution" in data:
        return float(data["weighted_contribution"])
    weights = scores.get("weights", {})
    return dimension_score(scores, key) * float(weights.get(WEIGHT_KEYS[key], 0.0))


def iter_indicators(dimension_data: dict[str, Any], key: str) -> list[dict[str, float | str]]:
    indicators = dimension_data.get("indicators")
    if isinstance(indicators, list):
        rows = []
        for item in indicators:
            if not isinstance(item, dict):
                continue
            if "sub_indicators" in item:
                max_score = float(item.get("max_score", 0.0))
                score = float(item.get("score", 0.0))
                rows.append(
                    {
                        "indicator": str(item.get("name", "")),
                        "score": score,
                        "max_score": max_score,
                        "normalized": score / max_score if max_score else 0.0,
                    }
                )
                continue
            max_score = float(item.get("max_score", 1.0))
            score = float(item.get("score", 0.0))
            rows.append(
                {
                    "indicator": str(item.get("name", "")),
                    "score": score,
                    "max_score": max_score,
                    "normalized": score / max_score if max_score else score,
                }
            )
        return rows

    details = dimension_data.get("details", {})
    if not isinstance(details, dict):
        return []

    if key == "d1_executability":
        return [
            {"indicator": name, "score": float(score), "max_score": 1.0, "normalized": float(score)}
            for name, score in details.get("indicators", {}).items()
        ]

    if key == "d2_functionality":
        return [
            {
                "indicator": name,
                "score": float(score),
                "max_score": 2.0,
                "normalized": float(score) / 2.0,
            }
            for name, score in details.get("criteria_scores", {}).items()
        ]

    if key == "d3_code_quality":
        max_scores = {
            "modularity": 20.0,
            "reuse": 20.0,
            "naming": 15.0,
            "comments": 15.0,
            "constants": 15.0,
            "complexity": 15.0,
        }
        return [
            {
                "indicator": name,
                "score": float(score),
                "max_score": max_scores.get(name, 1.0),
                "normalized": float(score) / max_scores.get(name, 1.0),
            }
            for name, score in details.get("indicator_scores", {}).items()
        ]

    if key == "d4_ux":
        rows = []
        for name in ("visual", "smoothness", "balance", "audio_animation"):
            section = details.get(name)
            if isinstance(section, dict):
                score = float(section.get("score", 0.0))
                max_score = float(section.get("max_score", 0.0))
                rows.append(
                    {
                        "indicator": name,
                        "score": score,
                        "max_score": max_score,
                        "normalized": score / max_score if max_score else 0.0,
                    }
                )
        return rows

    return []


def build_frames(results: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows = []
    indicator_rows = []

    for item in results:
        scores = item.get("scores", {})
        base = {
            "game": item.get("game", ""),
            "difficulty": item.get("difficulty", ""),
            "model": item.get("model", ""),
            "model_short": short_model_name(str(item.get("model", ""))),
            "provider": item.get("provider", ""),
            "timestamp": item.get("timestamp", ""),
            "total_score": float(scores.get("total_score", 0.0)),
        }

        for key, label in DIMENSIONS.items():
            base[label] = dimension_score(scores, key)
            base[f"{label} Contribution"] = dimension_weighted_contribution(scores, key)

            dimension_data = scores.get(key, {})
            for row in iter_indicators(dimension_data, key):
                indicator_rows.append(
                    {
                        **{k: base[k] for k in ("game", "difficulty", "model", "model_short", "timestamp")},
                        "dimension": label,
                        **row,
                    }
                )

        summary_rows.append(base)

    return pd.DataFrame(summary_rows), pd.DataFrame(indicator_rows)


def setup_style() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams.update(
        {
            "figure.dpi": 140,
            "savefig.dpi": 220,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "axes.titlesize": 15,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
        }
    )


def save_figure(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()


def plot_overall_ranking(df: pd.DataFrame, out_dir: Path) -> None:
    ranking = (
        df.groupby("model_short", as_index=False)["total_score"]
        .mean()
        .sort_values("total_score", ascending=True)
    )
    plt.figure(figsize=(8.5, 4.8))
    ax = sns.barplot(data=ranking, x="total_score", y="model_short", hue="model_short", palette="Set2", legend=False)
    ax.set_title("Overall Model Ranking")
    ax.set_xlabel("Mean Total Score")
    ax.set_ylabel("")
    ax.set_xlim(0, max(1.0, float(ranking["total_score"].max()) * 1.12))
    for container in ax.containers:
        ax.bar_label(container, fmt="%.3f", padding=4, fontsize=9)
    save_figure(out_dir / "01_overall_model_ranking.png")


def plot_model_game_heatmap(df: pd.DataFrame, out_dir: Path) -> None:
    pivot = df.pivot_table(index="game", columns="model_short", values="total_score", aggfunc="mean")
    pivot = pivot.loc[pivot.mean(axis=1).sort_values(ascending=False).index]
    plt.figure(figsize=(9, max(4.5, len(pivot) * 0.45)))
    ax = sns.heatmap(pivot, annot=True, fmt=".2f", cmap="viridis", vmin=0, vmax=1, linewidths=0.5)
    ax.set_title("Model Performance by Game")
    ax.set_xlabel("")
    ax.set_ylabel("")
    save_figure(out_dir / "02_model_game_heatmap.png")


def plot_dimension_profile(df: pd.DataFrame, out_dir: Path) -> None:
    dim_cols = list(DIMENSIONS.values())
    profile = df.groupby("model_short", as_index=False)[dim_cols].mean()
    long = profile.melt(id_vars="model_short", var_name="dimension", value_name="score")
    plt.figure(figsize=(10, 5))
    ax = sns.barplot(data=long, x="dimension", y="score", hue="model_short", palette="Set2")
    ax.set_title("Capability Profile by Dimension")
    ax.set_xlabel("")
    ax.set_ylabel("Mean Score")
    ax.set_ylim(0, 1)
    ax.legend(title="")
    save_figure(out_dir / "03_dimension_profile.png")


def plot_weighted_contributions(df: pd.DataFrame, out_dir: Path) -> None:
    contribution_cols = [f"{label} Contribution" for label in DIMENSIONS.values()]
    model_contrib = df.groupby("model_short")[contribution_cols].mean()
    model_contrib.columns = list(DIMENSIONS.values())
    ax = model_contrib.plot(kind="bar", stacked=True, figsize=(9, 5), color=sns.color_palette("Set2", 4))
    ax.set_title("Weighted Score Contributions")
    ax.set_xlabel("")
    ax.set_ylabel("Mean Weighted Contribution")
    ax.set_ylim(0, max(1.0, float(model_contrib.sum(axis=1).max()) * 1.15))
    ax.legend(title="", bbox_to_anchor=(1.02, 1), loc="upper left")
    save_figure(out_dir / "04_weighted_score_contributions.png")


def plot_difficulty_trend(df: pd.DataFrame, out_dir: Path) -> None:
    available_order = [d for d in DIFFICULTY_ORDER if d in set(df["difficulty"])]
    if len(available_order) < 2:
        return
    difficulty = (
        df.groupby(["difficulty", "model_short"], as_index=False)["total_score"]
        .mean()
        .assign(difficulty=lambda data: pd.Categorical(data["difficulty"], available_order, ordered=True))
        .sort_values("difficulty")
    )
    plt.figure(figsize=(8.5, 5))
    ax = sns.lineplot(
        data=difficulty,
        x="difficulty",
        y="total_score",
        hue="model_short",
        marker="o",
        linewidth=2.3,
        palette="Set2",
    )
    ax.set_title("Performance Across Difficulty Levels")
    ax.set_xlabel("")
    ax.set_ylabel("Mean Total Score")
    ax.set_ylim(0, 1)
    ax.legend(title="")
    save_figure(out_dir / "05_difficulty_trend.png")


def plot_indicator_heatmaps(indicators: pd.DataFrame, out_dir: Path) -> None:
    if indicators.empty:
        return

    for dimension in DIMENSIONS.values():
        subset = indicators[indicators["dimension"] == dimension]
        if subset.empty:
            continue
        pivot = subset.pivot_table(index="indicator", columns="model_short", values="normalized", aggfunc="mean")
        pivot = pivot.loc[pivot.mean(axis=1).sort_values(ascending=True).index]
        plt.figure(figsize=(8.5, max(3.8, len(pivot) * 0.42)))
        ax = sns.heatmap(pivot, annot=True, fmt=".2f", cmap="mako", vmin=0, vmax=1, linewidths=0.5)
        ax.set_title(f"{dimension} Indicator Diagnosis")
        ax.set_xlabel("")
        ax.set_ylabel("")
        save_figure(out_dir / f"06_{safe_name(dimension).lower()}_indicator_heatmap.png")


def export_tables(df: pd.DataFrame, indicators: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "summary_flat.csv", index=False, encoding="utf-8-sig")
    indicators.to_csv(out_dir / "indicator_flat.csv", index=False, encoding="utf-8-sig")

    model_table = df.groupby("model_short", as_index=False)[
        ["total_score", *DIMENSIONS.values()]
    ].mean().sort_values("total_score", ascending=False)
    model_table.to_csv(out_dir / "model_summary.csv", index=False, encoding="utf-8-sig")

    game_table = df.pivot_table(index="game", columns="model_short", values="total_score", aggfunc="mean")
    game_table.to_csv(out_dir / "model_game_matrix.csv", encoding="utf-8-sig")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate visualization figures for GameLLM-Benchmark results.")
    parser.add_argument("--run", help="Run directory name under data/scores, for example 20260416_233830.")
    parser.add_argument("--summary", help="Direct path to a summary.json file.")
    parser.add_argument("--out", help="Output directory. Defaults to analysis/figures/<run-name>.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary_path = resolve_summary_path(args.run, args.summary)
    results = load_results(summary_path)

    run_name = summary_path.parent.name
    out_dir = Path(args.out) if args.out else FIGURES_DIR / run_name
    if not out_dir.is_absolute():
        out_dir = ROOT_DIR / out_dir

    setup_style()
    df, indicators = build_frames(results)
    if df.empty:
        raise ValueError(f"No result records found in {summary_path}")

    export_tables(df, indicators, out_dir)
    plot_overall_ranking(df, out_dir)
    plot_model_game_heatmap(df, out_dir)
    plot_dimension_profile(df, out_dir)
    plot_weighted_contributions(df, out_dir)
    plot_difficulty_trend(df, out_dir)
    plot_indicator_heatmaps(indicators, out_dir)

    print(f"Summary: {summary_path}")
    print(f"Records: {len(df)}")
    print(f"Models: {df['model_short'].nunique()}")
    print(f"Games: {df['game'].nunique()}")
    print(f"Output: {out_dir}")


if __name__ == "__main__":
    main()
