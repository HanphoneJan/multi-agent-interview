"""Tests for EmbeddingService"""
import pytest
from unittest.mock import Mock, patch
import numpy as np
from app.recommenders.embedding_service import EmbeddingService


class TestEmbeddingService:
    """Test cases for EmbeddingService"""

    @pytest.fixture
    def mock_sentence_transformer(self):
        """Mock sentence-transformers model"""
        mock_model = Mock()

        def _encode(texts, **kwargs):
            n = len(texts) if isinstance(texts, list) else 1
            return np.random.rand(n, 384).astype(np.float32) if n > 1 else np.random.rand(384).astype(np.float32)

        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_model.encode.side_effect = _encode
        return mock_model

    @pytest.fixture
    def embedding_service(self, mock_sentence_transformer):
        """Create embedding service instance with mocked model - patch must stay active during test"""
        with patch('app.recommenders.embedding_service.SentenceTransformer', return_value=mock_sentence_transformer):
            service = EmbeddingService()
            yield service
            # Patch stays active for entire test when used as fixture

    def test_get_embedding(self, embedding_service):
        """Test getting embedding for a single text"""
        text = "这是一个测试文本"
        embedding = embedding_service.get_embedding(text)

        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)
        assert len(embedding) == embedding_service.embedding_dim

    def test_get_embedding_empty_text(self, embedding_service):
        """Test getting embedding for empty text"""
        embedding = embedding_service.get_embedding("")
        assert embedding == [0.0] * embedding_service.embedding_dim

        embedding = embedding_service.get_embedding("   ")
        assert embedding == [0.0] * embedding_service.embedding_dim

    def test_get_embeddings_batch(self, embedding_service):
        """Test getting embeddings for multiple texts"""
        texts = ["文本1", "文本2", "文本3"]
        embeddings = embedding_service.get_embeddings_batch(texts)

        assert len(embeddings) == len(texts)
        assert all(len(emb) == embedding_service.embedding_dim for emb in embeddings)

    def test_get_embeddings_batch_empty(self, embedding_service):
        """Test getting embeddings for empty list"""
        embeddings = embedding_service.get_embeddings_batch([])
        assert embeddings == []

    def test_compute_similarity(self, embedding_service):
        """Test computing similarity between two embeddings"""
        emb1 = [0.5, 0.5, 0.5, 0.5]
        emb2 = [0.6, 0.6, 0.6, 0.6]
        emb3 = [0.1, 0.9, 0.1, 0.9]

        sim12 = embedding_service.compute_similarity(emb1, emb2)
        sim13 = embedding_service.compute_similarity(emb1, emb3)

        assert 0 <= sim12 <= 1
        assert 0 <= sim13 <= 1
        # emb1 and emb2 should be more similar (both uniform)
        assert sim12 > sim13

        # Same vector should have similarity 1
        sim_self = embedding_service.compute_similarity(emb1, emb1)
        assert abs(sim_self - 1.0) < 0.01

    def test_compute_similarities(self, embedding_service):
        """Test computing similarities for multiple candidates"""
        query_emb = [1.0, 0.0, 0.0]
        candidate_embs = [
            [1.0, 0.0, 0.0],  # Identical
            [0.9, 0.1, 0.0],  # Similar
            [0.0, 1.0, 0.0],  # Different
            [0.0, 0.0, 1.0],  # Orthogonal
        ]

        similarities = embedding_service.compute_similarities(query_emb, candidate_embs)

        assert len(similarities) == 4
        assert all(0 <= s <= 1 for s in similarities)
        # First should be most similar
        assert similarities[0] == max(similarities)

    def test_get_top_k_similar(self, embedding_service):
        """Test getting top-k similar candidates"""
        query_emb = [1.0, 0.0, 0.0]
        candidate_embs = [
            [0.9, 0.1, 0.0],
            [0.8, 0.2, 0.0],
            [0.1, 0.9, 0.0],
            [0.0, 1.0, 0.0],
            [0.7, 0.3, 0.0],
        ]
        candidate_ids = [1, 2, 3, 4, 5]

        top3 = embedding_service.get_top_k_similar(query_emb, candidate_embs, candidate_ids, k=3)

        assert len(top3) == 3
        assert all(isinstance(item[0], int) for item in top3)
        assert all(isinstance(item[1], float) for item in top3)

        # Results should be sorted by similarity descending
        for i in range(len(top3) - 1):
            assert top3[i][1] >= top3[i + 1][1]

    def test_build_resource_text(self, embedding_service):
        """Test building resource text for embedding"""
        resource = {
            "name": "Python教程",
            "description": "从零开始学习Python编程",
            "tags": ["Python", "编程", "入门"],
            "difficulty": "easy",
            "resource_type": "course",
        }

        text = embedding_service.build_resource_text(resource)

        assert "Python教程" in text
        assert "从零开始学习Python编程" in text
        assert "Python" in text
        assert "编程" in text
        assert "入门" in text
        assert "难度:easy" in text
        assert "类型:course" in text

    def test_embedding_dim(self, embedding_service):
        """Test embedding dimension property"""
        dim = embedding_service.embedding_dim
        assert isinstance(dim, int)
        assert dim > 0

    def test_get_embedding_service_singleton(self):
        """Test that get_embedding_service returns singleton instance"""
        with patch('app.recommenders.embedding_service.SentenceTransformer'):
            from app.recommenders.embedding_service import get_embedding_service

            svc1 = get_embedding_service()
            svc2 = get_embedding_service()

            assert svc1 is svc2
