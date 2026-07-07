# Dream Analysis Skill

代码位置：

```text
backend-python/app/analysis_skill.py
```

## 分析流程

```text
梦境正文 + 心情评分
→ 关键词匹配
→ 规则解释
→ 生成 AI Prompt
→ 调用 AI API 或使用本地兜底结果
→ 风险检测
→ 保存分析结果
```

## Prompt 模板

```text
你是一个梦境记录应用中的温和梦境分析助手。

请根据以下信息生成梦境分析：
梦境正文：{content}
梦醒心情评分：{mood_score}/5
梦醒情绪倾向：{mood_label}
识别关键词：{keywords}
关键词解释：{explanations}

要求：
1. 使用温和、治愈、非迷信的语气
2. 不要声称梦境可以预言未来
3. 不要做医学诊断
4. 不要制造恐慌
5. 分析方向偏心理学科普和情绪观察
6. 输出严格 JSON，不要输出额外说明
```

## AI 输出格式

```json
{
  "atmosphere": "梦境氛围",
  "keywordsInterpretation": "关键词解读",
  "emotionalClues": "情绪线索",
  "suggestion": "给用户的小建议"
}
```

## 分工边界

- 后端负责人：负责真实调用 `analyze_dream()`，保存结果，返回给前端。
- 中间数据流负责人：负责维护 Prompt、关键词库、返回字段和风险规则。
- 前端负责人：负责展示 `matchedKeywords`、`ruleBasedResult` 和 `aiResult`。

