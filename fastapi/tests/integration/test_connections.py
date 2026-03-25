#!/usr/bin/env python3
"""测试本地 Python 连接到 Docker 数据服务"""

import asyncio
import sys

async def test_redis():
    """测试 Redis 连接"""
    import redis.asyncio as redis
    try:
        r = redis.from_url('redis://localhost:16379/0')
        await r.ping()
        print("[OK] Redis: 连接成功")
        await r.aclose()
        return True
    except Exception as e:
        print(f"[FAIL] Redis: 连接失败 - {e}")
        return False

async def test_postgres():
    """测试 PostgreSQL 连接"""
    try:
        import asyncpg
        conn = await asyncpg.connect(
            'postgresql://rec:rec123@localhost:15432/recommendation'
        )
        version = await conn.fetchval('SELECT version()')
        print(f"[OK] PostgreSQL: 连接成功")
        print(f"     版本: {version[:50]}...")
        await conn.close()
        return True
    except Exception as e:
        print(f"[FAIL] PostgreSQL: 连接失败 - {e}")
        return False

def test_milvus():
    """测试 Milvus 连接"""
    try:
        from pymilvus import connections, utility
        connections.connect(host='localhost', port='29530')
        collections = utility.list_collections()
        print(f"[OK] Milvus: 连接成功")
        print(f"     Collections: {collections if collections else '(none) '}")
        return True
    except Exception as e:
        print(f"[FAIL] Milvus: 连接失败 - {e}")
        return False

async def main():
    print("=" * 50)
    print("测试本地 Python 连接到 Docker 数据服务")
    print("=" * 50)

    results = []

    # Redis
    print("\n1. 测试 Redis 连接...")
    results.append(await test_redis())

    # PostgreSQL
    print("\n2. 测试 PostgreSQL 连接...")
    results.append(await test_postgres())

    # Milvus (同步 API)
    print("\n3. 测试 Milvus 连接...")
    results.append(test_milvus())

    # 总结
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"结果: {passed}/{total} 个服务连接成功")
    if passed == total:
        print("OK 本地开发环境已就绪!")
    else:
        print("WARN 部分服务连接失败，请检查配置")
    print("=" * 50)

    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
