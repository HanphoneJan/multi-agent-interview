#!/usr/bin/env python3
"""测试推荐 API"""

import asyncio
import httpx
import sys

BASE_URL = "http://localhost:8000"


async def test_health():
    """测试健康检查"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Health: {response.status_code} - {response.json()}")
        return response.status_code == 200


async def test_ready():
    """测试就绪检查"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/ready")
        print(f"Ready: {response.status_code} - {response.json()}")
        return response.status_code == 200


async def test_personalized_recommendation():
    """测试个性化推荐"""
    async with httpx.AsyncClient() as client:
        payload = {
            "user_id": "test_user_001",
            "query": "Python 编程",
            "top_k": 5,
            "diversity": True
        }

        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/recommendations/personalized",
                json=payload,
                timeout=30.0
            )
            print(f"\nPersonalized Recommendation:")
            print(f"  Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"  User: {data['user_id']}")
                print(f"  Total: {data['total']}")
                print("  Items:")
                for item in data['items']:
                    print(f"    - {item['resource_id']}: {item['score']:.4f}")
                return True
            else:
                print(f"  Error: {response.text}")
                return False
        except Exception as e:
            print(f"  Error: {e}")
            return False


async def test_hot_resources():
    """测试热门资源"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/recommendations/hot",
                params={"top_k": 5}
            )
            print(f"\nHot Resources:")
            print(f"  Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"  Type: {data['resource_type']}")
                print("  Items:")
                for item in data['items'][:5]:
                    print(f"    - {item['resource_id']}: {item['score']:.4f}")
                return True
            else:
                print(f"  Error: {response.text}")
                return False
        except Exception as e:
            print(f"  Error: {e}")
            return False


async def test_event_report():
    """测试事件上报"""
    async with httpx.AsyncClient() as client:
        payload = {
            "user_id": "test_user_001",
            "resource_id": "res_001",
            "event_type": "view",
            "session_id": "session_123"
        }

        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/recommendations/events",
                json=payload
            )
            print(f"\nEvent Report:")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"  Error: {e}")
            return False


async def main():
    print("=" * 60)
    print("推荐 API 测试")
    print("=" * 60)

    results = []

    # 基础检查
    print("\n1. 基础检查...")
    results.append(await test_health())
    results.append(await test_ready())

    # API 测试
    print("\n2. API 测试...")
    results.append(await test_hot_resources())
    results.append(await test_event_report())
    results.append(await test_personalized_recommendation())

    # 总结
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"结果: {passed}/{total} 个测试通过")

    if passed == total:
        print("[OK] 推荐 API 测试通过!")
    else:
        print("[WARN] 部分测试失败")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
