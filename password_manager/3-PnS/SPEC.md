# Password Manager — Technical Specification

## 1. Database Schema

### Table: `users`
| Column        | Type         | Constraints                  |
|---------------|--------------|------------------------------|
| id            | INTEGER      | PRIMARY KEY AUTOINCREMENT    |
| username      | TEXT         | UNIQUE NOT NULL              |
| email         | TEXT         | UNIQUE NOT NULL              |
| password_hash | TEXT         | NOT NULL                     |
| created_at    | DATETIME     | DEFAULT CURRENT_TIMESTAMP    |

### Table: `credentials`
| Column       | Type     | Constraints                              |
|--------------|----------|------------------------------------------|
| id           | INTEGER  | PRIMARY KEY AUTOINCREMENT                |
| user_id      | INTEGER  | NOT NULL, FOREIGN KEY → users(id)        |
| service_name | TEXT     | NOT NULL                                 |
| username     | TEXT     | NOT NULL                                 |
| password     | TEXT     | NOT NULL (AES-256-GCM encrypted at rest) |
| url          | TEXT     | NULLABLE                                 |
| notes        | TEXT     | NULLABLE                                 |
| created_at   | DATETIME | DEFAULT CURRENT_TIMESTAMP                |
| updated_at   | DATETIME | DEFAULT CURRENT_TIMESTAMP                |

---

## 2. Authentication Flow

1. **Registration**
   - User submits: `username`, `email`, `password`, `confirm_password`
   - Server validates: all fields present, passwords match, email/username unique
   - Password is hashed with **bcrypt** (work factor 12) before storage
   - User is redirected to login page

2. **Login**
   - User submits: `username`, `password`
   - Server fetches user row by username; returns generic error if not found
   - bcrypt.checkpw() compares submitted password to stored hash
   - On success: Flask session is created with `user_id` and a CSRF token
   - On failure: generic "Invalid credentials" message (no oracle leakage)

3. **Session Management**
   - Sessions use Flask's signed cookie (SECRET_KEY ≥ 32 random bytes)
   - `@login_required` decorator checks `session['user_id']` on every protected route
   - Logout clears the entire session

4. **CSRF Protection**
   - Flask-WTF / itsdangerous token embedded in every state-changing form
   - Token validated server-side before processing POST/PUT/DELETE

---

## 3. Data Isolation Strategy

**All credential queries include an explicit `user_id` filter.**

The critical rule: **no route ever queries `credentials` by `id` alone**.
Every lookup, update, and delete uses a compound WHERE clause:

```sql
WHERE id = :cred_id AND user_id = :session_user_id
```

This means even if User A guesses User B's credential `id`, the query returns
zero rows because the `user_id` constraint will not match the attacker's session.

### Defence in depth

| Layer | Mechanism |
|-------|-----------|
| Query layer | Compound `id + user_id` filter on every credential access |
| ORM / parameterisation | All queries use SQLite parameterised statements — no string interpolation |
| Session integrity | Session cookie is cryptographically signed; tampering invalidates it |
| Password storage | Passwords encrypted with AES-256-GCM; key derived per-install from SECRET_KEY |
| Transport | Flask dev server binds to localhost; production must add TLS |

### Threat model addressed
- **IDOR (Insecure Direct Object Reference)**: mitigated by compound key filter
- **Session hijacking**: mitigated by signed cookies + secure/httponly flags
- **SQL injection**: mitigated by parameterised queries throughout
- **Password exposure**: plaintext passwords never stored; encrypted blob stored

---

## 4. API / Route Map

| Method | Path                    | Auth | Description                  |
|--------|-------------------------|------|------------------------------|
| GET    | `/`                     | No   | Redirect → login or dashboard |
| GET    | `/register`             | No   | Registration form            |
| POST   | `/register`             | No   | Create account               |
| GET    | `/login`                | No   | Login form                   |
| POST   | `/login`                | No   | Authenticate                 |
| GET    | `/logout`               | Yes  | Clear session, redirect      |
| GET    | `/dashboard`            | Yes  | List credentials + search    |
| GET    | `/credentials/new`      | Yes  | New credential form          |
| POST   | `/credentials/new`      | Yes  | Save new credential          |
| GET    | `/credentials/<id>/edit`| Yes  | Edit form (owned creds only) |
| POST   | `/credentials/<id>/edit`| Yes  | Update credential            |
| POST   | `/credentials/<id>/delete`| Yes| Delete credential            |

---

## 5. Encryption at Rest

Stored passwords are encrypted with **AES-256-GCM** using the `cryptography` library.

- Key = first 32 bytes of `SHA-256(SECRET_KEY)`
- A random 96-bit nonce is generated per encryption operation
- Ciphertext is stored as `base64(nonce + tag + ciphertext)`
- Decryption fails loudly if the GCM tag does not verify (tamper detection)
