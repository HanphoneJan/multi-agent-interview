"""集成测试 - 端到端评估流程

测试目标：
1. 完整的评估流程
2. 并发评估能力
3. 错误处理和恢复
"""

import pytest
import asyncio
import time
from typing import List, Dict
from statistics import mean

from app.tests.benchmark.benchmark_data import (
    SINGLE_ANSWER_BENCHMARK,
    FULL_INTERVIEW_BENCHMARK,
)
from app.tasks.evaluation_tasks import evaluate_answer_task, generate_report_task


pytestmark = pytest.mark.asyncio


class TestEndToEndEvaluation:
    """端到端评估流程测试"""

    async def test_single_answer_evaluation_flow(self):
        """测试单题评估完整流程"""
        test_case = SINGLE_ANSWER_BENCHMARK[0]

        # 调用评估任务
        result = evaluate_answer_task.delay(
            question_id=1,
            answer_text=test_case["answer"]
        )

        # 获取结果（阻塞等待）
        evaluation = result.get(timeout=30)

        # 验证结果
        assert evaluation is not None
        assert "question_id" in evaluation
        assert evaluation["question_id"] == 1
        assert "score" in evaluation
        assert 0 <= evaluation["score"] <= 1
        assert "evaluation_text" in evaluation
        assert "strengths" in evaluation
        assert "weaknesses" in evaluation

    async def test_report_generation_flow(self):
        """测试报告生成完整流程"""
        # 使用模拟数据测试报告生成
        result = generate_report_task.delay(
            session_id=1,
            user_id=1
        )

        # 获取结果
        report = result.get(timeout=60)

        # 验证结果结构
        assert report is not None
        assert "session_id" in report
        assert report["session_id"] == 1


class TestConcurrentEvaluation:
    """并发评估测试"""

    async def test_concurrent_single_evaluations(self):
        """测试并发单题评估"""
        concurrent_count = 5
        test_cases = SINGLE_ANSWER_BENCHMARK[:concurrent_count]

        start = time.time()

        # 并发提交任务
        tasks = []
        for i, case in enumerate(test_cases):
            task = evaluate_answer_task.delay(
                question_id=i + 1,
                answer_text=case["answer"]
            )
            tasks.append(task)

        # 等待所有任务完成
        results = []
        for task in tasks:
            try:
                result = task.get(timeout=60)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})

        elapsed = time.time() - start

        # 统计结果
        success_count = sum(1 for r in results if "error" not in r)
        success_rate = success_count / concurrent_count

        print(f"\n并发评估结果:")
        print(f"  - 并发数: {concurrent_count}")
        print(f"  - 成功率: {success_rate:.1%}")
        print(f"  - 总时间: {elapsed:.2f}s")
        print(f"  - 平均每个: {elapsed/concurrent_count:.2f}s")

        # 成功率应大于 80%
        assert success_rate >= 0.80, f"并发评估成功率 {success_rate:.1%} 过低"

    async def test_sequential_vs_concurrent_performance(self):
        """测试串行 vs 并发性能对比"""
        test_count = 3
        test_cases = SINGLE_ANSWER_BENCHMARK[:test_count]

        # 串行执行
        sequential_start = time.time()
        sequential_results = []
        for i, case in enumerate(test_cases):
            task = evaluate_answer_task.delay(
                question_id=i + 1,
                answer_text=case["answer"]
            )
            sequential_results.append(task.get(timeout=60))
        sequential_time = time.time() - sequential_start

        # 并发执行
        concurrent_start = time.time()
        tasks = []
        for i, case in enumerate(test_cases):
            task = evaluate_answer_task.delay(
                question_id=i + 1,
                answer_text=case["answer"]
            )
            tasks.append(task)

        concurrent_results = [t.get(timeout=60) for t in tasks]
        concurrent_time = time.time() - concurrent_start

        print(f"\n性能对比:")
        print(f"  - 串行时间: {sequential_time:.2f}s")
        print(f"  - 并发时间: {concurrent_time:.2f}s")
        print(f"  - 加速比: {sequential_time/concurrent_time:.2f}x")

        # 并发应该比串行快或至少相当
        assert concurrent_time <= sequential_time * 1.2, "并发性能异常"


class TestErrorHandling:
    """错误处理测试"""

    async def test_empty_answer_handling(self):
        """测试空回答处理"""
        result = evaluate_answer_task.delay(
            question_id=1,
            answer_text=""
        )

        evaluation = result.get(timeout=30)

        # 应返回有效结果，而不是崩溃
        assert "score" in evaluation
        assert "evaluation_text" in evaluation

    async def test_long_answer_handling(self):
        """测试超长回答处理"""
        long_answer = "测试内容" * 1000

        result = evaluate_answer_task.delay(
            question_id=1,
            answer_text=long_answer
        )

        evaluation = result.get(timeout=60)

        # 应成功处理
        assert "score" in evaluation

    async def test_special_characters_handling(self):
        """测试特殊字符处理"""
        special_answer = "<script>alert('xss')</script> \n\t\r 🎮📚"

        result = evaluate_answer_task.delay(
            question_id=1,
            answer_text=special_answer
        )

        evaluation = result.get(timeout=30)

        # 应成功处理
        assert "score" in evaluation


class TestPerformanceBenchmark:
    """性能基准测试"""

    async def test_evaluation_throughput(self):
        """测试评估吞吐量"""
        test_count = 10
        test_cases = SINGLE_ANSWER_BENCHMARK[:test_count]

        start = time.time()

        # 批量提交
        tasks = []
        for i, case in enumerate(test_cases):
            task = evaluate_answer_task.delay(
                question_id=i + 1,
                answer_text=case["answer"]
            )
            tasks.append(task)

        # 等待完成
        results = []
        for task in tasks:
            try:
                result = task.get(timeout=60)
                results.append(result)
            except Exception as e:
                print(f"任务失败: {e}")

        elapsed = time.time() - start

        success_count = len(results)
        throughput = success_count / elapsed

        print(f"\n吞吐量测试:")
        print(f"  - 总请求: {test_count}")
        print(f"  - 成功: {success_count}")
        print(f"  - 总时间: {elapsed:.2f}s")
        print(f"  - 吞吐量: {throughput:.2f} 评估/秒")

        # 记录性能数据
        assert success_count > 0, "没有成功的评估"


async def run_integration_benchmark():
    """运行集成测试 benchmark"""
    print("\n" + "="*60)
    print("集成测试 Benchmark")
    print("="*60)

    # 端到端测试
    print("\n1. 单题评估流程测试...")
    e2e_test = TestEndToEndEvaluation()
    try:
        await e2e_test.test_single_answer_evaluation_flow()
        print("   ✓ 通过")
    except Exception as e:
        print(f"   ✗ 失败: {e}")

    # 并发测试
    print("\n2. 并发评估测试...")
    concurrent_test = TestConcurrentEvaluation()
    try:
        await concurrent_test.test_concurrent_single_evaluations()
        print("   ✓ 通过")
    except Exception as e:
        print(f"   ✗ 失败: {e}")

    # 错误处理测试
    print("\n3. 错误处理测试...")
    error_test = TestErrorHandling()
    try:
        await error_test.test_empty_answer_handling()
        print("   ✓ 通过")
    except Exception as e:
        print(f"   ✗ 失败: {e}")

    # 性能测试
    print("\n4. 性能基准测试...")
    perf_test = TestPerformanceBenchmark()
    try:
        await perf_test.test_evaluation_throughput()
        print("   ✓ 通过")
    except Exception as e:
        print(f"   ✗ 失败: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_integration_benchmark())
