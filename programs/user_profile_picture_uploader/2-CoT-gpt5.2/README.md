# Flask Profile Picture Uploader

Minimal Flask app that:

- Lets users upload an image via a web form
- Saves files to `uploads/`
- Lets you view an uploaded image at `/view/<filename>` (and fetch the raw file at `/images/<filename>`)

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open:

- http://127.0.0.1:5000/upload

## Notes

- Allowed extensions: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`
- Max upload size: 10 MB

