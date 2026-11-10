"""Base retrieval and ranking model interface."""

from abc import ABC, abstractmethod
from typing import List


class BaseRanker(ABC):
    """Abstract base class for all scoring models."""

    @abstractmethod
    def score_candidates(self, query_text: str, candidate_texts: List[str]) -> List[float]:
        """Calculates raw similarity or relevance scores for a list of candidate texts against a query."""
        pass
