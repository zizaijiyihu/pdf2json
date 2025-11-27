import os
import tempfile
from flask import Blueprint, request, jsonify
from app_api.services.validators import allowed_image
from ks_infrastructure import get_current_user
from tmp_image_repository import analyze_temp_image

images_bp = Blueprint('images', __name__)

@images_bp.route('/api/analyze-image', methods=['POST'])
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
