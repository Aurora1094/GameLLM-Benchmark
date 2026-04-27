"""AWS Bedrock API 客户端"""
import os
import json
import boto3
from botocore.config import Config


def call_bedrock(prompt: str, model: str = "anthropic.claude-3-sonnet-20240229-v1:0", 
                 aws_access_key_id: str = None, aws_secret_access_key: str = None,
                 region: str = "us-east-1") -> str:
    """
    调用 AWS Bedrock API 生成代码
    
    Args:
        prompt: 游戏开发提示词
        model: 模型名称，默认 claude-3-sonnet
        aws_access_key_id: AWS Access Key ID
        aws_secret_access_key: AWS Secret Access Key
        region: AWS 区域
    
    Returns:
        生成的 Python 代码
    """
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_REGION", "us-east-1")

    if not aws_access_key_id or not aws_secret_access_key:
        raise ValueError(
            "Missing AWS credentials. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."
        )

    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name=region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        config=Config(
            retries={"max_attempts": 3, "mode": "standard"}
        )
    )
    
    # 构建请求体（针对不同模型）
    if "anthropic.claude" in model:
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "temperature": 0.7,
            "system": "你是一个专业的 Python 游戏开发专家，擅长使用 Pygame 开发游戏。请只返回完整的 Python 代码，不要包含任何解释文字。",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        })
    elif "amazon.nova" in model:
        # Amazon Nova 使用 Converse API 格式
        body = json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": f"你是一个专业的 Python 游戏开发专家，擅长使用 Pygame 开发游戏。请只返回完整的 Python 代码，不要包含任何解释文字。\n\n{prompt}"
                        }
                    ]
                }
            ],
            "inferenceConfig": {
                "max_new_tokens": 4000,
                "temperature": 0.7
            }
        })
    elif "deepseek" in model or "qwen" in model or "mistral" in model or "minimax" in model or "zai.glm" in model or "moonshotai" in model:
        # 其他模型使用简化的消息格式
        body = json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": f"你是一个专业的 Python 游戏开发专家，擅长使用 Pygame 开发游戏。请只返回完整的 Python 代码，不要包含任何解释文字。\n\n{prompt}"
                }
            ],
            "inferenceConfig": {
                "max_new_tokens": 4000,
                "temperature": 0.7
            }
        })
    else:
        raise ValueError(f"不支持的 Bedrock 模型: {model}")
    
    # 调用 Bedrock API
    response = bedrock_runtime.invoke_model(
        modelId=model,
        body=body
    )
    
    # 解析响应
    response_body = json.loads(response['body'].read())
    
    if "anthropic.claude" in model:
        code = response_body['content'][0]['text']
    elif "amazon.nova" in model:
        code = response_body['output']['message']['content'][0]['text']
    elif "deepseek" in model or "qwen" in model or "mistral" in model or "minimax" in model or "zai.glm" in model:
        # 这些模型使用OpenAI兼容格式
        code = response_body['choices'][0]['message']['content']
    else:
        code = response_body.get('completion', '')
    
    # 提取代码块（如果 LLM 返回了 markdown 格式）
    if "```python" in code:
        code = code.split("```python")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()
    
    return code
