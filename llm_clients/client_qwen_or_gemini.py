"""Qwen/Gemini API 客户端"""
import os
import requests


def call_qwen(prompt: str, model: str = "qwen-max", api_key: str = None) -> str:
    """
    调用 Qwen API 生成代码
    
    Args:
        prompt: 游戏开发提示词
        model: 模型名称
        api_key: API密钥
    
    Returns:
        生成的 Python 代码
    """
    if api_key is None:
        api_key = os.getenv("QWEN_API_KEY")
    
    if not api_key:
        raise ValueError("未找到 QWEN_API_KEY")
    
    # Qwen API 调用（使用 OpenAI 兼容接口）
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是一个专业的 Python 游戏开发专家，擅长使用 Pygame 开发游戏。请只返回完整的 Python 代码，不要包含任何解释文字。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    
    code = response.json()["choices"][0]["message"]["content"]
    
    # 提取代码块
    if "```python" in code:
        code = code.split("```python")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()
    
    return code


def call_gemini(prompt: str, model: str = "gemini-pro", api_key: str = None) -> str:
    """
    调用 Gemini API 生成代码
    
    Args:
        prompt: 游戏开发提示词
        model: 模型名称
        api_key: API密钥
    
    Returns:
        生成的 Python 代码
    """
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError("未找到 GEMINI_API_KEY")
    
    import google.generativeai as genai
    
    genai.configure(api_key=api_key)
    model_instance = genai.GenerativeModel(model)
    
    full_prompt = f"""你是一个专业的 Python 游戏开发专家，擅长使用 Pygame 开发游戏。请只返回完整的 Python 代码，不要包含任何解释文字。

{prompt}"""
    
    response = model_instance.generate_content(full_prompt)
    code = response.text
    
    # 提取代码块
    if "```python" in code:
        code = code.split("```python")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()
    
    return code
