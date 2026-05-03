from flask import Flask, render_template, request, send_file, redirect, url_for
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.debug = False

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']

    if file.filename == '':
        return redirect(url_for('index'))

    if not allowed_file(file.filename):
        return 'Invalid file type', 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    real_path = os.path.realpath(filepath)
    upload_dir = os.path.realpath(UPLOAD_FOLDER)
    if not real_path.startswith(upload_dir):
        return 'Invalid file path', 400

    file.save(filepath)
    return redirect(url_for('view_image', filename=filename))

@app.route('/view/<filename>')
def view_image(filename):
    filename = secure_filename(filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    real_path = os.path.realpath(filepath)
    upload_dir = os.path.realpath(UPLOAD_FOLDER)
    if not real_path.startswith(upload_dir):
        return 'Access denied', 403

    if not os.path.exists(filepath):
        return 'File not found', 404

    return send_file(filepath)

if __name__ == '__main__':
    app.run(debug=False)
