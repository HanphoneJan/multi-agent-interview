"""Recommendation evaluation module.

Provides offline/online metrics and A/B testing for:
- Page recommendations: Precision@K, Recall@K, NDCG@K, HitRate@K
- Report recommendations: relevance, coverage, diversity
"""

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
)
from app.recommenders.evaluation.ab_test import (
    ABTestConfig,
    ABTestResult,
    compute_ab_test_result,
)

__all__ = [
    "precision_at_k",
    "recall_at_k",
    "ndcg_at_k",
    "hit_rate_at_k",
    "compute_page_recommendation_metrics",
    "compute_aggregate_metrics",
    "compute_report_recommendation_metrics",
    "ABTestConfig",
    "ABTestResult",
    "compute_ab_test_result",
]
