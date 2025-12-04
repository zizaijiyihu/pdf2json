#!/usr/bin/env python3
"""
提醒功能测试脚本 - 公开/私有功能测试

测试场景:
1. 创建公开提醒（最多10个）
2. 创建私有提醒（每个用户最多5个）
3. 查询提醒（公开 + 用户私有）
4. 切换公开/私有状态
5. 验证数量限制
"""

import requests
import json
from typing import List, Dict

BASE_URL = "http://localhost:8080/api/reminders"

class ReminderTester:
    def __init__(self):
        self.created_reminder_ids: List[int] = []
        
    def cleanup(self):
        """清理测试数据"""
        print("\n🧹 清理测试数据...")
        for reminder_id in self.created_reminder_ids:
            try:
                response = requests.delete(f"{BASE_URL}/{reminder_id}")
                if response.status_code == 200:
                    print(f"  ✓ 删除提醒 {reminder_id}")
            except Exception as e:
                print(f"  ✗ 删除提醒 {reminder_id} 失败: {e}")
        self.created_reminder_ids.clear()
    
    def create_reminder(self, content: str, is_public: bool = True, user_id: str = None) -> Dict:
        """创建提醒"""
        data = {"content": content, "is_public": is_public}
        if user_id:
            data["user_id"] = user_id
            
        response = requests.post(BASE_URL, json=data)
        result = response.json()
        
        if response.status_code == 201 and result.get("success"):
            self.created_reminder_ids.append(result["reminder_id"])
        
        return {
            "status_code": response.status_code,
            "result": result
        }
    
    def get_reminders(self, user_id: str = None) -> Dict:
        """获取提醒列表"""
        params = {"user_id": user_id} if user_id else {}
        response = requests.get(BASE_URL, params=params)
        return {
            "status_code": response.status_code,
            "result": response.json()
        }
    
    def update_reminder(self, reminder_id: int, content: str = None, 
                       is_public: bool = None, user_id: str = None) -> Dict:
        """更新提醒"""
        data = {}
        if content is not None:
            data["content"] = content
        if is_public is not None:
            data["is_public"] = is_public
        if user_id is not None:
            data["user_id"] = user_id
            
        response = requests.put(f"{BASE_URL}/{reminder_id}", json=data)
        return {
            "status_code": response.status_code,
            "result": response.json()
        }
    
    def test_create_public_reminders(self):
        """测试1: 创建公开提醒（最多10个）"""
        print("\n" + "="*60)
        print("测试1: 创建公开提醒（最多10个）")
        print("="*60)
        
        # 创建10个公开提醒
        for i in range(10):
            result = self.create_reminder(f"公开提醒 {i+1}", is_public=True)
            if result["status_code"] == 201:
                print(f"✓ 创建公开提醒 {i+1} 成功 (ID: {result['result']['reminder_id']})")
            else:
                print(f"✗ 创建公开提醒 {i+1} 失败: {result['result']}")
        
        # 尝试创建第11个，应该失败
        print("\n尝试创建第11个公开提醒（应该失败）...")
        result = self.create_reminder("公开提醒 11", is_public=True)
        if result["status_code"] == 400:
            print(f"✓ 正确拒绝: {result['result']['error']}")
        else:
            print(f"✗ 应该失败但成功了: {result}")
    
    def test_create_private_reminders(self):
        """测试2: 创建私有提醒（每个用户最多5个）"""
        print("\n" + "="*60)
        print("测试2: 创建私有提醒（每个用户最多5个）")
        print("="*60)
        
        user1 = "test_user_1"
        user2 = "test_user_2"
        
        # 用户1创建5个私有提醒
        print(f"\n用户 {user1} 创建私有提醒:")
        for i in range(5):
            result = self.create_reminder(f"用户1私有提醒 {i+1}", is_public=False, user_id=user1)
            if result["status_code"] == 201:
                print(f"✓ 创建私有提醒 {i+1} 成功 (ID: {result['result']['reminder_id']})")
            else:
                print(f"✗ 创建私有提醒 {i+1} 失败: {result['result']}")
        
        # 用户1尝试创建第6个，应该失败
        print(f"\n用户 {user1} 尝试创建第6个私有提醒（应该失败）...")
        result = self.create_reminder("用户1私有提醒 6", is_public=False, user_id=user1)
        if result["status_code"] == 400:
            print(f"✓ 正确拒绝: {result['result']['error']}")
        else:
            print(f"✗ 应该失败但成功了: {result}")
        
        # 用户2创建3个私有提醒（验证不同用户独立计数）
        print(f"\n用户 {user2} 创建私有提醒:")
        for i in range(3):
            result = self.create_reminder(f"用户2私有提醒 {i+1}", is_public=False, user_id=user2)
            if result["status_code"] == 201:
                print(f"✓ 创建私有提醒 {i+1} 成功 (ID: {result['result']['reminder_id']})")
            else:
                print(f"✗ 创建私有提醒 {i+1} 失败: {result['result']}")
    
    def test_query_reminders(self):
        """测试3: 查询提醒（公开 + 用户私有）"""
        print("\n" + "="*60)
        print("测试3: 查询提醒（公开 + 用户私有）")
        print("="*60)
        
        user1 = "test_user_1"
        user2 = "test_user_2"
        
        # 不带user_id查询（只返回公开提醒）
        print("\n不带user_id查询（只返回公开提醒）:")
        result = self.get_reminders()
        if result["status_code"] == 200:
            reminders = result["result"]["data"]
            public_count = sum(1 for r in reminders if r.get("is_public") == 1)
            print(f"✓ 查询成功，共 {len(reminders)} 条提醒，其中公开 {public_count} 条")
            print(f"  提醒列表: {[r['content'][:20] + '...' if len(r['content']) > 20 else r['content'] for r in reminders[:5]]}")
        else:
            print(f"✗ 查询失败: {result}")
        
        # 用户1查询（公开 + 用户1私有）
        print(f"\n用户 {user1} 查询（公开 + 用户1私有）:")
        result = self.get_reminders(user_id=user1)
        if result["status_code"] == 200:
            reminders = result["result"]["data"]
            public_count = sum(1 for r in reminders if r.get("is_public") == 1)
            user1_private_count = sum(1 for r in reminders if r.get("is_public") == 0 and r.get("user_id") == user1)
            print(f"✓ 查询成功，共 {len(reminders)} 条提醒")
            print(f"  - 公开: {public_count} 条")
            print(f"  - 用户1私有: {user1_private_count} 条")
        else:
            print(f"✗ 查询失败: {result}")
        
        # 用户2查询（公开 + 用户2私有）
        print(f"\n用户 {user2} 查询（公开 + 用户2私有）:")
        result = self.get_reminders(user_id=user2)
        if result["status_code"] == 200:
            reminders = result["result"]["data"]
            public_count = sum(1 for r in reminders if r.get("is_public") == 1)
            user2_private_count = sum(1 for r in reminders if r.get("is_public") == 0 and r.get("user_id") == user2)
            print(f"✓ 查询成功，共 {len(reminders)} 条提醒")
            print(f"  - 公开: {public_count} 条")
            print(f"  - 用户2私有: {user2_private_count} 条")
        else:
            print(f"✗ 查询失败: {result}")
    
    def test_toggle_visibility(self):
        """测试4: 切换公开/私有状态"""
        print("\n" + "="*60)
        print("测试4: 切换公开/私有状态")
        print("="*60)
        
        user1 = "test_user_1"
        
        # 创建一个公开提醒
        print("\n创建一个公开提醒...")
        result = self.create_reminder("测试切换提醒", is_public=True)
        if result["status_code"] != 201:
            print(f"✗ 创建失败: {result}")
            return
        
        reminder_id = result["result"]["reminder_id"]
        print(f"✓ 创建成功 (ID: {reminder_id})")
        
        # 切换为私有
        print(f"\n将提醒 {reminder_id} 切换为私有...")
        result = self.update_reminder(reminder_id, is_public=False, user_id=user1)
        if result["status_code"] == 200:
            print(f"✓ 切换成功: {result['result']['message']}")
        else:
            print(f"✗ 切换失败: {result}")
        
        # 验证切换结果
        print(f"\n验证提醒 {reminder_id} 的状态...")
        result = self.get_reminders(user_id=user1)
        if result["status_code"] == 200:
            reminders = result["result"]["data"]
            target = next((r for r in reminders if r["id"] == reminder_id), None)
            if target:
                if target["is_public"] == 0 and target["user_id"] == user1:
                    print(f"✓ 验证成功: 提醒已切换为私有，user_id={target['user_id']}")
                else:
                    print(f"✗ 验证失败: is_public={target['is_public']}, user_id={target['user_id']}")
            else:
                print(f"✗ 未找到提醒 {reminder_id}")
        
        # 切换回公开
        print(f"\n将提醒 {reminder_id} 切换回公开...")
        result = self.update_reminder(reminder_id, is_public=True)
        if result["status_code"] == 200:
            print(f"✓ 切换成功: {result['result']['message']}")
        else:
            print(f"✗ 切换失败: {result}")
    
    def run_all_tests(self):
        """运行所有测试"""
        try:
            self.test_create_public_reminders()
            self.test_create_private_reminders()
            self.test_query_reminders()
            self.test_toggle_visibility()
            
            print("\n" + "="*60)
            print("✅ 所有测试完成")
            print("="*60)
        finally:
            self.cleanup()


if __name__ == "__main__":
    print("🚀 开始测试提醒功能（公开/私有）")
    print("="*60)
    
    tester = ReminderTester()
    tester.run_all_tests()
