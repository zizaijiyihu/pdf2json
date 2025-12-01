"""
测试提醒（Reminders）API接口

测试增删改查功能
"""

import requests
import json

BASE_URL = "http://localhost:5000/api/reminders"


def print_response(title, response):
    """打印响应信息"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"状态码: {response.status_code}")
    try:
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except:
        print(f"响应: {response.text}")


def test_reminders():
    """测试提醒API的完整流程"""
    
    # 1. 创建第一个提醒
    print("\n\n【测试1: 创建提醒 - 今天谁比较辛苦】")
    response = requests.post(BASE_URL, json={
        "content": "今天谁比较辛苦"
    })
    print_response("创建提醒1", response)
    assert response.status_code == 201
    assert response.json()['success'] == True
    reminder_id_1 = response.json()['reminder_id']
    print(f"✓ 提醒1创建成功，ID: {reminder_id_1}")
    
    # 2. 创建第二个提醒
    print("\n\n【测试2: 创建提醒 - 最近有什么AI新闻】")
    response = requests.post(BASE_URL, json={
        "content": "最近有什么AI新闻"
    })
    print_response("创建提醒2", response)
    assert response.status_code == 201
    assert response.json()['success'] == True
    reminder_id_2 = response.json()['reminder_id']
    print(f"✓ 提醒2创建成功，ID: {reminder_id_2}")
    
    # 3. 创建第三个提醒
    print("\n\n【测试3: 创建提醒 - 今天天气怎么样】")
    response = requests.post(BASE_URL, json={
        "content": "今天天气怎么样"
    })
    print_response("创建提醒3", response)
    assert response.status_code == 201
    reminder_id_3 = response.json()['reminder_id']
    print(f"✓ 提醒3创建成功，ID: {reminder_id_3}")
    
    # 4. 获取所有提醒
    print("\n\n【测试4: 获取所有提醒】")
    response = requests.get(BASE_URL)
    print_response("获取所有提醒", response)
    assert response.status_code == 200
    assert response.json()['success'] == True
    reminders = response.json()['data']
    assert len(reminders) >= 3
    print(f"✓ 成功获取 {len(reminders)} 条提醒")
    
    # 5. 获取单个提醒详情
    print(f"\n\n【测试5: 获取提醒详情 - ID {reminder_id_1}】")
    response = requests.get(f"{BASE_URL}/{reminder_id_1}")
    print_response(f"获取提醒{reminder_id_1}详情", response)
    assert response.status_code == 200
    assert response.json()['success'] == True
    reminder = response.json()['data']
    assert reminder['id'] == reminder_id_1
    assert reminder['content'] == "今天谁比较辛苦"
    print(f"✓ 成功获取提醒详情")
    
    # 6. 更新提醒
    print(f"\n\n【测试6: 更新提醒 - ID {reminder_id_2}】")
    response = requests.put(f"{BASE_URL}/{reminder_id_2}", json={
        "content": "最近有什么科技新闻（已更新）"
    })
    print_response(f"更新提醒{reminder_id_2}", response)
    assert response.status_code == 200
    assert response.json()['success'] == True
    print(f"✓ 提醒更新成功")
    
    # 7. 验证更新结果
    print(f"\n\n【测试7: 验证更新结果 - ID {reminder_id_2}】")
    response = requests.get(f"{BASE_URL}/{reminder_id_2}")
    print_response(f"验证更新后的提醒{reminder_id_2}", response)
    assert response.status_code == 200
    reminder = response.json()['data']
    assert reminder['content'] == "最近有什么科技新闻（已更新）"
    print(f"✓ 更新验证成功")
    
    # 8. 删除提醒
    print(f"\n\n【测试8: 删除提醒 - ID {reminder_id_3}】")
    response = requests.delete(f"{BASE_URL}/{reminder_id_3}")
    print_response(f"删除提醒{reminder_id_3}", response)
    assert response.status_code == 200
    assert response.json()['success'] == True
    print(f"✓ 提醒删除成功")
    
    # 9. 验证删除结果
    print(f"\n\n【测试9: 验证删除结果 - ID {reminder_id_3}】")
    response = requests.get(f"{BASE_URL}/{reminder_id_3}")
    print_response(f"尝试获取已删除的提醒{reminder_id_3}", response)
    assert response.status_code == 404
    assert response.json()['success'] == False
    print(f"✓ 删除验证成功（提醒已不存在）")
    
    # 10. 测试错误情况 - 空内容
    print("\n\n【测试10: 错误测试 - 创建空内容提醒】")
    response = requests.post(BASE_URL, json={
        "content": ""
    })
    print_response("创建空内容提醒", response)
    assert response.status_code == 400
    assert response.json()['success'] == False
    print(f"✓ 空内容验证成功（正确拒绝）")
    
    # 11. 测试错误情况 - 缺少参数
    print("\n\n【测试11: 错误测试 - 缺少content参数】")
    response = requests.post(BASE_URL, json={})
    print_response("缺少content参数", response)
    assert response.status_code == 400
    assert response.json()['success'] == False
    print(f"✓ 参数验证成功（正确拒绝）")
    
    # 12. 最终检查 - 获取所有提醒
    print("\n\n【测试12: 最终检查 - 获取所有提醒】")
    response = requests.get(BASE_URL)
    print_response("最终提醒列表", response)
    assert response.status_code == 200
    reminders = response.json()['data']
    print(f"✓ 当前共有 {len(reminders)} 条提醒")
    
    print("\n\n" + "="*60)
    print("🎉 所有测试通过！")
    print("="*60)


if __name__ == "__main__":
    try:
        test_reminders()
    except AssertionError as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    except requests.exceptions.ConnectionError:
        print("\n\n❌ 连接失败: 请确保API服务器正在运行 (python app_api/api.py)")
    except Exception as e:
        print(f"\n\n❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
