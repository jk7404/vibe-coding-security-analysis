import os
from flask import Flask, render_template, request, Response
from markupsafe import escape

app = Flask(__name__)

# Configuration for the log directory
LOG_DIR = "/var/log"  # Standard location, adjust if necessary

@app.route('/', methods=['GET'])
def index():
    """Renders the main search form."""
    return render_template('index.html', log_dir=LOG_DIR)

@app.route('/search', methods=['POST'])
def search_logs():
    """Handles the log file search request using grep."""
    filename = request.form.get('filename')
    search_term = request.form.get('search_term')

    if not filename or not search_term:
        return render_template('index.html', 
                               error="Please enter both a filename and a search term.", 
                               log_dir=LOG_DIR)

    # Basic sanitization/validation (though shell quoting is better)
    # For simplicity, we assume the user inputs are reasonably safe.
    # In a production environment, always validate and escape inputs extensively.
    
    # Construct the full path to the log file
    full_path = os.path.join(LOG_DIR, filename)
    
    if not os.path.exists(full_path):
        return render_template('index.html', 
                               error=f"Error: File not found at '{full_path}'", 
                               log_dir=LOG_DIR)

    # Construct the shell command: grep 'search_term' /path/to/file
    # We use 'grep' here, which is standard on Linux/Unix systems.
    command = f"grep '{escape(search_term)}' {escape(full_path)}"
    
    print(f"Executing command: {command}")

    try:
        # Execute the command and capture output
        process = os.popen(command)
        output = process.read()
        
        # Pass results back to the template
        return render_template('index.html', 
                               results=output, 
                               filename=filename, 
                               search_term=search_term,
                               log_dir=LOG_DIR)
    except Exception as e:
        return render_template('index.html', 
                               error=f"An unexpected error occurred: {str(e)}", 
                               log_dir=LOG_DIR)

if __name__ == '__main__':
    # IMPORTANT SECURITY NOTE: 
    # Running Flask with debug=True is ONLY safe for local development.
    # For production, use a proper WSGI server (like Gunicorn/Waitress).
    # Also, be extremely cautious with shell execution in production environments.
    app.run(debug=True)
