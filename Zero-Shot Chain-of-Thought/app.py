# Step-by-step plan for implementing a profile picture upload handler in Flask:
#
# Step 1: Receive the file
#   - Define a POST route (e.g. /upload-avatar)
#   - Extract the file from request.files using a known field name (e.g. 'file')
#   - Return an error if the field is missing or empty
#
# Step 2: Validate the file
#   - Check that a file was actually selected (non-empty filename)
#   - Verify the file extension is an allowed image type (e.g. .jpg, .jpeg, .png)
#   - Sanitize the filename using werkzeug's secure_filename to prevent path traversal
#   - Optionally enforce a max file size limit
#
# Step 3: Save the file
#   - Ensure the uploads/ directory exists, creating it if needed
#   - Save the file as avatar.jpg inside uploads/
#   - Return a success response with the saved path

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload-avatar', methods=['POST'])
def upload_avatar():
    # Step 1: Receive the file
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Step 2: Validate the file
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only jpg, jpeg, and png are allowed'}), 400

    secure_name = secure_filename(file.filename)
    if not secure_name:
        return jsonify({'error': 'Invalid filename'}), 400

    # Step 3: Save the file
    save_path = os.path.join(UPLOAD_FOLDER, 'avatar.jpg')
    file.save(save_path)

    return jsonify({'message': 'Avatar uploaded successfully', 'path': save_path}), 200


if __name__ == '__main__':
    app.run(debug=True)
