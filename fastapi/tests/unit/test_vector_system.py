#!/usr/bin/env python3
"""测试向量检索系统"""

import asyncio
import sys
import os

# 设置环境变量使用本地开发配置
os.environ["MILVUS_HOST"] = "localhost"
os.environ["MILVUS_PORT"] = "29530"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.embedding import EmbeddingService
from app.core.milvus_client import MilvusClient


async def test_embedding():
    """测试 Embedding 服务"""
    print("\n--- 测试 Embedding 服务 ---")

    try:
        service = EmbeddingService()

        # 测试单文本编码
        text = "Python 编程基础教程"
        embedding = service.encode(text)
        print(f"单文本编码: '{text}'")
        print(f"  维度: {len(embedding)}")
        print(f"  前5个值: {embedding[:5]}")

        # 测试批量编码
        texts = ["机器学习入门", "深度学习框架", "数据结构与算法"]
        embeddings = service.encode_batch(texts)
        print(f"\n批量编码 {len(texts)} 个文本")
        print(f"  每个维度: {len(embeddings[0])}")

        # 测试相似度计算
        emb1 = service.encode("Python 编程")
        emb2 = service.encode("Python 开发")
        emb3 = service.encode("Java 编程")

        sim1 = service.compute_similarity(emb1, emb2)
        sim2 = service.compute_similarity(emb1, emb3)

        print(f"\n相似度测试:")
        print(f"  'Python 编程' vs 'Python 开发': {sim1:.4f}")
        print(f"  'Python 编程' vs 'Java 编程': {sim2:.4f}")

        return True
    except Exception as e:
        print(f"[FAIL] Embedding 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_milvus():
    """测试 Milvus 向量数据库"""
    print("\n--- 测试 Milvus 向量数据库 ---")

    client = MilvusClient()

    try:
        # 连接
        await client.connect()
        print("[OK] 连接成功")

        # 创建集合
        await client.create_collection(dim=384)
        print("[OK] 集合创建/已存在")

        # 插入测试数据
        test_resources = [
            {
                "resource_id": "res_001",
                "embedding": [0.1] * 384,
                "resource_type": "course",
                "difficulty": "easy",
                "tags": "Python,基础",
                "created_at": 1700000000
            },
            {
                "resource_id": "res_002",
                "embedding": [0.2] * 384,
                "resource_type": "course",
                "difficulty": "medium",
                "tags": "Python,进阶",
                "created_at": 1700000001
            },
            {
                "resource_id": "res_003",
                "embedding": [0.3] * 384,
                "resource_type": "question",
                "difficulty": "hard",
                "tags": "算法,DP",
                "created_at": 1700000002
            }
        ]

        ids = await client.insert_vectors(test_resources)
        print(f"[OK] 插入 {len(ids)} 条向量")

        # 搜索测试
        query = [0.15] * 384
        results = await client.search(query, top_k=3)
        print(f"[OK] 搜索返回 {len(results)} 条结果")

        for i, r in enumerate(results[:3]):
            print(f"  {i+1}. {r['resource_id']} (score: {r['score']:.4f})")

        # 带过滤条件的搜索
        results_filtered = await client.search(
            query,
            top_k=3,
            filters='difficulty == "easy"'
        )
        print(f"[OK] 过滤搜索返回 {len(results_filtered)} 条结果")

        return True
    except Exception as e:
        print(f"[FAIL] Milvus 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.disconnect()


async def test_integration():
    """测试 Embedding + Milvus 集成"""
    print("\n--- 测试 Embedding + Milvus 集成 ---")

    client = MilvusClient()

    try:
        await client.connect()
        await client.create_collection(dim=384)

        # 使用真实 embedding
        embed_service = EmbeddingService()

        resources = [
            {"resource_id": "py_basic", "name": "Python 基础教程", "tags": ["Python", "入门"], "resource_type": "course", "difficulty": "easy"},
            {"resource_id": "py_adv", "name": "Python 高级特性", "tags": ["Python", "进阶"], "resource_type": "course", "difficulty": "medium"},
            {"resource_id": "algo_sort", "name": "排序算法详解", "tags": ["算法", "排序"], "resource_type": "question", "difficulty": "medium"},
            {"resource_id": "sys_design", "name": "系统设计基础", "tags": ["系统设计", "架构"], "resource_type": "video", "difficulty": "hard"},
        ]

        # 构建并插入向量
        entities = []
        for r in resources:
            text = embed_service.build_resource_text(r)
            embedding = embed_service.encode(text)
            entities.append({
                "resource_id": r["resource_id"],
                "embedding": embedding,
                "resource_type": r["resource_type"],
                "difficulty": r["difficulty"],
                "tags": ",".join(r["tags"]),
                "created_at": 1700000000
            })
            print(f"  生成向量: {r['resource_id']} <- '{text[:30]}...'")

        ids = await client.insert_vectors(entities)
        print(f"[OK] 插入 {len(ids)} 条真实向量")

        # 搜索相似资源
        query_text = "我想学 Python 编程"
        query_emb = embed_service.encode(query_text)

        results = await client.search(query_emb, top_k=3)
        print(f"\n查询: '{query_text}'")
        print("搜索结果:")
        for i, r in enumerate(results[:3]):
            print(f"  {i+1}. {r['resource_id']} (score: {r['score']:.4f})")

        return True
    except Exception as e:
        print(f"[FAIL] 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.disconnect()


async def main():
    print("=" * 60)
    print("向量检索系统测试")
    print("=" * 60)

    results = []

    # 测试 1: Embedding
    results.append(await test_embedding())

    # 测试 2: Milvus
    results.append(await test_milvus())

    # 测试 3: 集成
    results.append(await test_integration())

    # 总结
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"结果: {passed}/{total} 个测试通过")

    if passed == total:
        print("[OK] 向量检索系统工作正常!")
    else:
        print("[WARN] 部分测试失败")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
