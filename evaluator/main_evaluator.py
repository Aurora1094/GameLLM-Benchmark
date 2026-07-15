from pathlib import Path
from typing import Any

from .ability_mapper import map_features_to_abilities
from .dimension1.dimension1_executable import evaluate_dimension1
from .dimension2_functionality import evaluate_dimension2
from .dimension3.dimension3_code_quality import evaluate_dimension3_code_quality
from .dimension4.dimension4_ux import evaluate_dimension4_ux


def _build_runtime_signals_from_dim1(dim1_result: dict[str, Any]) -> dict[str, bool]:
    indicators = dim1_result.get("indicators", {})
    has_event_handling = bool(indicators.get("event_handling_mechanism", 0))
    has_window = bool(indicators.get("window_creation", 0))
    stable_runtime = bool(indicators.get("short_runtime_stable", 0))
    controllable_exit = bool(indicators.get("process_controllability", 0))

    return {
        "state_changed": has_event_handling and stable_runtime,
        "input_effective": has_event_handling,
        "feedback_visible": has_window,
        "terminated": controllable_exit,
    }


def evaluate_submission(
    game_id: str,
    code_path: Path,
    spec_path: Path | None = None,
) -> dict:
    dim1_result = evaluate_dimension1(code_path=code_path)
    executable = float(dim1_result.get("score", 0.0))
    d1_gate_pass = bool(dim1_result.get("gate_pass", executable >= 1.0))

    runtime_signals = _build_runtime_signals_from_dim1(dim1_result)
    if d1_gate_pass:
        functionality_result = evaluate_dimension2(
            game_id=game_id,
            code_path=code_path,
            runtime_signals=runtime_signals,
            spec_path=spec_path,
        )
        functionality = float(functionality_result.score)

        code_quality_result = evaluate_dimension3_code_quality(code_path=code_path)
        code_quality = float(code_quality_result["score_normalized"])

        ux_result = evaluate_dimension4_ux(code_path=code_path)
        ux = float(ux_result["score_normalized"])
        functionality_raw = functionality_result.passed
        functionality_breakdown = functionality_result.criteria_scores
        ux_breakdown = {
            "visual": ux_result["visual"]["score"],
            "smoothness": ux_result["smoothness"]["score"],
            "balance": ux_result["balance"]["score"],
            "audio_animation": ux_result["audio_animation"]["score"],
        }
    else:
        functionality = 0.0
        code_quality = 0.0
        ux = 0.0
        functionality_raw = 0
        functionality_breakdown = {}
        code_quality_result = {
            "reason": "D1 gate failed; D3 skipped because the game did not pass the executable harness.",
            "indicator_scores": {},
        }
        ux_breakdown = {}

    weights = {
        "executable": 0.2,
        "functionality": 0.5,
        "code_quality": 0.15,
        "ux": 0.15,
    }

    total = (
        executable * weights["executable"]
        + functionality * weights["functionality"]
        + code_quality * weights["code_quality"]
        + ux * weights["ux"]
    )

    ability_breakdown = map_features_to_abilities(["basic_collision", "food_generation"])

    return {
        "game_id": game_id,
        "code_path": str(code_path),
        "scores": {
            "executable": executable,
            "executable_detail": dim1_result,
            "executable_gate_pass": d1_gate_pass,
            "executable_weighted": executable * weights["executable"],
            "functionality": functionality,
            "functionality_raw": functionality_raw,
            "functionality_breakdown": functionality_breakdown,
            "functionality_runtime_signals": runtime_signals,
            "functionality_weighted": functionality * weights["functionality"],
            "code_quality": code_quality,
            "code_quality_breakdown": code_quality_result.get("indicator_scores", {}),
            "code_quality_weighted": code_quality * weights["code_quality"],
            "ux": ux,
            "ux_breakdown": ux_breakdown,
            "ux_weighted": ux * weights["ux"],
            "total": total,
            "final_score_formula": "D1 score is pipeline_steps_passed / 6; D2-D4 run only when D1 gate_pass is true. Final Score = 0.2 * Dimension1 + 0.5 * Dimension2 + 0.15 * Dimension3 + 0.15 * Dimension4",
        },
        "weights": weights,
        "ability_breakdown": ability_breakdown,
    }
