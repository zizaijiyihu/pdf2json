"""
Flask API for Knowledge Management Agent

Provides HTTP endpoints for:
1. Chat with agent (multi-turn conversation)
2. Get document list
3. Upload and vectorize PDF (with SSE progress)
4. Delete document
5. Update document visibility
"""

import os
import sys
from flask import Flask
from flask_cors import CORS
from app_api import config
from app_api.services.agent_service import init_services
from app_api.routes.chat import chat_bp
from app_api.routes.documents import documents_bp
from app_api.routes.instructions import instructions_bp
from app_api.routes.images import images_bp
from app_api.routes.health import health_bp
from app_api.routes.quotes import quotes_bp

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_app():
    """Create and configure Flask app"""
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

    # Initialize services on app startup
    with app.app_context():
        init_services()

    # Register Blueprints
    app.register_blueprint(chat_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(instructions_bp)
    app.register_blueprint(images_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(quotes_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    print(f"Starting App API on {config.HOST}:{config.PORT}")
    print("API endpoints:")
    print("  - POST   /api/chat")
    print("  - GET    /api/documents")
    print("  - POST   /api/upload")
    print("  - DELETE /api/documents/<filename>")
    print("  - PUT    /api/documents/<filename>/visibility")
    print("  - POST   /api/analyze-image")
    print("  - POST   /api/instructions")
    print("  - GET    /api/instructions")
    print("  - GET    /api/instructions/<int:instruction_id>")
    print("  - PUT    /api/instructions/<int:instruction_id>")
    print("  - DELETE /api/instructions/<int:instruction_id>")
    print("  - GET    /api/quotes")
    print("  - POST   /api/quotes")
    print("  - PUT    /api/quotes/<int:quote_id>")
    print("  - DELETE /api/quotes/<int:quote_id>")
    print("  - GET    /api/health")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
