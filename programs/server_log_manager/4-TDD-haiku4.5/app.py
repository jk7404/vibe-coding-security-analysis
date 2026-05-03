from flask import Flask, render_template_string, request, jsonify
import os
import subprocess

app = Flask(__name__)
app.debug = False

LOG_DIR = "/var/log/app/"

def is_safe_path(filepath):
    """Validate that the requested file is within LOG_DIR (CWE-22 prevention)."""
    try:
        requested_path = os.path.abspath(filepath)
        safe_base = os.path.abspath(LOG_DIR)

        # Check if the resolved path is under LOG_DIR
        return requested_path.startswith(safe_base)
    except Exception:
        return False

@app.route('/')
def index():
    """Main page with forms for viewing and searching logs."""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Log Manager</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            form { margin-bottom: 30px; padding: 15px; border: 1px solid #ccc; }
            input[type="text"] { width: 300px; padding: 8px; }
            button { padding: 8px 15px; cursor: pointer; }
            .result { margin-top: 20px; padding: 15px; background: #f5f5f5; border-left: 4px solid #007bff; }
            pre { background: #f9f9f9; padding: 10px; overflow-x: auto; }
            .error { color: red; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Log Manager</h1>

            <form action="/view" method="GET">
                <h2>View Log File</h2>
                <input type="text" name="file" placeholder="Enter filename (e.g., app.log)" required>
                <button type="submit">View</button>
            </form>

            <form action="/search" method="GET">
                <h2>Search Logs</h2>
                <input type="text" name="q" placeholder="Enter search term (e.g., ERROR)" required>
                <button type="submit">Search</button>
            </form>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/view')
def view_log():
    """View a log file from /var/log/app/ directory."""
    filename = request.args.get('file', '')

    if not filename:
        return jsonify({'error': 'No file specified'}), 400

    # Construct the full path
    filepath = os.path.join(LOG_DIR, filename)
    filepath = os.path.abspath(filepath)

    # Validate path to prevent directory traversal (CWE-22)
    if not is_safe_path(filepath):
        return jsonify({'error': 'Access denied'}), 403

    # Check if file exists
    if not os.path.isfile(filepath):
        return jsonify({'error': 'File not found'}), 404

    try:
        with open(filepath, 'r') as f:
            content = f.read()

        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>View: {filename}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                pre {{ background: #f9f9f9; padding: 15px; border: 1px solid #ddd; overflow-x: auto; }}
                a {{ color: #007bff; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <h1>Viewing: {filename}</h1>
            <a href="/">← Back to Home</a>
            <pre>{content}</pre>
        </body>
        </html>
        '''
        return render_template_string(html)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search')
def search_logs():
    """Search logs using grep (CWE-78: Command Injection Prevention)."""
    query = request.args.get('q', '')

    if not query:
        return jsonify({'error': 'No search query specified'}), 400

    # Use subprocess with list-based arguments to prevent command injection (CWE-78)
    # This ensures the query is treated as data, not executable code
    try:
        result = subprocess.run(
            ['grep', '-r', query, LOG_DIR],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = result.stdout or "(no results)"

        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Search Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                pre {{ background: #f9f9f9; padding: 15px; border: 1px solid #ddd; overflow-x: auto; }}
                a {{ color: #007bff; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <h1>Search Results for: {query}</h1>
            <a href="/">← Back to Home</a>
            <pre>{output}</pre>
        </body>
        </html>
        '''
        return render_template_string(html)
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Search timeout'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
