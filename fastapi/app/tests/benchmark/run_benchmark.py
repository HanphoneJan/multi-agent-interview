"""Benchmark 测试运行脚本

运行所有 benchmark 测试并生成报告。

Usage:
    cd fastapi
    uv run python -m app.tests.benchmark.run_benchmark

Or with pytest:
    uv run pytest app/tests/benchmark/ -v --tb=short
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path
from statistics import mean

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.tests.benchmark.benchmark_data import (
    SINGLE_ANSWER_BENCHMARK,
    FULL_INTERVIEW_BENCHMARK,
    BOUNDARY_TEST_CASES,
    score_to_grade,
)
from app.tests.benchmark.test_single_evaluation import TestSingleAnswerEvaluation
from app.tests.benchmark.test_report_generation import TestReportGeneration
from app.tests.benchmark.test_integration import TestConcurrentEvaluation


class BenchmarkRunner:
    """Benchmark 测试运行器"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "single_evaluation": {},
            "report_generation": {},
            "integration": {},
            "summary": {},
        }
        self.passed = 0
        self.failed = 0

    async def run_single_evaluation_benchmark(self):
        """运行单题评估 benchmark"""
        print("\n" + "="*70)
        print("[单题评估] Benchmark测试")
        print("="*70)

        test = TestSingleAnswerEvaluation()
        scores = []
        response_times = []

        # 选择前10个测试用例
        test_cases = SINGLE_ANSWER_BENCHMARK[:10]

        for case in test_cases:
            try:
                from app.tasks.evaluation_tasks import _evaluate_answer_with_qwen

                start = time.time()
                result = await _evaluate_answer_with_qwen(case["answer"])
                elapsed = time.time() - start

                response_times.append(elapsed)

                actual = result.get("score", 0)
                expected = case["expected_score"]
                error = abs(actual - expected)

                scores.append({
                    "id": case["id"],
                    "category": case["category"],
                    "expected": expected,
                    "actual": actual,
                    "error": error,
                })

                print(f"[PASS] {case['id']}: 预期 {expected:.2f}, 实际 {actual:.2f}, 误差 {error:.2f}")

            except Exception as e:
                print(f"[FAIL] {case['id']}: 失败 - {e}")
                self.failed += 1

        # 计算统计指标
        if scores:
            errors = [s["error"] for s in scores]
            mae = mean(errors)

            self.results["single_evaluation"] = {
                "tested": len(scores),
                "mae": mae,
                "max_error": max(errors),
                "avg_response_time": mean(response_times),
                "scores": scores,
            }

            print(f"\n统计结果:")
            print(f"  - 测试用例数: {len(scores)}")
            print(f"  - 平均绝对误差 (MAE): {mae:.3f}")
            print(f"  - 最大误差: {max(errors):.3f}")
            print(f"  - 平均响应时间: {mean(response_times):.2f}s")

            # 判定
            if mae < 0.15:
                print(f"  - 状态: [PASS] 通过 (MAE < 0.15)")
                self.passed += 1
            else:
                print(f"  - 状态: [FAIL] 未通过 (MAE >= 0.15)")
                self.failed += 1

    async def run_boundary_tests(self):
        """运行边界测试"""
        print("\n" + "="*70)
        print("[边界] 边界情况测试")
        print("="*70)

        from app.tasks.evaluation_tasks import _evaluate_answer_with_qwen

        passed = 0
        failed = 0

        for case in BOUNDARY_TEST_CASES[:5]:  # 测试前5个边界用例
            try:
                answer = case.get("answer", "")
                result = await _evaluate_answer_with_qwen(answer)

                if "score" in result and 0 <= result["score"] <= 1:
                    print(f"[PASS] {case['id']} ({case['description']}): 处理成功")
                    passed += 1
                else:
                    print(f"[FAIL] {case['id']}: 返回结果异常")
                    failed += 1

            except Exception as e:
                print(f"[FAIL] {case['id']}: 异常 - {e}")
                failed += 1

        self.results["boundary"] = {
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / (passed + failed) if (passed + failed) > 0 else 0,
        }

        print(f"\n边界测试通过率: {passed}/{passed + failed} ({self.results['boundary']['pass_rate']:.1%})")

    async def run_report_benchmark(self):
        """运行报告生成 benchmark"""
        print("\n" + "="*70)
        print("[报告] 整体报告生成 Benchmark")
        print("="*70)

        test = TestReportGeneration()
        results = []

        for interview in FULL_INTERVIEW_BENCHMARK[:2]:  # 测试前2个面试用例
            try:
                qa_text = test._build_qa_text(interview["qa_pairs"])
                result = await test._generate_report(qa_text)

                actual = int(result.get("overall_score", 0))
                expected = interview["expected_overall_score"]
                error = abs(actual - expected)

                results.append({
                    "session_id": interview["session_id"],
                    "expected": expected,
                    "actual": actual,
                    "error": error,
                })

                print(f"[PASS] {interview['session_id']}: 预期 {expected}, 实际 {actual}, 误差 {error}")

            except Exception as e:
                print(f"[FAIL] {interview['session_id']}: 失败 - {e}")
                self.failed += 1

        if results:
            errors = [r["error"] for r in results]
            mae = mean(errors)

            self.results["report_generation"] = {
                "tested": len(results),
                "mae": mae,
                "results": results,
            }

            print(f"\n报告生成统计:")
            print(f"  - 测试面试数: {len(results)}")
            print(f"  - 平均绝对误差: {mae:.1f}分")

            if mae <= 15:
                print(f"  - 状态: [PASS] 通过 (MAE <= 15)")
                self.passed += 1
            else:
                print(f"  - 状态: [FAIL] 未通过 (MAE > 15)")
                self.failed += 1

    async def run_all(self):
        """运行所有 benchmark"""
        print("\n" + "=" * 70)
        print("   AI 面试评分系统 Benchmark 测试")
        print("=" * 70)

        start_time = time.time()

        # 检查 Qwen 配置
        from app.config import get_settings
        settings = get_settings()

        if not settings.QWEN_API_KEY:
            print("\n[WARN] 警告: QWEN_API_KEY 未配置，将使用模拟数据进行测试")
            print("要运行真实测试，请在 .env 文件中配置 QWEN_API_KEY")

        # 运行测试
        try:
            await self.run_single_evaluation_benchmark()
        except Exception as e:
            print(f"\n单题评估测试失败: {e}")

        try:
            await self.run_boundary_tests()
        except Exception as e:
            print(f"\n边界测试失败: {e}")

        try:
            await self.run_report_benchmark()
        except Exception as e:
            print(f"\n报告生成测试失败: {e}")

        elapsed = time.time() - start_time

        # 打印汇总
        print("\n" + "="*70)
        print("[统计] 测试结果汇总")
        print("="*70)
        print(f"通过: {self.passed}")
        print(f"失败: {self.failed}")
        print(f"总耗时: {elapsed:.2f}s")

        # 保存结果
        await self._save_results()

        return self.results

    async def _save_results(self):
        """保存测试结果"""
        output_dir = Path(__file__).parent.parent.parent.parent / "reports"
        output_dir.mkdir(exist_ok=True)

        import json
        output_path = output_dir / "benchmark_results.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n结果已保存: {output_path}")


def main():
    """主函数"""
    runner = BenchmarkRunner()
    asyncio.run(runner.run_all())


if __name__ == "__main__":
    main()
