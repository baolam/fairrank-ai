"""BM25 Lexical Retrieval Model (Stage 3).

Constraints from proposal:
- Fixed k1 = 1.2 and b = 0.75
- Documented lowercase tokenizer
- Fixed candidate index per partition
- Corpus statistics do not change between paired worlds
"""

import re
from typing import List
from rank_bm25 import BM25Okapi
from src.models.base import BaseRanker


def simple_lowercase_tokenizer(text: str) -> List[str]:
    """Documented lowercase alphanumeric tokenizer."""
    return re.findall(r"\w+", text.lower())


class BM25Ranker(BaseRanker):
    """Lexical baseline ranking using BM25 with k1=1.2, b=0.75."""

    def __init__(self, k1: float = 1.2, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def score_candidates(self, query_text: str, candidate_texts: List[str]) -> List[float]:
        if not candidate_texts:
            return []

        tokenized_corpus = [simple_lowercase_tokenizer(doc) for doc in candidate_texts]
        bm25 = BM25Okapi(tokenized_corpus, k1=self.k1, b=self.b)

        tokenized_query = simple_lowercase_tokenizer(query_text)
        scores = bm25.get_scores(tokenized_query)
        return [float(s) for s in scores]
