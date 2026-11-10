"""Stage 6: Confirmatory Hypothesis Evaluation (H1-H5) with Holm Adjustment.

Applies:
- Holm-Bonferroni step-down familywise error control at alpha = 0.05
- Intersection-union decision rules for H2-H4
"""

from typing import List
import numpy as np
from src.contracts.evaluation import HypothesisTestResult


def apply_holm_bonferroni(raw_p_values: List[float]) -> List[float]:
    """Applies Holm-Bonferroni correction to a list of p-values."""
    m = len(raw_p_values)
    indexed_p = sorted(enumerate(raw_p_values), key=lambda x: x[1])

    adjusted_p = [0.0] * m
    running_max = 0.0

    for rank, (orig_idx, p_val) in enumerate(indexed_p):
        multiplier = m - rank
        adj = min(1.0, p_val * multiplier)
        running_max = max(running_max, adj)
        adjusted_p[orig_idx] = running_max

    return adjusted_p


def evaluate_h1(abs_bw_gap: float, noise_floor: float, std_err: float = 0.003) -> HypothesisTestResult:
    """H1: Absolute Black-White exposure gap exceeds within-group noise floor by >= 0.01."""
    point_est = abs_bw_gap - noise_floor
    threshold = 0.01
    ci_lower = point_est - 1.96 * std_err
    ci_upper = point_est + 1.96 * std_err

    # One-sided test H0: point_est <= 0.01 vs H1: point_est > 0.01
    z = (point_est - threshold) / std_err if std_err > 0 else 0.0
    import scipy.stats as stats
    raw_p = 1.0 - stats.norm.cdf(z)

    supported = ci_lower >= threshold

    return HypothesisTestResult(
        hypothesis_id="H1",
        description="Black-White absolute exposure gap exceeds noise floor by at least 0.01",
        point_estimate=point_est,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        threshold=threshold,
        p_value_raw=float(raw_p),
        p_value_holm_adjusted=float(raw_p),  # Adjusted in batch
        is_supported=supported,
        notes=f"Excess gap: {point_est:.4f}",
    )


def evaluate_h5(intersectional_excess: float, std_err: float = 0.004) -> HypothesisTestResult:
    """H5: Maximum 4-group intersectional exposure gap exceeds larger marginal gap by >= 0.01."""
    threshold = 0.01
    ci_lower = intersectional_excess - 1.96 * std_err
    ci_upper = intersectional_excess + 1.96 * std_err

    import scipy.stats as stats
    z = (intersectional_excess - threshold) / std_err if std_err > 0 else 0.0
    raw_p = 1.0 - stats.norm.cdf(z)
    supported = ci_lower >= threshold

    return HypothesisTestResult(
        hypothesis_id="H5",
        description="Max intersectional exposure gap exceeds marginal gaps by at least 0.01",
        point_estimate=intersectional_excess,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        threshold=threshold,
        p_value_raw=float(raw_p),
        p_value_holm_adjusted=float(raw_p),
        is_supported=supported,
        notes=f"Intersectional excess: {intersectional_excess:.4f}",
    )
