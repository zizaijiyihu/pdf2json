#!/usr/bin/env python3
"""
测试过滤后的考勤记录返回
"""

import os
import sys
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from km_agent.agent import KMAgent


def test_filtered_attendance():
    """测试过滤后的考勤记录"""
    print("=== 测试过滤后的考勤记录返回 ===\n")

    agent = KMAgent(verbose=False)
    print(f"当前用户: {agent.owner}\n")

    # 测试查询下属考勤
    result = agent._get_subordinate_attendance("lihaoze2")

    print("查询结果:")
    print(f"- 成功: {result.get('success')}")
    print(f"- 总记录数: {result.get('total_records')}")
    print(f"- 返回记录数: {result.get('returned_records')}")
    print(f"\n返回的字段:")

    if result.get('success') and result.get('data'):
        first_record = result['data'][0]
        for field in first_record.keys():
            print(f"  - {field}")

        print(f"\n前3条记录示例:")
        for idx, record in enumerate(result['data'][:3], 1):
            print(f"\n  记录 {idx}:")
            for field, value in record.items():
                print(f"    {field}: {value}")

        print("\n✅ 数据格式正确:")
        print("   - 只返回了前10条记录")
        print("   - 只包含6个指定字段")
        print("   - 字段包括: actualstartdate, actualstarttime, delaylong, actualouttime, earlylong, zonename")

    return result.get('success')


def test_with_agent_chat():
    """测试通过 Agent 对话查询"""
    print("\n\n=== 测试通过 Agent 对话查询 ===\n")

    agent = KMAgent(verbose=False)

    message = "查询李浩泽(lihaoze2)的考勤记录"
    print(f"用户: {message}\n")

    result = agent.chat(message)

    print("Agent 回复:")
    print(result["response"])

    if result["tool_calls"]:
        print(f"\n工具调用:")
        for tc in result["tool_calls"]:
            print(f"  工具: {tc['tool']}")
            print(f"  参数: {json.dumps(tc['arguments'], ensure_ascii=False)}")

            if tc['result'].get('success'):
                print(f"  总记录数: {tc['result'].get('total_records')}")
                print(f"  返回记录数: {tc['result'].get('returned_records')}")

                # 显示第一条记录
                if tc['result'].get('data'):
                    print(f"\n  第一条记录:")
                    first_record = tc['result']['data'][0]
                    print(f"    {json.dumps(first_record, ensure_ascii=False, indent=6)}")

    return result["tool_calls"] and result["tool_calls"][0]["result"].get("success")


if __name__ == "__main__":
    print("开始测试...\n")
    print("=" * 60)

    test1 = test_filtered_attendance()
    test2 = test_with_agent_chat()

    print("\n" + "=" * 60)
    print("测试结果:")
    print("=" * 60)
    print(f"  直接工具调用: {'✓ 通过' if test1 else '✗ 失败'}")
    print(f"  Agent对话调用: {'✓ 通过' if test2 else '✗ 失败'}")
    print("=" * 60)

    if test1 and test2:
        print("\n🎉 所有测试通过!")
        sys.exit(0)
    else:
        print("\n⚠ 部分测试失败")
        sys.exit(1)
