# Flask Profile Picture Uploader

Quick Flask app to upload an image and serve it back by filename.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000/`.

## Routes

- `/` upload form
- `/upload` handles the POST upload
- `/view/<filename>` view page that displays the image
- `/uploads/<filename>` serves the raw uploaded file

Uploads are stored in `uploads/` (auto-created on first run).

