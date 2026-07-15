from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import platform
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEMO_ROOT = Path(__file__).resolve().parent
REPO_ROOT = DEMO_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluator.dimension1.dimension1_executable import evaluate_dimension1
from evaluator.dimension3.dimension3_code_quality import evaluate_dimension3_code_quality
from llm_clients.client_bedrock import call_bedrock_detailed, strip_code_fence
from prompt_builder import MAIN_TEMPLATE, SPECS_DIR, build_prompt, load_spec, write_prompt_snapshot


DEFAULT_MODEL = "qwen.qwen3-coder-next"
DEFAULT_REGION = "us-east-1"
DEFAULT_SPEC = SPECS_DIR / "easy" / "pong.md"
DEFAULT_RUNS_ROOT = DEMO_ROOT / "runs"
FENCE_PATTERN = re.compile(r"```(?P<label>[A-Za-z0-9_-]*)\s*\n(?P<code>.*?)```", re.DOTALL)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a game from a prompt spec with a real LLM, execute it, and report D1/D3."
    )
    parser.add_argument("--provider", choices=("bedrock",), default="bedrock")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--region",
        default=os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or DEFAULT_REGION,
    )
    parser.add_argument("--main", type=Path, default=MAIN_TEMPLATE)
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--runtime-sec", type=int, default=5)
    parser.add_argument("--max-tokens", type=int, default=8_000)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument(
        "--model-output-file",
        type=Path,
        default=None,
        help="Replay saved model text for plumbing tests; this is never labeled as a live generation.",
    )
    return parser.parse_args()


def safe_slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return cleaned or "run"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def credential_state() -> dict[str, Any]:
    return {
        "access_key_present": bool(os.getenv("AWS_ACCESS_KEY_ID")),
        "secret_key_present": bool(os.getenv("AWS_SECRET_ACCESS_KEY")),
        "session_token_present": bool(os.getenv("AWS_SESSION_TOKEN")),
        "source": "environment",
    }


def extract_python(model_text: str) -> tuple[str, dict[str, Any]]:
    cleaned = model_text.strip().lstrip("\ufeff")
    complete_fence = strip_code_fence(cleaned)
    if complete_fence != cleaned:
        source = complete_fence
        method = "complete_markdown_fence"
    else:
        matches = list(FENCE_PATTERN.finditer(cleaned))
        python_matches = [
            match for match in matches if match.group("label").lower() in {"python", "py"}
        ]
        selected = python_matches[0] if python_matches else (matches[0] if matches else None)
        if selected:
            source = selected.group("code").strip()
            method = "first_python_fence" if python_matches else "first_markdown_fence"
        else:
            source = cleaned
            method = "unfenced_text"
    return source.rstrip() + "\n", {
        "method": method,
        "model_text_chars": len(model_text),
        "source_chars": len(source),
    }


def syntax_status(source: str, filename: str) -> dict[str, Any]:
    try:
        ast.parse(source, filename=filename)
        return {"valid": True, "error": None}
    except SyntaxError as exc:
        return {
            "valid": False,
            "error": {
                "type": type(exc).__name__,
                "message": exc.msg,
                "line": exc.lineno,
                "offset": exc.offset,
            },
        }


def compact_d1(result: dict[str, Any]) -> dict[str, Any]:
    runtime = result.get("runtime", {})
    return {
        "score": result.get("score", 0.0),
        "pipeline_steps_passed": result.get("pipeline_steps_passed", 0),
        "raw_pass_count": result.get("raw_pass_count", 0),
        "gate_pass": bool(result.get("gate_pass", False)),
        "indicators": result.get("indicators", {}),
        "diagnosis": runtime.get("diagnosis", "not_run"),
        "reason": result.get("reason", ""),
        "actual_game_process_started": runtime.get("stability_probe") is not None,
    }


def compact_d3(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "completed",
        "score": result.get("score", 0),
        "score_normalized": result.get("score_normalized", 0.0),
        "indicator_scores": result.get("indicator_scores", {}),
        "category_scores": result.get("category_scores", {}),
        "reason": result.get("reason", ""),
    }


def build_artifact_index(run_dir: Path) -> list[dict[str, Any]]:
    return [
        {
            "path": path.relative_to(run_dir).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(run_dir.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    ]


def finish_run(run_dir: Path, summary: dict[str, Any]) -> None:
    summary_path = run_dir / "summary.json"
    write_json(summary_path, summary)
    manifest = {
        "format_version": 1,
        "run_id": summary["run_id"],
        "status": summary["status"],
        "generation_origin": summary["generation"]["origin"],
        "artifact_index": build_artifact_index(run_dir),
    }
    write_json(run_dir / "manifest.json", manifest)


def create_run_dir(args: argparse.Namespace, game_slug: str) -> tuple[str, Path]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    default_id = f"{timestamp}_{game_slug}_{safe_slug(args.model)}"
    run_id = safe_slug(args.run_id) if args.run_id else default_id
    runs_root = args.runs_root.resolve()
    runs_root.mkdir(parents=True, exist_ok=True)
    run_dir = (runs_root / run_id).resolve()
    if not run_dir.is_relative_to(runs_root):
        raise ValueError(f"Run directory escapes runs root: {run_dir}")
    if run_dir.exists():
        raise FileExistsError(f"Run directory already exists: {run_dir}")
    run_dir.mkdir(parents=True)
    return run_id, run_dir


def base_summary(
    args: argparse.Namespace,
    run_id: str,
    run_dir: Path,
    spec: dict[str, Any],
    game_slug: str,
) -> dict[str, Any]:
    return {
        "format_version": 1,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "initializing",
        "game": {
            "id": game_slug,
            "name": spec["game_name"],
            "difficulty": spec["difficulty"],
        },
        "generation": {
            "requested_origin": "response_replay" if args.model_output_file else "llm_api",
            "origin": "response_replay" if args.model_output_file else "not_generated",
            "provider": args.provider,
            "model": args.model,
            "region": args.region,
            "model_call_attempted": False,
            "model_call_succeeded": False,
            "credentials": credential_state(),
            "latency_seconds": None,
        },
        "configuration": {
            "runtime_sec": args.runtime_sec,
            "max_tokens": args.max_tokens,
            "temperature": args.temperature,
            "python": platform.python_version(),
        },
        "prompt": {},
        "code": {},
        "scores": {"d1": None, "d3": None},
        "error": None,
    }


def persist_inputs(
    args: argparse.Namespace,
    run_dir: Path,
    prompt: str,
    summary: dict[str, Any],
    game_slug: str,
) -> None:
    main_path = args.main.resolve()
    spec_path = args.spec.resolve()
    prompt_path = write_prompt_snapshot(prompt, run_dir, game_slug)
    inputs_dir = run_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    main_snapshot = inputs_dir / "main.md"
    spec_snapshot = inputs_dir / f"{game_slug}.md"
    main_snapshot.write_text(main_path.read_text(encoding="utf-8-sig"), encoding="utf-8")
    spec_snapshot.write_text(spec_path.read_text(encoding="utf-8-sig"), encoding="utf-8")
    summary["prompt"] = {
        "rendered_path": prompt_path.relative_to(run_dir).as_posix(),
        "rendered_sha256": sha256_file(prompt_path),
        "main_snapshot": main_snapshot.relative_to(run_dir).as_posix(),
        "main_sha256": sha256_file(main_snapshot),
        "spec_snapshot": spec_snapshot.relative_to(run_dir).as_posix(),
        "spec_sha256": sha256_file(spec_snapshot),
        "chars": len(prompt),
    }
    write_json(
        run_dir / "request.json",
        {
            "provider": args.provider,
            "model": args.model,
            "region": args.region,
            "max_tokens": args.max_tokens,
            "temperature": args.temperature,
            "prompt_path": summary["prompt"]["rendered_path"],
            "prompt_sha256": summary["prompt"]["rendered_sha256"],
            "credentials_saved": False,
        },
    )


def obtain_model_text(
    args: argparse.Namespace,
    run_dir: Path,
    prompt: str,
    summary: dict[str, Any],
) -> str | None:
    if args.model_output_file:
        source_path = args.model_output_file.resolve()
        if not source_path.is_file():
            raise FileNotFoundError(f"Saved model output not found: {source_path}")
        model_text = source_path.read_text(encoding="utf-8-sig")
        summary["generation"]["replay_source"] = str(source_path)
        summary["generation"]["model_call_attempted"] = False
        summary["generation"]["model_call_succeeded"] = False
        return model_text

    credentials = summary["generation"]["credentials"]
    if not credentials["access_key_present"] or not credentials["secret_key_present"]:
        summary["status"] = "credentials_missing"
        summary["error"] = {
            "type": "MissingCredentials",
            "message": "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are not set.",
        }
        return None

    summary["generation"]["model_call_attempted"] = True
    started = time.perf_counter()
    response = call_bedrock_detailed(
        prompt=prompt,
        model=args.model,
        region=args.region,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
    )
    summary["generation"]["latency_seconds"] = round(time.perf_counter() - started, 6)
    summary["generation"]["model_call_succeeded"] = True
    summary["generation"]["origin"] = "llm_api"
    summary["generation"]["request_id"] = response.get("request_id")
    summary["generation"]["http_status_code"] = response.get("http_status_code")
    write_json(run_dir / "responses" / "bedrock_response.json", response)
    return str(response["text"])


def evaluate_generated_game(
    args: argparse.Namespace,
    run_dir: Path,
    model_text: str,
    summary: dict[str, Any],
    game_slug: str,
) -> None:
    response_path = run_dir / "responses" / "model_output.txt"
    response_path.parent.mkdir(parents=True, exist_ok=True)
    response_path.write_text(model_text, encoding="utf-8")
    source, extraction = extract_python(model_text)
    code_path = run_dir / "generated" / f"{game_slug}__{safe_slug(args.model)}.py"
    code_path.parent.mkdir(parents=True, exist_ok=True)
    code_path.write_text(source, encoding="utf-8")
    syntax = syntax_status(source, code_path.name)
    summary["code"] = {
        "path": code_path.relative_to(run_dir).as_posix(),
        "sha256": sha256_file(code_path),
        "bytes": code_path.stat().st_size,
        "extraction": extraction,
        "syntax": syntax,
        "model_output_path": response_path.relative_to(run_dir).as_posix(),
        "model_output_sha256": sha256_file(response_path),
    }

    d1_result = evaluate_dimension1(code_path, runtime_sec=args.runtime_sec)
    write_json(run_dir / "scores" / "d1.json", d1_result)
    d1_compact = compact_d1(d1_result)
    summary["scores"]["d1"] = d1_compact

    if d1_compact["gate_pass"]:
        d3_result = evaluate_dimension3_code_quality(code_path)
        write_json(run_dir / "scores" / "d3.json", d3_result)
        summary["scores"]["d3"] = compact_d3(d3_result)
    else:
        skipped = {
            "status": "skipped_d1_gate",
            "reason": "D3 is gated because the generated game did not pass all six D1 steps.",
        }
        write_json(run_dir / "scores" / "d3.json", skipped)
        summary["scores"]["d3"] = skipped
    summary["status"] = "completed"


def main() -> int:
    args = parse_args()
    if args.runtime_sec < 3:
        raise ValueError("--runtime-sec must be at least 3")
    if args.max_tokens < 1:
        raise ValueError("--max-tokens must be positive")
    if not 0 <= args.temperature <= 1:
        raise ValueError("--temperature must be between 0 and 1")

    spec = load_spec(args.spec.resolve())
    game_slug = safe_slug(args.spec.stem.lower())
    run_id, run_dir = create_run_dir(args, game_slug)
    summary = base_summary(args, run_id, run_dir, spec, game_slug)
    try:
        prompt = build_prompt(args.main.resolve(), args.spec.resolve())
        persist_inputs(args, run_dir, prompt, summary, game_slug)
        model_text = obtain_model_text(args, run_dir, prompt, summary)
        if model_text is None:
            finish_run(run_dir, summary)
            print("Generation stopped: AWS credentials are missing.")
            print("Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION, then rerun.")
            print(f"Prompt and failure evidence: {run_dir}")
            return 2
        evaluate_generated_game(args, run_dir, model_text, summary, game_slug)
    except Exception as exc:
        summary["status"] = "generation_failed" if summary["generation"]["model_call_attempted"] else "failed"
        summary["error"] = {"type": type(exc).__name__, "message": str(exc)}
        finish_run(run_dir, summary)
        print(f"D1/D3 generation demo failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(f"Failure evidence: {run_dir}", file=sys.stderr)
        return 1

    finish_run(run_dir, summary)
    d1 = summary["scores"]["d1"]
    d3 = summary["scores"]["d3"]
    print("D1/D3 generation demo completed.")
    print(f"Origin: {summary['generation']['origin']}")
    print(f"Generated code: {run_dir / summary['code']['path']}")
    print(f"D1: {d1['pipeline_steps_passed']}/6, gate={d1['gate_pass']}")
    if d3["status"] == "completed":
        print(f"D3: {d3['score']}/100")
    else:
        print("D3: skipped by D1 gate")
    print(f"Summary: {run_dir / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
