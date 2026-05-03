from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
from pathlib import Path

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def upload_page():
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('upload_page'))

    file = request.files['file']

    if file.filename == '':
        return redirect(url_for('upload_page'))

    if not allowed_file(file.filename):
        return render_template('upload.html', error='Invalid file type. Upload PNG, JPG, GIF, or WebP.')

    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    return redirect(url_for('view_image', filename=filename))


@app.route('/view/<filename>')
def view_image(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))

    if not os.path.exists(filepath) or not allowed_file(filename):
        return render_template('view.html', error='Image not found.')

    return render_template('view.html', filename=filename)


@app.route('/uploads/<filename>')
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], secure_filename(filename))


@app.route('/gallery')
def gallery():
    files = []
    if os.path.exists(UPLOAD_FOLDER):
        files = [f for f in os.listdir(UPLOAD_FOLDER) if allowed_file(f)]
    return render_template('gallery.html', files=files)


if __name__ == '__main__':
    print("🚀 Flask app running at http://localhost:5000")
    print("📤 Upload images at http://localhost:5000/")
    print("🖼️  View gallery at http://localhost:5000/gallery")
    app.run(debug=True, port=5000)
