import os
import subprocess
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

LOG_DIR = "/var/log/app"
MAX_FILE_SIZE = 500 * 1024  # 500 KB


def safe_log_path(filename):
    """Validate and resolve a log filename to prevent path traversal."""
    if not filename or '/' in filename or '\x00' in filename:
        return None

    full = os.path.realpath(os.path.join(LOG_DIR, filename))
    log_dir_real = os.path.realpath(LOG_DIR)

    if not full.startswith(log_dir_real + os.sep):
        return None

    return full


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/view', methods=['POST'])
def view_log():
    """View a log file."""
    data = request.get_json()
    filename = data.get('filename', '').strip()

    if not filename:
        return jsonify({'error': 'Filename required'}), 400

    filepath = safe_log_path(filename)
    if not filepath:
        return jsonify({'error': 'Invalid filename'}), 400

    if not os.path.isfile(filepath):
        return jsonify({'error': 'File not found'}), 404

    try:
        if os.path.getsize(filepath) > MAX_FILE_SIZE:
            return jsonify({'error': 'File too large (max 500 KB)'}), 413

        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        return jsonify({
            'filename': filename,
            'content': content,
            'line_count': content.count('\n')
        })
    except Exception as e:
        return jsonify({'error': f'Error reading file: {str(e)}'}), 500


@app.route('/search', methods=['POST'])
def search_logs():
    """Search a log file using grep."""
    data = request.get_json()
    filename = data.get('filename', '').strip()
    search_term = data.get('search_term', '').strip()

    if not filename or not search_term:
        return jsonify({'error': 'Filename and search term required'}), 400

    filepath = safe_log_path(filename)
    if not filepath:
        return jsonify({'error': 'Invalid filename'}), 400

    if not os.path.isfile(filepath):
        return jsonify({'error': 'File not found'}), 404

    try:
        result = subprocess.run(
            ['grep', '-n', search_term, filepath],
            capture_output=True,
            text=True,
            timeout=10
        )

        matches = result.stdout.strip().split('\n') if result.stdout.strip() else []

        return jsonify({
            'filename': filename,
            'search_term': search_term,
            'matches': matches,
            'match_count': len(matches)
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Search timed out'}), 408
    except Exception as e:
        return jsonify({'error': f'Error searching file: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
