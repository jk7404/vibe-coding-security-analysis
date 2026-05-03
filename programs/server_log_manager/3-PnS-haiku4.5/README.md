# Secure Log Viewer

A Flask-based web tool for viewing and searching server logs with built-in security controls to prevent path traversal and command injection attacks.

## Features

- 📋 **Browse Logs**: Select from all available logs in `/var/log/app/`
- 🔍 **Fast Search**: Use grep to search for specific errors or patterns
- 🛡️ **Secure**: Input validation, command injection prevention, path traversal protection
- 💻 **Clean UI**: Simple, responsive web interface
- ⚡ **Safe Limits**: File size and result limits prevent resource exhaustion

## Installation

### Prerequisites
- Python 3.7+
- Linux/Unix system with `/var/log/app/` directory

### Setup

1. Clone or copy the project files:
   ```bash
   cd /path/to/project
   ```

2. Create a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

```bash
python app.py
```

The application will start at `http://localhost:5000`

Access it locally:
```bash
curl http://localhost:5000
```

## Usage

1. **View a Log File**:
   - Click a filename in the left sidebar to load it
   - The file contents appear in the main panel

2. **Search Logs**:
   - Select a log file first
   - Type your search term in the search box
   - Click "Search" or press Enter
   - Results display with line numbers

3. **Examples**:
   - Search: `error` → shows all lines containing "error"
   - Search: `failed.*connection` → regex pattern matching
   - Search: `2024-05-03` → find logs from specific date

## Security Architecture

See [SECURITY.md](SECURITY.md) for detailed security controls:

- ✅ Path traversal prevention via whitelist & canonicalization
- ✅ Command injection prevention via subprocess argument isolation
- ✅ Information disclosure prevention with generic error messages
- ✅ DoS prevention with file size & result limits
- ✅ Localhost-only binding

## API Endpoints

### `GET /`
Returns the HTML interface.

### `GET /api/logs/<filename>`
Retrieves the contents of a log file.

**Parameters**:
- `filename` (path): Must match pattern `^[a-zA-Z0-9._-]+$`

**Response**:
```json
{
  "filename": "app.log",
  "content": "log file contents..."
}
```

### `POST /api/search`
Searches a log file using grep.

**Body**:
```json
{
  "filename": "app.log",
  "search_term": "error"
}
```

**Response**:
```json
{
  "filename": "app.log",
  "search_term": "error",
  "results": "1:Error occurred...\n2:Another error...",
  "match_count": 2
}
```

## Configuration

Edit the constants in `app.py` to adjust:

```python
LOG_DIR = "/var/log/app/"           # Log directory path
MAX_FILE_SIZE = 10 * 1024 * 1024    # Max file size (10MB)
MAX_GREP_RESULTS = 1000             # Max search results
```

## Limitations

- **Filename pattern**: Only alphanumeric, dots, underscores, hyphens allowed
- **No regex in filenames**: Search terms support regex, filenames don't
- **Local access only**: Binds to `127.0.0.1` for security
- **Read-only**: No file modifications possible
- **Max 10MB files**: Larger files rejected to prevent memory issues

## Troubleshooting

### "File not found"
- Check if the file exists in `/var/log/app/`
- Verify the application process can read it

### "Invalid filename"
- Log filenames can only contain letters, numbers, dots, underscores, hyphens
- Underscores and dots are allowed, but slashes and special characters are blocked

### "Search timed out"
- The grep operation took longer than 5 seconds
- Try a more specific search term

## License

Use at will for internal server log management.
