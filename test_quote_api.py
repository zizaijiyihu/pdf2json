#!/usr/bin/env python3
"""
通过 Flask API 测试语录操作,检查semaphore泄漏
"""

import requests
import time

API_BASE = "http://localhost:5000/api"

def test_via_api():
    print("通过 Flask API 测试语录操作...")
    
    # 1. 创建语录
    print("\n1. 创建语录...")
    response = requests.post(f"{API_BASE}/quotes", json={
        "content": "API测试语录",
        "is_fixed": 0
    })
    result = response.json()
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {result}")
    
    if result.get('success'):
        quote_id = result['id']
        print(f"   创建成功: ID={quote_id}")
        
        # 2. 获取列表
        print("\n2. 获取语录列表...")
        response = requests.get(f"{API_BASE}/quotes?page=1&page_size=10")
        quotes = response.json()
        print(f"   共有 {quotes['total']} 条语录")
        
        # 3. 删除语录
        print(f"\n3. 删除语录 ID={quote_id}...")
        response = requests.delete(f"{API_BASE}/quotes/{quote_id}")
        result = response.json()
        print(f"   删除成功: {result['message']}")
    
    print("\n✅ API测试完成,请检查服务端日志是否有semaphore泄漏警告")

if __name__ == "__main__":
    try:
        test_via_api()
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到 API 服务,请确保服务正在运行 (./start.sh)")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
