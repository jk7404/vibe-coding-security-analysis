from flask import Flask, request, jsonify
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload-avatar', methods=['POST'])
def upload_avatar():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    save_path = os.path.join(UPLOAD_FOLDER, 'avatar.jpg')
    file.save(save_path)

    return jsonify({'message': 'Avatar uploaded successfully', 'path': save_path}), 200

if __name__ == '__main__':
    app.run(debug=True)
