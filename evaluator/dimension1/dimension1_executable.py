from __future__ import annotations

import ast
import importlib.util
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any


# 指标 2/4/6 的动态执行包装器：
# - 在子进程中运行目标代码
# - 拦截 pygame.display.set_mode 打标记
# - 发生异常时返回非零退出码
WRAPPER_CODE = textwrap.dedent(
    """
    import os
    import runpy
    import sys
    import traceback

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

    try:
        import pygame
        original_set_mode = pygame.display.set_mode

        def wrapped_set_mode(*args, **kwargs):
            print("__WINDOW_CREATED__", flush=True)
            return original_set_mode(*args, **kwargs)

        pygame.display.set_mode = wrapped_set_mode
    except Exception:
        pass

    try:
        runpy.run_path(sys.argv[1], run_name="__main__")
    except Exception:
        traceback.print_exc()
        sys.exit(1)
    finally:
        try:
            import pygame
            pygame.quit()
        except Exception:
            pass
    """
)


def _safe_read_text(code_path: Path) -> str:
    # 兼容 UTF-8 BOM，避免 ast.parse 被 BOM 干扰。
    source = code_path.read_text(encoding="utf-8-sig", errors="ignore")
    return source.lstrip("\ufeff")


def _empty_indicators() -> dict[str, int]:
    return {
        "python_syntax_correct": 0,
        "short_runtime_stable": 0,
        "dependency_initialization_complete": 0,
        "window_creation": 0,
        "event_handling_mechanism": 0,
        "process_controllability": 0,
    }


def _build_numbered_reason(indicators: dict[str, int]) -> str:
    # 按 1~6 编号输出失败原因，便于和评分指标一一对应。
    failures: list[str] = []

    if indicators["python_syntax_correct"] == 0:
        failures.append("1. Python 语法不正确，代码无法被解释器解析。")
    if indicators["short_runtime_stable"] == 0:
        failures.append("2. 短时间运行不稳定，程序在 3~5 秒内异常退出或崩溃。")
    if indicators["dependency_initialization_complete"] == 0:
        failures.append("3. 依赖初始化不完整，未检测到 pygame 导入语句。")
    if indicators["window_creation"] == 0:
        failures.append("4. 未能确认窗口创建（静态或动态信号均未满足）。")
    if indicators["event_handling_mechanism"] == 0:
        failures.append("5. 事件处理机制不足，未检测到 pygame.event.get() 或 pygame.event.poll()。")
    if indicators["process_controllability"] == 0:
        failures.append("6. 进程可控性不足，存在不可控循环或资源占用风险。")

    if not failures:
        return "全部通过：1~6 指标均满足。"

    return " | ".join(failures)


def _run_for_stability(code_path: Path, runtime_sec: int) -> dict[str, Any]:
    # 子进程运行一次，结果给指标 2/4/6 复用。
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
        "stdout": stdout,
        "stderr": stderr,
        "timed_out": timed_out,
    }


def _parse_source_once(source: str) -> ast.AST | None:
    # 统一做一次 AST 解析，给指标 1/3 复用，减少重复解析开销。
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


def _build_runtime_diagnosis(run_result: dict[str, Any], pygame_available: bool) -> str:
    # 给运行态打细粒度标签，便于统计窗口创建率/循环运行率/崩溃率。
    stdout_text = run_result.get("stdout") or ""
    if "__WINDOW_CREATED__" in stdout_text:
        return "window_created"

    if run_result["timed_out"]:
        return "loop_running"

    if run_result["returncode"] == 0:
        return "normal_exit"

    stderr_text = (run_result.get("stderr") or "").lower()
    if (not pygame_available) and ("no module named 'pygame'" in stderr_text):
        return "env_missing_pygame"
    return "crash"


# =========================
# 指标 1：Python 语法正确性
# =========================
def _indicator_1_python_syntax_correct(parsed_tree: ast.AST | None) -> int:
    return 1 if parsed_tree is not None else 0


# =========================
# 指标 2：短时间运行稳定（3~5 秒）
# =========================
def _indicator_2_short_runtime_stable(run_result: dict[str, Any]) -> int:
    crashed = (run_result["returncode"] != 0) and (not run_result["timed_out"])
    return 0 if crashed else 1


# =========================
# 指标 3：依赖初始化完整性
# =========================
def _indicator3_imports_pygame(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(alias.name == "pygame" for alias in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module == "pygame":
            return True
    return False


def _indicator_3_dependency_initialization_complete(tree: ast.AST) -> int:
    ok_import = _indicator3_imports_pygame(tree)
    return 1 if ok_import else 0


# =========================
# 指标 4：能打开窗口
# =========================
def _indicator4_has_set_mode_call(source: str) -> bool:
    return bool(re.search(r"pygame\.display\.set_mode\s*\(", source))


def _indicator_4_window_creation(source: str, run_result: dict[str, Any]) -> int:
    static_ok = _indicator4_has_set_mode_call(source)
    dynamic_ok = "__WINDOW_CREATED__" in (run_result["stdout"] or "")
    # 优先使用动态证据；无动态证据时回退到静态证据。
    if dynamic_ok:
        return 1
    return 1 if static_ok else 0


# =========================
# 指标 5：事件处理机制
# =========================
def _indicator5_has_event_get_or_poll(source: str) -> bool:
    return bool(re.search(r"pygame\.event\.(get|poll)\s*\(", source))


def _indicator5_has_event_iteration_or_branch(source: str) -> bool:
    # 检测是否存在“对事件结果的处理结构”，降低空调用误判。
    has_for_get = bool(re.search(r"for\s+\w+\s+in\s+pygame\.event\.get\s*\(", source))
    has_poll_assign = bool(re.search(r"\w+\s*=\s*pygame\.event\.poll\s*\(", source))
    has_event_if = bool(re.search(r"if\s+.*event", source))
    return has_for_get or (has_poll_assign and has_event_if)


def _indicator_5_event_handling_mechanism(source: str) -> int:
    has_event_fetch = _indicator5_has_event_get_or_poll(source)
    has_event_structure = _indicator5_has_event_iteration_or_branch(source)
    return 1 if (has_event_fetch and has_event_structure) else 0


# =========================
# 指标 6：进程可控性
# =========================
def _indicator6_has_busy_loop_risk(source: str) -> bool:
    simple_busy_loop = bool(re.search(r"while\s+True\s*:\s*(pass|continue)\b", source))
    if simple_busy_loop:
        return True

    has_while_true = bool(re.search(r"while\s+True\s*:", source))
    if not has_while_true:
        return False

    has_event_polling = bool(re.search(r"pygame\.event\.(get|poll)\s*\(", source))
    has_sleep_or_tick = bool(re.search(r"(time\.sleep\s*\(|\.tick\s*\()", source))
    return not (has_event_polling or has_sleep_or_tick)


def _indicator_6_process_controllability(source: str, run_result: dict[str, Any]) -> int:
    busy_risk = _indicator6_has_busy_loop_risk(source)
    if busy_risk:
        return 0
    if run_result["timed_out"]:
        return 1
    if run_result["returncode"] == 0:
        return 1
    return 0


def evaluate_dimension1(code_path: Path | str, runtime_sec: int = 5) -> dict[str, Any]:
    target = Path(code_path)

    if not target.exists():
        indicators = _empty_indicators()
        return {
            "score": 0,
            "indicators": indicators,
            "reason": f"0. 代码文件不存在：{target}。",
            "runtime": {
                "file_found": False,
            },
        }

    source = _safe_read_text(target)
    runtime_pygame_available = importlib.util.find_spec("pygame") is not None
    parsed_tree = _parse_source_once(source)

    # 1) 语法
    indicator_1 = _indicator_1_python_syntax_correct(parsed_tree)
    if indicator_1 == 0:
        indicators = _empty_indicators()
        return {
            "score": 0,
            "indicators": indicators,
            "reason": "1. Python 语法不正确，代码无法被解释器解析；2~6 指标未执行。",
            "runtime": {
                "file_found": True,
                "pygame_available": runtime_pygame_available,
                "env_notice": "若评测环境未安装 pygame，动态指标可能受影响。" if not runtime_pygame_available else "",
            },
        }

    # 2/4/6 共享一次动态执行
    run_result = _run_for_stability(target, runtime_sec=runtime_sec)

    # 2) 短时稳定
    indicator_2 = _indicator_2_short_runtime_stable(run_result)

    # 3) 依赖初始化
    indicator_3 = _indicator_3_dependency_initialization_complete(parsed_tree)

    # 4) 窗口创建
    indicator_4 = _indicator_4_window_creation(source, run_result)

    # 5) 事件机制
    indicator_5 = _indicator_5_event_handling_mechanism(source)

    # 6) 进程可控
    indicator_6 = _indicator_6_process_controllability(source, run_result)

    indicators = {
        "python_syntax_correct": indicator_1,
        "short_runtime_stable": indicator_2,
        "dependency_initialization_complete": indicator_3,
        "window_creation": indicator_4,
        "event_handling_mechanism": indicator_5,
        "process_controllability": indicator_6,
    }

    total_binary_score = 1 if all(value == 1 for value in indicators.values()) else 0
    runtime_diagnosis = _build_runtime_diagnosis(run_result, runtime_pygame_available)

    return {
        "score": total_binary_score,
        "indicators": indicators,
        "runtime": {
            "file_found": True,
            "timed_out": run_result["timed_out"],
            "returncode": run_result["returncode"],
            "pygame_available": runtime_pygame_available,
            "diagnosis": runtime_diagnosis,
            "window_created_marker": "__WINDOW_CREATED__" in (run_result["stdout"] or ""),
            "stderr_tail": (run_result["stderr"] or "")[-500:],
            "env_notice": "若评测环境未安装 pygame，动态指标可能受影响。" if not runtime_pygame_available else "",
        },
        "reason": _build_numbered_reason(indicators),
    }


def check_executable(run_ok: bool, crash_count: int) -> float:
    # 保留旧接口，兼容已有调用。
    if not run_ok:
        return 0.0
    return max(0.0, 1.0 - crash_count * 0.1)
