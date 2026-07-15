"""AWS Bedrock API client."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import boto3
from botocore.config import Config


SYSTEM_PROMPT = (
    "你是一个专业的 Python 游戏开发专家，擅长使用 Pygame 开发游戏。"
    "请只返回完整的 Python 代码，不要包含任何解释文字。"
)


def _resolve_credentials(
    aws_access_key_id: str | None,
    aws_secret_access_key: str | None,
) -> tuple[str, str]:
    access_key = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID", "")
    secret_key = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY", "")
    if not access_key or not secret_key:
        raise ValueError(
            "Missing AWS credentials. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."
        )
    return access_key, secret_key


def _request_body(prompt: str, model: str, max_tokens: int, temperature: float) -> dict[str, Any]:
    if "anthropic.claude" in model:
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}],
        }
    if "amazon.nova" in model:
        return {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": f"{SYSTEM_PROMPT}\n\n{prompt}"}],
                }
            ],
            "inferenceConfig": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
            },
        }
    if any(
        marker in model
        for marker in (
            "deepseek",
            "qwen",
            "mistral",
            "minimax",
            "zai.glm",
            "moonshotai",
        )
    ):
        return {
            "messages": [
                {
                    "role": "user",
                    "content": f"{SYSTEM_PROMPT}\n\n{prompt}",
                }
            ],
            "inferenceConfig": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
            },
        }
    raise ValueError(f"Unsupported Bedrock model: {model}")


def _response_text(response_body: dict[str, Any], model: str) -> str:
    if "anthropic.claude" in model:
        return str(response_body["content"][0]["text"])
    if "amazon.nova" in model:
        return str(response_body["output"]["message"]["content"][0]["text"])
    if any(
        marker in model
        for marker in (
            "deepseek",
            "qwen",
            "mistral",
            "minimax",
            "zai.glm",
            "moonshotai",
        )
    ):
        return str(response_body["choices"][0]["message"]["content"])
    raise ValueError(f"Unsupported Bedrock model response: {model}")


def strip_code_fence(text: str) -> str:
    """Strip one complete Markdown fence without altering unfenced model text."""
    cleaned = text.strip().lstrip("\ufeff")
    match = re.fullmatch(r"```(?:python|py)?\s*\n(?P<code>.*)\n```", cleaned, re.DOTALL)
    if match:
        cleaned = match.group("code").strip()
    return cleaned


def call_bedrock_detailed(
    prompt: str,
    model: str = "anthropic.claude-3-sonnet-20240229-v1:0",
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
    aws_session_token: str | None = None,
    region: str | None = None,
    max_tokens: int = 8_000,
    temperature: float = 0.2,
) -> dict[str, Any]:
    """Call Bedrock and retain the model text and non-secret response payload."""
    access_key, secret_key = _resolve_credentials(aws_access_key_id, aws_secret_access_key)
    session_token = aws_session_token or os.getenv("AWS_SESSION_TOKEN") or None
    resolved_region = region or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
    request_body = _request_body(prompt, model, max_tokens, temperature)
    runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name=resolved_region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        config=Config(retries={"max_attempts": 3, "mode": "standard"}),
    )
    response = runtime.invoke_model(modelId=model, body=json.dumps(request_body))
    response_body = json.loads(response["body"].read())
    response_metadata = response.get("ResponseMetadata", {})
    return {
        "model": model,
        "region": resolved_region,
        "text": _response_text(response_body, model),
        "response_body": response_body,
        "request_id": response_metadata.get("RequestId"),
        "http_status_code": response_metadata.get("HTTPStatusCode"),
        "retry_attempts": response_metadata.get("RetryAttempts"),
    }


def call_bedrock(
    prompt: str,
    model: str = "anthropic.claude-3-sonnet-20240229-v1:0",
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
    aws_session_token: str | None = None,
    region: str | None = None,
) -> str:
    """Backward-compatible code-only Bedrock interface used by run_pipeline.py."""
    result = call_bedrock_detailed(
        prompt=prompt,
        model=model,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        region=region,
    )
    return strip_code_fence(result["text"])
