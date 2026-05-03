import os
import re
import subprocess
from pathlib import Path
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

LOG_DIR = "/var/log/app/"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_GREP_RESULTS = 1000
FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')


def validate_filename(filename):
    """
    Validate that filename is safe and within the allowed directory.
    Returns (is_valid, resolved_path) tuple.
    """
    if not filename or not isinstance(filename, str):
        return False, None

    if not FILENAME_PATTERN.match(filename):
        return False, None

    requested_path = os.path.join(LOG_DIR, filename)
    resolved_path = os.path.realpath(requested_path)
    log_dir_real = os.path.realpath(LOG_DIR)

    if not resolved_path.startswith(log_dir_real + os.sep) and resolved_path != log_dir_real:
        return False, None

    if not os.path.isfile(resolved_path):
        return False, None

    return True, resolved_path


def get_log_files():
    """List all accessible log files in LOG_DIR."""
    try:
        if not os.path.isdir(LOG_DIR):
            return []

        files = []
        for filename in os.listdir(LOG_DIR):
            filepath = os.path.join(LOG_DIR, filename)
            if os.path.isfile(filepath) and FILENAME_PATTERN.match(filename):
                files.append(filename)
        return sorted(files)
    except Exception:
        return []


@app.route('/')
def index():
    """Render main page."""
    log_files = get_log_files()
    return render_template('index.html', log_files=log_files)


@app.route('/api/logs/<filename>')
def view_log(filename):
    """Retrieve and display log file content."""
    is_valid, resolved_path = validate_filename(filename)

    if not is_valid:
        return jsonify({'error': 'Invalid filename or file not found'}), 400

    try:
        file_size = os.path.getsize(resolved_path)
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': 'File is too large to display'}), 413

        with open(resolved_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        return jsonify({'filename': filename, 'content': content})
    except Exception:
        return jsonify({'error': 'Unable to read file'}), 500


@app.route('/api/search', methods=['POST'])
def search_logs():
    """Search logs using grep with user-provided search term."""
    data = request.get_json()
    filename = data.get('filename', '').strip()
    search_term = data.get('search_term', '').strip()

    if not filename or not search_term:
        return jsonify({'error': 'Filename and search term required'}), 400

    if len(search_term) > 500:
        return jsonify({'error': 'Search term too long'}), 400

    is_valid, resolved_path = validate_filename(filename)

    if not is_valid:
        return jsonify({'error': 'Invalid filename'}), 400

    try:
        result = subprocess.run(
            ['grep', '-n', search_term, resolved_path],
            capture_output=True,
            text=True,
            timeout=5,
            encoding='utf-8',
            errors='ignore'
        )

        lines = result.stdout.split('\n')[:MAX_GREP_RESULTS]
        output = '\n'.join(lines)

        return jsonify({
            'filename': filename,
            'search_term': search_term,
            'results': output,
            'match_count': len([l for l in lines if l.strip()])
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Search timed out'}), 504
    except Exception:
        return jsonify({'error': 'Search failed'}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Server error'}), 500


if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000)
