"""Tests for recommendation evaluation module"""
import pytest

from app.recommenders.evaluation.metrics import (
    precision_at_k,
    recall_at_k,
    ndcg_at_k,
    hit_rate_at_k,
    compute_page_recommendation_metrics,
    compute_aggregate_metrics,
)
from app.recommenders.evaluation.report_metrics import (
    compute_report_recommendation_metrics,
    compute_relevance_score,
    compute_coverage_score,
    compute_diversity_score,
)
from app.recommenders.evaluation.ab_test import (
    compute_ab_test_result,
    ABTestConfig,
)


class TestPageMetrics:
    """Tests for page recommendation metrics"""

    def test_precision_at_k_perfect(self):
        """Perfect precision: all top-K are relevant"""
        rec = [1, 2, 3, 4, 5]
        rel = {1, 2, 3}
        assert precision_at_k(rec, rel, 3) == 1.0
        assert precision_at_k(rec, rel, 5) == 0.6  # 3/5

    def test_precision_at_k_partial(self):
        """Partial precision"""
        rec = [1, 99, 2, 88, 3]
        rel = {1, 2, 3}
        assert precision_at_k(rec, rel, 3) == pytest.approx(2 / 3)
        assert precision_at_k(rec, rel, 5) == 0.6

    def test_precision_at_k_empty_relevant(self):
        """No relevant items"""
        rec = [1, 2, 3]
        rel = set()
        assert precision_at_k(rec, rel, 3) == 0.0

    def test_recall_at_k(self):
        """Recall calculation"""
        rec = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        rel = {1, 2, 3, 100}
        # Top 3 has 3 relevant, total 4 relevant
        assert recall_at_k(rec, rel, 3) == pytest.approx(3 / 4)
        assert recall_at_k(rec, rel, 10) == pytest.approx(3 / 4)

    def test_recall_at_k_empty_relevant(self):
        rec = [1, 2, 3]
        rel = set()
        assert recall_at_k(rec, rel, 3) == 0.0

    def test_ndcg_at_k(self):
        """NDCG: ideal ranking has NDCG=1"""
        rec = [1, 2, 3]
        rel = {1, 2, 3}
        assert ndcg_at_k(rec, rel, 3) == pytest.approx(1.0, rel=1e-5)

    def test_ndcg_at_k_worse_ranking(self):
        """Worse ranking gives lower NDCG when relevant items are at different positions"""
        # Put relevant items 1,2 at end -> worse than [1,2,...]
        rec = [99, 98, 1, 2]
        rel = {1, 2}
        worse = ndcg_at_k(rec, rel, 4)
        better = ndcg_at_k([1, 2, 99, 98], rel, 4)
        assert 0 < worse < 1.0
        assert better > worse

    def test_hit_rate_at_k(self):
        """Hit rate is 1 if any relevant in top-K"""
        rec = [99, 98, 1]
        rel = {1}
        assert hit_rate_at_k(rec, rel, 3) == 1.0
        assert hit_rate_at_k(rec, rel, 2) == 0.0

    def test_compute_page_recommendation_metrics(self):
        """Full metrics computation"""
        rec = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        rel = {1, 2, 3}
        m = compute_page_recommendation_metrics(rec, rel, k=10)
        assert "precision_at_k" in m
        assert "recall_at_k" in m
        assert "ndcg_at_k" in m
        assert "hit_rate_at_k" in m
        assert m["precision_at_k"] == pytest.approx(0.3)
        assert m["recall_at_k"] == pytest.approx(1.0)
        assert m["hit_rate_at_k"] == 1.0

    def test_compute_aggregate_metrics(self):
        """Aggregate across users"""
        results = [
            {"precision_at_k": 0.3, "recall_at_k": 0.5, "ndcg_at_k": 0.4, "hit_rate_at_k": 1.0},
            {"precision_at_k": 0.5, "recall_at_k": 0.5, "ndcg_at_k": 0.6, "hit_rate_at_k": 1.0},
        ]
        agg = compute_aggregate_metrics(results, k=10)
        assert agg["mean_precision_at_k"] == pytest.approx(0.4)
        assert agg["mean_recall_at_k"] == pytest.approx(0.5)
        assert agg["num_users"] == 2


class TestReportMetrics:
    """Tests for report recommendation metrics"""

    def test_relevance_score(self):
        """Relevance: resources matching weak dimensions"""
        resources = [
            {"tags": ["Python", "Django"], "resource_type": "course"},
            {"tags": ["算法", "LeetCode"], "resource_type": "article"},
        ]
        weak = ["professional_knowledge", "logical_thinking"]
        score = compute_relevance_score(
            resources, weak,
            {
                "professional_knowledge": ["Python", "Java", "Django"],
                "logical_thinking": ["算法", "LeetCode"],
            }
        )
        assert 0 < score <= 1.0

    def test_coverage_score(self):
        """Coverage: weak areas covered by recommendations"""
        resources = [
            {"tags": ["Python"], "resource_type": "course"},
            {"tags": ["算法"], "resource_type": "article"},
        ]
        weak = ["professional_knowledge", "logical_thinking"]
        tags_map = {
            "professional_knowledge": ["Python"],
            "logical_thinking": ["算法"],
        }
        cov = compute_coverage_score(resources, weak, tags_map)
        assert cov == 1.0

    def test_coverage_partial(self):
        """Partial coverage"""
        resources = [{"tags": ["Python"], "resource_type": "course"}]
        weak = ["professional_knowledge", "logical_thinking"]
        tags_map = {
            "professional_knowledge": ["Python"],
            "logical_thinking": ["算法"],
        }
        cov = compute_coverage_score(resources, weak, tags_map)
        assert cov == pytest.approx(0.5)

    def test_diversity_score(self):
        """Diversity: mixed resource types"""
        resources = [
            {"resource_type": "course"},
            {"resource_type": "article"},
            {"resource_type": "video"},
        ]
        d = compute_diversity_score(resources)
        assert 0 < d <= 1.0

    def test_diversity_score_same_type(self):
        """Low diversity when all same type"""
        resources = [
            {"resource_type": "course"},
            {"resource_type": "course"},
            {"resource_type": "course"},
        ]
        d = compute_diversity_score(resources)
        assert d == 0.0

    def test_compute_report_recommendation_metrics(self):
        """Full report metrics"""
        resources = [
            {"tags": ["Python", "Django"], "resource_type": "course"},
            {"tags": ["算法"], "resource_type": "article"},
        ]
        weak = ["professional_knowledge", "logical_thinking"]
        m = compute_report_recommendation_metrics(resources, weak)
        assert "relevance" in m
        assert "coverage" in m
        assert "diversity" in m


class TestABTest:
    """Tests for A/B test framework"""

    def test_ab_test_basic(self):
        """Basic A/B test computation"""
        control = [0.1, 0.2, 0.15, 0.18, 0.12] * 20  # 100 samples, mean ~0.15
        treatment = [0.2, 0.25, 0.22, 0.18, 0.2] * 20  # 100 samples, mean ~0.21
        result = compute_ab_test_result(control, treatment)
        assert result.control_metric == pytest.approx(0.15, rel=0.1)
        assert result.treatment_metric == pytest.approx(0.21, rel=0.1)
        assert result.absolute_lift > 0
        assert result.control_sample_size == 100
        assert result.treatment_sample_size == 100

    def test_ab_test_empty(self):
        """Empty groups"""
        result = compute_ab_test_result([], [])
        assert result.control_metric == 0.0
        assert result.treatment_metric == 0.0
        assert result.is_significant is False
