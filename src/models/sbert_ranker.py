"""Sentence-BERT Semantic Retrieval Model (Stage 3).

Constraints from proposal:
- Core model: sentence-transformers/all-mpnet-base-v2
- Deterministic section-aware chunks bounded by model input limit
- Normalized chunk embeddings averaged and renormalized
- Cosine similarity scoring between job and candidate embeddings
"""

from typing import List, Optional
import numpy as np
from src.models.base import BaseRanker


class SBERTRanker(BaseRanker):
    """Dense semantic ranker using Sentence-Transformers with chunk-averaging."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-mpnet-base-v2",
        chunk_size_words: int = 150,
        chunk_overlap_words: int = 30,
        device: Optional[str] = None,
    ):
        self.model_name = model_name
        self.chunk_size = chunk_size_words
        self.chunk_overlap = chunk_overlap_words
        self._model = None
        self.device = device

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name, device=self.device)

    def _split_into_chunks(self, text: str) -> List[str]:
        words = text.split()
        if len(words) <= self.chunk_size:
            return [text]

        chunks = []
        step = self.chunk_size - self.chunk_overlap
        for i in range(0, len(words), step):
            chunk = " ".join(words[i : i + self.chunk_size])
            chunks.append(chunk)
            if i + self.chunk_size >= len(words):
                break
        return chunks

    def encode_text(self, text: str) -> np.ndarray:
        """Encodes text with section-aware chunk averaging and L2 renormalization."""
        self._load_model()
        chunks = self._split_into_chunks(text)
        chunk_embeddings = self._model.encode(chunks, normalize_embeddings=True)

        if len(chunks) == 1:
            mean_embedding = chunk_embeddings[0]
        else:
            mean_embedding = np.mean(chunk_embeddings, axis=0)

        # Renormalize to unit sphere
        norm = np.linalg.norm(mean_embedding)
        if norm > 1e-12:
            mean_embedding = mean_embedding / norm
        return mean_embedding

    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """Encodes multiple short texts in a single batched model call (no chunk-averaging)."""
        self._load_model()
        return np.array(self._model.encode(texts, normalize_embeddings=True))

    def score_candidates(self, query_text: str, candidate_texts: List[str]) -> List[float]:
        if not candidate_texts:
            return []

        query_emb = self.encode_text(query_text)
        cand_embs = np.array([self.encode_text(c) for c in candidate_texts])

        # Cosine similarity is dot product of L2-normalized embeddings
        scores = np.dot(cand_embs, query_emb)
        return [float(s) for s in scores]
