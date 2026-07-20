"""Demo-local D3-v2 implementation.

This package is intentionally isolated from the production D3 evaluator.  The
formal benchmark continues to use ``evaluator.dimension3`` until the demo
method has been calibrated and explicitly migrated.
"""

from .evaluator import evaluate_d3_tools, load_d3_config
from .judge import build_judge_prompt, evaluate_d3_v2, run_judge_panel

__all__ = [
    "build_judge_prompt",
    "evaluate_d3_tools",
    "evaluate_d3_v2",
    "load_d3_config",
    "run_judge_panel",
]
