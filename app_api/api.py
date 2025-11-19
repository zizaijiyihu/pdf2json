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
import threading
from flask import Flask, request, jsonify, Response, stream_with_context
from werkzeug.utils import secure_filename

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from km_agent import KMAgent
from pdf_vectorizer import PDFVectorizer
from app_api import config


# Global instances
km_agent = None
vectorizer = None


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS


def init_services():
    """Initialize KM Agent and PDF Vectorizer"""
    global km_agent, vectorizer

    # Initialize KM Agent
    km_agent = KMAgent(
        openai_api_key=config.OPENAI_CONFIG["api_key"],
        openai_base_url=config.OPENAI_CONFIG["base_url"],
        openai_model=config.OPENAI_CONFIG["model"],
        embedding_url=config.EMBEDDING_CONFIG["url"],
        embedding_api_key=config.EMBEDDING_CONFIG["api_key"],
        qdrant_url=config.QDRANT_CONFIG["url"],
        qdrant_api_key=config.QDRANT_CONFIG["api_key"],
        collection_name=config.COLLECTION_NAME,
        vector_size=config.VECTOR_SIZE,
        verbose=False
    )

    # Initialize PDF Vectorizer
    vectorizer = PDFVectorizer(
        openai_api_key=config.OPENAI_CONFIG["api_key"],
        openai_base_url=config.OPENAI_CONFIG["base_url"],
        openai_model=config.OPENAI_CONFIG["model"],
        embedding_url=config.EMBEDDING_CONFIG["url"],
        embedding_api_key=config.EMBEDDING_CONFIG["api_key"],
        qdrant_url=config.QDRANT_CONFIG["url"],
        qdrant_api_key=config.QDRANT_CONFIG["api_key"],
        collection_name=config.COLLECTION_NAME,
        vector_size=config.VECTOR_SIZE
    )

    # Ensure upload directory exists
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

    print("✓ Services initialized successfully")


def create_app():
    """Create and configure Flask app"""
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

    # Initialize services on app startup
    with app.app_context():
        init_services()


    # ==================== API Endpoint 1: Chat with Agent ====================
    @app.route('/api/chat', methods=['POST'])
    def chat():
        """
        Chat with KM Agent (supports multi-turn conversation)

        Request body:
        {
            "message": "user question",
            "history": [...]  // optional, conversation history
        }

        Response:
        {
            "success": true,
            "response": "agent's response",
            "tool_calls": [...],
            "history": [...]  // updated history for next turn
        }
        """
        try:
            data = request.get_json()

            if not data or 'message' not in data:
                return jsonify({
                    "success": False,
                    "error": "Missing 'message' in request body"
                }), 400

            user_message = data['message']
            history = data.get('history', None)

            # Chat with agent
            result = km_agent.chat(user_message, history)

            return jsonify({
                "success": True,
                "response": result["response"],
                "tool_calls": result["tool_calls"],
                "history": result["history"]
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    # ==================== API Endpoint 2: Get Document List ====================
    @app.route('/api/documents', methods=['GET'])
    def get_documents():
        """
        Get list of documents accessible by user

        Query params:
        - owner: username (default: "hu")

        Response:
        {
            "success": true,
            "documents": [
                {
                    "filename": "doc.pdf",
                    "owner": "hu",
                    "is_public": 0,
                    "point_id": 123,
                    "page_count": 5
                }
            ]
        }
        """
        try:
            owner = request.args.get('owner', config.DEFAULT_USER)

            # Get document list
            documents = vectorizer.get_document_list(owner=owner, verbose=False)

            return jsonify({
                "success": True,
                "owner": owner,
                "count": len(documents),
                "documents": documents
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    # ==================== API Endpoint 3: Upload and Vectorize PDF (SSE) ====================
    @app.route('/api/upload', methods=['POST'])
    def upload_pdf():
        """
        Upload PDF and vectorize with SSE progress updates

        Form data:
        - file: PDF file
        - owner: username (default: "hu")
        - is_public: 0 or 1 (default: 0)

        Response: Server-Sent Events (SSE) stream with progress updates

        Event format:
        data: {"stage": "init", "progress": 0, "message": "..."}
        data: {"stage": "parsing", "progress": 10, "message": "..."}
        ...
        data: {"stage": "completed", "progress": 100, "result": {...}}
        """
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "No file provided"
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "No file selected"
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "error": "Invalid file type. Only PDF files are allowed"
            }), 400

        # Get parameters
        owner = request.form.get('owner', config.DEFAULT_USER)
        is_public = int(request.form.get('is_public', 0))

        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(config.UPLOAD_FOLDER, filename)
        file.save(filepath)

        def generate_progress():
            """Generate SSE progress updates"""
            try:
                # Start vectorization in background
                def vectorize():
                    vectorizer.vectorize_pdf(filepath, owner=owner, is_public=is_public, verbose=False)

                thread = threading.Thread(target=vectorize)
                thread.start()

                # Poll progress and send updates
                last_progress = -1
                while not vectorizer.progress.is_completed and not vectorizer.progress.is_error:
                    progress_data = vectorizer.progress.get()
                    current_progress = progress_data.get('progress_percent', 0)

                    # Only send update if progress changed
                    if current_progress != last_progress:
                        yield f"data: {jsonify(progress_data).get_data(as_text=True)}\n\n"
                        last_progress = current_progress

                    time.sleep(0.5)

                # Wait for thread to complete
                thread.join(timeout=5)

                # Send final result
                if vectorizer.progress.is_completed:
                    final_data = vectorizer.progress.get()
                    yield f"data: {jsonify(final_data).get_data(as_text=True)}\n\n"
                elif vectorizer.progress.is_error:
                    error_data = vectorizer.progress.get()
                    yield f"data: {jsonify(error_data).get_data(as_text=True)}\n\n"

            except Exception as e:
                error_msg = {
                    "stage": "error",
                    "error": str(e),
                    "progress_percent": 0
                }
                yield f"data: {jsonify(error_msg).get_data(as_text=True)}\n\n"

            finally:
                # Clean up uploaded file
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                except:
                    pass

        return Response(
            stream_with_context(generate_progress()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )


    # ==================== API Endpoint 4: Delete Document ====================
    @app.route('/api/documents/<filename>', methods=['DELETE'])
    def delete_document(filename):
        """
        Delete a document by filename and owner

        Query params:
        - owner: username (default: "hu")

        Response:
        {
            "success": true,
            "message": "Document deleted successfully"
        }
        """
        try:
            owner = request.args.get('owner', config.DEFAULT_USER)

            # Delete document
            vectorizer.delete_document(filename, owner, verbose=False)

            return jsonify({
                "success": True,
                "filename": filename,
                "owner": owner,
                "message": "Document deleted successfully"
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    # ==================== API Endpoint 5: Update Document Visibility ====================
    @app.route('/api/documents/<filename>/visibility', methods=['PUT'])
    def update_visibility(filename):
        """
        Update document visibility (public/private)

        Query params:
        - owner: username (default: "hu")

        Request body:
        {
            "is_public": 1  // 0 for private, 1 for public
        }

        Response:
        {
            "success": true,
            "updated_count": 3,
            "filename": "doc.pdf",
            "owner": "hu",
            "is_public": 1
        }
        """
        try:
            data = request.get_json()

            if not data or 'is_public' not in data:
                return jsonify({
                    "success": False,
                    "error": "Missing 'is_public' in request body"
                }), 400

            is_public = int(data['is_public'])

            if is_public not in [0, 1]:
                return jsonify({
                    "success": False,
                    "error": "'is_public' must be 0 or 1"
                }), 400

            owner = request.args.get('owner', config.DEFAULT_USER)

            # Update visibility
            result = vectorizer.update_document_visibility(
                filename=filename,
                owner=owner,
                is_public=is_public,
                verbose=False
            )

            if result['success']:
                return jsonify(result)
            else:
                return jsonify(result), 500

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    # ==================== Health Check ====================
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "services": {
                "km_agent": km_agent is not None,
                "vectorizer": vectorizer is not None
            }
        })


    return app


if __name__ == '__main__':
    app = create_app()
    print(f"Starting App API on {config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
