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
import json
import threading
import tempfile
from io import BytesIO
from flask import Flask, request, jsonify, Response, stream_with_context, send_file
from werkzeug.utils import secure_filename

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from km_agent import KMAgent
from pdf_vectorizer import PDFVectorizer
import file_repository
from tmp_image_repository import analyze_temp_image
from app_api import config
from ks_infrastructure import get_current_user


# Global instances
km_agent = None
vectorizer = None
km_agent_cache = {}  # Cache KMAgent instances per owner


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS


def allowed_image(filename):
    """Check if file is an allowed image type"""
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def get_or_create_km_agent(owner: str):
    """
    Get or create KMAgent instance for specific owner
    
    Caches instances to avoid recreating on every request
    """
    global km_agent_cache
    
    if owner not in km_agent_cache:
        km_agent_cache[owner] = KMAgent(verbose=True, owner=owner)
    
    return km_agent_cache[owner]


def init_services():
    """Initialize KM Agent and PDF Vectorizer"""
    global km_agent, vectorizer

    # Initialize KM Agent (uses ks_infrastructure, no parameters needed)
    km_agent = KMAgent(verbose=True)

    # Initialize PDF Vectorizer (uses ks_infrastructure, defaults from pdf_vectorizer)
    vectorizer = PDFVectorizer()

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
        Chat with KM Agent using streaming (SSE)

        Request body:
        {
            "message": "user question",
            "history": [...]  // optional, conversation history
        }

        Note: User identification is handled server-side via get_current_user()

        Response: Server-Sent Events (SSE) stream
        Event types:
        - content: Streaming response content
        - tool_call: Tool execution notification
        - done: Final result with history
        """
        try:
            data = request.get_json()
            print(f"\n[DEBUG] Received chat request: {data}", flush=True)

            if not data or 'message' not in data:
                return jsonify({
                    "success": False,
                    "error": "Missing 'message' in request body"
                }), 400

            user_message = data['message']
            history = data.get('history', None)
            owner = get_current_user() # Always use trusted user from server
            print(f"[DEBUG] Using owner: {owner}", flush=True)

            # Get or create KMAgent instance for the specific owner
            km_agent_instance = get_or_create_km_agent(owner)
            
            # Reload instructions to ensure we have the latest ones
            km_agent_instance.reload_instructions()

            def generate_stream():
                """Generate SSE stream from agent"""
                try:
                    for chunk in km_agent_instance.chat_stream(user_message, history):
                        yield f"data: {json.dumps(chunk)}\n\n"
                except Exception as e:
                    error_chunk = {
                        "type": "error",
                        "data": {"error": str(e)}
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"

            return Response(
                stream_with_context(generate_stream()),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'X-Accel-Buffering': 'no'
                }
            )

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

        Note: User identification is handled server-side via get_current_user()

        Response:
        {
            "success": true,
            "documents": [
                {
                    "filename": "doc.pdf",
                    "owner": "huxiaoxiao",
                    "is_public": 0,
                    "file_size": 12345,
                    "created_at": "2025-01-01T12:00:00",
                    "content_type": "application/pdf"
                }
            ]
        }
        """
        try:
            owner = get_current_user()

            # Get document list from file_repository
            files = file_repository.get_owner_file_list(
                owner=owner,
                include_public=True
            )

            # Format response
            documents = [
                {
                    "filename": f["filename"],
                    "owner": f["owner"],
                    "is_public": f["is_public"],
                    "file_size": f["file_size"],
                    "created_at": f["created_at"].isoformat() if f.get("created_at") else None,
                    "content_type": f.get("content_type")
                }
                for f in files
            ]

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
        - is_public: 0 or 1 (default: 0)

        Note: User identification is handled server-side via get_current_user()

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
        owner = get_current_user()
        is_public = int(request.form.get('is_public', 0))
        filename = file.filename

        def generate_progress():
            """Generate SSE progress updates"""
            tmp_filepath = None
            try:
                # 1. Upload to MinIO + save metadata to MySQL
                file.seek(0)
                file_repository.upload_file(
                    username=owner,
                    filename=filename,
                    file_data=file,
                    bucket='kms',
                    content_type='application/pdf',
                    is_public=is_public
                )

                # 2. Download from MinIO to temporary file
                content = file_repository.get_file(
                    username=owner,
                    filename=filename,
                    bucket='kms'
                )

                if not content:
                    raise Exception("Failed to retrieve uploaded file from MinIO")

                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(content)
                    tmp_filepath = tmp_file.name

                # 3. Vectorize using temporary file
                def vectorize():
                    try:
                        vectorizer.vectorize_pdf(
                            tmp_filepath,
                            owner=owner,
                            display_filename=filename,
                            verbose=False
                        )
                    finally:
                        # Clean up temporary file
                        if tmp_filepath and os.path.exists(tmp_filepath):
                            try:
                                os.remove(tmp_filepath)
                            except Exception as e:
                                print(f"Warning: Failed to delete temp file {tmp_filepath}: {e}")

                thread = threading.Thread(target=vectorize)
                thread.start()

                # 4. Poll progress and send SSE updates
                last_page = -1
                timeout = 300  # 5 minutes maximum
                start_time = time.time()

                while not vectorizer.progress.is_completed and not vectorizer.progress.is_error:
                    # Check timeout
                    if time.time() - start_time > timeout:
                        error_msg = {
                            "stage": "error",
                            "error": "处理超时，请检查文档大小或稍后重试",
                            "progress_percent": 0
                        }
                        yield f"data: {json.dumps(error_msg)}\n\n"
                        break

                    # Check if thread is still alive
                    if not thread.is_alive():
                        # Thread died without setting completion/error status
                        if not vectorizer.progress.is_completed and not vectorizer.progress.is_error:
                            error_msg = {
                                "stage": "error",
                                "error": "处理过程异常终止，请查看服务器日志",
                                "progress_percent": 0
                            }
                            yield f"data: {json.dumps(error_msg)}\n\n"
                            break

                    progress_data = vectorizer.progress.get()
                    current_page = progress_data.get('current_page', 0)

                    # Send update when page changes
                    if current_page != last_page:
                        yield f"data: {json.dumps(progress_data)}\n\n"
                        last_page = current_page

                    time.sleep(0.3)

                # Wait for thread to complete
                thread.join(timeout=5)

                # 5. Send final result
                if vectorizer.progress.is_completed:
                    final_data = vectorizer.progress.get()
                    yield f"data: {json.dumps(final_data)}\n\n"
                elif vectorizer.progress.is_error:
                    error_data = vectorizer.progress.get()
                    yield f"data: {json.dumps(error_data)}\n\n"

            except Exception as e:
                error_msg = {
                    "stage": "error",
                    "error": str(e),
                    "progress_percent": 0
                }
                yield f"data: {json.dumps(error_msg)}\n\n"
                # Clean up temp file on error
                if tmp_filepath and os.path.exists(tmp_filepath):
                    try:
                        os.remove(tmp_filepath)
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
        Delete a document by filename

        Note: User identification is handled server-side via get_current_user()

        Response:
        {
            "success": true,
            "message": "Document deleted successfully"
        }
        """
        try:
            owner = get_current_user()
            
            # Debug logging
            print(f"\n[DEBUG] Delete document request:", flush=True)
            print(f"  - Filename (raw): {repr(filename)}", flush=True)
            print(f"  - Filename (str): {filename}", flush=True)
            print(f"  - Owner: {owner}", flush=True)
            print(f"  - Filename type: {type(filename)}", flush=True)
            print(f"  - Filename bytes: {filename.encode('utf-8')}", flush=True)

            # 1. Delete from vector database (Qdrant)
            print(f"[DEBUG] Deleting from Qdrant...", flush=True)
            vectorizer.delete_document(filename, owner, verbose=True)

            # 2. Delete file and metadata (MinIO + MySQL)
            print(f"[DEBUG] Deleting from MinIO and MySQL...", flush=True)
            result = file_repository.delete_file(
                owner=owner,
                filename=filename,
                bucket='kms'
            )
            print(f"[DEBUG] Delete result: {result}", flush=True)

            return jsonify({
                "success": True,
                "filename": filename,
                "owner": owner,
                "message": "Document deleted successfully"
            })

        except Exception as e:
            print(f"[DEBUG] Delete error: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    # ==================== API Endpoint 5: Update Document Visibility ====================
    @app.route('/api/documents/<filename>/visibility', methods=['PUT'])
    def update_visibility(filename):
        """
        Update document visibility (public/private)

        Note: User identification is handled server-side via get_current_user()

        Request body:
        {
            "is_public": 1  // 0 for private, 1 for public
        }

        Response:
        {
            "success": true,
            "filename": "doc.pdf",
            "owner": "huxiaoxiao",
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

            owner = get_current_user()

            # Update visibility using file_repository
            success = file_repository.set_file_public(
                owner=owner,
                filename=filename,
                is_public=is_public
            )

            if success:
                return jsonify({
                    "success": True,
                    "filename": filename,
                    "owner": owner,
                    "is_public": is_public,
                    "message": "Visibility updated successfully"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "File not found or permission denied"
                }), 404

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    # ==================== API Endpoint 6: Get PDF File Content ====================
    @app.route('/api/documents/<filename>/content', methods=['GET'])
    def get_document_content(filename):
        """
        Get PDF file content for viewing

        Note: User identification is handled server-side via get_current_user()

        Returns:
            PDF file content or 404 if not found
        """
        try:
            owner = get_current_user()

            # Get file from MinIO
            content = file_repository.get_file(
                username=owner,
                filename=filename,
                bucket='kms'
            )

            if content:
                return send_file(
                    BytesIO(content),
                    mimetype='application/pdf',
                    as_attachment=False,
                    download_name=filename
                )
            else:
                return jsonify({
                    "success": False,
                    "error": "File not found"
                }), 404

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    # ==================== API Endpoint 7: Upload and Analyze Image ====================
    @app.route('/api/analyze-image', methods=['POST'])
    def analyze_image():
        """
        Upload image to tmp bucket and analyze with vision service

        Form data:
        - file: Image file (png, jpg, jpeg, gif, bmp, webp)
        - username: username (default: "system")
        - prompt: Analysis prompt (optional, uses default if not provided)

        Response:
        {
            "success": true,
            "image_url": "http://...",
            "analysis": "图片分析结果"
        }
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

        if not allowed_image(file.filename):
            return jsonify({
                "success": False,
                "error": "Invalid file type. Allowed types: png, jpg, jpeg, gif, bmp, webp"
            }), 400

        # Get parameters
        username = get_current_user()
        prompt = request.form.get('prompt', None)

        try:
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
                file.save(tmp_file.name)
                tmp_filepath = tmp_file.name

            try:
                # Analyze image
                kwargs = {
                    'image_path': tmp_filepath,
                    'username': username,
                    'custom_filename': file.filename
                }
                if prompt:
                    kwargs['prompt'] = prompt

                result = analyze_temp_image(**kwargs)

                return jsonify(result)

            finally:
                # Clean up temporary file
                if os.path.exists(tmp_filepath):
                    try:
                        os.remove(tmp_filepath)
                    except Exception as e:
                        print(f"Warning: Failed to delete temp file {tmp_filepath}: {e}")

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


    # ==================== API Endpoint 8: Create Instruction ====================
    @app.route('/api/instructions', methods=['POST'])
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
            from instruction_repository import create_instruction
            
            data = request.json
            owner = get_current_user()
            print(f"[DEBUG] create_user_instruction: Using owner {owner}", flush=True)

            content = data.get('content')
            priority = data.get('priority', 0)
            
            # if not owner:
            #     return jsonify({"success": False, "error": "owner参数不能为空"}), 400
            
            if not content:
                return jsonify({"success": False, "error": "content参数不能为空"}), 400
            
            result = create_instruction(owner, content, priority)
            result['message'] = "指示创建成功"
            return jsonify(result)
            
        except ValueError as e:
            return jsonify({"success": False, "error": str(e)}), 400
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # ==================== API Endpoint 9: Get Instructions ====================
    @app.route('/api/instructions', methods=['GET'])
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
            from instruction_repository import get_all_instructions
            
            owner = get_current_user()
            print(f"[DEBUG] get_user_instructions: Using owner {owner}", flush=True)

            include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
            
            print(f"[DEBUG] Getting instructions for owner: {owner}", flush=True)
            
            # if not owner:
            #     return jsonify({"success": False, "error": "owner参数不能为空"}), 400
            
            instructions = get_all_instructions(owner, include_inactive)
            return jsonify({
                "success": True,
                "instructions": instructions
            })
            
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # ==================== API Endpoint 9.5: Get Instruction Detail ====================
    @app.route('/api/instructions/<int:instruction_id>', methods=['GET'])
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
            from instruction_repository import get_instruction_by_id
            
            owner = get_current_user()
            
            # if not owner:
            #     return jsonify({"success": False, "error": "owner参数不能为空"}), 400
            
            instruction = get_instruction_by_id(instruction_id, owner)
            return jsonify({
                "success": True,
                "instruction": instruction
            })
            
        except ValueError as e:
            return jsonify({"success": False, "error": str(e)}), 404
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # ==================== API Endpoint 10: Update Instruction ====================
    @app.route('/api/instructions/<int:instruction_id>', methods=['PUT'])
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
            from instruction_repository import update_instruction
            
            data = request.json
            owner = get_current_user()
            
            # if not owner:
            #     return jsonify({"success": False, "error": "owner参数不能为空"}), 400
            
            content = data.get('content')
            is_active = data.get('is_active')
            priority = data.get('priority')
            
            result = update_instruction(
                instruction_id=instruction_id,
                owner=owner,
                content=content,
                is_active=is_active,
                priority=priority
            )
            return jsonify(result)
            
        except ValueError as e:
            return jsonify({"success": False, "error": str(e)}), 400
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # ==================== API Endpoint 11: Delete Instruction ====================
    @app.route('/api/instructions/<int:instruction_id>', methods=['DELETE'])
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
            from instruction_repository import delete_instruction
            
            data = request.json
            owner = get_current_user()
            
            # if not owner:
            #     return jsonify({"success": False, "error": "owner参数不能为空"}), 400
            
            result = delete_instruction(instruction_id, owner)
            return jsonify(result)
            
        except ValueError as e:
            return jsonify({"success": False, "error": str(e)}), 400
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

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
    print("  - GET    /api/documents/<filename>/content")
    print("  - POST   /api/analyze-image")
    print("  - POST   /api/instructions")
    print("  - GET    /api/instructions")
    print("  - GET    /api/instructions/<int:instruction_id>")
    print("  - PUT    /api/instructions/<int:instruction_id>")
    print("  - DELETE /api/instructions/<int:instruction_id>")
    print("  - GET    /api/health")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
