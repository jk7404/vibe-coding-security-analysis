import os
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template_string,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename


APP_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = APP_DIR / "uploads"

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me"),
    MAX_CONTENT_LENGTH=8 * 1024 * 1024,  # 8 MB
    UPLOAD_FOLDER=str(UPLOAD_DIR),
)


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


INDEX_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Upload Profile Picture</title>
    <style>
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 32px; max-width: 760px; }
      .card { border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px; }
      .muted { color: #6b7280; }
      input[type=file] { display: block; margin: 12px 0; }
      button { padding: 10px 14px; border: 0; border-radius: 8px; background: #111827; color: white; cursor: pointer; }
      button:hover { background: #0b1220; }
      .flash { margin: 12px 0; padding: 10px 12px; background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; }
      code { background: #f3f4f6; padding: 2px 6px; border-radius: 6px; }
    </style>
  </head>
  <body>
    <h1>Upload a profile picture</h1>
    <p class="muted">Allowed: {{ allowed }}. Max size: 8 MB.</p>

    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for m in messages %}
          <div class="flash">{{ m }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <div class="card">
      <form method="post" action="{{ url_for('upload') }}" enctype="multipart/form-data">
        <label for="file">Choose image</label>
        <input id="file" name="file" type="file" accept="image/*" required />
        <button type="submit">Upload</button>
      </form>
    </div>

    {% if uploaded_filename %}
      <p>Uploaded as: <code>{{ uploaded_filename }}</code></p>
      <p><a href="{{ url_for('view', filename=uploaded_filename) }}">View page</a> ·
         <a href="{{ url_for('uploaded_file', filename=uploaded_filename) }}">Direct image</a></p>
    {% endif %}

    <hr />
    <p class="muted">
      Tip: Open <code>/view/&lt;filename&gt;</code> to see an uploaded image by name.
    </p>
  </body>
</html>
"""


VIEW_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>View: {{ filename }}</title>
    <style>
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 32px; max-width: 900px; }
      img { max-width: 100%; height: auto; border-radius: 12px; border: 1px solid #e5e7eb; }
      code { background: #f3f4f6; padding: 2px 6px; border-radius: 6px; }
      .muted { color: #6b7280; }
    </style>
  </head>
  <body>
    <h1>Uploaded image</h1>
    <p class="muted">Filename: <code>{{ filename }}</code></p>
    <p><a href="{{ url_for('index') }}">Upload another</a></p>
    <img src="{{ url_for('uploaded_file', filename=filename) }}" alt="Uploaded image: {{ filename }}" />
  </body>
</html>
"""


@app.get("/")
def index():
    return render_template_string(
        INDEX_HTML, allowed=", ".join(sorted(ALLOWED_EXTENSIONS)), uploaded_filename=None
    )


@app.post("/upload")
def upload():
    if "file" not in request.files:
        flash("No file field found in form.")
        return redirect(url_for("index"))

    file = request.files["file"]
    if not file or file.filename is None or file.filename.strip() == "":
        flash("No file selected.")
        return redirect(url_for("index"))

    original_name = file.filename
    if not allowed_file(original_name):
        flash(f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
        return redirect(url_for("index"))

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = secure_filename(original_name)
    if safe_name == "":
        flash("Invalid filename.")
        return redirect(url_for("index"))

    dest = UPLOAD_DIR / safe_name
    if dest.exists():
        stem, suffix = dest.stem, dest.suffix
        for i in range(1, 10_000):
            candidate = UPLOAD_DIR / f"{stem}-{i}{suffix}"
            if not candidate.exists():
                dest = candidate
                safe_name = candidate.name
                break
        else:
            flash("Could not generate a unique filename. Try again.")
            return redirect(url_for("index"))

    file.save(dest)

    return render_template_string(
        INDEX_HTML, allowed=", ".join(sorted(ALLOWED_EXTENSIONS)), uploaded_filename=safe_name
    )


@app.get("/uploads/<path:filename>")
def uploaded_file(filename: str):
    safe = secure_filename(filename)
    if safe != filename:
        abort(404)
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.get("/view/<path:filename>")
def view(filename: str):
    safe = secure_filename(filename)
    if safe != filename:
        abort(404)
    file_path = UPLOAD_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        abort(404)
    return render_template_string(VIEW_HTML, filename=filename)


if __name__ == "__main__":
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=True)

