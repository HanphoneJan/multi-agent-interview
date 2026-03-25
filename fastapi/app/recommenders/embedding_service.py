"""Embedding service for text vectorization"""
import logging
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial.distance import cosine
from sentence_transformers import SentenceTransformer

from app.core.constants import (
    EMBEDDING_DEFAULT_MODEL,
    EMBEDDING_CACHE_DIR,
    EMBEDDING_DEFAULT_DIM,
)
from app.utils.log_helper import get_logger

logger = get_logger("recommenders.embedding")


class EmbeddingService:
    """Service for generating text embeddings and computing similarities"""

    DEFAULT_MODEL = EMBEDDING_DEFAULT_MODEL
    MODEL_CACHE_DIR = EMBEDDING_CACHE_DIR

    def __init__(self, model_name: str | None = None):
        """
        Initialize embedding service.

        Args:
            model_name: Name of the sentence-transformers model to use
        """
        self.model_name = model_name or EMBEDDING_DEFAULT_MODEL
        self._model = None
        self._embedding_dim = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the model"""
        if self._model is None:
            logger.info(f"Loading sentence-transformers model: {self.model_name}")
            cache_dir = Path(EMBEDDING_CACHE_DIR)
            cache_dir.mkdir(exist_ok=True)
            self._model = SentenceTransformer(self.model_name, cache_folder=str(cache_dir))
            self._embedding_dim = self._model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded successfully, embedding dimension: {self._embedding_dim}")
        return self._model

    def get_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * self.embedding_dim

        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return [emb.tolist() for emb in embeddings]

    def compute_similarity(
        self,
        emb1: list[float] | np.ndarray,
        emb2: list[float] | np.ndarray
    ) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            emb1: First embedding vector
            emb2: Second embedding vector

        Returns:
            Similarity score between 0 and 1 (1 = identical)
        """
        if isinstance(emb1, list):
            emb1 = np.array(emb1)
        if isinstance(emb2, list):
            emb2 = np.array(emb2)

        # Cosine distance, convert to similarity
        distance = cosine(emb1, emb2)
        similarity = 1 - distance
        return float(similarity)

    def compute_similarities(
        self,
        query_embedding: list[float] | np.ndarray,
        candidate_embeddings: list[list[float]] | np.ndarray
    ) -> list[float]:
        """
        Compute cosine similarities between query and multiple candidates.

        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embedding vectors

        Returns:
            List of similarity scores
        """
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding)
        if isinstance(candidate_embeddings, list):
            candidate_embeddings = np.array(candidate_embeddings)

        # Normalize vectors for efficient dot product similarity
        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
        candidates_norm = candidate_embeddings / (np.linalg.norm(candidate_embeddings, axis=1, keepdims=True) + 1e-8)

        # Dot product of normalized vectors = cosine similarity
        similarities = np.dot(candidates_norm, query_norm)
        return similarities.tolist()

    def get_top_k_similar(
        self,
        query_embedding: list[float],
        candidate_embeddings: list[list[float]],
        candidate_ids: list[Any],
        k: int = 10
    ) -> list[tuple[Any, float]]:
        """
        Get top-k most similar candidates based on embeddings.

        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embedding vectors
            candidate_ids: List of candidate IDs (must match embeddings)
            k: Number of top results to return

        Returns:
            List of (id, similarity) tuples sorted by similarity descending
        """
        if len(candidate_embeddings) == 0:
            return []

        similarities = self.compute_similarities(query_embedding, candidate_embeddings)

        # Sort by similarity descending and get top k
        sorted_indices = np.argsort(similarities)[::-1][:k]
        results = [(candidate_ids[i], similarities[i]) for i in sorted_indices]
        return results

    def build_resource_text(self, resource: dict[str, Any]) -> str:
        """
        Build a combined text representation of a resource for embedding.

        Args:
            resource: Resource dict with name, description, tags, etc.

        Returns:
            Combined text string
        """
        parts = []

        # Name
        if resource.get("name"):
            parts.append(resource["name"])

        # Description
        if resource.get("description"):
            parts.append(resource["description"])

        # Tags
        tags = resource.get("tags", [])
        if tags:
            if isinstance(tags, str):
                parts.append(tags)
            else:
                parts.append(" ".join(tags))

        # Difficulty and type as keywords
        if resource.get("difficulty"):
            parts.append(f"难度:{resource['difficulty']}")
        if resource.get("resource_type"):
            parts.append(f"类型:{resource['resource_type']}")

        return " ".join(parts)

    @property
    def embedding_dim(self) -> int:
        """Get embedding dimension"""
        if self._embedding_dim is None:
            # Load model to get dimension
            _ = self.model
        return self._embedding_dim or EMBEDDING_DEFAULT_DIM


# Global embedding service instance
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Get global embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
