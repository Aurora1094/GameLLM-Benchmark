from __future__ import annotations

import ast
import importlib.util
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any


WINDOW_MARKER = "__D1_WINDOW_CREATED__"
SURFACE_MARKER = "__D1_WINDOW_SURFACE__"
EVENT_MARKER = "__D1_EVENT_FETCH__"
QUIT_MARKER = "__D1_QUIT_POSTED__"


# D1 is a deterministic harness: no LLM calls, just static parsing and two
# short subprocess probes under pygame's dummy video driver.
WRAPPER_CODE = textwrap.dedent(
    """
    import os
    import runpy
    import sys
    import threading
    import time
    import traceback

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

    WINDOW_MARKER = "__D1_WINDOW_CREATED__"
    SURFACE_MARKER = "__D1_WINDOW_SURFACE__"
    EVENT_MARKER = "__D1_EVENT_FETCH__"
    QUIT_MARKER = "__D1_QUIT_POSTED__"

    mode = sys.argv[2] if len(sys.argv) > 2 else "stability"
    emitted = set()

    def emit_once(marker):
        if marker not in emitted:
            emitted.add(marker)
            print(marker, flush=True)

    try:
        import pygame

        original_set_mode = pygame.display.set_mode

        def wrapped_set_mode(*args, **kwargs):
            surface = original_set_mode(*args, **kwargs)
            emit_once(WINDOW_MARKER)
            try:
                if isinstance(surface, pygame.Surface):
                    emit_once(SURFACE_MARKER)
            except Exception:
                pass
            return surface

        pygame.display.set_mode = wrapped_set_mode

        original_get = pygame.event.get
        original_poll = pygame.event.poll

        def wrapped_get(*args, **kwargs):
            emit_once(EVENT_MARKER)
            return original_get(*args, **kwargs)

        def wrapped_poll(*args, **kwargs):
            emit_once(EVENT_MARKER)
            return original_poll(*args, **kwargs)

        pygame.event.get = wrapped_get
        pygame.event.poll = wrapped_poll

        def post_quit_repeatedly():
            time.sleep(1.0)
            deadline = time.time() + 3.0
            while time.time() < deadline:
                try:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                    emit_once(QUIT_MARKER)
                except Exception:
                    pass
                time.sleep(0.1)

        if mode == "quit":
            threading.Thread(target=post_quit_repeatedly, daemon=True).start()
    except Exception:
        pass

    try:
        runpy.run_path(sys.argv[1], run_name="__main__")
    except SystemExit as exc:
        code = exc.code
        if code is None:
            code = 0
        if not isinstance(code, int):
            code = 1
        sys.exit(code)
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


INDICATOR_ORDER: list[tuple[str, str]] = [
    ("python_syntax_correct", "Python 语法正确性"),
    ("dependency_initialization_complete", "导入 pygame"),
    ("window_creation", "图形窗口创建能力"),
    ("event_handling_mechanism", "事件循环处理完整性"),
    ("short_runtime_stable", "短时间运行稳定性"),
    ("process_controllability", "执行进程可控性"),
]


def _safe_read_text(code_path: Path) -> str:
    source = code_path.read_text(encoding="utf-8-sig", errors="ignore")
    return source.lstrip("\ufeff")


def _empty_indicators() -> dict[str, int]:
    return {key: 0 for key, _ in INDICATOR_ORDER}


def _parse_source_once(source: str) -> ast.AST | None:
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


def _attribute_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _attribute_name(node.value)
        if parent:
            return f"{parent}.{node.attr}"
    return None


def _imports_pygame(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == "pygame" for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if node.module == "pygame" or (node.module or "").startswith("pygame."):
                return True
    return False


def _subprocess_can_import_pygame(timeout_sec: int = 5) -> bool:
    env = os.environ.copy()
    env.setdefault("SDL_VIDEODRIVER", "dummy")
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import pygame"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_sec,
            env=env,
        )
    except Exception:
        return False
    return result.returncode == 0


def _has_event_fetch_call(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _attribute_name(node.func) in {
            "pygame.event.get",
            "pygame.event.poll",
        }:
            return True
    return False


def _has_event_loop_shape(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.For):
            iter_call = node.iter
            if isinstance(iter_call, ast.Call) and _attribute_name(iter_call.func) == "pygame.event.get":
                return True
        if isinstance(node, ast.Assign):
            value = node.value
            if isinstance(value, ast.Call) and _attribute_name(value.func) == "pygame.event.poll":
                return True
    return False


def _has_busy_loop_risk(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.While):
            continue
        if not (isinstance(node.test, ast.Constant) and node.test.value is True):
            continue

        body = node.body
        if len(body) == 1 and isinstance(body[0], (ast.Pass, ast.Continue)):
            return True

        has_event_fetch = any(
            isinstance(child, ast.Call)
            and _attribute_name(child.func) in {"pygame.event.get", "pygame.event.poll"}
            for child in ast.walk(node)
        )
        has_timing_control = any(
            isinstance(child, ast.Call)
            and (
                _attribute_name(child.func) == "time.sleep"
                or (
                    isinstance(child.func, ast.Attribute)
                    and child.func.attr == "tick"
                )
            )
            for child in ast.walk(node)
        )
        if not (has_event_fetch or has_timing_control):
            return True
    return False


def _run_probe(code_path: Path, mode: str, timeout_sec: int) -> dict[str, Any]:
    process = subprocess.Popen(
        [sys.executable, "-c", WRAPPER_CODE, str(code_path), mode],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        stdout, stderr = process.communicate(timeout=2)

    return {
        "mode": mode,
        "returncode": process.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "timed_out": timed_out,
        "window_created": WINDOW_MARKER in stdout,
        "surface_returned": SURFACE_MARKER in stdout,
        "event_fetch_seen": EVENT_MARKER in stdout,
        "quit_posted": QUIT_MARKER in stdout,
    }


def _pipeline_steps_passed(indicators: dict[str, int]) -> int:
    passed = 0
    for key, _ in INDICATOR_ORDER:
        if indicators.get(key) != 1:
            break
        passed += 1
    return passed


def _build_numbered_reason(indicators: dict[str, int]) -> str:
    failures: list[str] = []
    messages = {
        "python_syntax_correct": "1. Python 语法不正确，代码无法被解释器解析。",
        "dependency_initialization_complete": "2. pygame 导入不完整，未检测到有效 pygame 导入或评测环境无法 import pygame。",
        "window_creation": "3. 未能确认 pygame.display.set_mode 创建并返回 Surface。",
        "event_handling_mechanism": "4. 事件循环处理不足，未检测到 get/poll 事件读取结构。",
        "short_runtime_stable": "5. 短时间运行不稳定，程序崩溃或在检测窗口内提前退出。",
        "process_controllability": "6. 进程可控性不足，注入 QUIT 后未能在超时内干净退出。",
    }
    for key, _ in INDICATOR_ORDER:
        if indicators.get(key) == 0:
            failures.append(messages[key])

    if not failures:
        return "全部通过：D1 六级流水线均满足，可进入 D2-D4。"
    return " | ".join(failures)


def _runtime_diagnosis(stability: dict[str, Any] | None, quit_probe: dict[str, Any] | None) -> str:
    if stability is None:
        return "not_run"
    if stability["returncode"] not in (0, None) and not stability["timed_out"]:
        return "crash"
    if stability["returncode"] == 0 and not stability["timed_out"]:
        return "early_exit"
    if quit_probe and quit_probe["quit_posted"] and quit_probe["returncode"] == 0 and not quit_probe["timed_out"]:
        return "quit_controlled"
    if stability["timed_out"]:
        return "stable_loop"
    return "unknown"


def evaluate_dimension1(code_path: Path | str, runtime_sec: int = 5) -> dict[str, Any]:
    target = Path(code_path)

    if not target.exists():
        indicators = _empty_indicators()
        return {
            "score": 0.0,
            "raw_pass_count": 0,
            "pipeline_steps_passed": 0,
            "gate_pass": False,
            "indicators": indicators,
            "step_order": INDICATOR_ORDER,
            "reason": f"0. 代码文件不存在：{target}。",
            "runtime": {"file_found": False},
        }

    source = _safe_read_text(target)
    tree = _parse_source_once(source)
    pygame_available = importlib.util.find_spec("pygame") is not None
    pygame_import_ok = pygame_available and _subprocess_can_import_pygame()
    indicators = _empty_indicators()
    stability_probe: dict[str, Any] | None = None
    quit_probe: dict[str, Any] | None = None

    indicators["python_syntax_correct"] = 1 if tree is not None else 0
    if tree is not None:
        indicators["dependency_initialization_complete"] = 1 if (_imports_pygame(tree) and pygame_import_ok) else 0

        if indicators["dependency_initialization_complete"] == 1:
            stability_probe = _run_probe(target, mode="stability", timeout_sec=runtime_sec)
            indicators["window_creation"] = 1 if stability_probe["surface_returned"] else 0

            static_event_ok = _has_event_fetch_call(tree) and _has_event_loop_shape(tree)
            dynamic_event_ok = stability_probe["event_fetch_seen"]
            indicators["event_handling_mechanism"] = 1 if (dynamic_event_ok or static_event_ok) else 0

            indicators["short_runtime_stable"] = 1 if stability_probe["timed_out"] else 0

            if indicators["short_runtime_stable"] == 1 and not _has_busy_loop_risk(tree):
                quit_probe = _run_probe(target, mode="quit", timeout_sec=runtime_sec)
                clean_quit = (
                    quit_probe["quit_posted"]
                    and quit_probe["returncode"] == 0
                    and not quit_probe["timed_out"]
                )
                indicators["process_controllability"] = 1 if clean_quit else 0

    raw_pass_count = sum(indicators.values())
    pipeline_steps = _pipeline_steps_passed(indicators)
    gate_pass = pipeline_steps == len(INDICATOR_ORDER)

    return {
        "score": pipeline_steps / len(INDICATOR_ORDER),
        "raw_pass_count": raw_pass_count,
        "pipeline_steps_passed": pipeline_steps,
        "gate_pass": gate_pass,
        "indicators": indicators,
        "step_order": INDICATOR_ORDER,
        "runtime": {
            "file_found": True,
            "pygame_available": pygame_available,
            "pygame_import_ok": pygame_import_ok,
            "diagnosis": _runtime_diagnosis(stability_probe, quit_probe),
            "stability_probe": stability_probe,
            "quit_probe": quit_probe,
            "env_notice": "评测环境无法在子进程中 import pygame，D1 会停在第 2 级。" if not pygame_import_ok else "",
        },
        "reason": _build_numbered_reason(indicators),
    }


def check_executable(run_ok: bool, crash_count: int) -> float:
    # 保留旧接口，兼容已有调用。
    if not run_ok:
        return 0.0
    return max(0.0, 1.0 - crash_count * 0.1)
