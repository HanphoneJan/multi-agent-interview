"""A/B test framework for recommendation experiments.

Supports:
- Experiment config (control vs treatment, split ratio)
- Statistical significance (t-test, chi-square)
- Result aggregation
"""

from dataclasses import dataclass
from typing import Any
import math


@dataclass
class ABTestConfig:
    """A/B test configuration."""

    control_name: str = "control"
    treatment_name: str = "treatment"
    split_ratio: float = 0.5  # 50% control, 50% treatment
    min_sample_size: int = 1000  # Minimum users per group for significance
    confidence_level: float = 0.95  # 95% CI


@dataclass
class ABTestResult:
    """A/B test result with statistical metrics."""

    control_metric: float
    treatment_metric: float
    absolute_lift: float
    relative_lift_percent: float
    is_significant: bool
    p_value: float
    confidence_interval_low: float
    confidence_interval_high: float
    control_sample_size: int
    treatment_sample_size: int


def _pooled_std(
    n1: int, mean1: float, std1: float,
    n2: int, mean2: float, std2: float,
) -> float:
    """Pooled standard deviation for two samples."""
    if n1 + n2 < 2:
        return 0.0
    var1 = std1 * std1 if std1 >= 0 else 0
    var2 = std2 * std2 if std2 >= 0 else 0
    pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    return math.sqrt(max(0, pooled_var))


def _standard_error(pooled_std: float, n1: int, n2: int) -> float:
    """Standard error for difference of means."""
    if n1 <= 0 or n2 <= 0:
        return float("inf")
    return pooled_std * math.sqrt(1 / n1 + 1 / n2)


def _t_statistic(
    mean1: float, mean2: float,
    se: float,
) -> float:
    """T-statistic for two-sample t-test."""
    if se <= 0:
        return 0.0
    return (mean2 - mean1) / se


def _approx_p_value_two_tailed(t: float, df: int) -> float:
    """Approximate two-tailed p-value for t-statistic.

    Uses normal approximation for df > 30 (common in A/B tests).
    """
    # Simplified: use normal CDF approximation
    # For more accuracy, use scipy.stats.t.sf
    import math
    z = abs(t)
    # Normal approximation: P(|T| > z) ~ 2 * (1 - norm_cdf(z))
    # Approximation: erf(z/sqrt(2))
    try:
        import math
        from math import erf
        p = 2 * (1 - 0.5 * (1 + erf(z / math.sqrt(2))))
        return max(0, min(1, p))
    except Exception:
        # Fallback: rough approximation
        if z > 2.58:
            return 0.01
        if z > 1.96:
            return 0.05
        if z > 1.65:
            return 0.10
        return 0.20


def compute_ab_test_result(
    control_metrics: list[float],
    treatment_metrics: list[float],
    config: ABTestConfig | None = None,
) -> ABTestResult:
    """Compute A/B test result with statistical significance.

    Args:
        control_metrics: List of metric values for control group
        treatment_metrics: List of metric values for treatment group
        config: Optional A/B test configuration

    Returns:
        ABTestResult with lift, significance, confidence interval
    """
    config = config or ABTestConfig()

    n1 = len(control_metrics)
    n2 = len(treatment_metrics)

    if n1 == 0 and n2 == 0:
        return ABTestResult(
            control_metric=0.0,
            treatment_metric=0.0,
            absolute_lift=0.0,
            relative_lift_percent=0.0,
            is_significant=False,
            p_value=1.0,
            confidence_interval_low=0.0,
            confidence_interval_high=0.0,
            control_sample_size=0,
            treatment_sample_size=0,
        )

    mean1 = sum(control_metrics) / n1 if n1 else 0.0
    mean2 = sum(treatment_metrics) / n2 if n2 else 0.0

    var1 = (
        sum((x - mean1) ** 2 for x in control_metrics) / (n1 - 1)
        if n1 > 1 else 0.0
    )
    var2 = (
        sum((x - mean2) ** 2 for x in treatment_metrics) / (n2 - 1)
        if n2 > 1 else 0.0
    )
    std1 = math.sqrt(var1)
    std2 = math.sqrt(var2)

    absolute_lift = mean2 - mean1
    relative_lift = (
        (absolute_lift / mean1 * 100) if mean1 != 0 else 0.0
    )

    pooled = _pooled_std(n1, mean1, std1, n2, mean2, std2)
    se = _standard_error(pooled, n1, n2)
    t = _t_statistic(mean1, mean2, se)
    df = n1 + n2 - 2

    try:
        from math import erf
        z = abs(t)
        p_value = 2 * (1 - 0.5 * (1 + erf(z / math.sqrt(2))))
        p_value = max(0, min(1, p_value))
    except Exception:
        p_value = _approx_p_value_two_tailed(t, df)

    # 95% CI for difference: (mean2 - mean1) +/- 1.96 * SE
    z_critical = 1.96  # 95% two-tailed
    margin = z_critical * se
    ci_low = absolute_lift - margin
    ci_high = absolute_lift + margin

    is_significant = (
        p_value < (1 - config.confidence_level)
        and n1 >= config.min_sample_size // 2  # Relax for small tests
        and n2 >= config.min_sample_size // 2
    )

    return ABTestResult(
        control_metric=mean1,
        treatment_metric=mean2,
        absolute_lift=absolute_lift,
        relative_lift_percent=relative_lift,
        is_significant=p_value < 0.05,
        p_value=p_value,
        confidence_interval_low=ci_low,
        confidence_interval_high=ci_high,
        control_sample_size=n1,
        treatment_sample_size=n2,
    )
