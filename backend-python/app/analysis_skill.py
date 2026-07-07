import json
import os
from typing import Any

import requests

from .database import get_conn


def mood_label(score: int) -> str:
    return {
        1: "强烈负面",
        2: "偏负面",
        3: "中性",
        4: "偏正面",
        5: "积极愉快",
    }.get(score, "未知")


def match_keywords(content: str) -> list[dict[str, Any]]:
    with get_conn() as conn:
        symbols = conn.execute("SELECT * FROM dream_symbols").fetchall()
    return [dict(row) for row in symbols if row["keyword"] in content]


def detect_risk(content: str) -> bool:
    with get_conn() as conn:
        words = conn.execute("SELECT word FROM sensitive_words").fetchall()
    return any(row["word"] in content for row in words)


def build_rule_result(symbols: list[dict[str, Any]], mood_score: int) -> str:
    if not symbols:
        return "本次梦境没有命中预设关键词，可以先从梦醒情绪和梦境整体氛围进行观察。"
    explanations = "；".join(
        f"“{item['keyword']}”：{item['psychology_explanation']}" for item in symbols
    )
    return f"本次梦境命中了{len(symbols)}个关键词。梦醒情绪倾向为{mood_label(mood_score)}。{explanations}"


def build_prompt(content: str, mood_score: int, symbols: list[dict[str, Any]]) -> str:
    keywords = "、".join(item["keyword"] for item in symbols) or "暂无明显关键词"
    explanations = "；".join(
        f"{item['keyword']}：{item['psychology_explanation']}" for item in symbols
    ) or "暂无关键词解释"
    return f"""
你是一个梦境记录应用中的温和梦境分析助手。

请根据以下信息生成梦境分析：
梦境正文：{content}
梦醒心情评分：{mood_score}/5
梦醒情绪倾向：{mood_label(mood_score)}
识别关键词：{keywords}
关键词解释：{explanations}

要求：
1. 使用温和、治愈、非迷信的语气
2. 不要声称梦境可以预言未来
3. 不要做医学诊断
4. 不要制造恐慌
5. 分析方向偏心理学科普和情绪观察
6. 输出严格 JSON，不要输出额外说明

JSON 格式：
{{
  "atmosphere": "梦境氛围",
  "keywordsInterpretation": "关键词解读",
  "emotionalClues": "情绪线索",
  "suggestion": "给用户的小建议"
}}
""".strip()


def fallback_ai_result(symbols: list[dict[str, Any]], mood_score: int) -> str:
    keywords = "、".join(item["keyword"] for item in symbols) or "暂未命中明显关键词"
    result = {
        "atmosphere": "这个梦可以先从整体氛围和醒来后的感受来理解。",
        "keywordsInterpretation": f"系统识别到的关键词为：{keywords}。",
        "emotionalClues": f"梦醒情绪倾向为{mood_label(mood_score)}，这可以作为理解梦境的重要线索。",
        "suggestion": "建议记录最近让你印象深刻的压力、期待或关系变化，把梦境当作一次自我观察。",
    }
    return json.dumps(result, ensure_ascii=False)


def call_ai(prompt: str, fallback: str) -> str:
    api_url = os.getenv("AI_API_URL", "")
    api_key = os.getenv("AI_API_KEY", "")
    if not api_url or not api_key:
        return fallback
    try:
        response = requests.post(
            api_url,
            headers={"Authorization": f"Bearer {api_key}"},
            json={"prompt": prompt},
            timeout=20,
        )
        response.raise_for_status()
        return response.text or fallback
    except requests.RequestException:
        return fallback


def analyze_dream(dream_id: int, content: str, mood_score: int) -> dict[str, str]:
    symbols = match_keywords(content)
    keywords = ",".join(item["keyword"] for item in symbols)
    rule_result = build_rule_result(symbols, mood_score)
    prompt = build_prompt(content, mood_score, symbols)
    fallback = fallback_ai_result(symbols, mood_score)
    ai_result = call_ai(prompt, fallback)
    risk_level = "HIGH" if detect_risk(content) else "LOW"
    return {
        "dreamId": dream_id,
        "matchedKeywords": keywords,
        "ruleBasedResult": rule_result,
        "aiResult": ai_result,
        "riskLevel": risk_level,
    }

