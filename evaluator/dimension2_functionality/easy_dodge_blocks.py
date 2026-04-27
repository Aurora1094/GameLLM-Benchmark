from __future__ import annotations

from pathlib import Path

from .base import FunctionalityResult
from .common import evaluate_general_functionality


def evaluate_dimension2(
	code_path: Path | str,
	runtime_signals: dict[str, bool] | None = None,
	game_id: str | None = None,
) -> FunctionalityResult:
	"""Easy Dodge Blocks 维度2最小框架。

	当前阶段仅复用通用五指标评分；后续可在此叠加游戏专有证据。
	"""
	_ = game_id
	return evaluate_general_functionality(code_path=code_path, runtime_signals=runtime_signals)

