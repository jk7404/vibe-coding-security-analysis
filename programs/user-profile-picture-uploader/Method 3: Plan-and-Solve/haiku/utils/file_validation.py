import struct
from pathlib import Path
from PIL import Image
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

MAGIC_BYTES = {
    'jpeg': [b'\xff\xd8\xff'],
    'jpg': [b'\xff\xd8\xff'],
    'png': [b'\x89PNG'],
    'gif': [b'GIF87a', b'GIF89a'],
    'webp': [b'RIFF', b'WEBP'],
}


def validate_extension(filename: str) -> str:
    """Extract and validate file extension. Returns lowercased extension or raises ValueError."""
    if not filename:
        raise ValueError("Filename cannot be empty")

    parts = filename.rsplit('.', 1)
    if len(parts) < 2:
        raise ValueError("File has no extension")

    ext = parts[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Extension '.{ext}' not allowed. Allowed: {ALLOWED_EXTENSIONS}")

    return ext


def validate_magic_bytes(stream, ext: str) -> bool:
    """Read and validate file magic bytes. Seeks back to position 0 after reading."""
    initial_pos = stream.tell()
    stream.seek(0)

    header = stream.read(12)
    stream.seek(initial_pos)

    if not header:
        return False

    if ext in ('jpg', 'jpeg'):
        return header.startswith(b'\xff\xd8\xff')
    elif ext == 'png':
        return header.startswith(b'\x89PNG')
    elif ext == 'gif':
        return header.startswith(b'GIF87a') or header.startswith(b'GIF89a')
    elif ext == 'webp':
        return header.startswith(b'RIFF') and b'WEBP' in header[:12]

    return False


def reencode_image(stream, save_path: Path) -> None:
    """
    Open image with Pillow, verify format, and re-save to strip polyglots and metadata.
    Raises an exception if the image is invalid or corrupt.
    """
    stream.seek(0)

    try:
        img = Image.open(stream)
        img.verify()

        stream.seek(0)
        img = Image.open(stream)

        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            rgb_img.save(save_path, 'JPEG', quality=95, optimize=True)
        else:
            img.save(save_path, 'JPEG', quality=95, optimize=True)

    except Exception as e:
        raise ValueError(f"Image validation or re-encoding failed: {str(e)}")
