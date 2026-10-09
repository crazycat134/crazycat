"""DeepSeek API：根据商品信息生成日文商品描述。"""
import logging

import requests

log = logging.getLogger("secea")

# 固定免责声明（中古品必加）
DISCLAIMER = "\n\n中古品のため、現状渡しとなります。状態をご理解の上、ご購入をお願いいたします。"


def suggest_new_price(cfg, brand: str, model: str) -> dict:
    """根据品牌+型号，AI 给出全新品参考价格"""
    if not cfg.deepseek_enabled:
        return {"new_price": 30000, "confidence": "low", "note": "DeepSeek 未开启"}

    prompt = f"""
あなたは日本の価格調査アシスタントです。
以下の商品の「新品・定価・実勢価格」を日本の大手通販サイト（Amazon.co.jp、楽天市場、Yahoo!ショッピング、価格.com）の相場を参考に予想してください。

商品：{brand} {model}

回答は JSON 形式で：
{{
  "new_price": 新品実勢価格の目安（円、整数）,
  "confidence": "high" or "medium" or "low",
  "note": "補足説明（日本語、1〜2文）"
}}

必ず JSON だけを返してください。
"""
    try:
        url = f"{cfg.deepseek_base_url.rstrip('/')}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {cfg.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": cfg.deepseek_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 200,
        }
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        resp = data["choices"][0]["message"]["content"].strip()
        import json, re
        m = re.search(r'\{[^{}]*"new_price"[^{}]*\}', resp, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as e:
        log.exception("suggest_new_price failed: %s", e)
    return {"new_price": 30000, "confidence": "low", "note": "価格が不明なため仮の値です"}


def generate_description(cfg, title: str, brand: str = "", model: str = "",
                         status: str = "", accessories: list = None,
                         works_confirmed: bool = False,
                         custom_prompt: str = "") -> str:
    """调用 DeepSeek API 生成商品描述。

    cfg: Config 实例
    title: 商品标题
    brand: 品牌
    model: 型号
    status: 状态（BRAND_NEW 等）
    accessories: 附件列表 ["box", "manual"]
    works_confirmed: 动作确认済み True/False
    custom_prompt: 自定义提示词模板（可选，留空用默认）
    返回：生成的描述文本（末尾自动加免责声明）
    """
    if not cfg.deepseek_enabled:
        raise RuntimeError("DeepSeek 未开启（DEEPSEEK_ENABLED=false）")

    # 附件转日文
    accessory_map = {
        "box": "箱",
        "manual": "説明書",
        "charger": "充電器",
        "other": "その他付属品",
    }
    accessory_list = [accessory_map.get(a, a) for a in (accessories or [])]
    accessory_text = "・".join(accessory_list) if accessory_list else "本体のみ（付属品なし）"

    # 状态转日文
    status_map = {
        "BRAND_NEW": "新品、未使用",
        "ALMOST_NEW": "目立った傷や汚れなし",
        "CLEAN": "目立った傷や汚れなし",
        "LITTLE_DIRTY": "やや傷や汚れあり",
        "DIRTY": "目立った傷や汚れあり",
        "BAD": "全体的に状態が悪い",
    }
    status_text = status_map.get(status, status)

    # 动作确认转日文
    works_text = "動作確認済み（正常に動作することを確認済）" if works_confirmed else "動作未確認（ジャンク品・部品取り前提）"

    # 默认提示词：固定模板 + 商品介绍
    if not custom_prompt:
        custom_prompt = (
            "あなたは日本のフリマアプリ「メルカリ」の出品文案を書くプロです。\n"
            "以下のテンプレートに沿って商品説明文を作成してください。\n"
            "ネガティブ表現は使わず、商品の良いところだけを書いてください。\n"
            "\n"
            "【商品名】\n{title}\n\n"
            "【商品紹介】\nこの商品の特徴・おすすめポイントを1〜2文で書いてください。\n\n"
            "【状態】\n{status}\n\n"
            "【付属品】\n{accessories}\n\n"
            "【動作確認】\n{works}\n"
        )

    prompt = custom_prompt.format(
        title=title or "",
        brand=brand or "未記入",
        model=model or "未記入",
        status=status_text or "",
        accessories=accessory_text,
        works=works_text,
    )

    url = f"{cfg.deepseek_base_url.rstrip('/')}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg.deepseek_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": cfg.deepseek_model,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 500,
    }

    log.info("DeepSeek generating description for: %s (works=%s)", title, works_confirmed)
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    text = data["choices"][0]["message"]["content"].strip()
    # 末尾自动加固定免责声明
    text = text.rstrip() + DISCLAIMER
    log.info("DeepSeek generated %d chars", len(text))
    return text


def generate_checklist(cfg, title: str) -> dict:
    """根据商品标题生成标准检查清单：
    - works_items: 应该检查的动作项（电源/快门/对焦等）
    - standard_accessories: 标准附件清单（本体/电池/充电器/说明书/箱等）
    返回 {"works_items": [...], "standard_accessories": [...]}
    """
    if not cfg.deepseek_enabled:
        raise RuntimeError("DeepSeek 未开启（DEEPSEEK_ENABLED=false）")

    prompt = f"""
あなたは中古品買取・出品のプロです。
商品タイトル：{title}

この商品について、以下2つのリストをJSON形式で生成してください。

1. works_items：動作確認すべき項目（5〜8個、具体的なチェックポイント）
   例（カメラの場合）：「電源が入るか」「シャッターが切れるか」「液晶モニターは正常か」「バッテリーは充電できるか」「レンズにカビ・クモリはないか」

2. standard_accessories：標準付属品（同梱されているべきもの、4〜6個）
   例（カメラの場合）：「本体」「バッテリー」「充電器」「説明書」「元箱」

JSONのみ出力してください。説明文は不要です。
フォーマット：
{{"works_items": ["項目1", "項目2", ...], "standard_accessories": ["付属品1", "付属品2", ...]}}
"""

    url = f"{cfg.deepseek_base_url.rstrip('/')}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg.deepseek_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": cfg.deepseek_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 400,
    }

    log.info("DeepSeek generating checklist for: %s", title)
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    text = data["choices"][0]["message"]["content"].strip()

    # 提取 JSON
    import json, re
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        result = json.loads(match.group())
        return {
            "works_items": result.get("works_items", []),
            "standard_accessories": result.get("standard_accessories", []),
        }
    else:
        return {"works_items": [], "standard_accessories": [], "raw": text}
