# Security Controls Documentation

## Overview
This Flask log viewer implements strict security controls to prevent common web vulnerabilities while managing server logs.

## Security Controls Implemented

### 1. Path Traversal Prevention
**Threat**: Attacker attempts to read files outside `/var/log/app/` using `../` or symlinks.

**Control**: 
- **Whitelist Pattern**: Filenames must match `^[a-zA-Z0-9._-]+$` (alphanumeric, dots, underscores, hyphens only)
- **Canonicalization**: `os.path.realpath()` resolves all symlinks and relative paths
- **Boundary Verification**: Validates that the resolved path starts with the absolute path of `/var/log/app/`
- **File Existence Check**: Only serves files that exist and are readable

**Code Location**: `validate_filename()` function in `app.py`

### 2. Command Injection Prevention
**Threat**: Attacker injects shell metacharacters in grep search to execute arbitrary commands.

**Control**:
- **No Shell Execution**: `subprocess.run()` uses `shell=False` with explicit argument list
- **Argument Isolation**: Search term is passed as a separate argument, never interpreted by shell
- **Input Length Limit**: Search term capped at 500 characters to prevent DoS
- **Timeout Protection**: grep operations timeout after 5 seconds

**Code Location**: `search_logs()` function in `app.py`

### 3. Information Disclosure Prevention
**Threat**: Error messages leak system paths, permissions, or implementation details.

**Control**:
- **Generic Error Messages**: Returns "Invalid filename", "Search failed", etc. (never reveals actual paths)
- **Exception Suppression**: All exceptions caught and logged internally without user exposure
- **Minimal Status Info**: Only returns success/failure and match counts, not system details

**Code Location**: Error handling in both `/api/logs/` and `/api/search` routes

### 4. Denial of Service Prevention
**Threat**: Attacker performs operations designed to consume server resources.

**Controls**:
- **File Size Limit**: 10MB max for displayed files
- **Grep Result Limit**: Maximum 1000 results returned
- **Timeout**: 5-second timeout on grep operations
- **Debug Disabled**: `debug=False` in production

**Code Location**: Constants and subprocess configuration in `app.py`

### 5. Least Privilege & Local Binding
**Control**:
- **Local-Only Access**: Binds to `127.0.0.1` (localhost only)
- **Read-Only Operations**: No file write, delete, or modification capabilities
- **User Process Permissions**: Only accesses files readable by the application process

## Audit Checklist

- ✅ No user input flows directly to shell execution
- ✅ All file paths are validated and canonicalized before access
- ✅ Error messages are generic and non-revealing
- ✅ File and result sizes are limited
- ✅ Long-running operations have timeouts
- ✅ Application binds to localhost only
- ✅ Debug mode is disabled
- ✅ Only read-only operations are supported

## Testing Recommendations

1. **Path Traversal Test**:
   ```
   curl http://localhost:5000/api/logs/../../../etc/passwd
   curl http://localhost:5000/api/logs/..%2Fetc%2Fpasswd
   ```
   Expected: Both return "Invalid filename" error

2. **Command Injection Test**:
   ```json
   POST /api/search
   {
     "filename": "app.log",
     "search_term": "error; whoami"
   }
   ```
   Expected: Grep searches for literal string "; whoami", no command execution

3. **Null Byte Test**:
   ```
   curl http://localhost:5000/api/logs/app.log%00.safe
   ```
   Expected: "Invalid filename" error

4. **Symlink Test**:
   - Create symlink in `/var/log/app/`: `ln -s /etc/passwd secret.log`
   - Attempt to load it
   - Expected: Blocked by boundary check
