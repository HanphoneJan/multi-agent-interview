"""Milvus 向量数据库客户端"""
from typing import List, Dict, Any, Optional
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

from app.core.config import get_settings

settings = get_settings()


class MilvusClient:
    """Milvus 向量数据库客户端"""
    
    def __init__(self):
        self.host = settings.MILVUS_HOST
        self.port = settings.MILVUS_PORT
        self.collection_name = settings.MILVUS_COLLECTION
        self.collection: Optional[Collection] = None
    
    async def connect(self):
        """连接到 Milvus"""
        connections.connect(
            alias="default",
            host=self.host,
            port=self.port
        )
    
    async def disconnect(self):
        """断开连接"""
        connections.disconnect("default")
    
    async def create_collection(self, dim: int = 384):
        """创建资源向量集合"""
        if utility.has_collection(self.collection_name):
            return
        
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="resource_id", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
            FieldSchema(name="resource_type", dtype=DataType.VARCHAR, max_length=32),
            FieldSchema(name="difficulty", dtype=DataType.VARCHAR, max_length=16),
            FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="created_at", dtype=DataType.INT64),
        ]
        
        schema = CollectionSchema(fields, description="Learning resources vectors")
        collection = Collection(name=self.collection_name, schema=schema)
        
        # 创建 HNSW 索引
        index_params = {
            "metric_type": "COSINE",
            "index_type": "HNSW",
            "params": {"M": 16, "efConstruction": 64}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        collection.load()
    
    async def get_collection(self) -> Collection:
        """获取集合实例"""
        if self.collection is None:
            self.collection = Collection(self.collection_name)
            self.collection.load()
        return self.collection
    
    async def insert_vectors(self, entities: List[Dict[str, Any]]) -> List[int]:
        """插入向量"""
        collection = await self.get_collection()

        # 转换为 Milvus 格式: 按字段组织数据
        # 注意: Milvus 要求每个字段一个列表，而不是每个实体一个列表
        data = [
            [e.get("resource_id") for e in entities],
            [e.get("embedding") for e in entities],
            [e.get("resource_type") for e in entities],
            [e.get("difficulty") for e in entities],
            [e.get("tags", "") for e in entities],
            [e.get("created_at", 0) for e in entities]
        ]

        ids = collection.insert(data)

        collection.flush()
        return ids.primary_keys
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 100,
        filters: str = None
    ) -> List[Dict[str, Any]]:
        """向量相似度搜索"""
        collection = await self.get_collection()
        
        search_params = {"metric_type": "COSINE", "params": {"ef": 64}}
        
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=filters,
            output_fields=["resource_id", "resource_type", "difficulty", "tags"]
        )
        
        # 格式化结果
        hits = []
        for result in results[0]:
            hits.append({
                "resource_id": result.entity.get("resource_id"),
                "resource_type": result.entity.get("resource_type"),
                "difficulty": result.entity.get("difficulty"),
                "tags": result.entity.get("tags"),
                "score": result.score
            })
        
        return hits
    
    async def delete_by_resource_id(self, resource_id: str):
        """删除指定资源的向量"""
        collection = await self.get_collection()
        collection.delete(f'resource_id == "{resource_id}"')
