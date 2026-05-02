import io
import os
import uuid
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ── Security configuration ────────────────────────────────────────────────────
# T4: reject uploads larger than 2 MB before the route handler is reached
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2 MB

UPLOAD_FOLDER = Path(__file__).parent / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

# T2/T7: SVG is intentionally absent — it can carry inline JavaScript
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}

# T9: keep Pillow's decompression-bomb guard at its default; never raise it
# Image.MAX_IMAGE_PIXELS is ~89 M pixels by default — leave it alone


# ── Helpers ───────────────────────────────────────────────────────────────────

def _allowed_extension(filename: str) -> bool:
    """T2: whitelist check on the submitted filename's extension."""
    parts = filename.rsplit(".", 1)
    return len(parts) == 2 and parts[1].lower() in ALLOWED_EXTENSIONS


def _sanitize_image(file_storage) -> tuple[bytes, str]:
    """
    Validate and re-encode the uploaded file through Pillow.

    Controls enforced here:
      T2/T3 — actual image parse (not Content-Type header) proves it is an image
      T6     — re-saving through Pillow neutralises embedded malicious chunks
      T8     — new buffer contains no EXIF / XMP / ICC metadata from the original
      T9     — Pillow raises DecompressionBombError if pixel count exceeds the cap

    Returns (clean_bytes, lowercase_format_extension).
    Raises ValueError for anything that is not a safe, parseable image.
    """
    raw = file_storage.read()

    try:
        # First pass: verify structural integrity without decoding pixels
        with Image.open(io.BytesIO(raw)) as probe:
            probe.verify()

        # Second pass: decode pixels and re-encode without original metadata
        # (verify() exhausts the buffer; we must re-open from the raw bytes)
        with Image.open(io.BytesIO(raw)) as img:
            fmt = (img.format or "").upper()
            if fmt not in {"JPEG", "PNG", "GIF", "WEBP"}:
                raise ValueError(f"Unsupported image format: {fmt}")

            out = io.BytesIO()
            save_kwargs: dict = {"format": fmt}
            if fmt == "JPEG":
                # quality=85 is a reasonable default; exif is NOT forwarded
                save_kwargs["quality"] = 85
            img.save(out, **save_kwargs)

        return out.getvalue(), fmt.lower().replace("jpeg", "jpg")

    except UnidentifiedImageError as exc:
        raise ValueError("File is not a recognised image") from exc
    except Exception as exc:
        # Re-raise Pillow's DecompressionBombError and any other parse error
        raise ValueError(str(exc)) from exc


def _safe_save(data: bytes, ext: str) -> str:
    """
    Write clean image bytes to uploads/ with a UUID filename.

    T1: secure_filename + path confinement check prevent traversal
    T5: UUID storage key makes collisions statistically impossible
    """
    # T5: generate a storage key that is independent of user input
    storage_name = f"{uuid.uuid4().hex}.{ext}"

    # T1 (layer 1): secure_filename strips path separators and ".." sequences
    storage_name = secure_filename(storage_name)

    dest = (UPLOAD_FOLDER / storage_name).resolve()
    upload_root = UPLOAD_FOLDER.resolve()

    # T1 (layer 2): paranoid confinement — assert the resolved path is still
    # inside uploads/ even after any OS-level symlink resolution
    if not str(dest).startswith(str(upload_root) + os.sep):
        abort(400)

    dest.write_bytes(data)
    return storage_name


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/upload/avatar", methods=["POST"])
def upload_avatar():
    """
    Accept a profile picture upload.

    Expected request: multipart/form-data with a field named "file".
    Returns: { "filename": "<uuid>.ext" } on success.
    """
    if "file" not in request.files:
        return jsonify({"error": "Missing 'file' field in form data"}), 400

    upload = request.files["file"]

    if not upload.filename:
        return jsonify({"error": "No file selected"}), 400

    # T2: extension whitelist (fast pre-check before the more expensive parse)
    if not _allowed_extension(upload.filename):
        return jsonify({"error": "File extension not permitted"}), 415

    try:
        clean_bytes, ext = _sanitize_image(upload)
    except ValueError as exc:
        return jsonify({"error": f"Invalid image: {exc}"}), 415

    stored_name = _safe_save(clean_bytes, ext)
    return jsonify({"filename": stored_name}), 201


@app.route("/avatars/<path:filename>", methods=["GET"])
def serve_avatar(filename: str):
    """
    Serve a previously uploaded avatar.

    send_from_directory confines serving to UPLOAD_FOLDER and raises 404 for
    any path that would escape the directory, providing T1 protection on reads.
    """
    # T3: tell browsers not to sniff the content type
    response = send_from_directory(UPLOAD_FOLDER, filename)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Disposition"] = "inline"
    return response


@app.errorhandler(413)
def too_large(_):
    # T4: friendly message when Flask rejects an oversized upload
    return jsonify({"error": "File exceeds the 2 MB size limit"}), 413


if __name__ == "__main__":
    # Never run with debug=True in production — it exposes an interactive shell
    app.run(debug=False)
