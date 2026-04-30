import re
import uuid
from pathlib import Path
from io import BytesIO

from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename

from utils.file_validation import validate_extension, validate_magic_bytes, reencode_image

upload_bp = Blueprint('upload', __name__)

FILENAME_REGEX = re.compile(r'^[a-f0-9\-]+\.(jpg|jpeg|png|gif|webp)$', re.IGNORECASE)


@upload_bp.route('/upload', methods=['POST'])
def upload_avatar():
    """
    Handle avatar upload with security-first validation pipeline.
    Returns JSON with the new UUID filename on success.
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file field in request'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file or not hasattr(file, 'stream'):
            return jsonify({'error': 'Invalid file object'}), 400

        ext = validate_extension(file.filename)

        if not validate_magic_bytes(file.stream, ext):
            return jsonify({'error': 'File signature does not match extension'}), 400

        filename = f"{uuid.uuid4()}.jpg"
        upload_path = Path(current_app.config['UPLOAD_FOLDER']) / filename

        reencode_image(file.stream, upload_path)

        upload_path.chmod(0o644)

        return jsonify({'filename': filename}), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': 'File upload failed'}), 500


@upload_bp.route('/avatars/<filename>', methods=['GET'])
def serve_avatar(filename):
    """
    Serve an avatar by UUID filename. Strict regex validation prevents path traversal.
    """
    if not FILENAME_REGEX.match(filename):
        return jsonify({'error': 'Invalid filename format'}), 400

    file_path = Path(current_app.config['UPLOAD_FOLDER']) / filename

    if not file_path.exists() or not file_path.is_file():
        return jsonify({'error': 'Avatar not found'}), 404

    if not file_path.resolve().parent == Path(current_app.config['UPLOAD_FOLDER']).resolve():
        return jsonify({'error': 'Invalid file path'}), 400

    try:
        return send_file(
            file_path,
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=None
        )
    except Exception as e:
        current_app.logger.error(f"Serve error: {str(e)}")
        return jsonify({'error': 'Failed to serve avatar'}), 500


@upload_bp.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large (max 5 MB)'}), 413
