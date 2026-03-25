"""Embedding 服务"""
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings

settings = get_settings()

# 全局模型实例（懒加载）
_model = None


def get_model() -> SentenceTransformer:
    """获取 Embedding 模型（懒加载）"""
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


class EmbeddingService:
    """文本 Embedding 服务"""
    
    def __init__(self):
        self.model = get_model()
        self.dim = settings.EMBEDDING_DIM
    
    def encode(self, text: str) -> List[float]:
        """编码单个文本"""
        if not text or not text.strip():
            return [0.0] * self.dim
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """批量编码文本"""
        if not texts:
            return []
        
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()
    
    def build_resource_text(self, resource: Dict[str, Any]) -> str:
        """
        构建资源文本表示
        用于生成 embedding
        """
        parts = []
        
        # 资源名称
        if resource.get("name"):
            parts.append(resource["name"])
        
        # 标签
        tags = resource.get("tags", [])
        if tags:
            if isinstance(tags, list):
                parts.extend(tags)
            else:
                parts.append(tags)
        
        # 难度和类型
        if resource.get("difficulty"):
            parts.append(f"难度:{resource['difficulty']}")
        if resource.get("resource_type"):
            parts.append(f"类型:{resource['resource_type']}")
        
        return " ".join(parts)
    
    def compute_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """计算两个向量的余弦相似度"""
        vec1 = np.array(emb1)
        vec2 = np.array(emb2)
        
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
