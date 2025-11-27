import os
import time
import json
import threading
import tempfile
import logging
from io import BytesIO
from flask import Blueprint, request, jsonify, Response, stream_with_context, send_file
import file_repository
from app_api.services.validators import allowed_file
from app_api.services.agent_service import get_vectorizer
from ks_infrastructure import get_current_user

documents_bp = Blueprint('documents', __name__)

@documents_bp.route('/api/documents', methods=['GET'])
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


@documents_bp.route('/api/upload', methods=['POST'])
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
        # Import VectorizationProgress for per-request progress tracking
        from pdf_vectorizer.vectorizer import VectorizationProgress
        
        tmp_filepath = None
        # Create a dedicated progress instance for this upload request
        upload_progress = VectorizationProgress()
        
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

            # 3. Define vectorize function to run in thread
            def vectorize():
                vectorizer = get_vectorizer()
                try:
                    logging.info(f"Starting vectorization for {filename}")
                    vectorizer.vectorize_pdf(
                        tmp_filepath,
                        owner=owner,
                        display_filename=filename,
                        verbose=False,
                        progress_instance=upload_progress  # Pass dedicated progress instance
                    )
                    logging.info(f"Vectorization completed for {filename}")
                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    logging.error(f"Vectorization failed for {filename}: {e}")
                    logging.error(f"Traceback:\n{error_details}")
                    
                    # Update progress with error
                    error_message = f"向量化失败: {str(e)}"
                    upload_progress.update(
                        stage="error",
                        error=error_message,
                        message=error_message
                    )
                finally:
                    # Clean up temporary file
                    if tmp_filepath and os.path.exists(tmp_filepath):
                        try:
                            os.remove(tmp_filepath)
                            logging.info(f"Cleaned up temp file: {tmp_filepath}")
                        except Exception as e:
                            logging.warning(f"Failed to delete temp file {tmp_filepath}: {e}")


            # 4. Start vectorization in background thread
            thread = threading.Thread(target=vectorize)
            thread.start()

            # 4. Poll progress and send SSE updates
            last_page = -1
            last_step = ""
            timeout = 300  # 5 minutes maximum
            start_time = time.time()

            while not upload_progress.is_completed and not upload_progress.is_error:
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
                    if not upload_progress.is_completed and not upload_progress.is_error:
                        error_msg = {
                            "stage": "error",
                            "error": "处理过程异常终止，请查看服务器日志",
                            "progress_percent": 0
                        }
                        yield f"data: {json.dumps(error_msg)}\n\n"
                        break

                progress_data = upload_progress.get()
                current_page = progress_data.get('current_page', 0)
                current_step = progress_data.get('current_step', '')

                # Send update when page changes OR step changes (to show all stages)
                if current_page != last_page or current_step != last_step:
                    yield f"data: {json.dumps(progress_data)}\n\n"
                    last_page = current_page
                    last_step = current_step

                time.sleep(0.3)

            # Wait for thread to complete
            thread.join(timeout=5)

            # 5. Send final result
            if upload_progress.is_completed:
                final_data = upload_progress.get()
                yield f"data: {json.dumps(final_data)}\n\n"
            elif upload_progress.is_error:
                error_data = upload_progress.get()
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


@documents_bp.route('/api/documents/<filename>', methods=['DELETE'])
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
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        owner = get_current_user()
        
        # Debug logging (safe from BrokenPipeError)
        try:
            logger.info(f"Delete document request - Filename: {filename}, Owner: {owner}")
        except:
            pass

        # 1. Delete from vector database (Qdrant)
        try:
            logger.info(f"Deleting from Qdrant: {filename}")
        except:
            pass
        
        vectorizer = get_vectorizer()
        vectorizer.delete_document(filename, owner, verbose=False)

        # 2. Delete file and metadata (MinIO + MySQL)
        try:
            logger.info(f"Deleting from MinIO and MySQL: {filename}")
        except:
            pass
        result = file_repository.delete_file(
            owner=owner,
            filename=filename,
            bucket='kms'
        )
        try:
            logger.info(f"Delete result: {result}")
        except:
            pass

        return jsonify({
            "success": True,
            "filename": filename,
            "owner": owner,
            "message": "Document deleted successfully"
        })

    except Exception as e:
        # Safe error logging that won't raise BrokenPipeError
        try:
            logger.error(f"Delete error: {e}", exc_info=True)
        except:
            pass
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@documents_bp.route('/api/documents/<filename>/visibility', methods=['PUT'])
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


@documents_bp.route('/api/documents/<filename>/content', methods=['GET'])
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
