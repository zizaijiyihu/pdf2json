"""
Agent与ConversationManager集成测试脚本

测试场景：
1. 创建带会话管理的Agent
2. 进行多轮对话
3. 验证消息持久化
4. 加载历史记录
5. 继续对话
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from km_agent.agent import KMAgent
from km_agent.conversation_manager import ConversationManager
from ks_infrastructure.services.user_info_service import get_current_user


def print_separator(title=""):
    """打印分隔线"""
    if title:
        print(f"\n{'='*70}")
        print(f" {title}")
        print(f"{'='*70}")
    else:
        print(f"{'='*70}")


def print_message(role, content):
    """格式化打印消息"""
    role_emoji = {
        'user': '👤',
        'assistant': '🤖',
        'system': '⚙️',
        'tool': '🔧'
    }
    emoji = role_emoji.get(role, '📝')
    print(f"\n{emoji} {role.upper()}: {content[:200]}{'...' if len(content) > 200 else ''}")


def test_new_conversation():
    """测试1: 创建新会话并进行多轮对话"""
    print_separator("测试1: 创建新会话并进行多轮对话")

    # 创建启用历史记录的Agent
    current_user = get_current_user()
    print(f"\n当前用户: {current_user}")

    agent = KMAgent(
        verbose=True,
        owner=current_user,
        enable_history=True
    )

    conversation_id = agent.conversation_manager.get_conversation_id()
    print(f"\n✓ Agent创建成功")
    print(f"✓ 会话ID: {conversation_id}")

    # 第一轮对话
    print_separator("第一轮对话")
    print_message('user', "你好，请介绍一下你自己")

    result = agent.chat("你好，请介绍一下你自己")
    print_message('assistant', result['response'])
    print(f"\n工具调用次数: {len(result['tool_calls'])}")

    # 第二轮对话 - 使用历史
    print_separator("第二轮对话（使用历史）")
    print_message('user', "金山集团的主要业务是什么？")

    result = agent.chat("金山集团的主要业务是什么？", history=result['history'])
    print_message('assistant', result['response'])
    print(f"\n工具调用次数: {len(result['tool_calls'])}")

    # 第三轮对话 - 测试上下文记忆
    print_separator("第三轮对话（测试上下文记忆）")
    print_message('user', "刚才我问了你什么？")

    result = agent.chat("刚才我问了你什么？", history=result['history'])
    print_message('assistant', result['response'])

    # 验证历史记录
    print_separator("验证历史记录持久化")
    saved_history = agent.conversation_manager.load_history()
    print(f"\n✓ 从数据库加载的消息数: {len(saved_history)}")

    # 打印历史记录摘要
    role_counts = {}
    for msg in saved_history:
        role = msg.get('role')
        role_counts[role] = role_counts.get(role, 0) + 1

    print("\n消息类型统计:")
    for role, count in role_counts.items():
        print(f"  - {role}: {count}条")

    print(f"\n✓ 测试1完成，会话ID: {conversation_id}")
    return conversation_id


def test_load_existing_conversation(conversation_id):
    """测试2: 加载已存在的会话并继续对话"""
    print_separator("测试2: 加载已存在的会话并继续对话")

    current_user = get_current_user()

    # 使用已存在的conversation_id创建Agent
    agent = KMAgent(
        verbose=True,
        owner=current_user,
        conversation_id=conversation_id,
        enable_history=True
    )

    print(f"\n✓ 加载已存在的会话: {conversation_id}")

    # 从数据库加载历史
    history_from_db = agent.conversation_manager.load_history()
    print(f"✓ 从数据库加载了 {len(history_from_db)} 条消息")

    # 打印最近的3条消息
    print("\n最近的3条消息:")
    for msg in history_from_db[-3:]:
        print_message(msg['role'], msg.get('content', '[工具调用]'))

    # 继续对话（使用加载的历史）
    print_separator("继续对话（基于加载的历史）")

    # 将数据库历史转换为Agent需要的格式
    # 需要添加system message（如果第一条不是system）
    if not history_from_db or history_from_db[0].get('role') != 'system':
        history_messages = [{"role": "system", "content": agent.effective_system_prompt}] + history_from_db
    else:
        history_messages = history_from_db

    print_message('user', "我们之前聊了什么主题？")

    result = agent.chat("我们之前聊了什么主题？", history=history_messages)
    print_message('assistant', result['response'])

    # 再次验证历史记录
    print_separator("再次验证历史记录")
    updated_history = agent.conversation_manager.load_history()
    print(f"\n✓ 更新后的消息总数: {len(updated_history)}")

    print(f"\n✓ 测试2完成")


def test_conversation_info():
    """测试3: 获取会话信息和更新标题"""
    print_separator("测试3: 获取会话信息和更新标题")

    current_user = get_current_user()

    # 创建新会话
    agent = KMAgent(
        verbose=False,
        owner=current_user,
        enable_history=True
    )

    conversation_id = agent.conversation_manager.get_conversation_id()

    # 进行一次对话
    result = agent.chat("你好")

    # 获取会话信息
    info = agent.conversation_manager.get_info()
    print(f"\n会话信息:")
    print(f"  - ID: {info.get('id')}")
    print(f"  - Owner: {info.get('owner')}")
    print(f"  - Title: {info.get('title')}")
    print(f"  - Created: {info.get('created_at')}")
    print(f"  - Updated: {info.get('updated_at')}")

    # 自动生成标题
    auto_title = agent.conversation_manager.auto_generate_title("你好", max_length=20)
    print(f"\n✓ 自动生成的标题: {auto_title}")

    # 更新标题
    success = agent.conversation_manager.update_title(auto_title)
    print(f"✓ 标题更新{'成功' if success else '失败'}")

    # 再次获取信息验证
    updated_info = agent.conversation_manager.get_info()
    print(f"✓ 更新后的标题: {updated_info.get('title')}")

    print(f"\n✓ 测试3完成")


def test_tool_calls_persistence():
    """测试4: 验证工具调用的持久化"""
    print_separator("测试4: 验证工具调用的持久化")

    current_user = get_current_user()

    # 创建新会话
    agent = KMAgent(
        verbose=True,
        owner=current_user,
        enable_history=True
    )

    # 进行一次会触发工具调用的对话
    print_message('user', "查询一下金山集团的信息")

    result = agent.chat("查询一下金山集团的信息")
    print_message('assistant', result['response'])
    print(f"\n工具调用次数: {len(result['tool_calls'])}")

    # 打印工具调用详情
    if result['tool_calls']:
        print("\n工具调用详情:")
        for i, tc in enumerate(result['tool_calls'], 1):
            print(f"  {i}. 工具: {tc['tool']}")
            print(f"     参数: {tc['arguments']}")

    # 加载历史并验证工具调用
    history = agent.conversation_manager.load_history()

    # 统计包含tool_calls的消息
    messages_with_tool_calls = [msg for msg in history if msg.get('tool_calls')]
    tool_messages = [msg for msg in history if msg.get('role') == 'tool']

    print(f"\n✓ 包含工具调用的assistant消息: {len(messages_with_tool_calls)}条")
    print(f"✓ 工具结果消息: {len(tool_messages)}条")

    # 打印一个工具调用示例
    if messages_with_tool_calls:
        print("\n工具调用示例:")
        msg = messages_with_tool_calls[0]
        print(f"  - Role: {msg['role']}")
        print(f"  - Tool Calls: {len(msg['tool_calls'])}个")
        print(f"  - 第一个工具: {msg['tool_calls'][0]['function']['name']}")

    print(f"\n✓ 测试4完成")


def test_multiple_sessions():
    """测试5: 测试多个会话的隔离性"""
    print_separator("测试5: 测试多个会话的隔离性")

    current_user = get_current_user()

    # 创建第一个会话
    agent1 = KMAgent(verbose=False, owner=current_user, enable_history=True)
    result1 = agent1.chat("我喜欢苹果")
    conv_id_1 = agent1.conversation_manager.get_conversation_id()
    agent1.conversation_manager.update_title("会话1-水果")

    print(f"\n✓ 会话1创建: {conv_id_1}")
    print(f"  消息数: {len(agent1.conversation_manager.load_history())}")

    # 创建第二个会话
    agent2 = KMAgent(verbose=False, owner=current_user, enable_history=True)
    result2 = agent2.chat("我喜欢香蕉")
    conv_id_2 = agent2.conversation_manager.get_conversation_id()
    agent2.conversation_manager.update_title("会话2-水果")

    print(f"\n✓ 会话2创建: {conv_id_2}")
    print(f"  消息数: {len(agent2.conversation_manager.load_history())}")

    # 验证会话隔离
    print("\n验证会话隔离:")

    history1 = agent1.conversation_manager.load_history()
    history2 = agent2.conversation_manager.load_history()

    # 查找用户消息
    user_msg_1 = [msg for msg in history1 if msg['role'] == 'user'][0]['content']
    user_msg_2 = [msg for msg in history2 if msg['role'] == 'user'][0]['content']

    print(f"  会话1的用户消息: {user_msg_1}")
    print(f"  会话2的用户消息: {user_msg_2}")

    assert user_msg_1 == "我喜欢苹果", "会话1消息错误"
    assert user_msg_2 == "我喜欢香蕉", "会话2消息错误"

    print(f"\n✓ 会话隔离验证成功")
    print(f"\n✓ 测试5完成")


def main():
    """主测试函数"""
    print_separator("Agent与ConversationManager集成测试")
    print("\n测试环境:")
    print(f"  - Python版本: {sys.version.split()[0]}")
    print(f"  - 当前用户: {get_current_user()}")

    try:
        # 测试1: 新会话多轮对话
        conversation_id = test_new_conversation()

        # 测试2: 加载已存在的会话
        test_load_existing_conversation(conversation_id)

        # 测试3: 会话信息和标题管理
        test_conversation_info()

        # 测试4: 工具调用持久化
        test_tool_calls_persistence()

        # 测试5: 多会话隔离
        test_multiple_sessions()

        # 总结
        print_separator("所有测试完成")
        print("\n✅ 所有测试均通过！")
        print("\n测试覆盖:")
        print("  ✓ 创建新会话并进行多轮对话")
        print("  ✓ 加载已存在会话并继续对话")
        print("  ✓ 会话信息获取和标题管理")
        print("  ✓ 工具调用的持久化")
        print("  ✓ 多会话的隔离性")
        print_separator()

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
