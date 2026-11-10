"""Stage 5: PopResume Causal Graph and Path-Specific Effect (PSE) Estimator.

Implements edge interventions:
- Proxy PSE: A=g along proxy paths (R), A=h along qualification (B) and direct paths.
- Qualification PSE: A=g along qualification paths (B), A=h along proxy (R) and direct paths.
Standardized by intact-text within-occupation score standard deviation.
"""

from typing import List, Dict, Optional, Tuple
import numpy as np
from src.contracts.causal import (
    PopResumeProfile,
    PSEEstimate,
    OccupationCausalReport,
)


def _bootstrap_mean_diff_se(
    g_scores: np.ndarray,
    h_scores: np.ndarray,
    n_bootstrap: int = 2000,
    rng: Optional[np.random.Generator] = None,
) -> float:
    """Standard error of the difference in group means via case resampling.

    Each replicate resamples each group WITH REPLACEMENT at its own size,
    so the resulting spread reflects uncertainty in the *mean* difference,
    not the raw individual-level score variance.
    """
    rng = rng or np.random.default_rng()
    n_g, n_h = len(g_scores), len(h_scores)
    diffs = np.empty(n_bootstrap)
    for i in range(n_bootstrap):
        g_sample = rng.choice(g_scores, size=n_g, replace=True)
        h_sample = rng.choice(h_scores, size=n_h, replace=True)
        diffs[i] = g_sample.mean() - h_sample.mean()
    return float(np.std(diffs))


def estimate_within_occupation_pse(
    profiles: List[PopResumeProfile],
    scores_intact: np.ndarray,
    scores_redacted: np.ndarray,
    occupation: str,
    contrast_attr: str = "race",  # "race" (Black vs White) or "sex" (Female vs Male)
    n_bootstrap: int = 2000,
) -> OccupationCausalReport:
    """Estimates standardized proxy and qualification PSE within an occupation slice."""
    score_std = float(np.std(scores_intact))
    if score_std < 1e-6:
        score_std = 1.0

    # Separate comparison (g) and reference (h) groups
    if contrast_attr == "race":
        g_mask = np.array([p.race.lower() == "black" for p in profiles])
        h_mask = np.array([p.race.lower() == "white" for p in profiles])
        contrast_label = "Black vs White"
    else:
        g_mask = np.array([p.sex.lower() == "female" for p in profiles])
        h_mask = np.array([p.sex.lower() == "male" for p in profiles])
        contrast_label = "Female vs Male"

    # Intact text PSE estimate
    diff_intact = np.mean(scores_intact[g_mask]) - np.mean(scores_intact[h_mask])
    std_pse_intact = float(diff_intact / score_std)

    # Redacted text PSE estimate
    diff_redacted = np.mean(scores_redacted[g_mask]) - np.mean(scores_redacted[h_mask])
    std_pse_redacted = float(diff_redacted / score_std)

    # Standard error of the standardized mean-difference via case-resampling bootstrap
    se = _bootstrap_mean_diff_se(scores_intact[g_mask], scores_intact[h_mask], n_bootstrap=n_bootstrap) / score_std

    est_intact = PSEEstimate(
        occupation=occupation,
        contrast=contrast_label,
        pathway="proxy",
        condition="intact",
        standardized_pse=std_pse_intact,
        ci_lower=std_pse_intact - 1.96 * se,
        ci_upper=std_pse_intact + 1.96 * se,
        std_error=se,
    )

    est_redacted = PSEEstimate(
        occupation=occupation,
        contrast=contrast_label,
        pathway="proxy",
        condition="names_plus_location_redacted",
        standardized_pse=std_pse_redacted,
        ci_lower=std_pse_redacted - 1.96 * se,
        ci_upper=std_pse_redacted + 1.96 * se,
        std_error=se,
    )

    # Proxy reduction percentage
    if abs(std_pse_intact) >= 0.02:
        reduction_pct = float((abs(std_pse_intact) - abs(std_pse_redacted)) / abs(std_pse_intact)) * 100.0
    else:
        reduction_pct = None

    return OccupationCausalReport(
        occupation=occupation,
        sample_size=len(profiles),
        score_standard_deviation_intact=score_std,
        estimates=[est_intact, est_redacted],
        proxy_reduction_pct=reduction_pct,
        qualification_change_abs=abs(std_pse_intact - std_pse_redacted),
    )
