from __future__ import annotations

import ast
import importlib
import inspect
import re
from pathlib import Path
from typing import Any

from .base import FunctionalityResult

CRITERIA = (
    "rule_completeness",
    "state_evolution",
    "interaction_validity",
    "goal_feedback_alignment",
    "constraint_termination",
)

STATE_VAR_HINTS = {
    "x",
    "y",
    "dx",
    "dy",
    "vx",
    "vy",
    "pos",
    "position",
    "velocity",
    "speed",
    "direction",
    "score",
    "points",
    "lives",
    "health",
    "length",
    "state",
    "running",
    "game_over",
}

# 约定的最小 runtime 信号键；值为 True/False，由外部执行器注入。
RUNTIME_KEYS = {
    "state_changed",
    "input_effective",
    "feedback_visible",
    "terminated",
}

# game_id -> 模块名，统一使用 difficulty_game 命名。
GAME_MODULE_ROUTE = {
    "easy_dodge_blocks": "easy_dodge_blocks",
    "easy_flappy_bird": "easy_flappy_bird",
    "easy_maze_runner": "easy_maze_runner",
    "easy_pong": "easy_pong",
    "easy_snake": "easy_snake",
    "medium_breakout": "medium_breakout",
    "medium_space_invaders": "medium_space_invaders",
    "medium_tetris": "medium_tetris",
    "hard_platformer": "hard_platformer",
    "hard_roguelike_dungeon": "hard_roguelike_dungeon",
}


def evaluate_dimension2(
    game_id: str,
    code_path: Path | str,
    runtime_signals: dict[str, bool] | None = None,
) -> FunctionalityResult:
    """Unified entry for dimension2.

    For now this returns the cross-game generic score only. Per-game logic
    can be plugged in later behind this entry without changing callers.
    """
    # 先尝试路由到游戏独立文件；若未实现则回退通用评分。
    module_name = _resolve_game_module_name(game_id)
    game_specific_result, route_meta = _call_game_specific_evaluator(
        module_name=module_name,
        game_id=game_id,
        code_path=code_path,
        runtime_signals=runtime_signals,
    )
    if game_specific_result is not None:
        game_specific_result.evidence.setdefault("route", route_meta)
        return game_specific_result

    result = evaluate_general_functionality(
        code_path=code_path,
        runtime_signals=runtime_signals,
    )
    route_meta["used_game_specific"] = False
    result.evidence.setdefault("route", route_meta)
    return result


def evaluate_general_functionality(
    code_path: Path | str,
    source_code: str | None = None,
    runtime_signals: dict[str, bool] | None = None,
) -> FunctionalityResult:
    source = source_code if source_code is not None else _read_source(code_path)
    tree = _safe_parse(source)
    runtime = _normalize_runtime_signals(runtime_signals)

    criteria_scores: dict[str, int] = {}
    reasons: dict[str, str] = {}
    evidence: dict[str, Any] = {"runtime_signals": runtime, "evidence_strength": {}}
    review_required: list[str] = []

    # 指标1：规则闭合性 Rule Completeness
    criteria_scores["rule_completeness"], reasons["rule_completeness"], indicator_evidence = (
        _evaluate_indicator_1_rule_completeness(source, tree, runtime)
    )
    evidence["rule_completeness"] = indicator_evidence
    evidence["evidence_strength"]["rule_completeness"] = _classify_strength(indicator_evidence)
    if _needs_review(indicator_evidence):
        review_required.append("rule_completeness")

    # 指标2：状态演化性 State Evolution
    criteria_scores["state_evolution"], reasons["state_evolution"], indicator_evidence = (
        _evaluate_indicator_2_state_evolution(source, runtime)
    )
    evidence["state_evolution"] = indicator_evidence
    evidence["evidence_strength"]["state_evolution"] = _classify_strength(indicator_evidence)
    if _needs_review(indicator_evidence):
        review_required.append("state_evolution")

    # 指标3：交互有效性 Interaction Validity
    criteria_scores["interaction_validity"], reasons["interaction_validity"], indicator_evidence = (
        _evaluate_indicator_3_interaction_validity(source, runtime)
    )
    evidence["interaction_validity"] = indicator_evidence
    evidence["evidence_strength"]["interaction_validity"] = _classify_strength(indicator_evidence)
    if _needs_review(indicator_evidence):
        review_required.append("interaction_validity")

    # 指标4：目标与反馈一致性 Goal-Feedback Alignment
    criteria_scores["goal_feedback_alignment"], reasons["goal_feedback_alignment"], indicator_evidence = (
        _evaluate_indicator_4_goal_feedback_alignment(source, runtime)
    )
    evidence["goal_feedback_alignment"] = indicator_evidence
    evidence["evidence_strength"]["goal_feedback_alignment"] = _classify_strength(indicator_evidence)
    if _needs_review(indicator_evidence):
        review_required.append("goal_feedback_alignment")

    # 指标5：约束与终止机制 Constraint & Termination
    criteria_scores["constraint_termination"], reasons["constraint_termination"], indicator_evidence = (
        _evaluate_indicator_5_constraint_termination(source, runtime)
    )
    evidence["constraint_termination"] = indicator_evidence
    evidence["evidence_strength"]["constraint_termination"] = _classify_strength(indicator_evidence)
    if _needs_review(indicator_evidence):
        review_required.append("constraint_termination")

    raw_score = sum(criteria_scores.values())
    evidence["review_required"] = review_required

    return FunctionalityResult(
        passed=raw_score,
        total=10,
        criteria_scores=criteria_scores,
        reasons=reasons,
        evidence=evidence,
    )


def _read_source(code_path: Path | str) -> str:
    return Path(code_path).read_text(encoding="utf-8", errors="ignore")


def _safe_parse(source: str) -> ast.AST | None:
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


def _has_any_keyword(source: str, keywords: list[str]) -> bool:
    lower = source.lower()
    return any(k.lower() in lower for k in keywords)


def _normalize_runtime_signals(runtime_signals: dict[str, bool] | None) -> dict[str, bool]:
    normalized = {key: False for key in RUNTIME_KEYS}
    if runtime_signals is None:
        normalized["__provided__"] = False
        return normalized
    for key in RUNTIME_KEYS:
        if key in runtime_signals:
            normalized[key] = bool(runtime_signals[key])
    normalized["__provided__"] = True
    return normalized


def _normalize_game_id(game_id: str) -> str:
    normalized = game_id.strip().lower()
    normalized = normalized.replace("-", "_").replace("/", "_").replace(" ", "_")
    normalized = re.sub(r"_+", "_", normalized)
    return normalized


def _resolve_game_module_name(game_id: str) -> str | None:
    normalized = _normalize_game_id(game_id)
    if normalized in GAME_MODULE_ROUTE:
        return GAME_MODULE_ROUTE[normalized]

    # 兼容形如 snake_easy / pong_medium 的写法。
    for key, module_name in GAME_MODULE_ROUTE.items():
        difficulty, game = key.split("_", 1)
        if normalized == f"{game}_{difficulty}":
            return module_name

    return None


def _call_game_specific_evaluator(
    module_name: str | None,
    game_id: str,
    code_path: Path | str,
    runtime_signals: dict[str, bool] | None,
) -> tuple[FunctionalityResult | None, dict[str, Any]]:
    route_meta: dict[str, Any] = {
        "module": module_name,
        "used_game_specific": False,
        "status": "fallback",
        "reason": "module_not_mapped",
    }

    if not module_name:
        return None, route_meta

    try:
        module = importlib.import_module(f".{module_name}", package=__package__)
    except Exception as ex:
        route_meta["reason"] = f"import_error:{type(ex).__name__}"
        return None, route_meta

    route_meta["reason"] = "no_callable_evaluator"

    # 兼容多个函数名，便于逐步迁移老文件。
    for func_name in ("evaluate_dimension2", "evaluate", "evaluate_game"):
        evaluator = getattr(module, func_name, None)
        if not callable(evaluator):
            continue
        result = _invoke_evaluator(evaluator, game_id, code_path, runtime_signals)
        if result is None:
            route_meta["reason"] = f"invoke_failed:{func_name}"
            continue
        route_meta["used_game_specific"] = True
        route_meta["status"] = "game_specific"
        route_meta["reason"] = f"ok:{func_name}"
        return _coerce_result(result), route_meta

    return None, route_meta


def _invoke_evaluator(
    evaluator: Any,
    game_id: str,
    code_path: Path | str,
    runtime_signals: dict[str, bool] | None,
) -> Any:
    try:
        sig = inspect.signature(evaluator)
    except Exception:
        try:
            return evaluator(code_path)
        except Exception:
            return None

    kwargs: dict[str, Any] = {}
    for name in sig.parameters:
        if name == "game_id":
            kwargs[name] = game_id
        elif name == "code_path":
            kwargs[name] = code_path
        elif name == "runtime_signals":
            kwargs[name] = runtime_signals

    try:
        return evaluator(**kwargs)
    except Exception:
        return None


def _coerce_result(result: Any) -> FunctionalityResult:
    if isinstance(result, FunctionalityResult):
        return result

    if isinstance(result, dict):
        passed = int(result.get("passed", 0))
        total = int(result.get("total", 10))
        return FunctionalityResult(
            passed=passed,
            total=total,
            criteria_scores=result.get("criteria_scores", {}),
            reasons=result.get("reasons", {}),
            evidence=result.get("evidence", {}),
        )

    return FunctionalityResult(passed=0, total=10)


def _evaluate_indicator_1_rule_completeness(
    source: str,
    tree: ast.AST | None,
    runtime: dict[str, bool],
) -> tuple[int, str, dict[str, Any]]:
    has_rule_condition = _has_any_keyword(
        source,
        ["if", "elif", "collision", "collide", "hit", "eat", "overlap"],
    )
    has_rule_trigger = _has_any_keyword(
        source,
        ["collide", "collision", "hit", "intersect", "eat", "contact"],
    )
    has_state_change = _has_state_update(tree, source, STATE_VAR_HINTS)
    has_feedback = _has_any_keyword(
        source,
        ["score", "game over", "win", "lose", "render", "draw", "font", "text"],
    )
    runtime_state_changed = runtime["state_changed"]
    runtime_feedback_visible = runtime["feedback_visible"]

    evidence = {
        "indicator": 1,
        "has_rule_condition": has_rule_condition,
        "has_rule_trigger": has_rule_trigger,
        "has_state_change": has_state_change,
        "has_feedback": has_feedback,
        "runtime_state_changed": runtime_state_changed,
        "runtime_feedback_visible": runtime_feedback_visible,
        "runtime_conflict": (has_rule_trigger and has_state_change) and not runtime_state_changed,
    }

    # 红线：连规则触发都不存在时直接0分。
    if not has_rule_trigger:
        return 0, "No core rule loop evidence found.", evidence

    if (
        has_rule_condition
        and has_rule_trigger
        and has_state_change
        and has_feedback
        and (runtime_state_changed or runtime_feedback_visible)
    ):
        return 2, "Detected complete behavior-result-feedback loop.", evidence

    # 规则闭合的前提必须是存在规则触发，避免纯UI/文本代码拿分。
    if has_rule_trigger and (has_state_change or has_feedback):
        return 1, "Detected partial rule loop evidence.", evidence

    return 0, "Rule trigger exists but no reliable effect/feedback evidence.", evidence


def _evaluate_indicator_2_state_evolution(
    source: str,
    runtime: dict[str, bool],
) -> tuple[int, str, dict[str, Any]]:
    has_main_loop = _has_any_keyword(source, ["while", "game_loop", "running"])
    has_frame_loop = _has_any_keyword(source, ["for event in", "event.get", "pygame.event"])
    has_update_cycle = _has_any_keyword(source, ["update(", "draw(", "render("])
    # 游戏循环不等于 while；包含事件轮询和 update 周期同样可构成演化机制。
    has_loop = has_main_loop or has_frame_loop or has_update_cycle
    has_tick = _has_any_keyword(source, ["clock.tick", "tick(", "dt", "delta", "time"])
    has_motion_update = bool(
        re.search(r"\b(x|y|pos|position|velocity|speed)\b\s*([+\-*/]?=)", source)
    ) or _has_any_keyword(source, ["move(", "update("])
    runtime_state_changed = runtime["state_changed"]

    evidence = {
        "indicator": 2,
        "has_main_loop": has_main_loop,
        "has_frame_loop": has_frame_loop,
        "has_update_cycle": has_update_cycle,
        "has_loop": has_loop,
        "has_tick": has_tick,
        "has_motion_update": has_motion_update,
        "runtime_state_changed": runtime_state_changed,
        "runtime_conflict": has_loop and has_motion_update and not runtime_state_changed,
    }

    if not has_loop:
        return 0, "No continuous evolution loop detected.", evidence

    if has_motion_update and (has_tick or has_main_loop or has_update_cycle):
        if has_tick and has_motion_update and has_main_loop and runtime_state_changed:
            return 2, "Detected sustained loop with temporal and state updates.", evidence
        return 1, "Detected loop with partial evolution signals.", evidence

    return 0, "Loop exists but lacks credible evolving state updates.", evidence


def _evaluate_indicator_3_interaction_validity(
    source: str,
    runtime: dict[str, bool],
) -> tuple[int, str, dict[str, Any]]:
    has_input_capture = _has_any_keyword(
        source,
        ["event.get", "keydown", "key_up", "get_pressed", "pygame.key", "mouse", "keyboard"],
    )
    has_input_branch = _has_any_keyword(
        source,
        ["if event", "if key", "pygame.k_", "keys["],
    )
    has_input_effect = bool(
        re.search(r"\b(direction|x|y|velocity|speed|player|snake)\b\s*([+\-*/]?=)", source)
    )
    has_key_symbols = _has_any_keyword(source, ["pygame.k_", "k_left", "k_right", "k_up", "k_down"])
    runtime_input_effective = runtime["input_effective"]

    evidence = {
        "indicator": 3,
        "has_input_capture": has_input_capture,
        "has_input_branch": has_input_branch,
        "has_input_effect": has_input_effect,
        "has_key_symbols": has_key_symbols,
        "runtime_input_effective": runtime_input_effective,
        "runtime_conflict": (has_input_capture and has_input_branch) and not runtime_input_effective,
    }

    # 红线：没有输入捕获即0分。
    if not has_input_capture:
        return 0, "No reliable input capture detected.", evidence

    if has_input_capture and has_input_branch and has_input_effect and runtime_input_effective:
        return 2, "Detected input capture with observable state effect.", evidence

    if (has_input_branch and has_input_effect) or (has_input_branch and has_key_symbols):
        return 1, "Detected input handling with weak state-effect evidence.", evidence

    return 0, "Input capture exists but no reliable interaction effect detected.", evidence


def _evaluate_indicator_4_goal_feedback_alignment(
    source: str,
    runtime: dict[str, bool],
) -> tuple[int, str, dict[str, Any]]:
    has_goal = _has_any_keyword(
        source,
        ["win", "lose", "goal", "target", "level", "success", "fail"],
    )
    has_score_logic = _has_any_keyword(source, ["score", "points", "reward"])
    has_feedback_output = _has_any_keyword(
        source,
        ["render", "draw", "font", "text", "blit", "print(score", "hud"],
    )
    has_feedback_update = bool(re.search(r"\b(score|points|level)\b\s*([+\-*/]?=)", source))
    runtime_feedback_visible = runtime["feedback_visible"]

    evidence = {
        "indicator": 4,
        "has_goal": has_goal,
        "has_score_logic": has_score_logic,
        "has_feedback_output": has_feedback_output,
        "has_feedback_update": has_feedback_update,
        "runtime_feedback_visible": runtime_feedback_visible,
        "runtime_conflict": (has_score_logic and has_feedback_output) and not runtime_feedback_visible,
    }

    if not has_goal and not has_score_logic:
        return 0, "No clear goal or feedback signal detected.", evidence

    if has_score_logic and has_feedback_output:
        if runtime_feedback_visible and has_feedback_update:
            return 2, "Detected aligned goal and feedback signals.", evidence
        return 1, "Detected score-feedback path but runtime visibility is limited.", evidence

    if has_goal and has_feedback_output and runtime_feedback_visible:
        return 2, "Detected goal-feedback alignment with runtime support.", evidence

    if has_feedback_output or has_score_logic:
        return 1, "Detected partial goal-feedback signals.", evidence

    return 0, "Goal exists but no observable feedback alignment.", evidence


def _evaluate_indicator_5_constraint_termination(
    source: str,
    runtime: dict[str, bool],
) -> tuple[int, str, dict[str, Any]]:
    has_constraint = _has_any_keyword(
        source,
        [
            "wall",
            "boundary",
            "out_of_bounds",
            "width",
            "height",
            "collision",
            "hit",
        ],
    )
    has_end_condition = _has_any_keyword(
        source,
        ["game_over", "win", "lose", "done", "running = false", "running=false", "running=False"],
    )
    has_termination_action = _has_any_keyword(
        source,
        ["break", "return", "quit", "sys.exit", "pygame.quit"],
    )
    runtime_terminated = runtime["terminated"]
    runtime_provided = bool(runtime.get("__provided__", False))
    runtime_state_changed = runtime["state_changed"]

    evidence = {
        "indicator": 5,
        "has_constraint": has_constraint,
        "has_end_condition": has_end_condition,
        "has_termination_action": has_termination_action,
        "runtime_terminated": runtime_terminated,
        "runtime_provided": runtime_provided,
        "runtime_state_changed": runtime_state_changed,
        "runtime_conflict": (has_end_condition or has_termination_action) and not runtime_terminated,
    }

    # 红线：没有终止条件时必须0分。
    if not has_end_condition and not has_termination_action:
        return 0, "No clear termination mechanism detected.", evidence

    # 若 runtime 未提供或未触发终止，但能确认系统在演化，可放行 2 分，避免长循环样本系统性低估。
    if (
        has_end_condition
        and has_termination_action
        and has_constraint
        and (runtime_terminated or (not runtime_provided) or runtime_state_changed)
    ):
        return 2, "Detected constraints with explicit termination flow.", evidence

    # 收紧 1 分条件，避免仅出现关键词文本就给分。
    if has_end_condition and has_termination_action:
        return 1, "Detected partial constraint/termination signals.", evidence

    return 0, "Termination evidence is insufficient.", evidence


def _classify_strength(evidence: dict[str, Any]) -> str:
    static_true = 0
    runtime_true = 0
    for key, value in evidence.items():
        if key.startswith("runtime_"):
            if isinstance(value, bool) and value:
                runtime_true += 1
            continue
        if isinstance(value, bool) and value:
            static_true += 1

    # 简单三档：便于报告展示与后续阈值调优。
    if runtime_true >= 1 and static_true >= 3:
        return "strong"
    if static_true >= 2:
        return "medium"
    return "weak"


def _needs_review(evidence: dict[str, Any]) -> bool:
    # 静态强而runtime弱时，标记人工复核，避免误判高分。
    static_true = 0
    runtime_true = 0
    runtime_conflict = bool(evidence.get("runtime_conflict", False))

    for key, value in evidence.items():
        if not isinstance(value, bool):
            continue
        if key.startswith("runtime_"):
            runtime_true += int(value)
        else:
            static_true += int(value)

    return runtime_conflict or (static_true >= 3 and runtime_true == 0)


def _has_state_update(tree: ast.AST | None, source: str, hints: set[str]) -> bool:
    if tree is None:
        pattern = r"\b(" + "|".join(sorted(hints)) + r")\b\s*([+\-*/]?=)"
        return bool(re.search(pattern, source))

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            target_names = _extract_target_names(node)
            if any(name in hints for name in target_names):
                return True
    return False


def _extract_target_names(node: ast.AST) -> set[str]:
    names: set[str] = set()

    def _collect(target: ast.AST) -> None:
        if isinstance(target, ast.Name):
            names.add(target.id.lower())
            return
        if isinstance(target, ast.Attribute):
            names.add(target.attr.lower())
            return
        if isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                _collect(elt)

    if isinstance(node, ast.Assign):
        for t in node.targets:
            _collect(t)
    elif isinstance(node, ast.AugAssign):
        _collect(node.target)
    elif isinstance(node, ast.AnnAssign):
        _collect(node.target)

    return names
