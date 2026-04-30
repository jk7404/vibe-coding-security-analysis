# Security-First Avatar Upload Architecture

## Overview

This Flask application implements a secure file upload feature that prioritizes security at every layer. The design follows the principle of **"Security by Default"** and uses a **defense-in-depth** approach with multiple overlapping security controls.

---

## Data Flow & Security Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER BROWSER                                │
│         POST /upload + multipart/form-data                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FLASK MIDDLEWARE                              │
│  [1] MAX_CONTENT_LENGTH = 5 MB (enforced before route)          │
│  [2] CSRF token validation (CSRFProtect middleware)              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   POST /upload ROUTE                             │
│  [3] Rate limit: 10 requests/minute per IP (Flask-Limiter)      │
│  [4] Presence check: 'file' field must exist                     │
│  [5] Filename check: not empty string                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│             FILE VALIDATION (utils/file_validation.py)           │
│  [6] Extension allow-list: {jpg, jpeg, png, gif, webp}          │
│  [7] Magic-byte validation: first 12 bytes vs. signatures       │
│  [8] Pillow re-encode: Image.open() → verify() → save()        │
│      Strips: polyglots, EXIF, ICC profiles                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              FILE STORAGE & RESPONSE                             │
│  [9] Filename: UUID-based (original discarded)                  │
│  [10] Path: uploads/ (outside static tree)                       │
│  [11] Permissions: 0o644                                         │
│  [12] Response: JSON {filename: uuid.jpg} (no reflection)        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              GET /avatars/<filename> ROUTE                       │
│  [13] Filename regex: ^[a-f0-9\-]+\.(jpg|jpeg|png|gif|webp)$   │
│       (prevents path traversal)                                  │
│  [14] Existence check: file must exist in uploads/              │
│  [15] send_file() with MIME type image/jpeg                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Threat Model & Controls (STRIDE)

### 1. Spoofing: Attacker uploads `shell.php` renamed as `avatar.jpg`

**Controls:**
- Extension allow-list check (validates `.php` is rejected)
- Magic-byte validation (PHP header `<?ph` ≠ JPEG header `FF D8 FF`)
- Result: **400 Bad Request** — "File signature does not match extension"

---

### 2. Tampering: Attacker creates a polyglot file (JPEG + PHP payload)

**Attack:** Valid JPEG header + embedded PHP appended at end

**Controls:**
- Pillow `Image.open()` loads the image
- `Image.verify()` checks for format consistency; polyglot fails here
- Fresh `Image.save()` re-encodes from scratch; embedded payload is lost
- Result: **400 Bad Request** — "Image validation or re-encoding failed"

---

### 3. Repudiation: No audit trail of who uploaded what

**Controls:**
- Logging at route level: `current_app.logger.error()` captures upload errors
- UUID filename tied to upload timestamp in logs
- User ID can be added via Flask session/auth context
- Result: **Full audit trail** for accountability

---

### 4. Information Disclosure: Path traversal attack

**Attack:** `GET /avatars/../../etc/passwd` or `GET /avatars/../../../secret.txt`

**Controls:**
- Strict regex validation: `^[a-f0-9\-]+\.(jpg|jpeg|png|gif|webp)$`
- Only alphanumeric + hyphens allowed (no `/` or `.`)
- Second check: `file_path.resolve().parent == uploads_folder.resolve()` ensures file is in correct directory
- Result: **400 Bad Request** — "Invalid filename format"

---

### 5. Denial of Service: Large file uploads or upload flood

**Attack 1:** 1 GB file upload

**Controls:**
- `MAX_CONTENT_LENGTH = 5 * 1024 * 1024` (5 MB hard cap)
- Flask rejects request BEFORE route handler runs
- Result: **413 Request Entity Too Large**

**Attack 2:** 1000 uploads per minute from one IP

**Controls:**
- Flask-Limiter: `@limiter.limit("10/minute")` on upload route
- Per-IP rate limiting via `get_remote_address`
- Result: **429 Too Many Requests** after 10 requests/minute

---

### 6. Elevation of Privilege: Execute uploaded script

**Attack:** Upload `shell.jsp` or `shell.phtml` and execute via web server

**Controls:**
- Extension allow-list prevents non-image files
- `uploads/` directory NOT declared as Flask `static_folder`
- Serving via `send_file()` with `as_attachment=False` (inline display, no execution)
- If server misconfigures directory as CGI-enabled, Pillow re-encode prevents execution
- Result: **Impossible to execute** — only valid image formats reach disk

---

## File Validation Pipeline (in detail)

### Step 1: Extension Allow-List

```python
# utils/file_validation.py: validate_extension()
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
ext = filename.rsplit('.', 1)[1].lower()
if ext not in ALLOWED_EXTENSIONS:
    raise ValueError(...)
```

**Why:** Quick, lightweight first check. Rejects obvious non-images (`.exe`, `.php`, `.txt`).

---

### Step 2: Magic-Byte Validation

```python
# utils/file_validation.py: validate_magic_bytes()
stream.seek(0)
header = stream.read(12)

if ext in ('jpg', 'jpeg'):
    return header.startswith(b'\xff\xd8\xff')  # JPEG signature
elif ext == 'png':
    return header.startswith(b'\x89PNG')       # PNG signature
elif ext == 'gif':
    return header.startswith(b'GIF87a') or header.startswith(b'GIF89a')
elif ext == 'webp':
    return header.startswith(b'RIFF') and b'WEBP' in header[:12]
```

**Why:** Defeats file-rename attacks (PHP with `.jpg` extension). Content-Type header is NOT checked (attacker-controlled).

---

### Step 3: Pillow Re-Encoding

```python
# utils/file_validation.py: reencode_image()
img = Image.open(stream)
img.verify()  # Verify format integrity

stream.seek(0)
img = Image.open(stream)

if img.mode in ('RGBA', 'LA', 'P'):
    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
    rgb_img.paste(img, mask=...)
    rgb_img.save(save_path, 'JPEG', quality=95, optimize=True)
else:
    img.save(save_path, 'JPEG', quality=95, optimize=True)
```

**Why:**
- `img.verify()` detects corrupt files and polyglots
- Fresh `save()` re-encodes from scratch
- Strips EXIF data (location, camera model, etc.)
- Strips ICC color profiles
- Strips embedded thumbnails, comments, polyglot payloads
- All images normalized to JPEG format

---

### Step 4: Filename Sanitization & UUID Generation

```python
# routes/upload.py: upload_avatar()
filename = f"{uuid.uuid4()}.jpg"
# Original filename is NEVER stored or returned to client
```

**Why:**
- `werkzeug.secure_filename()` is NOT called on output; the original name is discarded
- UUID is cryptographically random, no enumeration possible
- No collision risk with concurrent uploads
- Original filename is logged (for audit), but never exposed to client

---

### Step 5: Safe Serving

```python
# routes/upload.py: serve_avatar()
if not FILENAME_REGEX.match(filename):
    return jsonify({'error': 'Invalid filename format'}), 400

file_path = Path(current_app.config['UPLOAD_FOLDER']) / filename

if not file_path.resolve().parent == Path(current_app.config['UPLOAD_FOLDER']).resolve():
    return jsonify({'error': 'Invalid file path'}), 400

return send_file(
    file_path,
    mimetype='image/jpeg',
    as_attachment=False,
    download_name=None
)
```

**Why:**
- Two-layer path traversal guard (regex + parent check)
- `send_file()` handles MIME type, caching headers, streaming
- `as_attachment=False` means inline display (browser renders image)
- `download_name=None` prevents "Save As" dialog

---

## Error Handling & Information Disclosure

All errors return **structured JSON** without reflecting user input:

```python
# ❌ Bad (leaks info)
return jsonify({'error': f'File {filename} not found'}), 404

# ✅ Good (generic error)
return jsonify({'error': 'Avatar not found'}), 404
```

**Why:** Prevents attackers from using error messages to discover filenames or directory structure.

---

## CSRF Protection

```python
# app.py
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)
app.config['WTF_CSRF_CHECK_DEFAULT'] = True
```

**Why:** Prevents cross-site request forgery where a malicious site tricks a user into uploading files. CSRF token is required for POST requests.

---

## Rate Limiting

```python
# app.py
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
)
limiter.limit("10/minute")(upload_bp)
```

**Why:**
- Prevents DoS attacks (upload flooding)
- Per-IP rate limiting (shared hosting scenarios)
- "10/minute" on upload, global "50/hour" as fallback

---

## Summary of Controls

| Layer | Control | Type | Enforcement |
|---|---|---|---|
| HTTP | Content-Length limit | Size | Flask `MAX_CONTENT_LENGTH` |
| HTTP | CSRF token | Auth | CSRFProtect middleware |
| HTTP | Rate limit | DoS | Flask-Limiter per IP |
| Request | Presence check | Validation | Route handler |
| File | Extension allow-list | Whitelist | Python validation |
| File | Magic-byte check | Signature | Binary comparison |
| File | Pillow re-encode | Sanitization | Image re-save |
| Storage | UUID filename | Isolation | Python `uuid.uuid4()` |
| Storage | Directory outside static | Isolation | Flask config |
| Serving | Regex filename guard | Validation | Route handler |
| Serving | Parent path check | Validation | `Path.resolve()` |
| Serving | `send_file()` API | Safe serving | Flask built-in |
| Response | Structured JSON errors | Info disclosure | No input reflection |

---

## Testing

See [TEST_GUIDE.md](TEST_GUIDE.md) for comprehensive security test cases:
- Valid uploads
- Renamed PHP files
- Polyglot JPEG+PHP
- Path traversal
- Large files
- Rate limiting
- Missing fields
- Invalid extensions

Each test validates a specific security control.
