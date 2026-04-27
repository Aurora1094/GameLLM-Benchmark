from __future__ import annotations

import ast
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any


WRAPPER_CODE = textwrap.dedent(
    """
    import os
    import runpy
    import sys
    import traceback
    import time

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

    frame_count = 0
    loop_count = 0
    start = time.time()

    try:
        import pygame

        original_set_mode = pygame.display.set_mode
        original_flip = pygame.display.flip
        original_update = pygame.display.update
        original_clock_cls = pygame.time.Clock

        def wrapped_set_mode(*args, **kwargs):
            print("__WINDOW_CREATED__", flush=True)
            return original_set_mode(*args, **kwargs)

        def wrapped_flip(*args, **kwargs):
            nonlocal_frame_count = globals().get("frame_count", 0) + 1
            globals()["frame_count"] = nonlocal_frame_count
            return original_flip(*args, **kwargs)

        def wrapped_update(*args, **kwargs):
            nonlocal_frame_count = globals().get("frame_count", 0) + 1
            globals()["frame_count"] = nonlocal_frame_count
            return original_update(*args, **kwargs)

        class WrappedClock:
            def __init__(self, *args, **kwargs):
                self._clock = original_clock_cls(*args, **kwargs)

            def tick(self, *args, **kwargs):
                nonlocal_frame_count = globals().get("frame_count", 0) + 1
                globals()["frame_count"] = nonlocal_frame_count
                return self._clock.tick(*args, **kwargs)

            def __getattr__(self, name):
                return getattr(self._clock, name)

        pygame.display.set_mode = wrapped_set_mode
        pygame.display.flip = wrapped_flip
        pygame.display.update = wrapped_update
        pygame.time.Clock = WrappedClock
    except Exception:
        pass

    try:
        runpy.run_path(sys.argv[1], run_name="__main__")
    except Exception:
        traceback.print_exc()
        sys.exit(1)
    finally:
        duration = max(1e-6, time.time() - start)
        print(f"__RUNTIME_DURATION__:{duration:.6f}", flush=True)
        print(f"__FRAME_COUNT__:{globals().get('frame_count', 0)}", flush=True)
        try:
            import pygame
            pygame.quit()
        except Exception:
            pass
    """
)


def _safe_read_text(code_path: Path) -> str:
    return code_path.read_text(encoding="utf-8-sig", errors="ignore").lstrip("\ufeff")


def _parse_source(source: str) -> ast.AST | None:
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


def _run_program(code_path: Path, runtime_sec: int) -> dict[str, Any]:
    process = subprocess.Popen(
        [sys.executable, "-c", WRAPPER_CODE, str(code_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=runtime_sec)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        stdout, stderr = process.communicate(timeout=2)

    return {
        "returncode": process.returncode,
        "stdout": stdout or "",
        "stderr": stderr or "",
        "timed_out": timed_out,
    }


def _line_text(node: ast.AST) -> str:
    return ast.dump(node, annotate_fields=False, include_attributes=False)


def _extract_string_literals(tree: ast.AST) -> list[str]:
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append(node.value)
    return out


def _extract_numeric_literals(tree: ast.AST) -> list[float]:
    nums: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            nums.append(float(node.value))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            operand = node.operand
            if isinstance(operand, ast.Constant) and isinstance(operand.value, (int, float)):
                nums.append(-float(operand.value))
    return nums


def _extract_rgb_tuples(tree: ast.AST) -> set[tuple[int, int, int]]:
    colors: set[tuple[int, int, int]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Tuple):
            continue
        if len(node.elts) != 3:
            continue
        values: list[int] = []
        valid = True
        for elt in node.elts:
            if not isinstance(elt, ast.Constant) or not isinstance(elt.value, int):
                valid = False
                break
            if elt.value < 0 or elt.value > 255:
                valid = False
                break
            values.append(elt.value)
        if valid:
            colors.add((values[0], values[1], values[2]))
    return colors


# =========================
# 维度 1：视觉表现（25）
# =========================
def _score_visual(source: str, tree: ast.AST) -> dict[str, Any]:
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    rgb_values = _extract_rgb_tuples(tree)
    strings = [s.lower() for s in _extract_string_literals(tree)]

    has_fill_or_color = (
        "fill(" in source
        or "Color(" in source
        or any(c for c in calls if isinstance(c.func, ast.Attribute) and c.func.attr in {"fill", "Color"})
    )
    has_text = (
        "font.render" in source
        or any(c for c in calls if isinstance(c.func, ast.Attribute) and c.func.attr == "render")
        or any("score" in s or "game over" in s for s in strings)
    )
    layout_draw_calls = sum(
        1
        for c in calls
        if isinstance(c.func, ast.Attribute) and c.func.attr in {"rect", "circle", "line", "polygon", "blit"}
    )
    has_layout = layout_draw_calls >= 2

    score = 0
    if has_fill_or_color:
        score += 5
    if len(rgb_values) >= 3:
        score += 5
    if has_text:
        score += 10
    if has_layout:
        score += 5

    return {
        "score": min(25, score),
        "max_score": 25,
        "indicators": {
            "has_color_rendering": int(has_fill_or_color),
            "multi_color_rgb_ge_3": int(len(rgb_values) >= 3),
            "has_text_rendering": int(has_text),
            "has_layout_structure": int(has_layout),
        },
        "details": {
            "rgb_tuple_count": len(rgb_values),
            "layout_draw_calls": layout_draw_calls,
        },
    }


# =========================
# 维度 2：操作流畅性（35）
# =========================
def _parse_runtime_marker(stdout: str, marker: str) -> float | None:
    for line in stdout.splitlines():
        if line.startswith(marker):
            raw = line.split(":", 1)[-1].strip()
            try:
                return float(raw)
            except ValueError:
                return None
    return None


def _has_infinite_busy_risk(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.While):
            continue
        if not isinstance(node.test, ast.Constant) or node.test.value is not True:
            continue

        local_calls = [n for n in ast.walk(node) if isinstance(n, ast.Call)]
        has_local_tick_or_sleep = any(
            isinstance(call.func, ast.Attribute) and call.func.attr == "tick"
            or isinstance(call.func, ast.Attribute) and call.func.attr == "sleep"
            for call in local_calls
        )
        has_local_event_poll = any(
            isinstance(call.func, ast.Attribute)
            and call.func.attr in {"get", "poll"}
            and isinstance(call.func.value, ast.Attribute)
            and call.func.value.attr == "event"
            for call in local_calls
        )

        if not has_local_tick_or_sleep and not has_local_event_poll:
            return True
    return False


def _score_smoothness(source: str, tree: ast.AST, run_result: dict[str, Any]) -> dict[str, Any]:
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    has_loop = any(isinstance(n, ast.While) for n in ast.walk(tree))
    has_event = any(
        isinstance(c.func, ast.Attribute)
        and c.func.attr in {"get", "poll"}
        and isinstance(c.func.value, ast.Attribute)
        and c.func.value.attr == "event"
        for c in calls
    ) or "pygame.event" in source
    has_clock = any(isinstance(c.func, ast.Attribute) and c.func.attr == "Clock" for c in calls) or "Clock(" in source
    has_tick = any(isinstance(c.func, ast.Attribute) and c.func.attr == "tick" for c in calls) or ".tick(" in source

    score = 0
    if has_loop:
        score += 5
    if has_event:
        score += 10
    if has_clock:
        score += 10
    if has_tick:
        score += 10

    crashed = (run_result["returncode"] != 0) and (not run_result["timed_out"])
    busy_risk = _has_infinite_busy_risk(tree)
    if crashed:
        score = min(score, 15)
    if busy_risk:
        score = max(0, score - 10)

    duration = _parse_runtime_marker(run_result["stdout"], "__RUNTIME_DURATION__")
    frame_count = _parse_runtime_marker(run_result["stdout"], "__FRAME_COUNT__")
    sampled_fps = None
    if duration and frame_count is not None and duration > 0:
        sampled_fps = frame_count / duration

    return {
        "score": min(35, max(0, score)),
        "max_score": 35,
        "indicators": {
            "has_main_loop": int(has_loop),
            "has_event_handling": int(has_event),
            "has_clock_control": int(has_clock),
            "has_tick_fps_limit": int(has_tick),
            "runtime_crash": int(crashed),
            "busy_loop_risk": int(busy_risk),
        },
        "details": {
            "timed_out": run_result["timed_out"],
            "returncode": run_result["returncode"],
            "sampled_fps": sampled_fps,
        },
    }


# =========================
# 维度 3：游戏平衡性（20）
# =========================
BALANCE_KEYWORDS = {
    "speed",
    "difficulty",
    "level",
    "spawn",
    "interval",
    "hp",
    "health",
    "life",
}

PROTECTION_KEYWORDS = {
    "reset",
    "restart",
    "respawn",
    "invincible",
    "life",
    "continue",
}

ANIMATION_NAME_HINTS = {
    "x",
    "y",
    "pos",
    "rect",
    "snake",
    "player",
}


def _is_balance_related_name(name: str) -> bool:
    lower = name.lower()
    return any(k in lower for k in BALANCE_KEYWORDS)


def _is_animation_related_name(name: str) -> bool:
    lower = name.lower()
    return any(k in lower for k in ANIMATION_NAME_HINTS)


def _score_balance(source: str, tree: ast.AST) -> dict[str, Any]:
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id.lower())
        if isinstance(node, ast.FunctionDef):
            names.add(node.name.lower())

    strings = [s.lower() for s in _extract_string_literals(tree)]
    full_text = "\n".join([source.lower(), "\n".join(strings), "\n".join(sorted(names))])

    parametric_vars: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and _is_balance_related_name(target.id):
                    parametric_vars.add(target.id.lower())
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if _is_balance_related_name(node.target.id):
                parametric_vars.add(node.target.id.lower())

    has_parametric_difficulty = len(parametric_vars) > 0

    has_progressive_change = False
    for node in ast.walk(tree):
        if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
            name = node.target.id.lower()
            if _is_balance_related_name(name) and isinstance(
                node.op,
                (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow),
            ):
                has_progressive_change = True
                break
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    n = target.id.lower()
                    if _is_balance_related_name(n):
                        value_repr = _line_text(node.value).lower()
                        has_arithmetic = isinstance(node.value, (ast.BinOp, ast.UnaryOp))
                        has_progress_signal = any(mark in value_repr for mark in {"score", "time", "level", n})
                        if has_arithmetic and has_progress_signal:
                            has_progressive_change = True
                            break

    has_protection_or_recovery = any(k in full_text for k in PROTECTION_KEYWORDS)

    score = 0
    if has_parametric_difficulty:
        score += 6
    if has_progressive_change:
        score += 8
    if has_protection_or_recovery:
        score += 6

    return {
        "score": min(20, score),
        "max_score": 20,
        "indicators": {
            "has_parametric_difficulty": int(has_parametric_difficulty),
            "has_progressive_difficulty": int(has_progressive_change),
            "has_protection_or_recovery": int(has_protection_or_recovery),
        },
        "details": {},
    }


# =========================
# 维度 4：音效与动画（20）
# =========================
def _score_audio_animation(source: str, tree: ast.AST) -> dict[str, Any]:
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]

    draw_calls = sum(
        1
        for c in calls
        if isinstance(c.func, ast.Attribute) and c.func.attr in {"rect", "circle", "line", "polygon", "blit"}
    )
    has_multiple_objects = draw_calls >= 3

    has_animation = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.AugAssign):
            continue

        if isinstance(node.target, ast.Name) and _is_animation_related_name(node.target.id):
            has_animation = True
            break

        if isinstance(node.target, ast.Attribute) and _is_animation_related_name(node.target.attr):
            has_animation = True
            break

    has_sound = (
        "mixer.sound" in source.lower()
        or "mixer.music" in source.lower()
        or any(
            isinstance(c.func, ast.Attribute)
            and c.func.attr in {"Sound", "play", "load"}
            and isinstance(c.func.value, ast.Attribute)
            and c.func.value.attr in {"mixer", "music"}
            for c in calls
        )
    )

    score = 0
    if has_multiple_objects:
        score += 8
    if has_animation:
        score += 6
    if has_sound:
        score += 6

    return {
        "score": min(20, score),
        "max_score": 20,
        "indicators": {
            "has_multiple_visual_objects": int(has_multiple_objects),
            "has_animation_update": int(has_animation),
            "has_sound_system": int(has_sound),
        },
        "details": {
            "draw_calls": draw_calls,
        },
    }


def _build_reason(result: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("visual", "smoothness", "balance", "audio_animation"):
        sec = result[key]
        parts.append(f"{key}:{sec['score']}/{sec['max_score']}")
    return " | ".join(parts)


def evaluate_dimension4_ux(code_path: Path | str, runtime_sec: int = 5) -> dict[str, Any]:
    target = Path(code_path)
    if not target.exists():
        return {
            "score": 0,
            "score_normalized": 0.0,
            "reason": f"代码文件不存在: {target}",
            "visual": {"score": 0, "max_score": 25, "indicators": {}, "details": {}},
            "smoothness": {"score": 0, "max_score": 35, "indicators": {}, "details": {}},
            "balance": {"score": 0, "max_score": 20, "indicators": {}, "details": {}},
            "audio_animation": {"score": 0, "max_score": 20, "indicators": {}, "details": {}},
            "runtime": {"file_found": False},
        }

    source = _safe_read_text(target)
    tree = _parse_source(source)
    if tree is None:
        return {
            "score": 0,
            "score_normalized": 0.0,
            "reason": "Python 语法错误，无法进行维度4评估。",
            "visual": {"score": 0, "max_score": 25, "indicators": {}, "details": {}},
            "smoothness": {"score": 0, "max_score": 35, "indicators": {}, "details": {}},
            "balance": {"score": 0, "max_score": 20, "indicators": {}, "details": {}},
            "audio_animation": {"score": 0, "max_score": 20, "indicators": {}, "details": {}},
            "runtime": {"file_found": True, "syntax_ok": False},
        }

    run_result = _run_program(target, runtime_sec=runtime_sec)

    visual = _score_visual(source, tree)
    smoothness = _score_smoothness(source, tree, run_result)
    balance = _score_balance(source, tree)
    audio_animation = _score_audio_animation(source, tree)

    total = visual["score"] + smoothness["score"] + balance["score"] + audio_animation["score"]

    result = {
        "score": total,
        "score_normalized": total / 100.0,
        "visual": visual,
        "smoothness": smoothness,
        "balance": balance,
        "audio_animation": audio_animation,
        "runtime": {
            "file_found": True,
            "timed_out": run_result["timed_out"],
            "returncode": run_result["returncode"],
            "window_created_marker": "__WINDOW_CREATED__" in run_result["stdout"],
            "stderr_tail": run_result["stderr"][-500:],
        },
    }
    result["reason"] = _build_reason(result)
    return result


def score_ux(
    frame_stability: float = 0.0,
    ui_feedback_score: float = 0.0,
    code_path: Path | str | None = None,
) -> float:
    """兼容旧接口，同时支持基于代码文件的维度4正式评分。"""
    if code_path is not None:
        result = evaluate_dimension4_ux(code_path=code_path)
        return result["score_normalized"]

    # 旧版兼容: 保持 main_evaluator 当前示例调用不崩。
    return max(0.0, min(1.0, frame_stability * 0.5 + ui_feedback_score * 0.5))
