"""Stage 4: Counterfactual Data Augmentation (CDA) & Invariance Loss (Equation 2).

Loss function:
    L = L_rank + alpha * (1 / |B|) sum_{(q, i) in B} (1 / |V_train|) sum_{v in V_train} (s_theta(q, r_i^{(v)}) - s_bar_{qi})^2
where L_rank is pairwise logistic ranking loss for judged pairs with different grades.
"""

from typing import List, Tuple
import torch
import torch.nn as nn
from src.contracts.mitigation import CDAMinibatchItem


class PairwiseLogisticLoss(nn.Module):
    """Pairwise logistic loss for ranking pairs with different grades within the same job."""

    def __init__(self):
        super().__init__()

    def forward(self, higher_grade_scores: torch.Tensor, lower_grade_scores: torch.Tensor) -> torch.Tensor:
        diff = higher_grade_scores - lower_grade_scores
        return torch.mean(torch.log1p(torch.exp(-diff)))


class InvarianceLoss(nn.Module):
    """CDA invariance penalty forcing name variants of the same resume to have identical scores."""

    def __init__(self):
        super().__init__()

    def forward(self, variant_scores: torch.Tensor) -> torch.Tensor:
        """variant_scores shape: [B, num_variants]. Computes mean squared deviation from item mean."""
        mean_scores = torch.mean(variant_scores, dim=1, keepdim=True)
        deviations = (variant_scores - mean_scores) ** 2
        return torch.mean(deviations)


def compute_cda_loss(
    ranked_pairs: List[Tuple[torch.Tensor, torch.Tensor]],
    batch_variant_scores: torch.Tensor,
    alpha: float = 1.0,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Computes total CDA loss: L = L_rank + alpha * L_invariance."""
    logistic = PairwiseLogisticLoss()
    invariance = InvarianceLoss()

    if ranked_pairs:
        l_rank = torch.tensor(0.0, device=batch_variant_scores.device)
        for s_high, s_low in ranked_pairs:
            l_rank = l_rank + logistic(s_high, s_low)
        l_rank = l_rank / len(ranked_pairs)
    else:
        l_rank = torch.tensor(0.0, device=batch_variant_scores.device)

    l_inv = invariance(batch_variant_scores)
    total_loss = l_rank + alpha * l_inv

    return total_loss, l_rank, l_inv
