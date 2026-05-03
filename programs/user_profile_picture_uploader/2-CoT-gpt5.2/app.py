from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def is_allowed_filename(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB
    app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    @app.get("/")
    def index():
        return redirect(url_for("upload"))

    @app.route("/upload", methods=["GET", "POST"])
    def upload():
        if request.method == "POST":
            if "file" not in request.files:
                abort(400, "Missing file field.")

            file = request.files["file"]
            if not file or file.filename is None or file.filename == "":
                abort(400, "No file selected.")

            if not is_allowed_filename(file.filename):
                abort(400, f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

            safe_name = secure_filename(file.filename)
            if not safe_name:
                abort(400, "Invalid filename.")

            dest_path = UPLOAD_DIR / safe_name
            file.save(dest_path)

            return redirect(url_for("view", filename=safe_name))

        return render_template("upload.html", allowed=", ".join(sorted(ALLOWED_EXTENSIONS)))

    @app.get("/view/<path:filename>")
    def view(filename: str):
        safe_name = secure_filename(filename)
        if safe_name != filename:
            abort(404)
        file_path = UPLOAD_DIR / safe_name
        if not file_path.is_file():
            abort(404)
        return render_template("view.html", filename=safe_name)

    @app.get("/images/<path:filename>")
    def images(filename: str):
        safe_name = secure_filename(filename)
        if safe_name != filename:
            abort(404)
        file_path = UPLOAD_DIR / safe_name
        if not file_path.is_file():
            abort(404)
        return send_from_directory(app.config["UPLOAD_FOLDER"], safe_name)

    return app


app = create_app()


if __name__ == "__main__":
    # Allow overriding host/port via env vars for convenience.
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host=host, port=port, debug=debug)

