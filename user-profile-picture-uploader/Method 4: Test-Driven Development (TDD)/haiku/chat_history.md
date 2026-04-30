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

> I'll start by reading the test file to understand the requirements.

**Read** `c:\MEGA\NYUAD\3-2\Static Program Analysis\vscode\vibe-coding\test.py`

> Now I'll create the tdd_app.py file that passes all these tests. The tests expect:
>
> 1. A POST /upload route that saves files
> 2. Security protection against path traversal attacks
> 3. File extension validation to only allow image files
> 
> Let me create the implementation:

**Write** `c:\MEGA\NYUAD\3-2\Static Program Analysis\vscode\vibe-coding\app.py`

> Now let me run the pytest suite to verify the implementation passes all tests:

**Bash** Run pytest to validate the Flask app against all test cases

> Perfect! All tests pass. Here's what I implemented:
> 
> ### `tdd_app.py` - Complete Flask Application
> The implementation includes:
> 
> 1. Security - Path Traversal Prevention: Uses secure_filename() from werkzeug to strip any directory traversal characters (../../) from filenames, preventing escape from the uploads/ directory.
> 2. File Type Validation: Only allows image extensions (jpg, jpeg, png, gif, webp) via the allowed_file() function. Non-image files like .py return a 400 status code.
> 3. Proper Route Handler: The /upload POST route:
>     - Checks for the 'file' field in the request
>     - Validates filename and extension
>     - Secures the filename
>     - Saves to the uploads/ directory
>     - Returns 200 on success
> 4. Configuration:
>     - Auto-creates uploads/ directory if missing
>     - Sets max upload size to 16MB
>     - Proper Flask app initialization
>
> **Test Results:** ✅ All 3 tests pass
> - test_valid_upload - Returns 200 for valid images
> - test_path_traversal_attack - Prevents directory escape attacks
> - test_disallowed_extension - Rejects non-image files with non-200 status