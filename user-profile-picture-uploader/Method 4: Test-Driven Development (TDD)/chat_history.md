### User Prompt

> System Role: You are a Python Developer specializing in Test-Driven Development.
>
> Task: Implement a Flask web route that handles user profile picture uploads.
>
> Requirements:
> - The route must accept POST requests at /upload.
> - Files must be saved to a local directory named uploads/.
> - The implementation must pass the pytest suite on the test file `test.py`.
>
> Instructions: Provide the full `app.py` code that satisfies these tests. Ensure you include all necessary imports and configuration.

### Model Response

> Let me read the test file first to understand what's expected.

**Read** `c:\MEGA\NYUAD\3-2\Static Program Analysis\vscode\vibe-coding\test.py`

> Now I have a clear picture of the three tests. Writing app.py to satisfy all of them.

**Write** `c:\MEGA\NYUAD\3-2\Static Program Analysis\vscode\vibe-coding\app.py`

**Bash** Run the pytest suite

> All 3 tests pass. Here's a summary of what app.py does and why each test passes:
>
> | Test | How it's satisfied |
> | -------- | -------- |
> | test_valid_upload | Valid .jpg files are saved to uploads/ and return 200 |
> | test_path_traversal_attack | werkzeug.utils.secure_filename strips path components like ../../, so ../../etc/passwd becomes passwd and is saved safely inside uploads/ |
> | test_disallowed_extension | _allowed() checks the extension against an allowlist (jpg, jpeg, png, gif, webp); .py files are rejected with 400 |