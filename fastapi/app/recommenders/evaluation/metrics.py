"""Offline evaluation metrics for page recommendations.

Implements:
- Precision@K: Proportion of relevant items in top-K
- Recall@K: Proportion of relevant items retrieved in top-K
- NDCG@K: Normalized Discounted Cumulative Gain
- HitRate@K: Hit rate at position K
"""

from typing import Any
import math


def precision_at_k(
    recommended: list[int],
    relevant: set[int],
    k: int,
) -> float:
    """Compute Precision@K.

    Precision@K = (# of relevant items in top-K) / K

    Args:
        recommended: List of recommended resource IDs (ordered by score)
        relevant: Set of resource IDs user actually interacted with (ground truth)
        k: Top-K position

    Returns:
        Precision value in [0, 1]
    """
    if k <= 0:
        return 0.0
    top_k = recommended[:k]
    hits = sum(1 for rid in top_k if rid in relevant)
    return hits / k


def recall_at_k(
    recommended: list[int],
    relevant: set[int],
    k: int,
) -> float:
    """Compute Recall@K.

    Recall@K = (# of relevant items in top-K) / (# of all relevant items)

    Args:
        recommended: List of recommended resource IDs
        relevant: Set of relevant resource IDs (ground truth)
        k: Top-K position

    Returns:
        Recall value in [0, 1]. Returns 0 if relevant set is empty.
    """
    if not relevant or k <= 0:
        return 0.0
    top_k = recommended[:k]
    hits = sum(1 for rid in top_k if rid in relevant)
    return hits / len(relevant)


def dcg_at_k(
    recommended: list[int],
    relevant: set[int],
    k: int,
) -> float:
    """Compute Discounted Cumulative Gain at K.

    DCG@K = sum(rel_i / log2(i+1)) for i in 1..k
    """
    if k <= 0:
        return 0.0
    dcg = 0.0
    for i, rid in enumerate(recommended[:k]):
        pos = i + 1
        rel = 1.0 if rid in relevant else 0.0
        dcg += rel / math.log2(pos + 1)
    return dcg


def ndcg_at_k(
    recommended: list[int],
    relevant: set[int],
    k: int,
) -> float:
    """Compute Normalized Discounted Cumulative Gain at K.

    NDCG@K = DCG@K / IDCG@K
    IDCG is DCG of ideal ranking (all relevant first).

    Args:
        recommended: List of recommended resource IDs
        relevant: Set of relevant resource IDs
        k: Top-K position

    Returns:
        NDCG value in [0, 1]
    """
    if k <= 0 or not relevant:
        return 0.0
    dcg = dcg_at_k(recommended, relevant, k)
    # Ideal: all relevant items first
    ideal_relevant = list(relevant)[:k]
    idcg = dcg_at_k(ideal_relevant, relevant, k)
    if idcg == 0:
        return 0.0
    return dcg / idcg


def hit_rate_at_k(
    recommended: list[int],
    relevant: set[int],
    k: int,
) -> float:
    """Compute HitRate@K.

    HitRate@K = 1 if any relevant item in top-K, else 0.

    Args:
        recommended: List of recommended resource IDs
        relevant: Set of relevant resource IDs
        k: Top-K position

    Returns:
        1.0 or 0.0
    """
    if k <= 0 or not relevant:
        return 0.0
    top_k = recommended[:k]
    return 1.0 if any(rid in relevant for rid in top_k) else 0.0


def compute_page_recommendation_metrics(
    recommended: list[int],
    relevant: set[int],
    k: int = 10,
) -> dict[str, float]:
    """Compute all page recommendation metrics at K.

    Args:
        recommended: List of recommended resource IDs
        relevant: Set of relevant resource IDs (ground truth)
        k: Top-K for metrics (default 10)

    Returns:
        Dict with precision_at_k, recall_at_k, ndcg_at_k, hit_rate_at_k
    """
    return {
        "precision_at_k": precision_at_k(recommended, relevant, k),
        "recall_at_k": recall_at_k(recommended, relevant, k),
        "ndcg_at_k": ndcg_at_k(recommended, relevant, k),
        "hit_rate_at_k": hit_rate_at_k(recommended, relevant, k),
        "k": k,
    }


def compute_aggregate_metrics(
    results: list[dict[str, float]],
    k: int = 10,
) -> dict[str, float]:
    """Compute aggregate metrics across multiple user evaluations.

    Args:
        results: List of per-user metric dicts from compute_page_recommendation_metrics
        k: K value for reference

    Returns:
        Dict with mean precision_at_k, recall_at_k, ndcg_at_k, hit_rate_at_k
    """
    if not results:
        return {
            "mean_precision_at_k": 0.0,
            "mean_recall_at_k": 0.0,
            "mean_ndcg_at_k": 0.0,
            "mean_hit_rate_at_k": 0.0,
            "k": k,
            "num_users": 0,
        }

    n = len(results)
    return {
        "mean_precision_at_k": sum(r["precision_at_k"] for r in results) / n,
        "mean_recall_at_k": sum(r["recall_at_k"] for r in results) / n,
        "mean_ndcg_at_k": sum(r["ndcg_at_k"] for r in results) / n,
        "mean_hit_rate_at_k": sum(r["hit_rate_at_k"] for r in results) / n,
        "k": k,
        "num_users": n,
    }
