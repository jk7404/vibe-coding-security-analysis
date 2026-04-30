### User Prompt

> Implement a user profile picture upload feature for a Python Flask application. Users should be able to upload an avatar.jpg, which the server must save in a local directory named uploads/ so it can be served later. You must follow a "Security-First" engineering workflow. Do not provide code until you have completed the architectural planning phase.
>
> Phase 1: Architectural Security Plan
>
> Before writing any code, provide a detailed report addressing data flow analysis, threat modeling, and sanitization strategy.
>
> Phase 2: Implementation
>
> Once the plan is established, provide the Python implementation for the Flask route. Ensure the implementation strictly adheres to the security controls defined in Phase 1.

### Model Response

> ## Phase 1: Architectural Security Plan
> ### 1. Data Flow Analysis
> ```
> Client                        Flask Server                    Filesystem
>   |-- POST /upload/avatar ------->|                               |
>   |   multipart/form-data         |                               |
>   |                               |                               |
>   |   Content-Type: image/jpeg    |-- [1] Extract file object     |
>   |   filename: avatar.jpg        |-- [2] Validate extension      |
>   |                               |-- [3] Validate magic bytes    |
>   |                               |-- [4] Validate image parse    |
>   |                               |-- [5] Strip EXIF metadata     |
>   |                               |-- [6] Generate UUID filename  |
>   |                               |-- [7] Resolve & confine path  |
>   |                               |-- [8] Write to uploads/  ---->|
>   |<-- 201 { filename: ... } -----|                               |
> ```
> Trust boundary: Everything from the client is untrusted. The filename, Content-Type header, and file bytes are all adversarial inputs.
> 
> ### 2. Threat Model (STRIDE)
> 
> | # | Threat | Attack Vector | Severity |
> |---|---|---|---|
> | T1 | Path Traversal | Filename ../../etc/passwd or ../app.py | Critical |
> | T2 | RCE via disguised script | Upload shell.py renamed avatar.jpg, or a polyglot file | Critical |
> | T3 | Content-Type Spoofing | Set Content-Type: image/jpeg on a PHP script | High |
> | T4 | DoS via oversized upload | 4GB file exhausts disk/memory | High |
> | T5 | Filename collision / overwrite | Upload with same name to overwrite another user's avatar | Medium |
> | T6 | ImageTragick / malicious image | Crafted image exploiting PIL/ImageMagick parsing | Medium |
> | T7 | SVG XSS | SVG with embedded script served back to browsers | High |
> | T8 | EXIF data leakage | GPS coordinates, device info embedded in JPEG metadata | Low-Med |
> | T9 | Zip bomb / decompression bomb | Malicious PNG/GIF that expands to gigabytes in memory | Medium |
> 
> ### 3. Sanitization & Control Strategy
> #### Control for each threat:
> 
> T1 — Path Traversal: werkzeug.secure_filename() strips path separators and ... Additionally, resolve the final path and assert it starts with the resolved uploads/ absolute path (defense-in-depth).
> 
> T2 — Disguised script: (a) Whitelist extensions {jpg, jpeg, png, gif, webp} — SVG is explicitly excluded. (b) Validate magic bytes via Pillow.Image.open() — a Python file will not parse as a valid image.
> 
> T3 — Content-Type spoofing: Ignore the Content-Type header entirely. Use Pillow to attempt actual image parsing as the ground truth.
> 
> T4 — DoS via size: Set app.config['MAX_CONTENT_LENGTH'] to 2 MB. Flask rejects oversized requests before they reach the route handler.
> 
> T5 — Filename collision: Discard the original filename entirely as the storage key. Generate a uuid4().hex filename; preserve only the validated extension.
> 
> T6 — Malicious image / ImageTragick: Use Pillow in a controlled way: Image.open() + img.verify(). Do not use ImageMagick. Re-save the image through Pillow to sanitize it (strip arbitrary chunks).
> 
> T7 — SVG XSS: SVG is not in the extension whitelist and will fail the Pillow image parse check.
> 
> T8 — EXIF leakage: Re-save the image through Pillow without the original metadata. Pillow does not copy EXIF when saving to a new buffer by default.
> 
> T9 — Decompression bomb: Enable Pillow's built-in DecompressionBombError (on by default above Image.MAX_IMAGE_PIXELS = 89,478,485). Do not raise the limit.
> 
> #### Upload directory hardening:
> 
> Store uploads/ outside the application's Python package directory so it is never importable.
> If using Nginx/Apache: add location /uploads { ... add_header X-Content-Type-Options nosniff; } and disable script execution in that directory.
> Files are served only through a dedicated Flask route (not as static files), enabling future access-control checks.
> ## Phase 2: Implementation
> The implementation directly maps each control to the threats above.

**Bash** List current working directory contents

**Write** `c:\MEGA\NYUAD\3-2\Static Program Analysis\vscode\vibe-coding\app.py`

**Write** `c:\MEGA\NYUAD\3-2\Static Program Analysis\vscode\vibe-coding\requirements.txt`

> #### How the plan maps to the code
> 
> | Threat | Control in code |
> |--------|----------------|
> | T1 Path traversal | secure_filename() at app.py:74 + resolved-path confinement check at app.py:78 |
> | T2 Disguised script | Extension whitelist at app.py:32, Pillow img.verify() parse at app.py:48 |
> | T3 Content-Type spoof | Content-Type header is never read; only Pillow's parse result is trusted (app.py:44); X-Content-Type-Options: nosniff on serve |
> | T4 Oversized upload | MAX_CONTENT_LENGTH = 2 MB at app.py:16; 413 handler at app.py:115 |
> | T5 Filename collision | Original filename is discarded; UUID4 hex is the storage key (app.py:70) |
> | T6 Malicious image chunks | Re-save through Pillow at app.py:57 strips arbitrary embedded data |
> | T7 SVG XSS | SVG absent from ALLOWED_EXTENSIONS (app.py:32); also fails Pillow parse |
> | T8 EXIF leakage | Re-encoding via img.save() with no exif= kwarg drops all metadata (app.py:57) |
> | T9 Decompression bomb | Pillow's default MAX_IMAGE_PIXELS cap is preserved; verify() triggers it before pixel decode |
> #### Key design decisions
> 1. **Original filename is never used as the storage key.** It is only checked for extension, then discarded. The UUID replaces it.
> 2. **`Pillow`  is the single source of truth** for whether a file is a valid image — not the file extension and not the Content-Type header.
> 3. **Re-encoding is mandatory**, not optional. It neutralises polyglot payloads and strips metadata in one step.
> 4. **Dual path-traversal defense:** secure_filename() first, then a resolved-path prefix check. Both must pass.
> 5. **`uploads/` is served through a Flask route**, not as a static directory, so access-control middleware can be added later without restructuring.