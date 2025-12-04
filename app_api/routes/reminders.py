"""
Reminders API Routes - 提醒管理接口

提供全局提醒的增删改查功能
"""

import logging
from flask import Blueprint, request, jsonify
from reminder_repository import db as reminder_repository

logger = logging.getLogger(__name__)

reminders_bp = Blueprint('reminders', __name__, url_prefix='/api/reminders')


@reminders_bp.route('', methods=['GET'])
def get_reminders():
    """
    获取提醒列表
    
    Query Parameters:
        user_id: 用户ID（可选，如果提供则返回所有公开提醒+该用户的私有提醒）
    
    Returns:
        {
            "success": true,
            "data": [
                {
                    "id": 1,
                    "content": "今天谁比较辛苦",
                    "is_public": 1,
                    "user_id": null,
                    "created_at": "2025-12-01 11:00:00",
                    "updated_at": "2025-12-01 11:00:00"
                }
            ]
        }
    """
    try:
        user_id = request.args.get('user_id')
        reminders = reminder_repository.get_all_reminders(user_id=user_id)
        return jsonify({
            'success': True,
            'data': reminders
        })
    except Exception as e:
        logger.error(f"Failed to get reminders: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@reminders_bp.route('', methods=['POST'])
def create_reminder():
    """
    创建新提醒
    
    Request Body:
        {
            "content": "今天谁比较辛苦",
            "is_public": true,  // 可选，默认true
            "user_id": "user123"  // 可选，私有提醒时必填
        }
    
    Returns:
        {
            "success": true,
            "reminder_id": 1
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必需参数: content'
            }), 400
        
        is_public = data.get('is_public', True)
        user_id = data.get('user_id')
        
        result = reminder_repository.create_reminder(
            content=data['content'],
            is_public=is_public,
            user_id=user_id
        )
        
        return jsonify(result), 201
    except ValueError as e:
        logger.warning(f"Invalid reminder data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Failed to create reminder: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@reminders_bp.route('/<int:reminder_id>', methods=['GET'])
def get_reminder(reminder_id):
    """
    获取单个提醒详情
    
    Returns:
        {
            "success": true,
            "data": {
                "id": 1,
                "content": "今天谁比较辛苦",
                "created_at": "2025-12-01 11:00:00",
                "updated_at": "2025-12-01 11:00:00"
            }
        }
    """
    try:
        reminder = reminder_repository.get_reminder_by_id(reminder_id)
        return jsonify({
            'success': True,
            'data': reminder
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        logger.error(f"Failed to get reminder {reminder_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@reminders_bp.route('/<int:reminder_id>', methods=['PUT'])
def update_reminder(reminder_id):
    """
    更新提醒
    
    Request Body:
        {
            "content": "最近有什么AI新闻",  // 可选
            "is_public": false,  // 可选
            "user_id": "user123"  // 可选，切换为私有时必填
        }
    
    Returns:
        {
            "success": true,
            "message": "提醒更新成功"
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空'
            }), 400
        
        content = data.get('content')
        is_public = data.get('is_public')
        user_id = data.get('user_id')
        
        result = reminder_repository.update_reminder(
            reminder_id=reminder_id,
            content=content,
            is_public=is_public,
            user_id=user_id
        )
        
        return jsonify(result)
    except ValueError as e:
        logger.warning(f"Invalid reminder update: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        logger.error(f"Failed to update reminder {reminder_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@reminders_bp.route('/<int:reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    """
    删除提醒
    
    Returns:
        {
            "success": true,
            "message": "提醒删除成功"
        }
    """
    try:
        result = reminder_repository.delete_reminder(reminder_id)
        return jsonify(result)
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        logger.error(f"Failed to delete reminder {reminder_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
