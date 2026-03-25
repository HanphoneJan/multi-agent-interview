"""Benchmark 测试报告生成脚本

生成包含以下内容的 HTML 报告：
1. 测试概览统计
2. 分数分布对比图（AI vs 预期）
3. 维度雷达图
4. 详细测试结果表格
5. 性能指标图表
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from statistics import mean, stdev

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.tests.benchmark.benchmark_data import (
    SINGLE_ANSWER_BENCHMARK,
    FULL_INTERVIEW_BENCHMARK,
    score_to_grade,
)


def generate_html_report(results: Dict) -> str:
    """生成 HTML 报告"""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Interview Benchmark Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}
        header .timestamp {{
            opacity: 0.9;
            font-size: 0.9rem;
        }}
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: transform 0.2s;
        }}
        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .card-title {{
            font-size: 0.9rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        .card-value {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #333;
        }}
        .card-value.success {{
            color: #22c55e;
        }}
        .card-value.warning {{
            color: #f59e0b;
        }}
        .card-value.danger {{
            color: #ef4444;
        }}
        .card-subtitle {{
            font-size: 0.85rem;
            color: #999;
            margin-top: 5px;
        }}
        .section {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .section h2 {{
            font-size: 1.5rem;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 10px;
        }}
        .chart-container {{
            position: relative;
            height: 400px;
            margin: 20px 0;
        }}
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }}
        th {{
            background: #f9fafb;
            font-weight: 600;
            color: #374151;
        }}
        tr:hover {{
            background: #f9fafb;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .badge-success {{
            background: #d1fae5;
            color: #065f46;
        }}
        .badge-warning {{
            background: #fef3c7;
            color: #92400e;
        }}
        .badge-danger {{
            background: #fee2e2;
            color: #991b1b;
        }}
        .progress-bar {{
            height: 8px;
            background: #e5e7eb;
            border-radius: 4px;
            overflow: hidden;
        }}
        .progress-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 4px;
            transition: width 0.3s;
        }}
        .metric-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 0;
            border-bottom: 1px solid #e5e7eb;
        }}
        .metric-row:last-child {{
            border-bottom: none;
        }}
        .metric-label {{
            font-weight: 500;
            color: #374151;
        }}
        .metric-value {{
            font-weight: 600;
            color: #111827;
        }}
        .status-pass {{
            color: #22c55e;
        }}
        .status-fail {{
            color: #ef4444;
        }}
        footer {{
            text-align: center;
            padding: 30px;
            color: #6b7280;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎯 AI 面试评分系统 Benchmark 报告</h1>
            <p class="timestamp">生成时间: {timestamp}</p>
        </header>

        <div class="summary-cards">
            <div class="card">
                <div class="card-title">测试用例总数</div>
                <div class="card-value">{results.get('total_cases', 0)}</div>
                <div class="card-subtitle">单题评估 + 完整面试</div>
            </div>
            <div class="card">
                <div class="card-title">平均绝对误差 (MAE)</div>
                <div class="card-value {get_mae_class(results.get('mae', 0))}">{results.get('mae', 0):.3f}</div>
                <div class="card-subtitle">目标: &lt; 0.15</div>
            </div>
            <div class="card">
                <div class="card-title">JSON 格式成功率</div>
                <div class="card-value {get_success_class(results.get('json_validity', 0))}">{results.get('json_validity', 0):.1%}</div>
                <div class="card-subtitle">目标: &gt; 99%</div>
            </div>
            <div class="card">
                <div class="card-title">平均响应时间</div>
                <div class="card-value {get_time_class(results.get('avg_response_time', 0))}">{results.get('avg_response_time', 0):.2f}s</div>
                <div class="card-subtitle">目标: &lt; 5s</div>
            </div>
        </div>

        <div class="section">
            <h2>📊 关键指标概览</h2>
            <div class="metric-row">
                <span class="metric-label">分类准确率</span>
                <span class="metric-value {get_status_class(results.get('classification_accuracy', 0), 0.80)}">
                    {results.get('classification_accuracy', 0):.1%} {'✓' if results.get('classification_accuracy', 0) >= 0.80 else '✗'}
                </span>
            </div>
            <div class="metric-row">
                <span class="metric-label">重复一致性</span>
                <span class="metric-value {get_status_class(results.get('repeatability', 0), 0.90)}">
                    {results.get('repeatability', 0):.1%} {'✓' if results.get('repeatability', 0) >= 0.90 else '✗'}
                </span>
            </div>
            <div class="metric-row">
                <span class="metric-label">边界测试通过率</span>
                <span class="metric-value {get_status_class(results.get('boundary_pass_rate', 0), 0.95)}">
                    {results.get('boundary_pass_rate', 0):.1%} {'✓' if results.get('boundary_pass_rate', 0) >= 0.95 else '✗'}
                </span>
            </div>
            <div class="metric-row">
                <span class="metric-label">并发测试成功率</span>
                <span class="metric-value {get_status_class(results.get('concurrent_success_rate', 0), 0.80)}">
                    {results.get('concurrent_success_rate', 0):.1%} {'✓' if results.get('concurrent_success_rate', 0) >= 0.80 else '✗'}
                </span>
            </div>
        </div>

        <div class="section">
            <h2>📈 分数分布对比</h2>
            <div class="chart-container">
                <canvas id="scoreChart"></canvas>
            </div>
        </div>

        <div class="chart-grid">
            <div class="section">
                <h2>🎯 维度雷达图</h2>
                <div class="chart-container">
                    <canvas id="dimensionChart"></canvas>
                </div>
            </div>
            <div class="section">
                <h2>⚡ 性能指标</h2>
                <div class="chart-container">
                    <canvas id="performanceChart"></canvas>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>📋 详细测试结果</h2>
            <table>
                <thead>
                    <tr>
                        <th>用例 ID</th>
                        <th>分类</th>
                        <th>问题</th>
                        <th>预期分数</th>
                        <th>实际分数</th>
                        <th>误差</th>
                        <th>状态</th>
                    </tr>
                </thead>
                <tbody>
                    {generate_results_table(results.get('detailed_results', []))}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>🎓 面试报告测试</h2>
            <table>
                <thead>
                    <tr>
                        <th>面试 ID</th>
                        <th>类型</th>
                        <th>预期总分</th>
                        <th>实际总分</th>
                        <th>误差</th>
                        <th>状态</th>
                    </tr>
                </thead>
                <tbody>
                    {generate_interview_table(results.get('interview_results', []))}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>📝 结论与建议</h2>
            <div style="padding: 20px;">
                <h3 style="margin-bottom: 15px; color: #374151;">评估结论</h3>
                <p style="margin-bottom: 20px; color: #6b7280; line-height: 1.8;">
                    {generate_conclusion(results)}
                </p>
                <h3 style="margin-bottom: 15px; color: #374151;">优化建议</h3>
                <ul style="color: #6b7280; padding-left: 20px; line-height: 2;">
                    {generate_recommendations(results)}
                </ul>
            </div>
        </div>

        <footer>
            <p>AI Interview Benchmark System v1.0 | Generated on {timestamp}</p>
        </footer>
    </div>

    <script>
        // 分数分布对比图
        const scoreCtx = document.getElementById('scoreChart').getContext('2d');
        new Chart(scoreCtx, {{
            type: 'scatter',
            data: {{
                datasets: [{{
                    label: '预期分数 vs 实际分数',
                    data: {json.dumps([{'x': r['expected'], 'y': r['actual']} for r in results.get('detailed_results', [])])},
                    backgroundColor: 'rgba(102, 126, 234, 0.6)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    pointRadius: 6,
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{
                        type: 'linear',
                        position: 'bottom',
                        title: {{ display: true, text: '预期分数' }},
                        min: 0,
                        max: 1
                    }},
                    y: {{
                        title: {{ display: true, text: '实际分数' }},
                        min: 0,
                        max: 1
                    }}
                }},
                plugins: {{
                    annotation: {{
                        annotations: {{
                            line1: {{
                                type: 'line',
                                xMin: 0,
                                xMax: 1,
                                yMin: 0,
                                yMax: 1,
                                borderColor: 'rgba(239, 68, 68, 0.5)',
                                borderWidth: 2,
                                borderDash: [5, 5],
                                label: {{ content: '理想线 (y=x)', enabled: true }}
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // 维度雷达图
        const dimensionCtx = document.getElementById('dimensionChart').getContext('2d');
        new Chart(dimensionCtx, {{
            type: 'radar',
            data: {{
                labels: ['专业知识', '技能匹配', '语言表达', '逻辑思维', '抗压能力', '个性特征', '求职动机', '价值观'],
                datasets: [{{
                    label: '平均维度分数',
                    data: {results.get('dimension_scores', [70]*8)},
                    backgroundColor: 'rgba(118, 75, 162, 0.2)',
                    borderColor: 'rgba(118, 75, 162, 1)',
                    pointBackgroundColor: 'rgba(118, 75, 162, 1)',
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    r: {{
                        min: 0,
                        max: 100,
                        ticks: {{ stepSize: 20 }}
                    }}
                }}
            }}
        }});

        // 性能指标图
        const perfCtx = document.getElementById('performanceChart').getContext('2d');
        new Chart(perfCtx, {{
            type: 'bar',
            data: {{
                labels: ['< 1s', '1-2s', '2-3s', '3-4s', '4-5s', '> 5s'],
                datasets: [{{
                    label: '响应时间分布',
                    data: {results.get('response_time_distribution', [0, 0, 0, 0, 0, 0])},
                    backgroundColor: [
                        'rgba(34, 197, 94, 0.8)',
                        'rgba(34, 197, 94, 0.6)',
                        'rgba(245, 158, 11, 0.6)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(239, 68, 68, 0.6)',
                        'rgba(239, 68, 68, 0.8)'
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{ display: true, text: '用例数' }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    return html


def get_mae_class(mae: float) -> str:
    """根据 MAE 返回 CSS 类名"""
    if mae < 0.10:
        return "success"
    elif mae < 0.15:
        return "warning"
    return "danger"


def get_success_class(rate: float) -> str:
    """根据成功率返回 CSS 类名"""
    if rate >= 0.99:
        return "success"
    elif rate >= 0.95:
        return "warning"
    return "danger"


def get_time_class(time: float) -> str:
    """根据响应时间返回 CSS 类名"""
    if time < 3:
        return "success"
    elif time < 5:
        return "warning"
    return "danger"


def get_status_class(value: float, threshold: float) -> str:
    """根据阈值返回状态类名"""
    return "status-pass" if value >= threshold else "status-fail"


def generate_results_table(results: List[Dict]) -> str:
    """生成详细结果表格"""
    rows = []
    for r in results[:20]:  # 只显示前20条
        error = abs(r.get('expected', 0) - r.get('actual', 0))
        status_class = "badge-success" if error < 0.2 else "badge-warning" if error < 0.3 else "badge-danger"
        status_text = "通过" if error < 0.2 else "偏差" if error < 0.3 else "失败"

        rows.append(f"""
            <tr>
                <td>{r.get('id', 'N/A')}</td>
                <td>{r.get('category', 'N/A')}</td>
                <td title="{r.get('question', '')}">{r.get('question', '')[:30]}...</td>
                <td>{r.get('expected', 0):.2f}</td>
                <td>{r.get('actual', 0):.2f}</td>
                <td>{error:.2f}</td>
                <td><span class="badge {status_class}">{status_text}</span></td>
            </tr>
        """)
    return "\n".join(rows)


def generate_interview_table(results: List[Dict]) -> str:
    """生成面试结果表格"""
    rows = []
    for r in results:
        error = abs(r.get('expected', 0) - r.get('actual', 0))
        status_class = "badge-success" if error <= 15 else "badge-warning" if error <= 25 else "badge-danger"
        status_text = "通过" if error <= 15 else "偏差" if error <= 25 else "失败"

        rows.append(f"""
            <tr>
                <td>{r.get('session_id', 'N/A')}</td>
                <td>{r.get('category', 'N/A')}</td>
                <td>{r.get('expected', 0)}</td>
                <td>{r.get('actual', 0)}</td>
                <td>{error}</td>
                <td><span class="badge {status_class}">{status_text}</span></td>
            </tr>
        """)
    return "\n".join(rows)


def generate_conclusion(results: Dict) -> str:
    """生成结论文本"""
    mae = results.get('mae', 0)
    json_validity = results.get('json_validity', 0)
    avg_time = results.get('avg_response_time', 0)

    parts = []

    if mae < 0.15:
        parts.append(f"单题评估的 MAE 为 {mae:.3f}，达到优秀标准（< 0.15），评分准确性良好。")
    else:
        parts.append(f"单题评估的 MAE 为 {mae:.3f}，未达到标准（< 0.15），需要优化评分算法。")

    if json_validity >= 0.99:
        parts.append(f"JSON 格式成功率为 {json_validity:.1%}，输出格式稳定性优秀。")
    else:
        parts.append(f"JSON 格式成功率为 {json_validity:.1%}，存在格式解析问题需要修复。")

    if avg_time < 5:
        parts.append(f"平均响应时间为 {avg_time:.2f} 秒，满足性能要求（< 5s）。")
    else:
        parts.append(f"平均响应时间为 {avg_time:.2f} 秒，超出性能目标，建议优化。")

    return " ".join(parts)


def generate_recommendations(results: Dict) -> str:
    """生成优化建议"""
    recommendations = []
    mae = results.get('mae', 0)
    json_validity = results.get('json_validity', 0)
    repeatability = results.get('repeatability', 0)

    if mae >= 0.15:
        recommendations.append("<li>优化评分提示词（prompt），增加更多评分示例和指导</li>")
        recommendations.append("<li>针对偏差较大的题目类型（如行为面试题）进行专项调优</li>")

    if json_validity < 0.99:
        recommendations.append("<li>加强 JSON 格式约束，使用更严格的输出格式规范</li>")
        recommendations.append("<li>增加 JSON 解析失败时的重试和降级机制</li>")

    if repeatability < 0.90:
        recommendations.append("<li>增加采样次数取平均，提高评分稳定性</li>")
        recommendations.append("<li>调整模型 temperature 参数，降低随机性</li>")

    if not recommendations:
        recommendations.append("<li>系统整体表现良好，建议持续监控生产环境的评分质量</li>")
        recommendations.append("<li>定期收集人工评分数据进行对比校准</li>")

    recommendations.append("<li>建立评分质量监控告警机制</li>")

    return "\n".join(recommendations)


def create_mock_results() -> Dict:
    """创建模拟结果（用于演示）"""
    detailed_results = []
    for case in SINGLE_ANSWER_BENCHMARK[:15]:
        import random
        expected = case["expected_score"]
        # 模拟实际分数，添加一些随机偏差
        noise = random.gauss(0, 0.08)
        actual = max(0, min(1, expected + noise))

        detailed_results.append({
            "id": case["id"],
            "category": case["category"],
            "question": case["question"],
            "expected": expected,
            "actual": actual,
        })

    interview_results = []
    for interview in FULL_INTERVIEW_BENCHMARK:
        expected = interview["expected_overall_score"]
        noise = random.gauss(0, 8)
        actual = max(0, min(100, expected + noise))

        interview_results.append({
            "session_id": interview["session_id"],
            "category": interview["category"],
            "expected": expected,
            "actual": int(actual),
        })

    # 计算 MAE
    errors = [abs(r["expected"] - r["actual"]) for r in detailed_results]
    mae = mean(errors)

    return {
        "total_cases": len(SINGLE_ANSWER_BENCHMARK) + len(FULL_INTERVIEW_BENCHMARK),
        "mae": mae,
        "json_validity": 0.985,
        "avg_response_time": 3.2,
        "classification_accuracy": 0.82,
        "repeatability": 0.92,
        "boundary_pass_rate": 0.98,
        "concurrent_success_rate": 0.88,
        "dimension_scores": [75, 72, 78, 80, 76, 74, 77, 73],
        "response_time_distribution": [5, 8, 4, 2, 1, 0],
        "detailed_results": detailed_results,
        "interview_results": interview_results,
    }


def main():
    """主函数"""
    print("Generating benchmark report...")

    # 创建输出目录
    output_dir = Path(__file__).parent.parent.parent.parent / "reports"
    output_dir.mkdir(exist_ok=True)

    # 使用模拟数据生成报告
    # 实际使用时，应从测试结果文件加载
    results = create_mock_results()

    # 生成 HTML
    html = generate_html_report(results)

    # 保存报告
    output_path = output_dir / "benchmark_report.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Report saved to: {output_path}")


if __name__ == "__main__":
    main()
