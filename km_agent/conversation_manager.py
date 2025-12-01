"""
Agent会话管理器
负责Agent对话历史的持久化和检索
"""

import logging
from typing import List, Dict, Optional, Any
from conversation_repository import (
    create_conversation,
    add_message,
    get_conversation_history,
    get_conversation,
    update_conversation_title,
)

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Agent会话管理器
    
    职责：
    - 管理会话的生命周期
    - 保存和加载对话历史
    - 协调消息的持久化
    
    使用示例：
        # 创建新会话
        manager = ConversationManager(owner="user@example.com")
        manager.start_conversation(title="关于居住证的咨询")
        
        # 保存消息
        manager.save_user_message("如何办理居住证?")
        manager.save_assistant_message("办理居住证需要以下材料...")
        
        # 加载历史
        history = manager.load_history()
    """
    
    def __init__(self, owner: str, conversation_id: str = None, verbose: bool = False):
        """
        初始化会话管理器
        
        Args:
            owner: 会话所有者(用户标识)
            conversation_id: 会话ID(可选，如果不提供则需要调用start_conversation创建)
            verbose: 是否打印调试信息
        """
        self.owner = owner
        self.conversation_id = conversation_id
        self.verbose = verbose
        
        if self.verbose and conversation_id:
            logger.info(f"ConversationManager initialized with conversation_id: {conversation_id}")
    
    def start_conversation(self, title: str = None) -> str:
        """
        创建新会话
        
        Args:
            title: 会话标题(可选)
        
        Returns:
            str: 会话ID
        """
        if not self.conversation_id:
            self.conversation_id = create_conversation(self.owner, title)
            if self.verbose:
                logger.info(f"Started new conversation: {self.conversation_id}")
        else:
            if self.verbose:
                logger.warning(f"Conversation already exists: {self.conversation_id}")
        
        return self.conversation_id
    
    def get_conversation_id(self) -> Optional[str]:
        """
        获取当前会话ID
        
        Returns:
            str: 会话ID，如果未创建则返回None
        """
        return self.conversation_id
    
    def save_user_message(self, content: str) -> Optional[int]:
        """
        保存用户消息
        
        Args:
            content: 消息内容
        
        Returns:
            int: 消息ID，如果会话未创建则返回None
        """
        if not self.conversation_id:
            if self.verbose:
                logger.warning("Cannot save user message: conversation not started")
            return None
        
        message_id = add_message(
            conversation_id=self.conversation_id,
            role='user',
            content=content
        )
        
        if self.verbose:
            logger.debug(f"Saved user message (id={message_id}): {content[:50]}...")
            
        # 尝试自动生成标题
        self._ensure_title(content)
        
        return message_id
    
    def save_assistant_message(
        self,
        content: str,
        tool_calls: List[Dict] = None
    ) -> Optional[int]:
        """
        保存助手消息
        
        Args:
            content: 消息内容
            tool_calls: 工具调用信息(可选)
        
        Returns:
            int: 消息ID，如果会话未创建则返回None
        """
        if not self.conversation_id:
            if self.verbose:
                logger.warning("Cannot save assistant message: conversation not started")
            return None
        
        message_id = add_message(
            conversation_id=self.conversation_id,
            role='assistant',
            content=content,
            tool_calls=tool_calls
        )
        
        if self.verbose:
            logger.debug(f"Saved assistant message (id={message_id}): {content[:50]}...")
        
        return message_id
    
    def save_tool_message(self, tool_call_id: str, content: str) -> Optional[int]:
        """
        保存工具调用结果消息
        
        Args:
            tool_call_id: 工具调用ID
            content: 工具返回的结果
        
        Returns:
            int: 消息ID，如果会话未创建则返回None
        """
        if not self.conversation_id:
            if self.verbose:
                logger.warning("Cannot save tool message: conversation not started")
            return None
        
        message_id = add_message(
            conversation_id=self.conversation_id,
            role='tool',
            content=content,
            tool_call_id=tool_call_id
        )
        
        if self.verbose:
            logger.debug(f"Saved tool message (id={message_id}, tool_call_id={tool_call_id})")
        
        return message_id
    
    def save_system_message(self, content: str) -> Optional[int]:
        """
        保存系统消息
        
        Args:
            content: 系统提示词内容
        
        Returns:
            int: 消息ID，如果会话未创建则返回None
        """
        if not self.conversation_id:
            if self.verbose:
                logger.warning("Cannot save system message: conversation not started")
            return None
        
        message_id = add_message(
            conversation_id=self.conversation_id,
            role='system',
            content=content
        )
        
        if self.verbose:
            logger.debug(f"Saved system message (id={message_id})")
        
        return message_id
    
    def load_history(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        加载会话历史
        
        Args:
            limit: 限制返回的消息数量(可选)
        
        Returns:
            List[Dict]: 消息列表，格式与Agent的history兼容
        """
        if not self.conversation_id:
            if self.verbose:
                logger.warning("Cannot load history: conversation not started")
            return []
        
        messages = get_conversation_history(self.conversation_id, limit)
        
        # 转换为Agent兼容的格式
        history = []
        for msg in messages:
            message_dict = {
                'role': msg['role'],
                'content': msg.get('content')
            }
            
            # 添加tool_calls字段(如果存在)
            if msg.get('tool_calls'):
                message_dict['tool_calls'] = msg['tool_calls']
            
            # 添加tool_call_id字段(如果存在)
            if msg.get('tool_call_id'):
                message_dict['tool_call_id'] = msg['tool_call_id']
            
            history.append(message_dict)
        
        if self.verbose:
            logger.info(f"Loaded {len(history)} messages from conversation {self.conversation_id}")
        
        return history
    
    def get_info(self) -> Optional[Dict[str, Any]]:
        """
        获取会话信息
        
        Returns:
            Dict: 会话信息，如果会话不存在则返回None
        """
        if not self.conversation_id:
            return None
        
        return get_conversation(self.conversation_id)
    
    def update_title(self, title: str) -> bool:
        """
        更新会话标题
        
        Args:
            title: 新标题
        
        Returns:
            bool: 是否更新成功
        """
        if not self.conversation_id:
            if self.verbose:
                logger.warning("Cannot update title: conversation not started")
            return False
        
        success = update_conversation_title(self.conversation_id, title)
        
        if self.verbose and success:
            logger.info(f"Updated conversation title to: {title}")
        
        return success
    
    def auto_generate_title(self, first_user_message: str, max_length: int = 13) -> str:
        """
        根据首条用户消息自动生成标题
        
        Args:
            first_user_message: 首条用户消息
            max_length: 标题最大长度(默认13，对应展示时的全角字符限制)
        
        Returns:
            str: 生成的标题
        """
        # 移除换行符，取第一行或替换为空格
        title = first_user_message.strip().split('\n')[0]
        
        # 截取前N个字符作为标题
        if len(title) > max_length:
            title = title[:max_length]
        
        return title

    def _ensure_title(self, content: str):
        """
        确保会话有标题，如果没有则从内容生成
        
        Args:
            content: 用户消息内容
        """
        if not self.conversation_id:
            return
            
        try:
            # 获取当前会话信息
            conversation = self.get_info()
            # 如果会话存在且没有标题（或标题为空）
            if conversation and not conversation.get('title'):
                # 生成新标题
                new_title = self.auto_generate_title(content)
                if new_title:
                    self.update_title(new_title)
        except Exception as e:
            if self.verbose:
                logger.warning(f"Failed to auto generate title: {e}")
