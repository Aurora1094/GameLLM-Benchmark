from __future__ import annotations

import hashlib
import json
import os
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import boto3
from botocore.config import Config

from llm_clients.client_bedrock import strip_code_fence

from .evaluator import CONFIG_PATH, evaluate_d3_tools, load_d3_config


JUDGE_RUBRIC = {
    "abstraction_and_responsibility": 5,
    "semantic_readability": 4,
    "comment_usefulness": 3,
    "changeability_and_testability": 3,
}


def _call_judge_bedrock(
    prompt: str,
    model: str,
    region: str,
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    """Call Bedrock without the code-generation system prompt used by shared clients."""
    access_key = os.getenv("AWS_ACCESS_KEY_ID", "")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    if not access_key or not secret_key:
        raise ValueError("Missing AWS credentials for D3-v2 judge panel")
    if "amazon.nova" in model:
        request_body = {
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "inferenceConfig": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
            },
        }
    elif any(marker in model for marker in ("deepseek", "qwen")):
        request_body = {
            "messages": [{"role": "user", "content": prompt}],
            "inferenceConfig": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
            },
        }
    else:
        raise ValueError(f"Unsupported D3-v2 judge model: {model}")
    runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=os.getenv("AWS_SESSION_TOKEN") or None,
        config=Config(retries={"max_attempts": 3, "mode": "standard"}),
    )
    response = runtime.invoke_model(modelId=model, body=json.dumps(request_body))
    response_body = json.loads(response["body"].read())
    if "amazon.nova" in model:
        text = str(response_body["output"]["message"]["content"][0]["text"])
    else:
        text = str(response_body["choices"][0]["message"]["content"])
    metadata = response.get("ResponseMetadata", {})
    return {
        "model": model,
        "region": region,
        "text": text,
        "request_id": metadata.get("RequestId"),
        "http_status_code": metadata.get("HTTPStatusCode"),
    }


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def _safe_slug(value: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in value)


def build_judge_prompt(source: str) -> str:
    return f"""You are an impartial code-quality reviewer. Evaluate one anonymous, single-file
Python pygame program. Executability is evaluated separately and may have passed or failed; you
are not given that result. Do not judge runtime success or whether all game rules are functionally
correct, do not infer the author or model, and do not reward verbosity. Judge only semantic
qualities that deterministic static tools cannot reliably measure from the submitted source.

Return exactly one JSON object and no markdown. Use integer scores with these exact ranges:
- abstraction_and_responsibility: 0..5
- semantic_readability: 0..4
- comment_usefulness: 0..3
- changeability_and_testability: 0..3

The total must equal the four scores and be in 0..15. For every criterion, provide a concise
reason grounded in the code and a list of relevant 1-based line numbers. Comments that merely
repeat the code are not useful. More functions or classes are not automatically better.

IMPORTANT: every value inside "evidence" MUST be a JSON object with exactly two fields,
"reason" (a JSON string) and "lines" (an array of JSON integers). Never put a plain string in
"evidence", never encode a line range as text, and never rename or omit a rubric key.

Required JSON schema:
{{
  "scores": {{
    "abstraction_and_responsibility": 0,
    "semantic_readability": 0,
    "comment_usefulness": 0,
    "changeability_and_testability": 0
  }},
  "total": 0,
  "evidence": {{
    "abstraction_and_responsibility": {{"reason": "", "lines": []}},
    "semantic_readability": {{"reason": "", "lines": []}},
    "comment_usefulness": {{"reason": "", "lines": []}},
    "changeability_and_testability": {{"reason": "", "lines": []}}
  }}
}}

Anonymous candidate source:
```python
{source.rstrip()}
```
"""


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = strip_code_fence(text.strip().lstrip("\ufeff")).strip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Judge response contains no JSON object")
        value = json.loads(cleaned[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("Judge response must be a JSON object")
    return value


def validate_judge_result(value: dict[str, Any], source_line_count: int) -> dict[str, Any]:
    if set(value) != {"scores", "total", "evidence"}:
        raise ValueError("Judge object must contain exactly scores, total, and evidence")
    scores = value.get("scores")
    evidence = value.get("evidence")
    if not isinstance(scores, dict) or set(scores) != set(JUDGE_RUBRIC):
        raise ValueError("Judge scores must contain exactly the four rubric keys")
    if not isinstance(evidence, dict) or set(evidence) != set(JUDGE_RUBRIC):
        raise ValueError("Judge evidence must contain exactly the four rubric keys")
    normalized_scores: dict[str, int] = {}
    normalized_evidence: dict[str, Any] = {}
    for key, maximum in JUDGE_RUBRIC.items():
        score = scores[key]
        if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= maximum:
            raise ValueError(f"Judge score {key} must be an integer in 0..{maximum}")
        normalized_scores[key] = score
        item = evidence[key]
        if (
            not isinstance(item, dict)
            or set(item) != {"reason", "lines"}
            or not isinstance(item.get("reason"), str)
            or not item["reason"].strip()
        ):
            raise ValueError(f"Judge evidence {key} must contain a reason")
        lines = item.get("lines")
        if not isinstance(lines, list) or any(
            isinstance(line, bool)
            or not isinstance(line, int)
            or not 1 <= line <= max(1, source_line_count)
            for line in lines
        ):
            raise ValueError(f"Judge evidence {key}.lines contains invalid line numbers")
        normalized_evidence[key] = {"reason": item["reason"].strip(), "lines": lines}
    total = sum(normalized_scores.values())
    if value.get("total") != total:
        raise ValueError("Judge total does not equal the rubric score sum")
    return {"scores": normalized_scores, "total": total, "evidence": normalized_evidence}


def run_judge_panel(
    code_path: Path | str,
    run_dir: Path | str,
    region: str,
    config_path: Path = CONFIG_PATH,
    call_model: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    target = Path(code_path).resolve()
    destination = Path(run_dir).resolve()
    source = target.read_text(encoding="utf-8-sig", errors="replace").lstrip("\ufeff")
    prompt = build_judge_prompt(source)
    prompt_path = destination / "prompts" / "d3_judge.txt"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(prompt, encoding="utf-8")

    config = load_d3_config(config_path)
    judge_config = config["judge"]
    resolved_call_model = call_model or _call_judge_bedrock
    results: list[dict[str, Any]] = []
    for model in judge_config["models"]:
        judge_dir = destination / "judges" / _safe_slug(model)
        request = {
            "provider": "bedrock",
            "model": model,
            "region": region,
            "temperature": judge_config["temperature"],
            "max_tokens": judge_config["max_tokens"],
            "prompt_path": prompt_path.relative_to(destination).as_posix(),
            "prompt_sha256": _sha256_text(prompt),
            "candidate_identity_in_prompt": False,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        _write_json(judge_dir / "request.json", request)
        attempts: list[dict[str, Any]] = []
        parsed: dict[str, Any] | None = None
        raw_text = ""
        response_metadata: dict[str, Any] = {}
        last_validation_error = ""
        for attempt in range(1, int(judge_config["max_retries"]) + 2):
            started = time.perf_counter()
            attempt_prompt = prompt
            if last_validation_error:
                attempt_prompt += (
                    "\n\nYour previous response was rejected by the strict parser with this error: "
                    f"{last_validation_error}\nReturn a corrected JSON object. In particular, every "
                    'evidence value must be an object shaped as {"reason":"...","lines":[1,2]}. '
                    "Do not return the rejected structure again."
                )
            attempt_dir = judge_dir / "attempts"
            attempt_dir.mkdir(parents=True, exist_ok=True)
            attempt_prompt_path = attempt_dir / f"{attempt:02d}_prompt.txt"
            attempt_prompt_path.write_text(attempt_prompt, encoding="utf-8")
            attempt_raw_text = ""
            try:
                response = resolved_call_model(
                    prompt=attempt_prompt,
                    model=model,
                    region=region,
                    max_tokens=int(judge_config["max_tokens"]),
                    temperature=float(judge_config["temperature"]),
                )
                attempt_raw_text = str(response["text"])
                raw_text = attempt_raw_text
                attempt_raw_path = attempt_dir / f"{attempt:02d}_raw_response.txt"
                attempt_raw_path.write_text(attempt_raw_text, encoding="utf-8")
                candidate = validate_judge_result(
                    _extract_json(attempt_raw_text), len(source.splitlines())
                )
                parsed = candidate
                response_metadata = {
                    "request_id": response.get("request_id"),
                    "http_status_code": response.get("http_status_code"),
                }
                attempts.append(
                    {
                        "attempt": attempt,
                        "status": "completed",
                        "latency_seconds": round(time.perf_counter() - started, 6),
                        "prompt_sha256": _sha256_text(attempt_prompt),
                        "raw_response_sha256": _sha256_text(attempt_raw_text),
                    }
                )
                break
            except Exception as exc:
                last_validation_error = f"{type(exc).__name__}: {exc}"
                attempts.append(
                    {
                        "attempt": attempt,
                        "status": "failed",
                        "latency_seconds": round(time.perf_counter() - started, 6),
                        "prompt_sha256": _sha256_text(attempt_prompt),
                        "raw_response_sha256": (
                            _sha256_text(attempt_raw_text) if attempt_raw_text else None
                        ),
                        "error": {"type": type(exc).__name__, "message": str(exc)},
                    }
                )
        (judge_dir / "raw_response.txt").write_text(raw_text, encoding="utf-8")
        record: dict[str, Any] = {
            "model": model,
            "status": "completed" if parsed is not None else "failed",
            "attempts": attempts,
            **response_metadata,
        }
        if parsed is not None:
            record.update(parsed)
        else:
            record["error"] = attempts[-1].get("error") if attempts else None
        _write_json(judge_dir / "parsed_score.json", record)
        results.append(record)

    valid = [item for item in results if item["status"] == "completed"]
    minimum = int(judge_config["minimum_valid_judges"])
    if len(valid) < minimum:
        return {
            "status": "incomplete_judge",
            "score": None,
            "max_score": 15,
            "valid_judge_count": len(valid),
            "required_judge_count": minimum,
            "judge_results": results,
            "prompt_sha256": _sha256_text(prompt),
        }
    totals = [float(item["total"]) for item in valid]
    score = statistics.mean(totals)
    score_range = max(totals) - min(totals)
    criterion_means = {
        key: statistics.mean(float(item["scores"][key]) for item in valid)
        for key in JUDGE_RUBRIC
    }
    return {
        "status": "completed" if len(valid) == len(results) else "panel_degraded",
        "score": round(score, 3),
        "max_score": 15,
        "valid_judge_count": len(valid),
        "configured_judge_count": len(results),
        "criterion_means": criterion_means,
        "score_std": round(statistics.stdev(totals), 3) if len(totals) > 1 else 0.0,
        "score_range": round(score_range, 3),
        "high_disagreement": score_range > float(judge_config["high_disagreement_range"]),
        "judge_results": results,
        "prompt_sha256": _sha256_text(prompt),
    }


def evaluate_d3_v2(
    code_path: Path | str,
    run_dir: Path | str,
    region: str,
    config_path: Path = CONFIG_PATH,
    include_judges: bool = True,
    call_model: Callable[..., dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    tools = evaluate_d3_tools(code_path, config_path=config_path)
    if tools["status"] != "completed":
        result = {
            "schema_version": 2,
            "status": tools["status"],
            "score": None,
            "score_normalized": None,
            "indicator_scores": tools.get("indicator_scores", {}),
            "reason": tools["reason"],
            "tools": tools,
            "judge_panel": {"status": "not_run"},
        }
        return result, tools

    if not include_judges:
        result = {
            "schema_version": 2,
            "status": "tools_only",
            "score": tools["score"],
            "score_normalized": tools["score"] / 85.0,
            "max_score": 85,
            "indicator_scores": tools["indicator_scores"],
            "reason": "D3-v2 deterministic tool evaluation completed; judge panel not requested.",
            "tools": tools,
            "judge_panel": {"status": "not_run"},
        }
        return result, tools

    panel = run_judge_panel(
        code_path=code_path,
        run_dir=run_dir,
        region=region,
        config_path=config_path,
        call_model=call_model,
    )
    if panel["status"] == "incomplete_judge":
        result = {
            "schema_version": 2,
            "status": "incomplete_judge",
            "score": None,
            "score_normalized": None,
            "indicator_scores": {**tools["indicator_scores"], "llm_review": None},
            "reason": "Fewer than two valid anonymous judge results were available.",
            "tools": tools,
            "judge_panel": panel,
        }
        return result, tools

    raw_total = float(tools["score"]) + float(panel["score"])
    cap_applied = bool(tools["critical_security_risk"])
    final_score = min(raw_total, float(tools["critical_total_cap"])) if cap_applied else raw_total
    indicators = {**tools["indicator_scores"], "llm_review": panel["score"]}
    result = {
        "schema_version": 2,
        "status": "completed" if panel["status"] == "completed" else "panel_degraded",
        "score": round(final_score, 3),
        "score_normalized": round(final_score / 100.0, 6),
        "max_score": 100,
        "raw_score_before_cap": round(raw_total, 3),
        "security_cap_applied": cap_applied,
        "indicator_scores": indicators,
        "reason": "D3-v2 tools and anonymous three-model panel evaluation completed.",
        "tools": tools,
        "judge_panel": panel,
    }
    return result, tools
