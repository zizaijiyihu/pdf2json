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
import time
import traceback
import logging
from flask import Flask, request, g
from flask_cors import CORS
from app_api import config
from app_api.services.agent_service import init_services
from app_api.routes.chat import chat_bp
from app_api.routes.documents import documents_bp
from app_api.routes.instructions import instructions_bp
from app_api.routes.images import images_bp
from app_api.routes.health import health_bp
from app_api.routes.quotes import quotes_bp
from app_api.routes.conversations import conversations_bp
from app_api.routes.reminders import reminders_bp

# Configure logging with enhanced format for call tracking
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enable debug level for conversation-related modules
logging.getLogger('conversation_repository.db').setLevel(logging.DEBUG)
logging.getLogger('km_agent.conversation_manager').setLevel(logging.DEBUG)
logging.getLogger('app_api.routes.conversations').setLevel(logging.DEBUG)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_app():
    """Create and configure Flask app"""
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

    # Enable CORS for cross-origin requests
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:8080", "http://127.0.0.1:8080"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Request tracking middleware
    @app.before_request
    def log_request_start():
        """在请求开始前记录日志"""
        g.start_time = time.time()

        logger.info("="*80)
        logger.info(f"[请求开始] {request.method} {request.path}")

        # 记录请求参数
        if request.args:
            logger.info(f"[URL参数] {dict(request.args)}")

        # 记录请求体 (非文件上传)
        if request.method in ['POST', 'PUT', 'PATCH']:
            if request.is_json:
                try:
                    data = request.get_json()
                    # 隐藏敏感信息
                    if isinstance(data, dict):
                        safe_data = {k: ('***' if 'password' in k.lower() or 'token' in k.lower() else v)
                                    for k, v in data.items()}
                        logger.info(f"[请求体] {safe_data}")
                except Exception as e:
                    logger.debug(f"无法解析请求体: {e}")
            elif 'multipart/form-data' not in request.content_type:
                logger.info(f"[请求体] Content-Type: {request.content_type}")

        logger.info("="*80)

    @app.after_request
    def log_request_end(response):
        """在请求结束后记录日志"""
        duration = time.time() - g.get('start_time', time.time())

        logger.info("-"*80)
        logger.info(f"[请求结束] {request.method} {request.path}")
        logger.info(f"[状态码] {response.status_code}")
        logger.info(f"[耗时] {duration:.3f}秒")

        # 记录响应内容 (非流式响应)
        if response.content_type and 'text/event-stream' not in response.content_type:
            if response.is_json:
                try:
                    resp_data = response.get_json()
                    if isinstance(resp_data, dict):
                        # 简化输出，只显示关键字段
                        if 'success' in resp_data:
                            response_info = f"[响应] success={resp_data.get('success')}"
                            if 'error' in resp_data:
                                response_info += f", error={resp_data.get('error')}"
                            if 'message' in resp_data:
                                response_info += f", message={resp_data.get('message')}"
                            logger.info(response_info)
                except Exception as e:
                    logger.debug(f"无法解析响应体: {e}")
        else:
            logger.info("[响应] 流式响应 (SSE)")

        logger.info("-"*80)
        return response

    @app.errorhandler(413)
    def handle_file_too_large(e):
        """处理文件过大错误"""
        logger.warning(f"[文件过大] {request.method} {request.path}")
        max_size = app.config.get('MAX_CONTENT_LENGTH', 0) / (1024 * 1024)
        return {
            'success': False,
            'error': 'FILE_TOO_LARGE',
            'message': f'文件大小超过限制（最大 {max_size:.0f}MB）'
        }, 413

    @app.errorhandler(Exception)
    def handle_exception(e):
        """捕获并处理所有异常"""
        duration = time.time() - g.get('start_time', time.time())

        logger.error("!"*80)
        logger.error(f"[异常] {request.method} {request.path}")
        logger.error(f"[异常类型] {type(e).__name__}")
        logger.error(f"[异常信息] {str(e)}")
        logger.error(f"[耗时] {duration:.3f}秒")
        logger.error("[异常追踪]")
        logger.error(traceback.format_exc())
        logger.error("!"*80)

        # 区分不同类型的错误
        error_type = type(e).__name__
        error_message = str(e)

        # 端口冲突错误
        if 'Address already in use' in error_message or 'OSError' in error_type:
            return {
                'success': False,
                'error': 'PORT_CONFLICT',
                'message': f'端口已被占用：{error_message}',
                'details': {'type': error_type}
            }, 500

        # 数据库错误
        if any(db_err in error_type for db_err in ['OperationalError', 'IntegrityError', 'DatabaseError', 'MySQLError']):
            return {
                'success': False,
                'error': 'DATABASE_ERROR',
                'message': f'数据库错误：{error_message}',
                'details': {'type': error_type}
            }, 500

        # 业务逻辑错误 (ValueError, KeyError 等)
        if error_type in ['ValueError', 'KeyError', 'AttributeError']:
            return {
                'success': False,
                'error': 'BUSINESS_LOGIC_ERROR',
                'message': f'业务逻辑错误：{error_message}',
                'details': {'type': error_type}
            }, 400

        # 文件系统错误
        if error_type in ['FileNotFoundError', 'PermissionError', 'IOError']:
            return {
                'success': False,
                'error': 'FILE_SYSTEM_ERROR',
                'message': f'文件系统错误：{error_message}',
                'details': {'type': error_type}
            }, 500

        # 其他未知错误
        return {
            'success': False,
            'error': 'INTERNAL_SERVER_ERROR',
            'message': f'内部服务器错误：{error_message}',
            'details': {'type': error_type}
        }, 500

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
    app.register_blueprint(conversations_bp)
    app.register_blueprint(reminders_bp)

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
    print("  - GET    /api/reminders")
    print("  - POST   /api/reminders")
    print("  - GET    /api/reminders/<int:reminder_id>")
    print("  - PUT    /api/reminders/<int:reminder_id>")
    print("  - DELETE /api/reminders/<int:reminder_id>")
    print("  - GET    /api/health")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
