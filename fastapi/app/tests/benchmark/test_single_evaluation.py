"""单题评估 Benchmark 测试

测试目标：
1. 评分准确性（与预期分数的误差）
2. 评分范围有效性（0-1）
3. JSON 格式稳定性
4. 响应时间
5. strengths/weaknesses 提取质量
"""

import pytest
import asyncio
import time
import json
from statistics import mean, stdev
from typing import List, Dict

from app.tests.benchmark.benchmark_data import (
    SINGLE_ANSWER_BENCHMARK,
    BOUNDARY_TEST_CASES,
    MAE_THRESHOLD,
    SINGLE_EVAL_TIME_THRESHOLD,
    JSON_VALIDITY_THRESHOLD,
    score_to_grade,
)
from app.tasks.evaluation_tasks import _evaluate_answer_with_qwen
from app.config import get_settings


pytestmark = pytest.mark.asyncio


class TestSingleAnswerEvaluation:
    """单题回答评估测试类"""

    async def _run_evaluation(self, answer_text: str) -> Dict:
        """运行单次评估"""
        return await _evaluate_answer_with_qwen(answer_text)

    @pytest.mark.parametrize("test_case", SINGLE_ANSWER_BENCHMARK)
    async def test_score_range(self, test_case):
        """测试分数是否在有效范围 [0, 1]"""
        result = await self._run_evaluation(test_case["answer"])
        score = result.get("score", 0)

        assert 0 <= score <= 1, f"分数 {score} 超出有效范围 [0, 1]"

    @pytest.mark.parametrize("test_case", SINGLE_ANSWER_BENCHMARK)
    async def test_score_accuracy(self, test_case):
        """测试评分准确性（与预期分数的误差）"""
        result = await self._run_evaluation(test_case["answer"])
        actual_score = result.get("score", 0)
        expected_score = test_case["expected_score"]

        # 允许 ±0.2 的误差
        assert abs(actual_score - expected_score) < 0.2, (
            f"用例 {test_case['id']} 评分偏差过大: "
            f"预期 {expected_score}, 实际 {actual_score}, "
            f"偏差 {abs(actual_score - expected_score):.2f}"
        )

    @pytest.mark.parametrize("test_case", SINGLE_ANSWER_BENCHMARK)
    async def test_result_structure(self, test_case):
        """测试结果结构完整性"""
        result = await self._run_evaluation(test_case["answer"])

        # 必需字段
        required_fields = ["score", "evaluation_text", "strengths", "weaknesses"]
        for field in required_fields:
            assert field in result, f"结果缺少必需字段: {field}"

        # 字段类型检查
        assert isinstance(result["score"], (int, float)), "score 必须是数字"
        assert isinstance(result["evaluation_text"], str), "evaluation_text 必须是字符串"
        assert isinstance(result["strengths"], list), "strengths 必须是列表"
        assert isinstance(result["weaknesses"], list), "weaknesses 必须是列表"

    @pytest.mark.parametrize("test_case", SINGLE_ANSWER_BENCHMARK)
    async def test_strengths_weaknesses_count(self, test_case):
        """测试 strengths 和 weaknesses 数量是否符合预期"""
        result = await self._run_evaluation(test_case["answer"])

        strengths_count = len(result.get("strengths", []))
        weaknesses_count = len(result.get("weaknesses", []))

        # strengths 和 weaknesses 总数应在合理范围内
        total = strengths_count + weaknesses_count
        assert 1 <= total <= 10, f"strengths + weaknesses 总数 {total} 不在合理范围 [1, 10]"

        # 检查每个项目是字符串
        for s in result.get("strengths", []):
            assert isinstance(s, str), f"strength 必须是字符串: {s}"
        for w in result.get("weaknesses", []):
            assert isinstance(w, str), f"weakness 必须是字符串: {w}"

    @pytest.mark.parametrize("test_case", SINGLE_ANSWER_BENCHMARK)
    async def test_evaluation_text_quality(self, test_case):
        """测试评估文本质量"""
        result = await self._run_evaluation(test_case["answer"])
        eval_text = result.get("evaluation_text", "")

        # 评估文本不应为空
        assert len(eval_text) > 10, f"评估文本过短: {len(eval_text)} 字符"

        # 评估文本不应是默认错误信息
        assert "暂时无法" not in eval_text, "评估返回了错误信息"
        assert "未配置" not in eval_text, "Qwen 未配置"

    async def test_response_time(self):
        """测试响应时间"""
        test_cases = SINGLE_ANSWER_BENCHMARK[:5]  # 取前5个测试
        response_times = []

        for test_case in test_cases:
            start = time.time()
            await self._run_evaluation(test_case["answer"])
            elapsed = time.time() - start
            response_times.append(elapsed)

        avg_time = mean(response_times)
        max_time = max(response_times)

        print(f"\n平均响应时间: {avg_time:.2f}s")
        print(f"最大响应时间: {max_time:.2f}s")

        assert avg_time < SINGLE_EVAL_TIME_THRESHOLD, (
            f"平均响应时间 {avg_time:.2f}s 超过阈值 {SINGLE_EVAL_TIME_THRESHOLD}s"
        )


class TestBoundaryCases:
    """边界情况测试"""

    @pytest.mark.parametrize("test_case", BOUNDARY_TEST_CASES)
    async def test_boundary_handling(self, test_case):
        """测试边界情况处理"""
        answer = test_case.get("answer", "")

        # 不应抛出异常
        try:
            result = await _evaluate_answer_with_qwen(answer)

            # 检查结果结构
            assert "score" in result
            assert 0 <= result["score"] <= 1
            assert "evaluation_text" in result

        except Exception as e:
            pytest.fail(f"边界情况 {test_case['id']} ({test_case['description']}) 处理失败: {e}")

    async def test_none_answer(self):
        """测试 None 回答"""
        result = await _evaluate_answer_with_qwen(None)
        assert "score" in result
        assert result["score"] >= 0

    async def test_very_long_answer(self):
        """测试超长回答"""
        long_answer = "测试内容" * 1000  # 约 4000 字
        result = await _evaluate_answer_with_qwen(long_answer)
        assert "score" in result
        assert "evaluation_text" in result


class TestRepeatability:
    """重复一致性测试"""

    @pytest.mark.parametrize("test_case", [SINGLE_ANSWER_BENCHMARK[0], SINGLE_ANSWER_BENCHMARK[4]])
    async def test_score_repeatability(self, test_case):
        """测试同一输入多次评估的分数一致性"""
        repeat_count = 3
        scores = []

        for _ in range(repeat_count):
            result = await _evaluate_answer_with_qwen(test_case["answer"])
            scores.append(result["score"])

        # 计算变异系数 (CV = std / mean)
        if len(scores) > 1:
            cv = stdev(scores) / mean(scores) if mean(scores) > 0 else 0
            print(f"\n用例 {test_case['id']} 分数变异系数: {cv:.3f}")
            print(f"分数列表: {scores}")

            # 变异系数应小于 0.15 (15%)
            assert cv < 0.15, f"分数变异系数 {cv:.3f} 过高，说明稳定性不足"


class TestClassificationAccuracy:
    """分类准确性测试"""

    async def test_grade_classification(self):
        """测试等级分类准确性"""
        test_cases = [
            (case, score_to_grade(case["expected_score"]))
            for case in SINGLE_ANSWER_BENCHMARK[:10]
        ]

        correct = 0
        total = len(test_cases)

        for case, expected_grade in test_cases:
            result = await _evaluate_answer_with_qwen(case["answer"])
            actual_score = result["score"]
            actual_grade = score_to_grade(actual_score)

            # 允许相邻等级
            grade_order = ["不及格", "及格", "良好", "优秀"]
            expected_idx = grade_order.index(expected_grade)
            actual_idx = grade_order.index(actual_grade)

            if abs(expected_idx - actual_idx) <= 1:
                correct += 1

        accuracy = correct / total
        print(f"\n分类准确率: {accuracy:.2%} ({correct}/{total})")

        # 分类准确率应大于 60%
        assert accuracy >= 0.60, f"分类准确率 {accuracy:.2%} 过低"


class TestPerformanceMetrics:
    """性能指标测试"""

    async def test_batch_evaluation_performance(self):
        """测试批量评估性能"""
        batch_size = 5
        test_cases = SINGLE_ANSWER_BENCHMARK[:batch_size]

        start = time.time()
        tasks = [self._run_evaluation(case["answer"]) for case in test_cases]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start

        # 计算统计信息
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        success_rate = success_count / batch_size

        print(f"\n批量评估结果:")
        print(f"  - 成功率: {success_rate:.1%}")
        print(f"  - 总时间: {elapsed:.2f}s")
        print(f"  - 平均每个: {elapsed/batch_size:.2f}s")

        # 成功率应大于 95%
        assert success_rate >= 0.95, f"批量评估成功率 {success_rate:.1%} 过低"


# ============ 统计汇总 ============

async def run_benchmark_summary():
    """运行完整的 benchmark 统计"""
    print("\n" + "="*60)
    print("单题评估 Benchmark 汇总")
    print("="*60)

    scores = []
    response_times = []
    errors = []

    for case in SINGLE_ANSWER_BENCHMARK[:10]:  # 前10个用例
        try:
            start = time.time()
            result = await _evaluate_answer_with_qwen(case["answer"])
            elapsed = time.time() - start

            response_times.append(elapsed)

            actual = result["score"]
            expected = case["expected_score"]
            error = abs(actual - expected)
            errors.append(error)

            scores.append({
                "id": case["id"],
                "category": case["category"],
                "expected": expected,
                "actual": actual,
                "error": error
            })

        except Exception as e:
            print(f"用例 {case['id']} 失败: {e}")

    if errors:
        print(f"\n测试用例数: {len(errors)}")
        print(f"平均绝对误差 (MAE): {mean(errors):.3f}")
        print(f"最大误差: {max(errors):.3f}")
        print(f"平均响应时间: {mean(response_times):.2f}s")
        print(f"最大响应时间: {max(response_times):.2f}s")

        # 分级统计
        categories = {}
        for s in scores:
            cat = s["category"].split("_")[0]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(s["error"])

        print("\n按类别 MAE:")
        for cat, errs in sorted(categories.items()):
            print(f"  {cat}: {mean(errs):.3f}")

    return scores


if __name__ == "__main__":
    # 直接运行测试
    asyncio.run(run_benchmark_summary())
