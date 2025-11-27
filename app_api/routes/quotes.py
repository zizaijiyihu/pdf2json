from flask import Blueprint, request, jsonify
from ks_infrastructure import get_current_user
from quote_repository.db import (
    create_quote,
    get_quotes,
    update_quote,
    delete_quote
)

quotes_bp = Blueprint('quotes', __name__)

@quotes_bp.route('/api/quotes', methods=['POST'])
def create_new_quote():
    """
    Create a new quote
    
    Request JSON:
    {
        "content": "语录内容",
        "is_fixed": 0  // optional, default 0
    }
    
    Response:
    {
        "success": true,
        "id": 1,
        "content": "...",
        "is_fixed": 0
    }
    """
    try:
        # Ensure user is logged in
        get_current_user()
        
        data = request.json
        content = data.get('content')
        is_fixed = data.get('is_fixed', 0)
        
        if not content:
            return jsonify({"success": False, "error": "content参数不能为空"}), 400
        
        result = create_quote(content, is_fixed)
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@quotes_bp.route('/api/quotes', methods=['GET'])
def get_quote_list():
    """
    Get quotes list
    
    Query params:
    - page: int (optional, default 1)
    - page_size: int (optional, default 10)
    
    Response:
    {
        "items": [...],
        "total": 100,
        "page": 1,
        "page_size": 10,
        "total_pages": 10
    }
    """
    try:
        # Ensure user is logged in
        get_current_user()
        
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        
        result = get_quotes(page, page_size)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@quotes_bp.route('/api/quotes/<int:quote_id>', methods=['PUT'])
def update_existing_quote(quote_id):
    """
    Update a quote
    
    Request JSON:
    {
        "content": "...",    // optional
        "is_fixed": 1        // optional
    }
    
    Response:
    {
        "success": true,
        "message": "Quote updated successfully"
    }
    """
    try:
        # Ensure user is logged in
        get_current_user()
        
        data = request.json
        content = data.get('content')
        is_fixed = data.get('is_fixed')
        
        result = update_quote(quote_id, content, is_fixed)
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@quotes_bp.route('/api/quotes/<int:quote_id>', methods=['DELETE'])
def delete_existing_quote(quote_id):
    """
    Delete a quote
    
    Response:
    {
        "success": true,
        "message": "Quote deleted successfully"
    }
    """
    try:
        # Ensure user is logged in
        get_current_user()
        
        result = delete_quote(quote_id)
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
