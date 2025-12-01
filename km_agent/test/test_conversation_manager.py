"""
ConversationManager测试文件

测试所有公开函数的功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import unittest
from unittest.mock import patch, MagicMock
from km_agent.conversation_manager import ConversationManager
from ks_infrastructure.services.user_info_service import get_current_user


class TestConversationManager(unittest.TestCase):
    """ConversationManager测试类"""

    def setUp(self):
        """测试前置设置"""
        # 使用get_current_user获取owner
        self.owner = get_current_user()
        print(f"\n当前测试用户: {self.owner}")

    @patch('km_agent.conversation_manager.update_conversation_title')
    @patch('km_agent.conversation_manager.get_conversation')
    @patch('km_agent.conversation_manager.create_conversation')
    @patch('km_agent.conversation_manager.add_message')
    @patch('km_agent.conversation_manager.get_conversation_history')
    def test_basic_workflow(self, mock_get_history, mock_add_message, mock_create_conv, mock_get_conv, mock_update_title):
        """测试基本工作流程：创建会话、保存消息、加载历史"""
        # 模拟返回值
        mock_create_conv.return_value = "conv_123"
        mock_add_message.side_effect = [1, 2, 3]  # 依次返回消息ID
        mock_get_history.return_value = [
            {'role': 'user', 'content': '你好'},
            {'role': 'assistant', 'content': '您好，有什么可以帮您？'},
        ]
        # 模拟获取会话信息（用于自动生成标题检查）
        mock_get_conv.return_value = {'title': None}

        # 创建管理器并开始会话
        manager = ConversationManager(owner=self.owner, verbose=True)
        conv_id = manager.start_conversation(title="测试会话")

        # 验证会话ID
        self.assertEqual(conv_id, "conv_123")
        self.assertEqual(manager.get_conversation_id(), "conv_123")
        print(f"✓ 会话创建成功，ID: {conv_id}")

        # 保存用户消息
        msg_id = manager.save_user_message("你好")
        self.assertEqual(msg_id, 1)
        print(f"✓ 用户消息保存成功，ID: {msg_id}")

        # 保存助手消息
        msg_id = manager.save_assistant_message("您好，有什么可以帮您？")
        self.assertEqual(msg_id, 2)
        print(f"✓ 助手消息保存成功，ID: {msg_id}")

        # 加载历史
        history = manager.load_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]['role'], 'user')
        self.assertEqual(history[1]['role'], 'assistant')
        print(f"✓ 历史加载成功，共{len(history)}条消息")

    @patch('km_agent.conversation_manager.create_conversation')
    def test_start_conversation_with_existing_id(self, mock_create_conv):
        """测试使用已存在的会话ID初始化"""
        existing_id = "existing_conv_456"
        manager = ConversationManager(owner=self.owner, conversation_id=existing_id, verbose=True)

        # 调用start_conversation应该不创建新会话
        returned_id = manager.start_conversation()

        # 验证不会创建新会话
        mock_create_conv.assert_not_called()
        self.assertEqual(returned_id, existing_id)
        print(f"✓ 已存在会话ID测试通过，ID: {existing_id}")

    @patch('km_agent.conversation_manager.add_message')
    def test_save_message_without_conversation(self, mock_add_message):
        """测试在未创建会话时保存消息"""
        manager = ConversationManager(owner=self.owner, verbose=True)

        # 未创建会话时保存消息应该返回None
        result = manager.save_user_message("测试消息")
        self.assertIsNone(result)
        mock_add_message.assert_not_called()
        print("✓ 未创建会话时保存消息返回None，符合预期")

    @patch('km_agent.conversation_manager.update_conversation_title')
    @patch('km_agent.conversation_manager.get_conversation')
    @patch('km_agent.conversation_manager.create_conversation')
    @patch('km_agent.conversation_manager.add_message')
    def test_save_all_message_types(self, mock_add_message, mock_create_conv, mock_get_conv, mock_update_title):
        """测试保存所有类型的消息"""
        mock_create_conv.return_value = "conv_789"
        mock_add_message.side_effect = [1, 2, 3, 4]
        mock_get_conv.return_value = {'title': '已有标题'} # 模拟已有标题，避免触发自动生成

        manager = ConversationManager(owner=self.owner, verbose=True)
        manager.start_conversation(title="消息类型测试")

        # 测试系统消息
        msg_id = manager.save_system_message("你是一个知识库助手")
        self.assertEqual(msg_id, 1)
        print(f"✓ 系统消息保存成功，ID: {msg_id}")

        # 测试用户消息
        msg_id = manager.save_user_message("如何办理居住证？")
        self.assertEqual(msg_id, 2)
        print(f"✓ 用户消息保存成功，ID: {msg_id}")

        # 测试助手消息（带工具调用）
        tool_calls = [
            {
                'id': 'call_123',
                'type': 'function',
                'function': {'name': 'search_kb', 'arguments': '{"query": "居住证"}'}
            }
        ]
        msg_id = manager.save_assistant_message("正在查询...", tool_calls=tool_calls)
        self.assertEqual(msg_id, 3)
        print(f"✓ 助手消息（带工具调用）保存成功，ID: {msg_id}")

        # 测试工具消息
        msg_id = manager.save_tool_message("call_123", "找到3条相关文档...")
        self.assertEqual(msg_id, 4)
        print(f"✓ 工具消息保存成功，ID: {msg_id}")

    @patch('km_agent.conversation_manager.create_conversation')
    @patch('km_agent.conversation_manager.get_conversation_history')
    def test_load_history_with_limit(self, mock_get_history, mock_create_conv):
        """测试加载历史时使用限制"""
        mock_create_conv.return_value = "conv_limit"
        mock_get_history.return_value = [
            {'role': 'user', 'content': '消息1'},
            {'role': 'assistant', 'content': '回复1'},
        ]

        manager = ConversationManager(owner=self.owner, verbose=True)
        manager.start_conversation()

        # 加载最近10条消息
        history = manager.load_history(limit=10)

        # 验证调用参数
        mock_get_history.assert_called_with("conv_limit", 10)
        self.assertEqual(len(history), 2)
        print(f"✓ 限制条数加载历史成功，获取{len(history)}条消息")

    @patch('km_agent.conversation_manager.get_conversation_history')
    def test_load_history_without_conversation(self, mock_get_history):
        """测试在未创建会话时加载历史"""
        manager = ConversationManager(owner=self.owner, verbose=True)

        # 未创建会话时加载历史应该返回空列表
        history = manager.load_history()

        self.assertEqual(history, [])
        mock_get_history.assert_not_called()
        print("✓ 未创建会话时加载历史返回空列表，符合预期")

    @patch('km_agent.conversation_manager.create_conversation')
    @patch('km_agent.conversation_manager.get_conversation')
    def test_get_info(self, mock_get_conv, mock_create_conv):
        """测试获取会话信息"""
        mock_create_conv.return_value = "conv_info"
        mock_get_conv.return_value = {
            'id': 'conv_info',
            'owner': self.owner,
            'title': '测试会话',
            'created_at': '2025-11-28 10:00:00'
        }

        manager = ConversationManager(owner=self.owner, verbose=True)
        manager.start_conversation(title="测试会话")

        # 获取会话信息
        info = manager.get_info()

        self.assertIsNotNone(info)
        self.assertEqual(info['id'], 'conv_info')
        self.assertEqual(info['title'], '测试会话')
        print(f"✓ 会话信息获取成功: {info}")

    @patch('km_agent.conversation_manager.get_conversation')
    def test_get_info_without_conversation(self, mock_get_conv):
        """测试未创建会话时获取信息"""
        manager = ConversationManager(owner=self.owner, verbose=True)

        # 未创建会话时应返回None
        info = manager.get_info()

        self.assertIsNone(info)
        mock_get_conv.assert_not_called()
        print("✓ 未创建会话时获取信息返回None，符合预期")

    @patch('km_agent.conversation_manager.create_conversation')
    @patch('km_agent.conversation_manager.update_conversation_title')
    def test_update_title(self, mock_update_title, mock_create_conv):
        """测试更新会话标题"""
        mock_create_conv.return_value = "conv_update"
        mock_update_title.return_value = True

        manager = ConversationManager(owner=self.owner, verbose=True)
        manager.start_conversation(title="旧标题")

        # 更新标题
        success = manager.update_title("新标题")

        self.assertTrue(success)
        mock_update_title.assert_called_with("conv_update", "新标题")
        print("✓ 标题更新成功")

    @patch('km_agent.conversation_manager.update_conversation_title')
    def test_update_title_without_conversation(self, mock_update_title):
        """测试未创建会话时更新标题"""
        manager = ConversationManager(owner=self.owner, verbose=True)

        # 未创建会话时应返回False
        success = manager.update_title("新标题")

        self.assertFalse(success)
        mock_update_title.assert_not_called()
        print("✓ 未创建会话时更新标题返回False，符合预期")

    def test_auto_generate_title(self):
        """测试自动生成标题"""
        manager = ConversationManager(owner=self.owner, verbose=True)

        # 测试短消息
        title = manager.auto_generate_title("如何办理居住证？")
        self.assertEqual(title, "如何办理居住证？")
        print(f"✓ 短消息标题生成: {title}")

        # 测试长消息
        long_message = "这是一条非常长的消息" * 10
        title = manager.auto_generate_title(long_message, max_length=20)
        self.assertEqual(len(title), 20)  # No "..."
        self.assertFalse(title.endswith("..."))
        print(f"✓ 长消息标题生成: {title}")

    @patch('km_agent.conversation_manager.create_conversation')
    @patch('km_agent.conversation_manager.get_conversation_history')
    def test_history_format_conversion(self, mock_get_history, mock_create_conv):
        """测试历史记录格式转换"""
        mock_create_conv.return_value = "conv_format"

        # 模拟包含tool_calls和tool_call_id的消息
        mock_get_history.return_value = [
            {'role': 'user', 'content': '查询居住证'},
            {
                'role': 'assistant',
                'content': '正在查询...',
                'tool_calls': [{'id': 'call_1', 'type': 'function'}]
            },
            {
                'role': 'tool',
                'content': '查询结果...',
                'tool_call_id': 'call_1'
            },
        ]

        manager = ConversationManager(owner=self.owner, verbose=True)
        manager.start_conversation()

        # 加载历史
        history = manager.load_history()

        # 验证格式转换
        self.assertEqual(len(history), 3)
        self.assertIn('tool_calls', history[1])
        self.assertIn('tool_call_id', history[2])
        print("✓ 历史记录格式转换成功")
        print(f"  - 用户消息: {history[0]}")
        print(f"  - 助手消息（带工具调用）: {history[1]}")
        print(f"  - 工具消息: {history[2]}")

    def test_owner_from_get_current_user(self):
        """测试使用get_current_user作为owner"""
        current_user = get_current_user()
        manager = ConversationManager(owner=current_user, verbose=True)

        self.assertEqual(manager.owner, current_user)
        print(f"✓ Owner设置成功: {current_user}")


def run_tests():
    """运行所有测试"""
    print("=" * 70)
    print("ConversationManager 公开函数测试")
    print("=" * 70)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestConversationManager)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 打印总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
