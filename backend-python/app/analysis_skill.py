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
    if not content:
        return []
    with get_conn() as conn:
        symbols = conn.execute("SELECT * FROM dream_symbols").fetchall()
    return [dict(row) for row in symbols if row["keyword"] in content]


def detect_risk(content: str) -> bool:
    with get_conn() as conn:
        words = conn.execute("SELECT word FROM sensitive_words").fetchall()
    return any(row["word"] in content for row in words)


def _semantic_summary(content: str) -> str:
    if not content:
        return "梦境文本较短，先关注睡眠节奏和当下压力。"
    if "怕" in content or "恐" in content:
        return "梦里出现明显防御反应，像是在用梦境演绎“担忧-寻找安全”的关系。"
    if "飞" in content or "飞翔" in content or "自由" in content:
        return "梦境强调扩张和突破，常见于想摆脱压力、寻求控制感的情绪转换。"
    if "坠" in content or "落" in content:
        return "有失重或下坠意象，通常对应现实中的焦虑、失衡或不确定感。"
    if "水" in content or "海" in content:
        return "包含水域意象，常与情绪流动、清理压力有关。"
    return "梦境文本以片段化情景为主，建议结合近期事件看“触发-情绪-结果”的链条。"


def build_rule_result(symbols: list[dict[str, Any]], mood_score: int) -> str:
    if not symbols:
        return f"本次梦境未命中固定关键词库，先从整体氛围与情绪观察：{mood_label(mood_score)}。"
    explanations = "；".join(
        f"“{item['keyword']}”：{item['psychology_explanation']}" for item in symbols
    )
    return f"本次梦境命中了{len(symbols)}个关键词，语义走向较完整。梦醒情绪偏{mood_label(mood_score)}。{explanations}"


def build_prompt(content: str, mood_score: int, symbols: list[dict[str, Any]]) -> str:
    keywords = "、".join(item["keyword"] for item in symbols) or "暂无明显关键词"
    explanations = "；".join(
        f"{item['keyword']}：{item['psychology_explanation']}" for item in symbols
    ) or "暂无关键词解释"
    summary = _semantic_summary(content)
    return f"""
你是梦境记录应用中的温和分析助手，输出需安全、非迷信、可行动。

梦境内容：{content}
睡前/醒后情绪评分：{mood_score}/5（{mood_label(mood_score)}）
命中关键词：{keywords}
关键词解释：{explanations}
语义摘要：{summary}

请按中文自然段输出，不要 JSON，不要给出医学诊断、算命、预测类结论。
输出结构：
1）氛围与主题（120字内）
2）情绪与认知线索（120字内）
3）生活化建议与自我照护（120字内）
4）一句温柔提醒（避免恐慌）
""".strip()


def fallback_ai_result(symbols: list[dict[str, Any]], mood_score: int) -> str:
    keywords = "、".join(item["keyword"] for item in symbols) or "暂未命中明显关键词"
    return (
        f"氛围与主题：本梦境以“{keywords}”为核心意象，当前可先理解为情绪和记忆的重组。\n\n"
        f"情绪与认知线索：梦醒时情绪偏{mood_label(mood_score)}，说明梦境中的紧张/不适更多是内在体验，而非预兆。\n\n"
        "生活化建议与自我照护：记录触发点（时间、场景、当天事件），当晚睡前做 3 分钟深呼吸，醒来后给梦境加一句短评。\n\n"
        "温柔提醒：梦境可被当作情绪日志，适度记录更能帮助你看清自己。"
    )


def call_ai(prompt: str, fallback: str) -> str:
    api_url = os.getenv("AI_API_URL", "")
    api_key = os.getenv("AI_API_KEY", "")
    if not api_url or not api_key:
        return fallback
    try:
        response = requests.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": os.getenv("AI_MODEL", "deepseek-chat"),
                "messages": [
                    {
                        "role": "system",
                        "content": "你是温和、非迷信、非诊疗性质的梦境分析助手。",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.6,
                "max_tokens": 1200,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices") or []
        if choices:
            msg = choices[0].get("message") or {}
            content = msg.get("content")
            if content:
                return str(content).strip()
        return fallback
    except requests.RequestException:
        return fallback
    except ValueError:
        return fallback


def analyze_dream(dream_id: int, content: str, mood_score: int) -> dict[str, str]:
    symbols = match_keywords(content)
    keywords = "、".join(item["keyword"] for item in symbols)
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

