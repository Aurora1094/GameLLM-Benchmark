"""Anthropic API 客户端"""
import os
from anthropic import Anthropic


def call_anthropic(prompt: str, model: str = "claude-3-opus-20240229", api_key: str = None) -> str:
    """
    调用 Anthropic API 生成代码
    
    Args:
        prompt: 游戏开发提示词
        model: 模型名称，默认 claude-3-opus-20240229
        api_key: API密钥，如果为None则从环境变量读取
    
    Returns:
        生成的 Python 代码
    """
    if api_key is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        raise ValueError("未找到 ANTHROPIC_API_KEY，请设置环境变量或传入 api_key 参数")
    
    client = Anthropic(api_key=api_key)
    
    response = client.messages.create(
        model=model,
        max_tokens=4000,
        temperature=0.7,
        system="你是一个专业的 Python 游戏开发专家，擅长使用 Pygame 开发游戏。请只返回完整的 Python 代码，不要包含任何解释文字。",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    code = response.content[0].text
    
    # 提取代码块（如果 LLM 返回了 markdown 格式）
    if "```python" in code:
        code = code.split("```python")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()
    
    return code
