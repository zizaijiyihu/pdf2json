from flask import Blueprint, jsonify
from app_api.services import agent_service

health_bp = Blueprint('health', __name__)

@health_bp.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "services": {
            "km_agent": agent_service.km_agent is not None,
            "vectorizer": agent_service.vectorizer is not None
        }
    })
