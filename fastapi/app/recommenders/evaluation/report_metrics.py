"""Offline evaluation metrics for interview report recommendations.

Implements:
- 推荐相关性 (Relevance): Match between recommended resources and evaluation weak areas
- 推荐覆盖率 (Coverage): Proportion of weak areas covered by recommendations
- 推荐多样性 (Diversity): Variety of resource types in recommendations
"""

from typing import Any


def compute_relevance_score(
    recommended_resources: list[dict[str, Any]],
    weak_dimensions: list[str],
    dimension_to_tags: dict[str, list[str]],
) -> float:
    """Compute recommendation relevance.

    Relevance = how well recommended resources match the user's weak areas.
    Uses tag overlap between resource tags and weak dimension tags.

    Args:
        recommended_resources: List of recommended resources with 'tags' field
        weak_dimensions: List of weak dimension names from evaluation
        dimension_to_tags: Map from dimension name to expected tags

    Returns:
        Relevance score in [0, 1]
    """
    if not recommended_resources or not weak_dimensions:
        return 0.0

    total_match = 0.0
    weak_tags = set()
    for dim in weak_dimensions:
        weak_tags.update(dimension_to_tags.get(dim, []))

    if not weak_tags:
        return 0.0

    for rec in recommended_resources:
        resource_tags = rec.get("tags", [])
        if isinstance(resource_tags, str):
            resource_tags = [t.strip() for t in resource_tags.split(",") if t.strip()]
        rec_set = set(resource_tags)
        overlap = len(rec_set & weak_tags) / max(1, len(weak_tags))
        total_match += min(1.0, overlap * 2)  # Cap per-resource contribution

    return min(1.0, total_match / len(recommended_resources))


def compute_coverage_score(
    recommended_resources: list[dict[str, Any]],
    weak_dimensions: list[str],
    dimension_to_tags: dict[str, list[str]],
) -> float:
    """Compute coverage of weak areas by recommendations.

    Coverage = proportion of weak dimensions that have at least one
    matching resource in recommendations.

    Args:
        recommended_resources: List of recommended resources
        weak_dimensions: List of weak dimension names
        dimension_to_tags: Map from dimension to expected tags

    Returns:
        Coverage score in [0, 1]
    """
    if not weak_dimensions:
        return 1.0
    if not recommended_resources:
        return 0.0

    covered = 0
    for dim in weak_dimensions:
        expected_tags = set(dimension_to_tags.get(dim, []))
        if not expected_tags:
            covered += 1
            continue
        for rec in recommended_resources:
            resource_tags = rec.get("tags", [])
            if isinstance(resource_tags, str):
                resource_tags = [t.strip() for t in resource_tags.split(",") if t.strip()]
            if set(resource_tags) & expected_tags:
                covered += 1
                break

    return covered / len(weak_dimensions)


def compute_diversity_score(
    recommended_resources: list[dict[str, Any]],
) -> float:
    """Compute diversity of recommended resources.

    Diversity = 1 - (dominant_type_ratio).
    Higher when resource types are more evenly distributed.

    Args:
        recommended_resources: List with 'resource_type' field

    Returns:
        Diversity score in [0, 1]
    """
    if not recommended_resources or len(recommended_resources) < 2:
        return 0.0

    type_counts: dict[str, int] = {}
    for rec in recommended_resources:
        t = rec.get("resource_type", "unknown")
        if hasattr(t, "value"):  # Enum
            t = t.value
        else:
            t = str(t) if t else "unknown"
        type_counts[t] = type_counts.get(t, 0) + 1

    n = len(recommended_resources)
    # Simpson diversity index: 1 - sum(p_i^2)
    simpson = 1.0
    for count in type_counts.values():
        p = count / n
        simpson -= p * p

    return max(0.0, simpson)


from app.core.constants import DIMENSION_TAGS

# Default dimension-to-tags mapping (re-export for backward compatibility)
DEFAULT_DIMENSION_TAGS = DIMENSION_TAGS


def compute_report_recommendation_metrics(
    recommended_resources: list[dict[str, Any]],
    weak_dimensions: list[str],
    dimension_to_tags: dict[str, list[str]] | None = None,
) -> dict[str, float]:
    """Compute all report recommendation metrics.

    Args:
        recommended_resources: List of recommended resources
        weak_dimensions: List of weak dimension names from evaluation
        dimension_to_tags: Optional custom dimension-tag mapping

    Returns:
        Dict with relevance, coverage, diversity
    """
    tags_map = dimension_to_tags or DEFAULT_DIMENSION_TAGS

    return {
        "relevance": compute_relevance_score(
            recommended_resources, weak_dimensions, tags_map
        ),
        "coverage": compute_coverage_score(
            recommended_resources, weak_dimensions, tags_map
        ),
        "diversity": compute_diversity_score(recommended_resources),
    }
