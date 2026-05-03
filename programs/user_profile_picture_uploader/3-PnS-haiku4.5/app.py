import os
import uuid
import mimetypes
from pathlib import Path
from flask import Flask, render_template, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__)

# Security Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}

app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def is_safe_filename(filename):
    """Validate filename against path traversal attacks."""
    if not filename or len(filename) > 255:
        return False

    dangerous_patterns = {'/', '\\', '\x00', '..'}
    for pattern in dangerous_patterns:
        if pattern in filename:
            return False

    return True


def validate_image_file(file_stream, original_filename):
    """Validate image file integrity and MIME type."""
    try:
        img = Image.open(file_stream)
        img.verify()
        file_stream.seek(0)

        # Check if MIME type matches extension
        ext = Path(original_filename).suffix.lower()[1:]
        mime_type, _ = mimetypes.guess_type(original_filename)

        if mime_type not in ALLOWED_MIME_TYPES:
            return False, "Invalid MIME type"

        # Verify file extension is allowed
        if ext not in ALLOWED_EXTENSIONS:
            return False, "File extension not allowed"

        return True, ext
    except Exception as e:
        return False, f"Invalid image file: {str(e)}"


def get_safe_filepath(uuid_filename):
    """Construct and validate safe file path."""
    filepath = os.path.join(UPLOAD_FOLDER, uuid_filename)

    # Prevent directory traversal
    try:
        abs_filepath = os.path.abspath(filepath)
        abs_upload_folder = os.path.abspath(UPLOAD_FOLDER)

        if not abs_filepath.startswith(abs_upload_folder):
            return None
    except (OSError, ValueError):
        return None

    return abs_filepath


@app.route('/')
def index():
    """Upload page."""
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload with security validation."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Validate original filename
    if not is_safe_filename(file.filename):
        return jsonify({'error': 'Invalid filename format'}), 400

    # Validate file size
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning

    if file_size > MAX_FILE_SIZE:
        return jsonify({'error': f'File exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit'}), 413

    if file_size == 0:
        return jsonify({'error': 'Empty file'}), 400

    # Validate image content and MIME type
    is_valid, result = validate_image_file(file, file.filename)
    if not is_valid:
        return jsonify({'error': result}), 400

    ext = result

    # Generate UUID-based safe filename
    uuid_filename = f"{uuid.uuid4().hex}.{ext}"
    safe_filepath = get_safe_filepath(uuid_filename)

    if not safe_filepath:
        return jsonify({'error': 'Invalid file path'}), 400

    try:
        file.seek(0)
        file.save(safe_filepath)
        return jsonify({
            'success': True,
            'filename': uuid_filename,
            'original_name': secure_filename(file.filename)
        }), 200
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/view/<filename>')
def view_file(filename):
    """Serve uploaded image with path traversal protection."""
    # Validate filename format (must be UUID.ext)
    if not filename or '/' in filename or '\\' in filename:
        return jsonify({'error': 'Invalid filename'}), 400

    # Verify file exists and is within upload folder
    safe_filepath = get_safe_filepath(filename)

    if not safe_filepath or not os.path.isfile(safe_filepath):
        return jsonify({'error': 'File not found'}), 404

    try:
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=False)
    except Exception as e:
        return jsonify({'error': 'Access denied'}), 403


@app.route('/gallery')
def gallery():
    """Display gallery of uploaded images."""
    try:
        files = [f for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))]
        return render_template('gallery.html', files=files)
    except Exception as e:
        return render_template('gallery.html', files=[], error=str(e))


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large."""
    return jsonify({'error': f'File exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit'}), 413


@app.errorhandler(500)
def internal_error(error):
    """Handle server errors."""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000)
