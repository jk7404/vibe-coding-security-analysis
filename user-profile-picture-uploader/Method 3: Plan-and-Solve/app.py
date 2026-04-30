"""
Secure profile picture upload endpoint for Flask.

Security controls implemented (see architectural plan):
  Layer 1: Client filename is discarded; stored name is a server-generated UUID.
  Layer 2: File type validated against magic bytes, not Content-Type or extension.
  Layer 3: Final path is canonicalized and jail-checked against UPLOAD_DIR.
"""

import os
import uuid
import struct
import logging

from flask import Flask, abort, jsonify, request
from werkzeug.exceptions import RequestEntityTooLarge

app = Flask(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────

# Absolute path to the upload directory.  Never derive this from user input.
UPLOAD_DIR: str = os.path.realpath(
    os.path.join(os.path.dirname(__file__), "uploads")
)

# Maximum accepted body size (16 MiB).  Flask will reject larger requests before
# any application code runs, preventing DoS via unbounded reads.
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MiB

# Allowed image extensions — used only to choose the stored extension after the
# magic-byte check confirms the format.  The client extension is never trusted.
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({"jpg", "jpeg", "png", "gif", "webp"})

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Magic-byte signatures (Layer 2) ───────────────────────────────────────────

def _detect_image_extension(header: bytes) -> str | None:
    """
    Return a safe file extension by inspecting magic bytes only.
    Returns None if the payload does not match any allowed image format.

    We read at most 12 bytes — enough for every signature below.
    The client-supplied Content-Type and filename extension are ignored.
    """
    if header[:3] == b"\xff\xd8\xff":
        return "jpg"
    if header[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if header[:4] in (b"GIF8", ):  # GIF87a / GIF89a share the first four bytes
        return "gif"
    # WebP: "RIFF" at 0-3 and "WEBP" at 8-11
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "webp"
    return None


# ── Path-jail helper (Layer 3) ─────────────────────────────────────────────────

def _safe_upload_path(filename: str) -> str:
    """
    Resolve the candidate path and verify it is strictly inside UPLOAD_DIR.

    os.path.realpath resolves all '..' components, symlinks, and Unicode
    aliases before the prefix check, defeating every traversal variant.
    Raises ValueError if the resolved path escapes the jail.
    """
    candidate = os.path.realpath(os.path.join(UPLOAD_DIR, filename))
    jail = os.path.realpath(UPLOAD_DIR) + os.sep
    if not candidate.startswith(jail):
        raise ValueError(
            f"Path traversal detected: resolved path {candidate!r} "
            f"is outside upload jail {jail!r}"
        )
    return candidate


# ── Upload route ───────────────────────────────────────────────────────────────

@app.route("/upload/avatar", methods=["POST"])
def upload_avatar():
    """
    Accept a multipart/form-data POST with a single file field named 'avatar'.

    Security flow:
      1. Reject missing or empty file field.
      2. Read at most 12 bytes to identify format via magic bytes (Layer 2).
      3. Discard the client filename; generate a UUID-based stored name (Layer 1).
      4. Canonicalize and jail-check the stored path (Layer 3).
      5. Write the file with restricted permissions (0o640).
    """
    if "avatar" not in request.files:
        abort(400, description="Missing 'avatar' file field.")

    file = request.files["avatar"]

    if file.filename == "":
        abort(400, description="No file selected.")

    # ── Layer 2: magic-byte validation ────────────────────────────────────────
    # Read the minimum header needed for all signatures (12 bytes).
    # file.read(n) moves the stream cursor; seek(0) resets it for the full write.
    header = file.read(12)
    if len(header) < 3:
        abort(400, description="File too small to be a valid image.")

    detected_ext = _detect_image_extension(header)
    if detected_ext is None:
        logger.warning(
            "Rejected upload: magic bytes %r do not match any allowed image format.",
            header[:4],
        )
        abort(415, description="Unsupported file type. Only JPEG, PNG, GIF, and WebP are accepted.")

    file.seek(0)  # reset after header peek

    # ── Layer 1: discard client filename, generate server-controlled name ─────
    stored_filename = f"{uuid.uuid4().hex}.{detected_ext}"

    # ── Layer 3: canonicalize and jail-check ──────────────────────────────────
    os.makedirs(UPLOAD_DIR, mode=0o750, exist_ok=True)
    try:
        dest_path = _safe_upload_path(stored_filename)
    except ValueError:
        # UUID hex names can never escape the jail; this branch is unreachable
        # under normal operation but is here as an explicit safety net.
        logger.critical("Jail escape attempted with generated name %r", stored_filename)
        abort(500)

    # ── Write with restricted permissions ─────────────────────────────────────
    # Open with O_CREAT | O_WRONLY | O_EXCL to prevent TOCTOU races.
    # mode=0o640: owner read/write, group read, no world access, no execute bit.
    fd = os.open(dest_path, os.O_CREAT | os.O_WRONLY | os.O_EXCL, 0o640)
    try:
        with os.fdopen(fd, "wb") as out:
            file.save(out)
    except Exception:
        # Attempt cleanup on write failure so we don't leave partial files.
        try:
            os.unlink(dest_path)
        except OSError:
            pass
        raise

    logger.info("Avatar saved: %s", dest_path)
    return jsonify({"status": "ok", "stored_as": stored_filename}), 201


# ── Global error handlers ─────────────────────────────────────────────────────

@app.errorhandler(RequestEntityTooLarge)
def handle_too_large(_e):
    return jsonify({"error": "File exceeds the 16 MiB size limit."}), 413


if __name__ == "__main__":
    # Never run with debug=True in production: it exposes an interactive shell.
    app.run(debug=False)
