# Flask Profile Picture Upload (Security-First)

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000/`.

## Routes

- `GET /` Upload form
- `POST /upload` Upload a profile picture (stored in `uploads/`)
- `GET /image/<filename>` View page for an uploaded image
- `GET /uploads/<filename>` Serves the uploaded image bytes (restricted to server-generated filenames)

## Security Controls Implemented

- Server-generated filenames (UUID hex) to avoid traversal/overwrite
- Strict allowlist of extensions: `png/jpg/jpeg/webp/gif`
- Image verification with Pillow before saving
- 5MB request size limit via `MAX_CONTENT_LENGTH`
- Strict filename regex + `send_from_directory` for safe serving
- `X-Content-Type-Options: nosniff` on served uploads

