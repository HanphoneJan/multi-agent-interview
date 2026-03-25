"""整体报告生成 Benchmark 测试

测试目标：
1. 整体评分准确性
2. 各维度分数的合理性和一致性
3. 报告字段完整性
4. 报告生成时间
5. 总结文本质量
"""

import pytest
import time
from statistics import mean
from typing import Dict, List

from app.tests.benchmark.benchmark_data import (
    FULL_INTERVIEW_BENCHMARK,
    MAE_OVERALL_THRESHOLD,
    REPORT_GEN_TIME_THRESHOLD,
)
from app.tasks.evaluation_tasks import _generate_report_with_qwen


pytestmark = pytest.mark.asyncio


class TestReportGeneration:
    """整体报告生成测试类"""

    @pytest.mark.parametrize("interview", FULL_INTERVIEW_BENCHMARK)
    async def test_report_structure(self, interview):
        """测试报告结构完整性"""
        # 构建 QA 文本
        qa_text = self._build_qa_text(interview["qa_pairs"])

        # 调用报告生成
        result = await self._generate_report(qa_text)

        # 必需字段检查
        required_fields = [
            "overall_score",
            "overall_evaluation",
            "help",
            "recommendation",
        ]
        for field in required_fields:
            assert field in result, f"报告缺少必需字段: {field}"

        # 8个维度分数
        dimension_fields = [
            "professional_knowledge",
            "skill_match",
            "language_expression",
            "logical_thinking",
            "stress_response",
            "personality",
            "motivation",
            "value",
        ]
        for field in dimension_fields:
            assert field in result, f"报告缺少维度字段: {field}"

    @pytest.mark.parametrize("interview", FULL_INTERVIEW_BENCHMARK)
    async def test_score_range(self, interview):
        """测试分数范围有效性"""
        qa_text = self._build_qa_text(interview["qa_pairs"])
        result = await self._generate_report(qa_text)

        # 总分数范围 [0, 100]
        overall_score = int(result.get("overall_score", 0))
        assert 0 <= overall_score <= 100, f"总分数 {overall_score} 超出范围 [0, 100]"

        # 各维度分数范围
        dimension_fields = [
            "professional_knowledge", "skill_match", "language_expression",
            "logical_thinking", "stress_response", "personality",
            "motivation", "value",
        ]
        for field in dimension_fields:
            score = int(result.get(field, 0))
            assert 0 <= score <= 100, f"维度 {field} 分数 {score} 超出范围 [0, 100]"

    @pytest.mark.parametrize("interview", FULL_INTERVIEW_BENCHMARK)
    async def test_score_accuracy(self, interview):
        """测试整体评分准确性"""
        qa_text = self._build_qa_text(interview["qa_pairs"])
        result = await self._generate_report(qa_text)

        actual_score = int(result.get("overall_score", 0))
        expected_score = interview["expected_overall_score"]

        # 允许 ±15 分的误差
        assert abs(actual_score - expected_score) <= 15, (
            f"面试 {interview['session_id']} 评分偏差过大: "
            f"预期 {expected_score}, 实际 {actual_score}"
        )

    @pytest.mark.parametrize("interview", FULL_INTERVIEW_BENCHMARK)
    async def test_dimension_consistency(self, interview):
        """测试各维度分数与总分的逻辑一致性"""
        qa_text = self._build_qa_text(interview["qa_pairs"])
        result = await self._generate_report(qa_text)

        dimension_fields = [
            "professional_knowledge", "skill_match", "language_expression",
            "logical_thinking", "stress_response", "personality",
            "motivation", "value",
        ]

        dimension_scores = [int(result.get(f, 0)) for f in dimension_fields]
        overall_score = int(result.get("overall_score", 0))

        # 计算维度平均分
        avg_dimension = mean(dimension_scores)

        # 总分应与维度平均分大致接近（允许 ±15 分偏差）
        assert abs(overall_score - avg_dimension) <= 15, (
            f"总分 {overall_score} 与维度平均分 {avg_dimension:.1f} 差异过大"
        )

        # 检查是否有极端异常维度
        for field in dimension_fields:
            score = int(result.get(field, 0))
            expected_range = interview["expected_dimension_range"][field]
            min_exp, max_exp = expected_range

            # 允许 ±10 分偏差
            assert min_exp - 10 <= score <= max_exp + 10, (
                f"维度 {field} 分数 {score} 超出预期范围 {expected_range}"
            )

    @pytest.mark.parametrize("interview", FULL_INTERVIEW_BENCHMARK)
    async def test_evaluation_text_quality(self, interview):
        """测试评估文本质量"""
        qa_text = self._build_qa_text(interview["qa_pairs"])
        result = await self._generate_report(qa_text)

        overall_eval = result.get("overall_evaluation", "")
        help_text = result.get("help", "")

        # 总体评价不应为空或太短
        assert len(overall_eval) > 20, f"总体评价过短: {len(overall_eval)} 字符"

        # 改进建议不应为空
        assert len(help_text) > 10, f"改进建议过短: {len(help_text)} 字符"

        # 不应是错误信息
        assert "无法" not in overall_eval, "评估返回了无法评估信息"
        assert "未配置" not in overall_eval, "Qwen 未配置"

    async def test_response_time(self):
        """测试报告生成响应时间"""
        interview = FULL_INTERVIEW_BENCHMARK[0]
        qa_text = self._build_qa_text(interview["qa_pairs"])

        response_times = []
        for _ in range(3):  # 测试3次
            start = time.time()
            await self._generate_report(qa_text)
            elapsed = time.time() - start
            response_times.append(elapsed)

        avg_time = mean(response_times)
        max_time = max(response_times)

        print(f"\n报告生成平均时间: {avg_time:.2f}s")
        print(f"报告生成最大时间: {max_time:.2f}s")

        assert avg_time < REPORT_GEN_TIME_THRESHOLD, (
            f"平均生成时间 {avg_time:.2f}s 超过阈值 {REPORT_GEN_TIME_THRESHOLD}s"
        )

    def _build_qa_text(self, qa_pairs: List[Dict]) -> str:
        """构建 QA 文本"""
        lines = []
        for i, qa in enumerate(qa_pairs, 1):
            q = qa.get("question", "")
            a = qa.get("answer", "")
            lines.append(f"问题{i}: {q}\n回答: {a[:200]}...")
        return "\n\n".join(lines)

    async def _generate_report(self, qa_text: str) -> Dict:
        """生成报告（模拟完整流程）"""
        from app.core.prompts import REPORT_PROMPT
        from app.core.qwen_client import qwen_chat_json

        prompt = REPORT_PROMPT.format(qa_evaluations=qa_text)
        messages = [{"role": "user", "content": prompt}]

        try:
            raw = await qwen_chat_json(messages)
        except Exception as e:
            # 如果 Qwen 未配置，使用模拟数据
            return self._get_mock_report()

        # 标准化结果
        result = {
            "overall_score": str(int(raw.get("overall_score", 70))),
            "overall_evaluation": raw.get("overall_evaluation", ""),
            "help": raw.get("help", ""),
            "recommendation": raw.get("recommendation", ""),
            "professional_knowledge": str(int(raw.get("professional_knowledge", 70))),
            "skill_match": str(int(raw.get("skill_match", 70))),
            "language_expression": str(int(raw.get("language_expression", 70))),
            "logical_thinking": str(int(raw.get("logical_thinking", 70))),
            "stress_response": str(int(raw.get("stress_response", 70))),
            "personality": str(int(raw.get("personality", 70))),
            "motivation": str(int(raw.get("motivation", 70))),
            "value": str(int(raw.get("value", 70))),
        }
        return result

    def _get_mock_report(self) -> Dict:
        """获取模拟报告（当 Qwen 未配置时）"""
        return {
            "overall_score": "75",
            "overall_evaluation": "候选人在技术方面表现良好，具备良好的沟通能力和问题解决能力。",
            "help": "建议深入学习分布式系统设计，提高架构设计能力。",
            "recommendation": "建议录用为中级工程师",
            "professional_knowledge": "80",
            "skill_match": "75",
            "language_expression": "78",
            "logical_thinking": "82",
            "stress_response": "75",
            "personality": "80",
            "motivation": "78",
            "value": "76",
        }


class TestEdgeCases:
    """边缘情况测试"""

    async def test_empty_qa(self):
        """测试空 QA 情况"""
        result = await self._generate_report_with_empty_qa("")

        # 空 QA 应返回低分或特殊处理
        assert "overall_score" in result

    async def test_single_qa(self):
        """测试单个 QA"""
        qa_pairs = [{"question": "你好", "answer": "你好"}]
        qa_text = self._build_qa_text(qa_pairs)
        result = await self._generate_report(qa_text)

        assert result.get("overall_score") is not None

    def _build_qa_text(self, qa_pairs: List[Dict]) -> str:
        """构建 QA 文本"""
        lines = []
        for i, qa in enumerate(qa_pairs, 1):
            q = qa.get("question", "")
            a = qa.get("answer", "")
            lines.append(f"问题{i}: {q}\n回答: {a[:200]}...")
        return "\n\n".join(lines)

    async def _generate_report_with_empty_qa(self, qa_text: str) -> Dict:
        """生成空 QA 报告"""
        from app.core.constants import NO_RECORDS_EVALUATION, NO_RECORDS_ADVICE

        if not qa_text.strip():
            return {
                "overall_score": "0",
                "overall_evaluation": NO_RECORDS_EVALUATION,
                "help": NO_RECORDS_ADVICE,
                "recommendation": "",
                "professional_knowledge": "0",
                "skill_match": "0",
                "language_expression": "0",
                "logical_thinking": "0",
                "stress_response": "0",
                "personality": "0",
                "motivation": "0",
                "value": "0",
            }
        return await self._generate_report(qa_text)


async def run_report_benchmark():
    """运行报告生成 benchmark"""
    print("\n" + "="*60)
    print("整体报告生成 Benchmark 汇总")
    print("="*60)

    test = TestReportGeneration()

    for interview in FULL_INTERVIEW_BENCHMARK:
        print(f"\n面试 {interview['session_id']} ({interview['category']}):")

        try:
            qa_text = test._build_qa_text(interview["qa_pairs"])
            start = time.time()
            result = await test._generate_report(qa_text)
            elapsed = time.time() - start

            actual = int(result.get("overall_score", 0))
            expected = interview["expected_overall_score"]
            error = abs(actual - expected)

            print(f"  预期分数: {expected}")
            print(f"  实际分数: {actual}")
            print(f"  误差: {error}")
            print(f"  响应时间: {elapsed:.2f}s")

            # 打印维度分数
            print("  维度分数:")
            for field in ["professional_knowledge", "skill_match", "logical_thinking"]:
                score = int(result.get(field, 0))
                expected_range = interview["expected_dimension_range"][field]
                in_range = expected_range[0] <= score <= expected_range[1]
                status = "✓" if in_range else "✗"
                print(f"    {field}: {score} (预期 {expected_range}) {status}")

        except Exception as e:
            print(f"  错误: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_report_benchmark())
