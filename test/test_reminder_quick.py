#!/usr/bin/env python3
"""
提醒功能快速测试脚本

快速验证公开/私有提醒的核心功能
"""

import requests
import json

BASE_URL = "http://localhost:8080/api/reminders"

def test_basic_flow():
    """测试基本流程"""
    print("🧪 测试基本流程\n")
    
    created_ids = []
    
    try:
        # 1. 创建3个公开提醒
        print("1️⃣ 创建3个公开提醒...")
        for i in range(3):
            response = requests.post(BASE_URL, json={
                "content": f"公开提醒测试 {i+1}",
                "is_public": True
            })
            if response.status_code == 201:
                reminder_id = response.json()["reminder_id"]
                created_ids.append(reminder_id)
                print(f"   ✓ 创建成功 (ID: {reminder_id})")
            else:
                print(f"   ✗ 创建失败: {response.json()}")
        
        # 2. 创建2个私有提醒（用户test_user）
        print("\n2️⃣ 创建2个私有提醒（用户test_user）...")
        for i in range(2):
            response = requests.post(BASE_URL, json={
                "content": f"私有提醒测试 {i+1}",
                "is_public": False,
                "user_id": "test_user"
            })
            if response.status_code == 201:
                reminder_id = response.json()["reminder_id"]
                created_ids.append(reminder_id)
                print(f"   ✓ 创建成功 (ID: {reminder_id})")
            else:
                print(f"   ✗ 创建失败: {response.json()}")
        
        # 3. 查询所有公开提醒
        print("\n3️⃣ 查询所有公开提醒...")
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            reminders = response.json()["data"]
            public_reminders = [r for r in reminders if r.get("is_public") == 1]
            print(f"   ✓ 查询成功，共 {len(public_reminders)} 条公开提醒")
        else:
            print(f"   ✗ 查询失败: {response.json()}")
        
        # 4. 查询test_user的提醒（公开+私有）
        print("\n4️⃣ 查询test_user的提醒（公开+私有）...")
        response = requests.get(BASE_URL, params={"user_id": "test_user"})
        if response.status_code == 200:
            reminders = response.json()["data"]
            public_count = sum(1 for r in reminders if r.get("is_public") == 1)
            private_count = sum(1 for r in reminders if r.get("is_public") == 0 and r.get("user_id") == "test_user")
            print(f"   ✓ 查询成功")
            print(f"     - 公开提醒: {public_count} 条")
            print(f"     - 私有提醒: {private_count} 条")
            print(f"     - 总计: {len(reminders)} 条")
        else:
            print(f"   ✗ 查询失败: {response.json()}")
        
        # 5. 切换第一个公开提醒为私有
        if created_ids:
            first_id = created_ids[0]
            print(f"\n5️⃣ 切换提醒 {first_id} 为私有...")
            response = requests.put(f"{BASE_URL}/{first_id}", json={
                "is_public": False,
                "user_id": "test_user"
            })
            if response.status_code == 200:
                print(f"   ✓ 切换成功: {response.json()['message']}")
            else:
                print(f"   ✗ 切换失败: {response.json()}")
            
            # 验证切换结果
            print(f"\n6️⃣ 验证切换结果...")
            response = requests.get(f"{BASE_URL}/{first_id}")
            if response.status_code == 200:
                reminder = response.json()["data"]
                if reminder["is_public"] == 0 and reminder["user_id"] == "test_user":
                    print(f"   ✓ 验证成功: 提醒已切换为私有")
                else:
                    print(f"   ✗ 验证失败: is_public={reminder['is_public']}, user_id={reminder['user_id']}")
            else:
                print(f"   ✗ 验证失败: {response.json()}")
        
        print("\n✅ 测试完成")
        
    finally:
        # 清理测试数据
        print("\n🧹 清理测试数据...")
        for reminder_id in created_ids:
            response = requests.delete(f"{BASE_URL}/{reminder_id}")
            if response.status_code == 200:
                print(f"   ✓ 删除提醒 {reminder_id}")
            else:
                print(f"   ✗ 删除提醒 {reminder_id} 失败")


def test_limits():
    """测试数量限制"""
    print("\n🧪 测试数量限制\n")
    
    created_ids = []
    
    try:
        # 测试公开提醒限制（10个）
        print("1️⃣ 测试公开提醒限制（最多10个）...")
        for i in range(11):
            response = requests.post(BASE_URL, json={
                "content": f"公开提醒限制测试 {i+1}",
                "is_public": True
            })
            if response.status_code == 201:
                created_ids.append(response.json()["reminder_id"])
                print(f"   ✓ 创建第 {i+1} 个公开提醒成功")
            else:
                if i < 10:
                    print(f"   ✗ 创建第 {i+1} 个公开提醒失败（不应该失败）: {response.json()}")
                else:
                    print(f"   ✓ 创建第 {i+1} 个公开提醒被正确拒绝: {response.json()['error']}")
        
        # 测试私有提醒限制（每用户5个）
        print("\n2️⃣ 测试私有提醒限制（每用户最多5个）...")
        for i in range(6):
            response = requests.post(BASE_URL, json={
                "content": f"私有提醒限制测试 {i+1}",
                "is_public": False,
                "user_id": "limit_test_user"
            })
            if response.status_code == 201:
                created_ids.append(response.json()["reminder_id"])
                print(f"   ✓ 创建第 {i+1} 个私有提醒成功")
            else:
                if i < 5:
                    print(f"   ✗ 创建第 {i+1} 个私有提醒失败（不应该失败）: {response.json()}")
                else:
                    print(f"   ✓ 创建第 {i+1} 个私有提醒被正确拒绝: {response.json()['error']}")
        
        print("\n✅ 限制测试完成")
        
    finally:
        # 清理测试数据
        print("\n🧹 清理测试数据...")
        for reminder_id in created_ids:
            response = requests.delete(f"{BASE_URL}/{reminder_id}")


if __name__ == "__main__":
    print("="*60)
    print("🚀 提醒功能快速测试")
    print("="*60)
    
    # 运行基本流程测试
    test_basic_flow()
    
    # 运行限制测试
    test_limits()
    
    print("\n" + "="*60)
    print("✅ 所有测试完成")
    print("="*60)
