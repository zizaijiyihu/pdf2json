#!/usr/bin/env python3
"""
测试 KMAgent 的考勤功能集成

该脚本测试 KMAgent 中新增的 get_subordinate_attendance 工具
"""

import os
import sys
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from km_agent.agent import KMAgent


def test_agent_with_attendance_tool():
    """测试 Agent 使用考勤工具"""
    print("=== 测试 Agent 考勤工具集成 ===\n")

    try:
        # 初始化 Agent（使用默认用户 huxiaoxiao）
        agent = KMAgent(verbose=True)
        print(f"✓ 成功初始化 KMAgent，当前用户: {agent.owner}\n")

        # 检查工具是否正确注册
        tool_names = [tool["function"]["name"] for tool in agent.tools]
        print(f"已注册的工具: {tool_names}")

        if "get_subordinate_attendance" in tool_names:
            print("✓ get_subordinate_attendance 工具已成功注册\n")
        else:
            print("✗ get_subordinate_attendance 工具未注册\n")
            return False

        # 测试1: 查询下属考勤（有权限）
        print("-" * 60)
        print("测试1: 查询下属考勤记录（应该有权限）")
        print("-" * 60)

        test_message_1 = "帮我查询一下李浩泽(lihaoze2)的考勤记录"
        print(f"用户消息: {test_message_1}\n")

        result_1 = agent.chat(test_message_1)
        print("\nAgent 回复:")
        print(result_1["response"])

        if result_1["tool_calls"]:
            print(f"\n工具调用记录 ({len(result_1['tool_calls'])} 次):")
            for idx, tc in enumerate(result_1["tool_calls"], 1):
                print(f"\n  {idx}. 工具: {tc['tool']}")
                print(f"     参数: {json.dumps(tc['arguments'], ensure_ascii=False)}")
                print(f"     结果: success={tc['result'].get('success')}")
                if tc['result'].get('success'):
                    data = tc['result'].get('data', [])
                    print(f"     数据: {len(data)} 条考勤记录")
                else:
                    print(f"     消息: {tc['result'].get('message', tc['result'].get('error'))}")

        # 测试2: 查询非下属考勤（无权限）
        print("\n" + "=" * 60)
        print("测试2: 查询非下属考勤记录（应该无权限）")
        print("=" * 60)

        test_message_2 = "帮我查询一下 huxiaoxiao 的考勤记录"
        print(f"用户消息: {test_message_2}\n")

        result_2 = agent.chat(test_message_2, history=result_1["history"])
        print("\nAgent 回复:")
        print(result_2["response"])

        if result_2["tool_calls"]:
            print(f"\n工具调用记录 ({len(result_2['tool_calls'])} 次):")
            for idx, tc in enumerate(result_2["tool_calls"], 1):
                print(f"\n  {idx}. 工具: {tc['tool']}")
                print(f"     参数: {json.dumps(tc['arguments'], ensure_ascii=False)}")
                print(f"     结果: success={tc['result'].get('success')}")
                if not tc['result'].get('success'):
                    print(f"     消息: {tc['result'].get('message', tc['result'].get('error'))}")

        print("\n" + "=" * 60)
        print("✓ 测试完成")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_direct_tool_execution():
    """直接测试工具执行"""
    print("\n=== 测试直接工具执行 ===\n")

    try:
        agent = KMAgent(verbose=False)

        # 测试1: 有权限的查询
        print("测试1: 直接调用工具查询下属考勤")
        result_1 = agent._get_subordinate_attendance("lihaoze2")
        print(f"结果: {json.dumps(result_1, ensure_ascii=False, indent=2)[:500]}...\n")

        # 测试2: 无权限的查询
        print("测试2: 直接调用工具查询非下属考勤")
        result_2 = agent._get_subordinate_attendance("huxiaoxiao")
        print(f"结果: {json.dumps(result_2, ensure_ascii=False, indent=2)}\n")

        print("✓ 直接工具执行测试完成")
        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("开始测试 KMAgent 考勤功能集成...")
    print("=" * 60)

    test_results = {}

    # 测试1: 直接工具执行
    test_results['直接工具执行'] = test_direct_tool_execution()

    # 测试2: Agent 完整对话
    test_results['Agent完整对话'] = test_agent_with_attendance_tool()

    # 输出测试总结
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print("=" * 60)

    passed_tests = 0
    total_tests = len(test_results)

    for test_name, result in test_results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name:>15}: {status}")
        if result:
            passed_tests += 1

    print("-" * 60)
    print(f"总计: {passed_tests}/{total_tests} 项测试通过")

    if passed_tests == total_tests:
        print("\n🎉 所有测试均通过!")
        return 0
    else:
        print(f"\n⚠ {total_tests - passed_tests} 项测试失败。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
