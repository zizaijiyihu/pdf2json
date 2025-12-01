"""
会话管理API路由
提供会话的CRUD操作接口
"""

import logging
from flask import Blueprint, request, jsonify
from ks_infrastructure import get_current_user
from conversation_repository import (
    create_conversation,
    get_conversation,
    list_conversations,
    count_conversations,
    update_conversation_title,
    delete_conversation,
    get_conversation_history,
    search_conversations,
)

logger = logging.getLogger(__name__)
conversations_bp = Blueprint('conversations', __name__)


@conversations_bp.route('/api/conversations', methods=['GET'])
def get_conversations():
    """
    获取用户的会话列表(分页)

    Query Parameters:
        limit: 每页数量(默认20)
        offset: 偏移量(默认0)

    Response:
        {
            "success": true,
            "data": {
                "conversations": [...],
                "total": 100,
                "limit": 20,
                "offset": 0
            }
        }
    """
    logger.debug(f"→ 调用 conversations.get_conversations()")
    try:
        logger.debug(f"  → 调用 ks_infrastructure.get_current_user()")
        owner = get_current_user()
        logger.debug(f"  ← 返回 owner={owner}")

        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)

        # 限制每页最大数量
        limit = min(limit, 100)

        logger.debug(f"  → 调用 conversation_repository.list_conversations(owner={owner}, limit={limit}, offset={offset})")
        conversations = list_conversations(owner, limit, offset)
        logger.debug(f"  ← 返回 {len(conversations)} 个会话")

        logger.debug(f"  → 调用 conversation_repository.count_conversations(owner={owner})")
        total = count_conversations(owner)
        logger.debug(f"  ← 返回 total={total}")

        logger.debug(f"← 返回成功响应")
        return jsonify({
            "success": True,
            "data": {
                "conversations": conversations,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        })

    except Exception as e:
        logger.error(f"← 返回错误: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@conversations_bp.route('/api/conversations', methods=['POST'])
def create_new_conversation():
    """
    创建新会话

    Request Body:
        {
            "title": "会话标题" (可选)
        }

    Response:
        {
            "success": true,
            "data": {
                "conversation_id": "uuid-string"
            }
        }
    """
    logger.debug(f"→ 调用 conversations.create_new_conversation()")
    try:
        logger.debug(f"  → 调用 ks_infrastructure.get_current_user()")
        owner = get_current_user()
        logger.debug(f"  ← 返回 owner={owner}")

        data = request.get_json() or {}
        title = data.get('title')
        logger.debug(f"  请求参数: title={title}")

        logger.debug(f"  → 调用 conversation_repository.create_conversation(owner={owner}, title={title})")
        conversation_id = create_conversation(owner, title)
        logger.debug(f"  ← 返回 conversation_id={conversation_id}")

        logger.debug(f"← 返回成功响应")
        return jsonify({
            "success": True,
            "data": {
                "conversation_id": conversation_id
            }
        }), 201

    except Exception as e:
        logger.error(f"← 返回错误: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@conversations_bp.route('/api/conversations/<conversation_id>', methods=['GET'])
def get_conversation_detail(conversation_id):
    """
    获取会话详情

    Response:
        {
            "success": true,
            "data": {
                "id": 1,
                "conversation_id": "uuid",
                "owner": "user@example.com",
                "title": "会话标题",
                "created_at": "2025-11-28T10:00:00",
                "updated_at": "2025-11-28T10:00:00"
            }
        }
    """
    logger.debug(f"→ 调用 conversations.get_conversation_detail(conversation_id={conversation_id})")
    try:
        logger.debug(f"  → 调用 ks_infrastructure.get_current_user()")
        owner = get_current_user()
        logger.debug(f"  ← 返回 owner={owner}")

        logger.debug(f"  → 调用 conversation_repository.get_conversation(conversation_id={conversation_id})")
        conversation = get_conversation(conversation_id)
        logger.debug(f"  ← 返回 conversation={conversation}")

        if not conversation:
            logger.debug(f"← 返回404: 会话不存在")
            return jsonify({
                "success": False,
                "error": "Conversation not found"
            }), 404

        # 验证所有权
        if conversation['owner'] != owner:
            logger.debug(f"← 返回403: 权限不足 (owner={conversation['owner']}, current_user={owner})")
            return jsonify({
                "success": False,
                "error": "Permission denied"
            }), 403

        logger.debug(f"← 返回成功响应")
        return jsonify({
            "success": True,
            "data": conversation
        })

    except Exception as e:
        logger.error(f"← 返回错误: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@conversations_bp.route('/api/conversations/<conversation_id>/messages', methods=['GET'])
def get_conversation_messages(conversation_id):
    """
    获取会话的消息历史

    Query Parameters:
        limit: 限制返回的消息数量(可选)

    Response:
        {
            "success": true,
            "data": {
                "conversation_id": "uuid",
                "messages": [...]
            }
        }
    """
    logger.debug(f"→ 调用 conversations.get_conversation_messages(conversation_id={conversation_id})")
    try:
        logger.debug(f"  → 调用 ks_infrastructure.get_current_user()")
        owner = get_current_user()
        logger.debug(f"  ← 返回 owner={owner}")

        limit = request.args.get('limit', type=int)
        logger.debug(f"  请求参数: limit={limit}")

        # 验证会话所有权
        logger.debug(f"  → 调用 conversation_repository.get_conversation(conversation_id={conversation_id})")
        conversation = get_conversation(conversation_id)
        logger.debug(f"  ← 返回 conversation={conversation}")

        if not conversation:
            logger.debug(f"← 返回404: 会话不存在")
            return jsonify({
                "success": False,
                "error": "Conversation not found"
            }), 404

        if conversation['owner'] != owner:
            logger.debug(f"← 返回403: 权限不足")
            return jsonify({
                "success": False,
                "error": "Permission denied"
            }), 403

        logger.debug(f"  → 调用 conversation_repository.get_conversation_history(conversation_id={conversation_id}, limit={limit})")
        messages = get_conversation_history(conversation_id, limit)
        
        # 过滤掉内部消息(工具调用、系统提示词等)，只返回面向用户的对话历史
        # 1. 保留用户消息
        # 2. 保留有内容的助手消息(过滤掉纯工具调用的助手消息)
        filtered_messages = [
            msg for msg in messages
            if msg['role'] == 'user' or (
                msg['role'] == 'assistant' and msg.get('content') and msg['content'].strip()
            )
        ]
        
        logger.debug(f"  ← 返回 {len(filtered_messages)} 条消息 (过滤前 {len(messages)} 条)")

        logger.debug(f"← 返回成功响应")
        return jsonify({
            "success": True,
            "data": {
                "conversation_id": conversation_id,
                "messages": filtered_messages
            }
        })

    except Exception as e:
        logger.error(f"← 返回错误: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@conversations_bp.route('/api/conversations/<conversation_id>', methods=['PUT'])
def update_conversation(conversation_id):
    """
    更新会话信息
    
    Request Body:
        {
            "title": "新标题"
        }
    
    Response:
        {
            "success": true
        }
    """
    try:
        owner = get_current_user()
        data = request.get_json()
        
        if not data or 'title' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'title' in request body"
            }), 400
        
        # 验证会话所有权
        conversation = get_conversation(conversation_id)
        if not conversation:
            return jsonify({
                "success": False,
                "error": "Conversation not found"
            }), 404
        
        if conversation['owner'] != owner:
            return jsonify({
                "success": False,
                "error": "Permission denied"
            }), 403
        
        title = data['title']
        success = update_conversation_title(conversation_id, title)
        
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({
                "success": False,
                "error": "Failed to update conversation"
            }), 500
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@conversations_bp.route('/api/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation_endpoint(conversation_id):
    """
    删除会话(软删除)
    
    Response:
        {
            "success": true
        }
    """
    try:
        owner = get_current_user()
        
        # 验证会话所有权
        conversation = get_conversation(conversation_id)
        if not conversation:
            return jsonify({
                "success": False,
                "error": "Conversation not found"
            }), 404
        
        if conversation['owner'] != owner:
            return jsonify({
                "success": False,
                "error": "Permission denied"
            }), 403
        
        success = delete_conversation(conversation_id)
        
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({
                "success": False,
                "error": "Failed to delete conversation"
            }), 500
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@conversations_bp.route('/api/conversations/search', methods=['GET'])
def search_conversations_endpoint():
    """
    搜索会话
    
    Query Parameters:
        q: 搜索关键词
        limit: 返回结果数量限制(默认20)
    
    Response:
        {
            "success": true,
            "data": {
                "conversations": [...],
                "keyword": "搜索词"
            }
        }
    """
    try:
        owner = get_current_user()
        keyword = request.args.get('q', '').strip()
        limit = request.args.get('limit', 20, type=int)
        
        if not keyword:
            return jsonify({
                "success": False,
                "error": "Missing search keyword 'q'"
            }), 400
        
        # 限制每页最大数量
        limit = min(limit, 100)
        
        conversations = search_conversations(owner, keyword, limit)
        
        return jsonify({
            "success": True,
            "data": {
                "conversations": conversations,
                "keyword": keyword
            }
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
