from flask import Flask, render_template_string, request, jsonify
import os
import subprocess
from pathlib import Path

app = Flask(__name__)

LOG_DIR = "/var/log/app"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB limit to prevent loading huge files

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Log Viewer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: monospace; background: #1e1e1e; color: #d4d4d4; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #569cd6; margin-bottom: 30px; }
        .section { background: #252526; border-radius: 5px; padding: 20px; margin-bottom: 20px; }
        .section h2 { color: #4ec9b0; margin-bottom: 15px; font-size: 16px; }
        input, button {
            padding: 10px;
            background: #3e3e42;
            border: 1px solid #555;
            color: #d4d4d4;
            border-radius: 3px;
            font-family: monospace;
        }
        input { flex: 1; min-width: 200px; }
        button { background: #007acc; cursor: pointer; border: none; margin-left: 5px; }
        button:hover { background: #005a9e; }
        .form-group { display: flex; gap: 5px; margin-bottom: 15px; }
        #output {
            background: #1e1e1e;
            border: 1px solid #555;
            padding: 15px;
            border-radius: 3px;
            max-height: 600px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 13px;
            line-height: 1.5;
        }
        .error { color: #f48771; }
        .success { color: #6a9955; }
        .info { color: #9cdcfe; }
        .loading { color: #ce9178; }
        button:disabled { background: #555; cursor: not-allowed; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 Log Viewer</h1>

        <div class="section">
            <h2>View Log File</h2>
            <div class="form-group">
                <input type="text" id="filename" placeholder="e.g., app.log, error.log" />
                <button onclick="viewFile()">View</button>
            </div>
        </div>

        <div class="section">
            <h2>Search Logs (grep)</h2>
            <div class="form-group">
                <input type="text" id="searchTerm" placeholder="e.g., ERROR, WARNING" />
                <button onclick="searchLogs()">Search</button>
            </div>
        </div>

        <div class="section">
            <h2>Output</h2>
            <div id="output">Ready to view or search logs...</div>
        </div>
    </div>

    <script>
        function updateOutput(content, type = 'info') {
            const output = document.getElementById('output');
            output.textContent = content;
            output.className = type;
        }

        function viewFile() {
            const filename = document.getElementById('filename').value.trim();
            if (!filename) {
                updateOutput('❌ Please enter a filename', 'error');
                return;
            }

            updateOutput('Loading...', 'loading');
            fetch('/api/view', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename })
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    updateOutput('❌ ' + data.error, 'error');
                } else {
                    updateOutput(data.content, 'info');
                }
            })
            .catch(e => updateOutput('❌ Request failed: ' + e.message, 'error'));
        }

        function searchLogs() {
            const term = document.getElementById('searchTerm').value.trim();
            if (!term) {
                updateOutput('❌ Please enter a search term', 'error');
                return;
            }

            updateOutput('Searching...', 'loading');
            fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ term })
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    updateOutput('❌ ' + data.error, 'error');
                } else {
                    const lines = data.results.length;
                    const header = `✓ Found ${lines} matching lines:\n\n`;
                    updateOutput(header + data.results.join('\n'), 'success');
                }
            })
            .catch(e => updateOutput('❌ Request failed: ' + e.message, 'error'));
        }

        document.getElementById('filename').addEventListener('keypress', e => {
            if (e.key === 'Enter') viewFile();
        });
        document.getElementById('searchTerm').addEventListener('keypress', e => {
            if (e.key === 'Enter') searchLogs();
        });
    </script>
</body>
</html>
"""

def is_safe_path(requested_path):
    """Prevent path traversal attacks."""
    try:
        real_log_dir = Path(LOG_DIR).resolve()
        requested_full = (real_log_dir / requested_path).resolve()
        return str(requested_full).startswith(str(real_log_dir))
    except:
        return False

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/view', methods=['POST'])
def view_log():
    data = request.get_json()
    filename = data.get('filename', '').strip()

    if not filename:
        return jsonify({'error': 'Filename is required'}), 400

    if not is_safe_path(filename):
        return jsonify({'error': 'Invalid path or access denied'}), 403

    filepath = os.path.join(LOG_DIR, filename)

    try:
        if not os.path.isfile(filepath):
            return jsonify({'error': f'File not found: {filename}'}), 404

        file_size = os.path.getsize(filepath)
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': f'File too large ({file_size / 1024 / 1024:.1f}MB). Max: {MAX_FILE_SIZE / 1024 / 1024:.1f}MB'}), 413

        with open(filepath, 'r', errors='ignore') as f:
            content = f.read()

        return jsonify({'content': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search_logs():
    data = request.get_json()
    term = data.get('term', '').strip()

    if not term:
        return jsonify({'error': 'Search term is required'}), 400

    if not os.path.isdir(LOG_DIR):
        return jsonify({'error': f'Log directory not found: {LOG_DIR}'}), 404

    try:
        result = subprocess.run(
            ['grep', '-r', term, LOG_DIR],
            capture_output=True,
            text=True,
            timeout=10
        )

        lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
        lines = [line for line in lines if line]  # Remove empty lines
        lines = lines[:1000]  # Cap at 1000 results

        return jsonify({'results': lines})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Search timed out'}), 408
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000)
