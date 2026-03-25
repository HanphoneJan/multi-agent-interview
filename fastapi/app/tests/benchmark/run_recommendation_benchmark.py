"""推荐系统 Benchmark 运行脚本

运行所有推荐系统测试并生成报告。

Usage:
    cd fastapi
    uv run python -m app.tests.benchmark.run_recommendation_benchmark
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path
from statistics import mean
import json

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.tests.benchmark.recommendation_data import (
    TEST_USER_PROFILES,
    TEST_RESOURCES,
    PRECISION_AT_K_THRESHOLD,
    INTERVIEW_CORRELATION_THRESHOLD,
    get_user_profile,
)
from app.tests.benchmark.test_recommendation_accuracy import (
    TestRecommendationAccuracy,
    TestRAGRecommendation,
)
from app.tests.benchmark.test_recommendation_integration import (
    TestEndToEndRecommendation,
    TestRecommendationPerformance,
)


class RecommendationBenchmarkRunner:
    """推荐系统 Benchmark 运行器"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "accuracy": {},
            "integration": {},
            "performance": {},
            "summary": {},
        }
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    async def run_accuracy_benchmark(self):
        """运行准确性测试"""
        print("\n" + "="*70)
        print("[准确性测试]")
        print("="*70)

        test = TestRecommendationAccuracy()
        accuracy_results = []

        # 测试每个有评估数据的用户
        test_users = [p for p in TEST_USER_PROFILES if p["evaluation"] is not None]

        for user_profile in test_users:
            try:
                print(f"\n用户 {user_profile['user_id']} ({user_profile['type']})...")

                # 获取混合推荐
                recommendations = await test._get_hybrid_recommendations(
                    user_profile["user_id"], limit=10
                )

                if not recommendations:
                    print("  [WARN] 无推荐结果")
                    self.warnings += 1
                    continue

                relevant_items = test._get_relevant_items_for_user(user_profile)

                # 计算指标
                precision = test._calculate_precision_at_k(recommendations, relevant_items, k=5)
                recall = test._calculate_recall_at_k(recommendations, relevant_items, k=5)
                ndcg = test._calculate_ndcg_at_k(recommendations, relevant_items, k=5)
                correlation = calculate_tag_overlap(recommendations[:5], user_profile.get("expected_tags", []))

                accuracy_results.append({
                    "user_id": user_profile["user_id"],
                    "type": user_profile["type"],
                    "precision": precision,
                    "recall": recall,
                    "ndcg": ndcg,
                    "correlation": correlation,
                })

                print(f"  Precision@5: {precision:.3f}")
                print(f"  Recall@5: {recall:.3f}")
                print(f"  NDCG@5: {ndcg:.3f}")
                print(f"  面试关联度: {correlation:.3f}")

                # 判定
                if precision >= PRECISION_AT_K_THRESHOLD:
                    print("  [PASS] 精度达标")
                    self.passed += 1
                else:
                    print(f"  [WARN] 精度 {precision:.3f} 低于阈值 {PRECISION_AT_K_THRESHOLD}")
                    self.warnings += 1

            except Exception as e:
                print(f"  [FAIL] 测试失败: {e}")
                self.failed += 1

        # 汇总统计
        if accuracy_results:
            self.results["accuracy"] = {
                "tested": len(accuracy_results),
                "avg_precision": mean([r["precision"] for r in accuracy_results]),
                "avg_recall": mean([r["recall"] for r in accuracy_results]),
                "avg_ndcg": mean([r["ndcg"] for r in accuracy_results]),
                "avg_correlation": mean([r["correlation"] for r in accuracy_results]),
                "results": accuracy_results,
            }

            print(f"\n准确性汇总:")
            print(f"  测试用户数: {len(accuracy_results)}")
            print(f"  平均 Precision@5: {self.results['accuracy']['avg_precision']:.3f}")
            print(f"  平均 Recall@5: {self.results['accuracy']['avg_recall']:.3f}")
            print(f"  平均 NDCG@5: {self.results['accuracy']['avg_ndcg']:.3f}")
            print(f"  平均面试关联度: {self.results['accuracy']['avg_correlation']:.3f}")

    async def run_cold_start_benchmark(self):
        """运行冷启动测试"""
        print("\n" + "="*70)
        print("[冷启动测试]")
        print("="*70)

        test = TestRecommendationAccuracy()
        cold_user = get_user_profile(1005)  # 冷启动用户

        try:
            recommendations = await test._get_hybrid_recommendations(cold_user["user_id"], limit=5)

            print(f"\n冷启动用户 {cold_user['user_id']}:")
            print(f"  推荐数量: {len(recommendations)}")

            if recommendations:
                expected_tags = cold_user.get("expected_tags", [])
                overlap = calculate_tag_overlap(recommendations, expected_tags)

                print(f"  与基础标签重叠度: {overlap:.3f}")

                self.results["cold_start"] = {
                    "recommendation_count": len(recommendations),
                    "tag_overlap": overlap,
                }

                if overlap >= 0.30:
                    print("  [PASS] 冷启动推荐达标")
                    self.passed += 1
                else:
                    print("  [WARN] 冷启动推荐可能不够基础")
                    self.warnings += 1
            else:
                print("  [FAIL] 冷启动用户无推荐")
                self.failed += 1

        except Exception as e:
            print(f"  [FAIL] 冷启动测试失败: {e}")
            self.failed += 1

    async def run_performance_benchmark(self):
        """运行性能测试"""
        print("\n" + "="*70)
        print("[性能测试]")
        print("="*70)

        from app.tests.benchmark.recommendation_data import PERSONALIZED_REC_TIME_THRESHOLD

        test = TestRecommendationPerformance()

        try:
            print("\n响应时间测试...")
            await test.test_personalized_response_time()
            print("  [PASS] 响应时间测试完成")
            self.passed += 1
        except AssertionError as e:
            print(f"  [WARN] 响应时间警告: {e}")
            self.warnings += 1
        except Exception as e:
            print(f"  [FAIL] 响应时间测试失败: {e}")
            self.failed += 1

        try:
            print("\n并发测试...")
            await test.test_concurrent_recommendations()
            print("  [PASS] 并发测试完成")
            self.passed += 1
        except Exception as e:
            print(f"  [FAIL] 并发测试失败: {e}")
            self.failed += 1

    async def run_integration_benchmark(self):
        """运行集成测试"""
        print("\n" + "="*70)
        print("[集成测试]")
        print("="*70)

        test = TestEndToEndRecommendation()

        try:
            print("\n端到端流程测试...")
            await test.test_complete_recommendation_flow()
            print("  [PASS] 端到端流程测试完成")
            self.passed += 1
        except Exception as e:
            print(f"  [FAIL] 端到端流程测试失败: {e}")
            self.failed += 1

    async def run_all(self):
        """运行所有 benchmark"""
        print("\n" + "="*70)
        print("   AI 面试资源推荐系统 Benchmark 测试")
        print("="*70)

        start_time = time.time()

        # 运行测试
        await self.run_accuracy_benchmark()
        await self.run_cold_start_benchmark()
        await self.run_performance_benchmark()
        await self.run_integration_benchmark()

        elapsed = time.time() - start_time

        # 打印汇总
        print("\n" + "="*70)
        print("[测试结果汇总]")
        print("="*70)
        print(f"通过: {self.passed}")
        print(f"警告: {self.warnings}")
        print(f"失败: {self.failed}")
        print(f"总耗时: {elapsed:.2f}s")

        # 判定标准
        print("\n[判定标准]")
        if self.results.get("accuracy"):
            precision = self.results["accuracy"]["avg_precision"]
            correlation = self.results["accuracy"]["avg_correlation"]

            print(f"Precision@5: {precision:.3f} (阈值: {PRECISION_AT_K_THRESHOLD})")
            print(f"面试关联度: {correlation:.3f} (阈值: {INTERVIEW_CORRELATION_THRESHOLD})")

            if precision >= PRECISION_AT_K_THRESHOLD and correlation >= INTERVIEW_CORRELATION_THRESHOLD:
                print("\n[结论] 推荐系统表现良好，满足生产环境要求")
            else:
                print("\n[结论] 推荐系统需要优化，建议查看详细测试报告")

        # 保存结果
        await self._save_results()

        return self.results

    async def _save_results(self):
        """保存测试结果"""
        output_dir = Path(__file__).parent.parent.parent.parent / "reports"
        output_dir.mkdir(exist_ok=True)

        # 保存 JSON
        json_path = output_dir / "recommendation_benchmark_results.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n结果已保存: {json_path}")

        # 生成 HTML 报告
        await self._generate_html_report(output_dir)

    async def _generate_html_report(self, output_dir: Path):
        """生成 HTML 报告"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 面试推荐系统 Benchmark 报告</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f7fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; }}
        .card {{ background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .metric {{ display: inline-block; padding: 10px 20px; margin: 5px; border-radius: 8px; font-weight: bold; }}
        .pass {{ background: #d1fae5; color: #065f46; }}
        .warn {{ background: #fef3c7; color: #92400e; }}
        .fail {{ background: #fee2e2; color: #991b1b; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
        th {{ background: #f9fafb; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>AI 面试推荐系统 Benchmark 报告</h1>
            <p>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </header>

        <div class="card">
            <h2>测试汇总</h2>
            <div class="metric pass">通过: {self.passed}</div>
            <div class="metric warn">警告: {self.warnings}</div>
            <div class="metric fail">失败: {self.failed}</div>
        </div>
"""

        if self.results.get("accuracy"):
            html += f"""
        <div class="card">
            <h2>准确性指标</h2>
            <table>
                <tr><th>指标</th><th>平均值</th><th>阈值</th><th>状态</th></tr>
                <tr>
                    <td>Precision@5</td>
                    <td>{self.results['accuracy']['avg_precision']:.3f}</td>
                    <td>{PRECISION_AT_K_THRESHOLD}</td>
                    <td>{'通过' if self.results['accuracy']['avg_precision'] >= PRECISION_AT_K_THRESHOLD else '需优化'}</td>
                </tr>
                <tr>
                    <td>Recall@5</td>
                    <td>{self.results['accuracy']['avg_recall']:.3f}</td>
                    <td>-</td>
                    <td>-</td>
                </tr>
                <tr>
                    <td>NDCG@5</td>
                    <td>{self.results['accuracy']['avg_ndcg']:.3f}</td>
                    <td>-</td>
                    <td>-</td>
                </tr>
                <tr>
                    <td>面试关联度</td>
                    <td>{self.results['accuracy']['avg_correlation']:.3f}</td>
                    <td>{INTERVIEW_CORRELATION_THRESHOLD}</td>
                    <td>{'通过' if self.results['accuracy']['avg_correlation'] >= INTERVIEW_CORRELATION_THRESHOLD else '需优化'}</td>
                </tr>
            </table>
        </div>
"""

        html += """
    </div>
</body>
</html>
"""

        html_path = output_dir / "recommendation_benchmark_report.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"HTML 报告: {html_path}")


def calculate_tag_overlap(recommendations, expected_tags):
    """计算标签重叠度"""
    if not recommendations or not expected_tags:
        return 0.0

    rec_tags = set()
    for rec in recommendations:
        tags = rec.get("tags", [])
        if isinstance(tags, str):
            tags = tags.split(",")
        rec_tags.update(tags)

    expected_set = set(expected_tags)
    overlap = len(rec_tags & expected_set)
    return overlap / len(expected_set) if expected_set else 0.0


def main():
    """主函数"""
    runner = RecommendationBenchmarkRunner()
    asyncio.run(runner.run_all())


if __name__ == "__main__":
    main()
