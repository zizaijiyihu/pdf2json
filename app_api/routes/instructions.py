from flask import Blueprint, request, jsonify
from ks_infrastructure import get_current_user
from instruction_repository import (
    create_instruction,
    get_all_instructions,
    get_instruction_by_id,
    update_instruction,
    delete_instruction
)

instructions_bp = Blueprint('instructions', __name__)

@instructions_bp.route('/api/instructions', methods=['POST'])
def create_user_instruction():
    """
    Create a new custom instruction for user
    
    Request JSON:
    {
        "owner": "user123",
        "content": "回答要简洁明了",
        "priority": 10  // optional, default 0
    }
    
    Response:
    {
        "success": true,
        "instruction_id": 1,
        "message": "指示创建成功"
    }
    """
    try:
        data = request.json
        owner = get_current_user()
        print(f"[DEBUG] create_user_instruction: Using owner {owner}", flush=True)

        content = data.get('content')
        priority = data.get('priority', 0)
        
        if not content:
            return jsonify({"success": False, "error": "content参数不能为空"}), 400
        
        result = create_instruction(owner, content, priority)
        result['message'] = "指示创建成功"
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@instructions_bp.route('/api/instructions', methods=['GET'])
def get_user_instructions():
    """
    Get user's instructions
    
    Query params:
    - owner: username (required)
    - include_inactive: true/false (optional, default false)
    
    Response:
    {
        "success": true,
        "instructions": [...]
    }
    """
    try:
        owner = get_current_user()
        print(f"[DEBUG] get_user_instructions: Using owner {owner}", flush=True)

        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        
        print(f"[DEBUG] Getting instructions for owner: {owner}", flush=True)
        
        instructions = get_all_instructions(owner, include_inactive)
        return jsonify({
            "success": True,
            "instructions": instructions
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@instructions_bp.route('/api/instructions/<int:instruction_id>', methods=['GET'])
def get_instruction_detail(instruction_id):
    """
    Get single instruction detail
    
    Query params:
    - owner: username (required)
    
    Response:
    {
        "success": true,
        "instruction": {
            "id": 1,
            "content": "...",
            "is_active": 1,
            "priority": 10,
            "created_at": "...",
            "updated_at": "..."
        }
    }
    """
    try:
        owner = get_current_user()
        
        instruction = get_instruction_by_id(instruction_id, owner)
        return jsonify({
            "success": True,
            "instruction": instruction
        })
        
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@instructions_bp.route('/api/instructions/<int:instruction_id>', methods=['PUT'])
def update_user_instruction(instruction_id):
    """
    Update an instruction
    
    Request JSON:
    {
        "owner": "user123",
        "content": "...",    // optional
        "is_active": 1,      // optional
        "priority": 5        // optional
    }
    
    Response:
    {
        "success": true,
        "message": "指示更新成功"
    }
    """
    try:
        data = request.json
        owner = get_current_user()
        
        content = data.get('content')
        is_active = data.get('is_active')
        priority = data.get('priority')
        
        update_instruction(instruction_id, owner, content, is_active, priority)
        
        return jsonify({
            "success": True,
            "message": "指示更新成功"
        })
        
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@instructions_bp.route('/api/instructions/<int:instruction_id>', methods=['DELETE'])
def delete_user_instruction(instruction_id):
    """
    Delete an instruction
    
    Request JSON:
    {
        "owner": "user123"
    }
    
    Response:
    {
        "success": true,
        "message": "指示删除成功"
    }
    """
    try:
        owner = get_current_user()
        
        delete_instruction(instruction_id, owner)
        
        return jsonify({
            "success": True,
            "message": "指示删除成功"
        })
        
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
