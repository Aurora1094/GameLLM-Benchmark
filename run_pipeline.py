"""GameLLM-Benchmark 主流程入口。"""
import json
from datetime import datetime
from pathlib import Path

import yaml

# from llm_clients.client_openai import call_openai
from config import ROOT_DIR
from evaluator.dimension1.dimension1_executable import evaluate_dimension1
from evaluator.dimension2_functionality import evaluate_dimension2
from evaluator.dimension3.dimension3_code_quality import evaluate_dimension3_code_quality
from evaluator.dimension4.dimension4_ux import evaluate_dimension4_ux
from llm_clients.client_anthropic import call_anthropic
from llm_clients.client_bedrock import call_bedrock
from llm_clients.client_qwen_or_gemini import call_gemini, call_qwen


def load_config(config_file: Path) -> dict:
    with open(config_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def call_llm(provider: str, model: str, prompt: str) -> str:
    if provider == "openai":
        return call_openai(prompt, model)
    if provider == "anthropic":
        return call_anthropic(prompt, model)
    if provider == "qwen":
        return call_qwen(prompt, model)
    if provider == "gemini":
        return call_gemini(prompt, model)
    if provider == "bedrock":
        return call_bedrock(prompt, model)
    raise ValueError(f"不支持的 provider: {provider}")


def _build_runtime_signals_from_dim1(dim1_result: dict) -> dict[str, bool]:
    indicators = dim1_result.get("indicators", {})
    runtime_info = dim1_result.get("runtime", {})
    diagnosis = str(runtime_info.get("diagnosis", "")).lower()
    has_event_handling = bool(indicators.get("event_handling_mechanism", 0))
    has_window = bool(indicators.get("window_creation", 0))

    return {
        "state_changed": has_event_handling and diagnosis in {"loop_running", "normal_exit"},
        "input_effective": has_event_handling,
        "feedback_visible": has_window,
        "terminated": (not runtime_info.get("timed_out", False)) and runtime_info.get("returncode", 1) == 0,
    }


def _build_indicator_list(scores: dict, max_scores: dict | None = None) -> list[dict]:
    items = []
    for name, score in scores.items():
        item = {"name": name, "score": float(score)}
        if max_scores and name in max_scores:
            item["max_score"] = float(max_scores[name])
        items.append(item)
    return items


def evaluate_code(game_name: str, code_path: Path, weights: dict) -> dict:
    d1_result = evaluate_dimension1(code_path)
    d1_score = float(d1_result["score"])

    runtime_signals = _build_runtime_signals_from_dim1(d1_result)
    d2_result = evaluate_dimension2(game_id=game_name, code_path=code_path, runtime_signals=runtime_signals)
    d2_score = float(d2_result.score)

    d3_result = evaluate_dimension3_code_quality(code_path)
    d3_score = float(d3_result["score_normalized"])

    d4_result = evaluate_dimension4_ux(code_path)
    d4_score = float(d4_result["score_normalized"])

    total_score = (
        d1_score * weights["executability"]
        + d2_score * weights["functionality"]
        + d3_score * weights["code_quality"]
        + d4_score * weights["ux"]
    )

    return {
        "d1_executability": {
            "score": d1_score,
            "raw_score": float(sum(d1_result.get("indicators", {}).values())),
            "max_score": float(len(d1_result.get("indicators", {}))),
            "weighted_contribution": d1_score * weights["executability"],
            "indicators": _build_indicator_list(
                d1_result.get("indicators", {}),
                {key: 1.0 for key in d1_result.get("indicators", {})},
            ),
            "details": d1_result,
        },
        "d2_functionality": {
            "score": d2_score,
            "raw_score": float(d2_result.passed),
            "max_score": float(d2_result.total),
            "weighted_contribution": d2_score * weights["functionality"],
            "indicators": _build_indicator_list(
                d2_result.criteria_scores,
                {key: 2.0 for key in d2_result.criteria_scores},
            ),
            "details": d2_result.to_dict(),
        },
        "d3_code_quality": {
            "score": d3_score,
            "raw_score": float(d3_result["score"]),
            "max_score": 100.0,
            "weighted_contribution": d3_score * weights["code_quality"],
            "indicators": _build_indicator_list(
                d3_result.get("indicator_scores", {}),
                {
                    "modularity": 20.0,
                    "reuse": 20.0,
                    "naming": 15.0,
                    "comments": 15.0,
                    "constants": 15.0,
                    "complexity": 15.0,
                },
            ),
            "details": d3_result,
        },
        "d4_ux": {
            "score": d4_score,
            "raw_score": float(d4_result["score"]),
            "max_score": 100.0,
            "weighted_contribution": d4_score * weights["ux"],
            "indicators": [
                {
                    "name": "visual",
                    "score": float(d4_result["visual"]["score"]),
                    "max_score": float(d4_result["visual"]["max_score"]),
                    "sub_indicators": _build_indicator_list(
                        d4_result["visual"].get("indicators", {}),
                        {key: 1.0 for key in d4_result["visual"].get("indicators", {})},
                    ),
                },
                {
                    "name": "smoothness",
                    "score": float(d4_result["smoothness"]["score"]),
                    "max_score": float(d4_result["smoothness"]["max_score"]),
                    "sub_indicators": _build_indicator_list(
                        d4_result["smoothness"].get("indicators", {}),
                        {key: 1.0 for key in d4_result["smoothness"].get("indicators", {})},
                    ),
                },
                {
                    "name": "balance",
                    "score": float(d4_result["balance"]["score"]),
                    "max_score": float(d4_result["balance"]["max_score"]),
                    "sub_indicators": _build_indicator_list(
                        d4_result["balance"].get("indicators", {}),
                        {key: 1.0 for key in d4_result["balance"].get("indicators", {})},
                    ),
                },
                {
                    "name": "audio_animation",
                    "score": float(d4_result["audio_animation"]["score"]),
                    "max_score": float(d4_result["audio_animation"]["max_score"]),
                    "sub_indicators": _build_indicator_list(
                        d4_result["audio_animation"].get("indicators", {}),
                        {key: 1.0 for key in d4_result["audio_animation"].get("indicators", {})},
                    ),
                },
            ],
            "details": d4_result,
        },
        "total_score": total_score,
        "weights": weights,
        "final_score_formula": (
            "Final Score = 0.2 * Dimension1 + 0.5 * Dimension2 + "
            "0.15 * Dimension3 + 0.15 * Dimension4"
        ),
    }


def main():
    print("=" * 60)
    print("GameLLM-Benchmark Pipeline 启动")
    print("=" * 60)

    config_dir = ROOT_DIR / "config"
    games_config = load_config(config_dir / "games.yaml")
    models_config = load_config(config_dir / "models.yaml")
    weights_config = load_config(config_dir / "weights.yaml")

    weights = dict(weights_config["dimension_weights"])
    weights.update(
        {
            "executability": 0.2,
            "functionality": 0.5,
            "code_quality": 0.15,
            "ux": 0.15,
        }
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_dir = ROOT_DIR / "data" / "raw" / timestamp
    scores_dir = ROOT_DIR / "data" / "scores" / timestamp
    raw_dir.mkdir(parents=True, exist_ok=True)
    scores_dir.mkdir(parents=True, exist_ok=True)

    all_games = []
    for difficulty, game_list in games_config["games"].items():
        for game in game_list:
            all_games.append({"difficulty": difficulty, "name": game})

    print(f"\n共 {len(all_games)} 个游戏，{len(models_config['models'])} 个模型")
    print(f"总计 {len(all_games) * len(models_config['models'])} 个测试任务\n")

    all_results = []

    for game_info in all_games:
        difficulty = game_info["difficulty"]
        game_name = game_info["name"]
        prompt_file = ROOT_DIR / "prompts" / difficulty / game_name / "prompt.txt"

        if not prompt_file.exists():
            print(f"[SKIP] 跳过 {game_name}，prompt 文件不存在")
            continue

        with open(prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read()

        print(f"\n{'=' * 60}")
        print(f"游戏: {game_name} ({difficulty})")
        print(f"{'=' * 60}")

        for model_config in models_config["models"]:
            model_name = model_config["name"]
            provider = model_config["provider"]

            print(f"\n  模型: {model_name}")

            try:
                print(f"    -> 调用 {provider} API...")
                generated_code = call_llm(provider, model_name, prompt)

                safe_model_name = model_name.replace("/", "_").replace(":", "_")
                code_filename = f"{game_name}_{safe_model_name}.py"
                code_path = raw_dir / code_filename
                with open(code_path, "w", encoding="utf-8") as f:
                    f.write(generated_code)
                print(f"    -> 代码已保存: {code_filename}")

                print("    -> 开始评分...")
                scores = evaluate_code(game_name, code_path, weights)

                result = {
                    "game": game_name,
                    "difficulty": difficulty,
                    "model": model_name,
                    "provider": provider,
                    "timestamp": timestamp,
                    "code_path": str(code_path),
                    "scores": scores,
                }
                all_results.append(result)

                result_filename = f"{game_name}_{safe_model_name}.json"
                result_path = scores_dir / result_filename
                with open(result_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)

                print(f"    [OK] 最终得分: {scores['total_score']:.3f}")
                print(
                    "      - D1 可执行性: "
                    f"{scores['d1_executability']['score']:.3f} "
                    f"(raw {scores['d1_executability']['raw_score']:.0f}/{scores['d1_executability']['max_score']:.0f})"
                )
                print(
                    "      - D2 功能正确性: "
                    f"{scores['d2_functionality']['score']:.3f} "
                    f"(raw {scores['d2_functionality']['raw_score']:.0f}/{scores['d2_functionality']['max_score']:.0f})"
                )
                print(
                    "      - D3 代码质量: "
                    f"{scores['d3_code_quality']['score']:.3f} "
                    f"(raw {scores['d3_code_quality']['raw_score']:.0f}/{scores['d3_code_quality']['max_score']:.0f})"
                )
                print(
                    "      - D4 用户体验: "
                    f"{scores['d4_ux']['score']:.3f} "
                    f"(raw {scores['d4_ux']['raw_score']:.0f}/{scores['d4_ux']['max_score']:.0f})"
                )
            except Exception as e:
                print(f"    [ERR] 错误: {str(e)}")
                continue

    summary_path = scores_dir / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print("测试完成")
    print(f"  - 原始代码: {raw_dir}")
    print(f"  - 评分结果: {scores_dir}")
    print(f"  - 汇总报告: {summary_path}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
