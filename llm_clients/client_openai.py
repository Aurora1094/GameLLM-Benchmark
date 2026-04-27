"""OpenAI API 客户端"""
import os
from openai import OpenAI


def call_openai(prompt: str, model: str = "gpt-4", api_key: str = None) -> str:
    """
    调用 OpenAI API 生成代码
    
    Args:
        prompt: 游戏开发提示词
        model: 模型名称，默认 gpt-4
        api_key: API密钥，如果为None则从环境变量读取
    
    Returns:
        生成的 Python 代码
    """
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("未找到 OPENAI_API_KEY，请设置环境变量或传入 api_key 参数")
    
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你是一个专业的 Python 游戏开发专家，擅长使用 Pygame 开发游戏。请只返回完整的 Python 代码，不要包含任何解释文字。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=4000
    )
    
    code = response.choices[0].message.content
    
    # 提取代码块（如果 LLM 返回了 markdown 格式）
    if "```python" in code:
        code = code.split("```python")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()
    
    return code
