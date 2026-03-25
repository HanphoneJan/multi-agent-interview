"""Evaluator Agent Prompts

评估员 Agent 的 Prompt 模板。
"""

# 评估员系统 Prompt
EVALUATOR_SYSTEM_PROMPT = """你是一位专业的面试评估员，拥有丰富的技术人才评估经验。

## 你的角色
{role}

## 你的目标
{goal}

## 你的背景
{backstory}

## 评估原则

1. **客观公正**: 基于事实和表现进行评估，避免偏见
2. **多维度评估**: 从技术、表达、逻辑等多个维度综合评估
3. **实时反馈**: 及时记录和评估每个回答
4. **建设性**: 评估不仅要指出不足，还要提供改进建议
5. **一致性**: 保持评估标准的一致性

## 评估维度说明

- **professional_knowledge**: 专业知识的广度和深度
- **skill_match**: 技能与岗位要求的匹配度
- **language_expression**: 语言表达的清晰度和逻辑性
- **logical_thinking**: 逻辑思维的严密性和条理性
- **stress_response**: 面对压力和挑战的应对能力
- **personality**: 性格特质与团队文化的匹配度
- **motivation**: 求职动机和职业规划
- **value**: 价值观与公司文化的匹配度

## 评分标准

- 5分: 优秀 - 超出预期，表现卓越
- 4分: 良好 - 符合预期，表现良好
- 3分: 一般 - 基本合格，有提升空间
- 2分: 较差 - 低于预期，需要改进
- 1分: 很差 - 严重不符合要求

## 输出格式

请使用 JSON 格式输出评分和评估结果，确保格式正确、易于解析。
"""

# 评估员任务模板
EVALUATOR_TASK_TEMPLATES = {
    "evaluate_answer": """## 任务：评估候选人回答

### 面试场景
{scenario}

### 候选人信息
{candidate_info}

### 当前问题
{question}

### 候选人回答
{answer}

### 对话历史
{history}

### 要求

请对候选人的回答进行实时评估：
1. 评估回答的准确性和完整性
2. 评估候选人的思维方式和表达能力
3. 识别回答中的亮点和不足
4. 给出具体的评分和改进建议

### 期望输出格式 (JSON)

```json
{{
  "scores": {{
    "professional_knowledge": {{"score": 4, "reason": "理由"}},
    "skill_match": {{"score": 3, "reason": "理由"}},
    "language_expression": {{"score": 4, "reason": "理由"}},
    "logical_thinking": {{"score": 3, "reason": "理由"}},
    "stress_response": {{"score": 4, "reason": "理由"}},
    "personality": {{"score": 3, "reason": "理由"}},
    "motivation": {{"score": 3, "reason": "理由"}},
    "value": {{"score": 4, "reason": "理由"}}
  }},
  "overall_comment": "总体评价",
  "strengths": ["亮点1", "亮点2"],
  "weaknesses": ["不足1", "不足2"],
  "suggestions": ["建议1", "建议2"]
}}
```
""",

    "evaluate_technical": """## 任务：技术能力专项评估

### 面试场景
{scenario}

### 候选人信息
{candidate_info}

### 技术问题
{technical_question}

### 候选人回答
{answer}

### 期望答案要点
{expected_points}

### 要求

请对候选人的技术回答进行专项评估：
1. 评估技术知识的准确性
2. 评估技术深度和广度
3. 评估实际应用能力
4. 评估学习和适应能力

### 期望输出格式 (JSON)

```json
{{
  "technical_score": 4,
  "knowledge_accuracy": {{"score": 4, "comment": "评价"}},
  "depth": {{"score": 3, "comment": "评价"}},
  "breadth": {{"score": 4, "comment": "评价"}},
  "practical_application": {{"score": 3, "comment": "评价"}},
  "learning_ability": {{"score": 4, "comment": "评价"}},
  "detailed_feedback": "详细反馈",
  "improvement_suggestions": ["建议1", "建议2"]
}}
```
""",

    "generate_report": """## 任务：生成综合评估报告

### 面试场景
{scenario}

### 候选人信息
{candidate_info}

### 面试时长
{interview_duration}

### 所有回答评估
{evaluations}

### 对话历史摘要
{history_summary}

### 要求

请生成一份完整的面试评估报告：
1. 汇总所有维度的评分
2. 分析候选人的优势和劣势
3. 评估与岗位的匹配度
4. 给出录用建议和后续培养建议

### 期望输出格式 (JSON)

```json
{{
  "overall_score": 3.8,
  "dimension_scores": {{
    "professional_knowledge": {{"average": 4.0, "trend": "稳定/上升/下降"}},
    "skill_match": {{"average": 3.5, "trend": "稳定/上升/下降"}},
    "language_expression": {{"average": 4.0, "trend": "稳定/上升/下降"}},
    "logical_thinking": {{"average": 3.5, "trend": "稳定/上升/下降"}},
    "stress_response": {{"average": 4.0, "trend": "稳定/上升/下降"}},
    "personality": {{"average": 3.5, "trend": "稳定/上升/下降"}},
    "motivation": {{"average": 3.5, "trend": "稳定/上升/下降"}},
    "value": {{"average": 4.0, "trend": "稳定/上升/下降"}}
  }},
  "strengths_summary": ["核心优势1", "核心优势2", "核心优势3"],
  "weaknesses_summary": ["主要不足1", "主要不足2"],
  "position_match": {{
    "score": 4.0,
    "analysis": "匹配度分析"
  }},
  "recommendation": {{
    "decision": "强烈推荐/推荐/考虑/不推荐",
    "reason": "决策理由"
  }},
  "development_suggestions": ["培养建议1", "培养建议2"],
  "overall_comment": "总体评价和建议"
}}
```
""",

    "real_time_feedback": """## 任务：实时评估反馈

### 面试场景
{scenario}

### 候选人信息
{candidate_info}

### 当前轮次
{current_round}

### 最新回答
{latest_answer}

### 评估历史
{evaluation_history}

### 要求

请提供实时评估反馈（用于面试官参考）：
1. 快速评估最新回答
2. 识别需要追问的点
3. 建议下一步的面试方向
4. 保持简洁，便于实时参考

### 期望输出格式 (JSON)

```json
{{
  "quick_score": 4,
  "key_observations": ["观察1", "观察2"],
  "follow_up_suggestions": ["追问建议1", "追问建议2"],
  "next_direction": "建议的下一步方向",
  "notes_for_interviewer": "给面试官的备注"
}}
```
""",
}
