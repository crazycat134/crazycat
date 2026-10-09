import requests
from app.config import Config

def ask_deepseek(prompt: str) -> str:
    if not Config.DEEPSEEK_ENABLED:
        return ""
    url = f"{Config.DEEPSEEK_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {Config.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": Config.DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": "你是二手商品上架助手。"},
            {"role": "user", "content": prompt}
        ]
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]