import os

from flask import Flask, abort, redirect, render_template_string, request, send_from_directory, url_for
from werkzeug.utils import secure_filename


UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR


def _ensure_upload_dir() -> None:
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def _allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


@app.get("/")
def index():
    return render_template_string(
        """
        <!doctype html>
        <html>
          <head><meta charset="utf-8"><title>Upload Profile Picture</title></head>
          <body>
            <h1>Upload Profile Picture</h1>
            <form action="{{ url_for('upload') }}" method="post" enctype="multipart/form-data">
              <input type="file" name="file" accept="image/*" required>
              <button type="submit">Upload</button>
            </form>
          </body>
        </html>
        """
    )


@app.post("/upload")
def upload():
    _ensure_upload_dir()

    if "file" not in request.files:
        abort(400)
    file = request.files["file"]
    if not file or file.filename is None or file.filename == "":
        abort(400)

    filename = secure_filename(file.filename)
    if not filename or not _allowed_file(filename):
        abort(400)

    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)

    # Redirect to a view page for convenience; tests follow redirects and expect 200.
    return redirect(url_for("view_image", filename=filename))


@app.get("/view/<filename>")
def view_image(filename: str):
    _ensure_upload_dir()
    safe_name = secure_filename(filename)
    if not safe_name or safe_name != filename or not _allowed_file(safe_name):
        abort(404)
    return send_from_directory(app.config["UPLOAD_FOLDER"], safe_name)


if __name__ == "__main__":
    _ensure_upload_dir()
    app.run(host="127.0.0.1", port=5000, debug=False)

