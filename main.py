"""Unified command entry for the GameLLM-Benchmark project and D1/D3 demo."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Sequence

from aws_credentials import DEFAULT_CREDENTIALS_CSV, load_aws_credentials
from prompt_builder import MAIN_TEMPLATE, SPECS_DIR


DEFAULT_MODEL = "qwen.qwen3-coder-next"
DEFAULT_REGION = "us-east-1"


def _normalized_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _resolve_spec(game: str, explicit_spec: Path | None) -> Path:
    if explicit_spec is not None:
        path = explicit_spec.expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Game spec not found: {path}")
        return path

    target = _normalized_name(game)
    matches = [
        path.resolve()
        for path in SPECS_DIR.glob("*/*.md")
        if _normalized_name(path.stem) == target
    ]
    if not matches:
        available = ", ".join(sorted(path.stem for path in SPECS_DIR.glob("*/*.md")))
        raise ValueError(f"Unknown game spec '{game}'. Available games: {available}")
    if len(matches) > 1:
        raise ValueError(f"Game spec name is ambiguous: {game}")
    return matches[0]


def _load_credentials(args: argparse.Namespace) -> dict:
    state = load_aws_credentials(args.credentials_csv, args.region)
    if state["loaded"]:
        print(f"AWS credentials: {state['source']} (region={state['region']})")
    else:
        print(f"AWS credentials not found: {state['csv_path']}")
    return state


def _run_demo(args: argparse.Namespace) -> int:
    from D1_D3_demo.run_demo import main as run_demo

    spec_path = _resolve_spec(args.game, args.spec)
    if args.model_output_file is None:
        _load_credentials(args)

    forwarded = [
        "--model",
        args.model,
        "--region",
        args.region,
        "--main",
        str(args.main_template),
        "--spec",
        str(spec_path),
        "--runs-root",
        str(args.runs_root),
        "--runtime-sec",
        str(args.runtime_sec),
        "--max-tokens",
        str(args.max_tokens),
        "--temperature",
        str(args.temperature),
    ]
    if args.run_id:
        forwarded.extend(["--run-id", args.run_id])
    if args.model_output_file:
        forwarded.extend(["--model-output-file", str(args.model_output_file)])

    print(f"Prompt route: {Path(args.main_template).resolve()} + {spec_path}")
    print("Evaluation route: aligned D1 (6-step gate) + D3 (6 static indicators)")
    return run_demo(forwarded)


def _run_benchmark(args: argparse.Namespace) -> int:
    from run_pipeline import main as run_pipeline

    state = _load_credentials(args)
    if not state["loaded"]:
        print("Benchmark stopped before model calls because AWS credentials are missing.")
        return 2

    forwarded = ["--main", str(args.main_template)]
    for game in args.games or []:
        forwarded.extend(["--game", _normalized_name(game)])
    for model in args.models or []:
        forwarded.extend(["--model", model])

    print(f"Prompt route: {Path(args.main_template).resolve()} + selected game specs")
    print("Evaluation route: aligned D1-D4; D2-D4 require the complete D1 gate")
    return run_pipeline(forwarded)


def _add_aws_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--credentials-csv",
        type=Path,
        default=DEFAULT_CREDENTIALS_CSV,
        help="Local AWS CSV. Values are loaded into this process and never copied to run artifacts.",
    )
    parser.add_argument("--region", default=DEFAULT_REGION)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="GameLLM-Benchmark unified generation and evaluation entry."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser(
        "demo",
        help="Generate one game and run the aligned D1/D3 demo.",
    )
    demo.add_argument("--game", default="pong", help="Game spec name; defaults to pong.")
    demo.add_argument("--spec", type=Path, default=None, help="Explicit game spec path.")
    demo.add_argument("--model", default=DEFAULT_MODEL)
    demo.add_argument("--main-template", type=Path, default=MAIN_TEMPLATE)
    demo.add_argument("--runs-root", type=Path, default=Path("D1_D3_demo/runs"))
    demo.add_argument("--run-id", default=None)
    demo.add_argument("--runtime-sec", type=int, default=5)
    demo.add_argument("--max-tokens", type=int, default=8_000)
    demo.add_argument("--temperature", type=float, default=0.2)
    demo.add_argument("--model-output-file", type=Path, default=None)
    _add_aws_arguments(demo)
    demo.set_defaults(handler=_run_demo)

    benchmark = subparsers.add_parser(
        "benchmark",
        help="Generate configured games and run the aligned formal D1-D4 benchmark.",
    )
    benchmark.add_argument(
        "--game",
        action="append",
        dest="games",
        help="Limit to one game; repeat for multiple games. Defaults to all active games.",
    )
    benchmark.add_argument(
        "--model",
        action="append",
        dest="models",
        help="Limit to one model; repeat for multiple models. Defaults to all configured models.",
    )
    benchmark.add_argument("--main-template", type=Path, default=MAIN_TEMPLATE)
    _add_aws_arguments(benchmark)
    benchmark.set_defaults(handler=_run_benchmark)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except (FileNotFoundError, ValueError) as exc:
        print(f"Input error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
