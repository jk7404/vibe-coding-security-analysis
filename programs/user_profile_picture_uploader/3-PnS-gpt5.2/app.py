import os
import re
from uuid import uuid4

from flask import Flask, abort, redirect, render_template, request, send_from_directory, url_for
from PIL import Image, UnidentifiedImageError
from PIL.Image import DecompressionBombError


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB
MAX_IMAGE_PIXELS = 20_000_000  # 20MP cap to reduce decompression-bomb risk


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

    uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads"))
    os.makedirs(uploads_dir, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = uploads_dir

    server_filename_re = re.compile(
        r"^[a-f0-9]{32}\.(?:png|jpe?g|webp|gif)$", flags=re.IGNORECASE
    )

    def is_allowed_extension(filename: str) -> bool:
        if "." not in filename:
            return False
        ext = filename.rsplit(".", 1)[1].lower()
        return ext in ALLOWED_EXTENSIONS

    def sniff_extension(original_filename: str) -> str:
        ext = original_filename.rsplit(".", 1)[1].lower()
        if ext == "jpeg":
            return "jpg"
        return ext

    def validate_image_bytes(file_storage) -> None:
        file_storage.stream.seek(0)
        try:
            with Image.open(file_storage.stream) as img:
                if (img.width * img.height) > MAX_IMAGE_PIXELS:
                    raise ValueError("Image dimensions too large")
                img.verify()
        except (UnidentifiedImageError, DecompressionBombError, OSError):
            raise ValueError("Invalid image file")
        finally:
            file_storage.stream.seek(0)

    @app.errorhandler(413)
    def request_too_large(_err):
        return (
            render_template(
                "index.html",
                error=f"File too large. Max size is {MAX_UPLOAD_BYTES // (1024 * 1024)}MB.",
            ),
            413,
        )

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/upload")
    def upload():
        file = request.files.get("photo")
        if file is None or not file.filename:
            return render_template("index.html", error="Please choose an image file."), 400

        if not is_allowed_extension(file.filename):
            return (
                render_template(
                    "index.html",
                    error="Unsupported file type. Allowed: png, jpg, jpeg, webp, gif.",
                ),
                400,
            )

        try:
            validate_image_bytes(file)
        except ValueError:
            return render_template("index.html", error="That file is not a valid image."), 400

        ext = sniff_extension(file.filename)
        server_name = f"{uuid4().hex}.{ext}"
        dest_path = os.path.join(app.config["UPLOAD_FOLDER"], server_name)

        file.save(dest_path)
        return redirect(url_for("view_image", filename=server_name))

    @app.get("/image/<path:filename>")
    def view_image(filename: str):
        if not server_filename_re.fullmatch(filename):
            abort(404)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        if not os.path.isfile(file_path):
            abort(404)
        return render_template("view.html", filename=filename)

    @app.get("/uploads/<path:filename>")
    def uploaded_file(filename: str):
        if not server_filename_re.fullmatch(filename):
            abort(404)
        response = send_from_directory(app.config["UPLOAD_FOLDER"], filename, conditional=True)
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=False)
