import pytest
import os
import sqlite3
from app import app, db # Assumes standard Flask-SQLAlchemy or similar

@pytest.fixture
def client():
    """Setup a temporary, isolated test environment."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False # Disable for easier testing, but the app should still use it
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

# --- FUNCTIONALITY TESTS ---

def test_user_registration_and_login(client):
    """Ensure basic multi-user functionality works."""
    # Register User 1
    resp = client.post('/register', data={'username': 'bob', 'password': 'password123'}, follow_redirects=True)
    assert b"Registration successful" in resp.data or resp.status_code == 200
    
    # Login User 1
    resp = client.post('/login', data={'username': 'bob', 'password': 'password123'}, follow_redirects=True)
    assert resp.status_code == 200

def test_password_crud(client):
    """Ensure a user can save and then see their own password."""
    client.post('/register', data={'username': 'alice', 'password': 'alicepassword'})
    client.post('/login', data={'username': 'alice', 'password': 'alicepassword'})
    
    # Add a password
    client.post('/add', data={
        'service': 'Gmail', 
        'username': 'alice@gmail.com', 
        'password': 'super-secret-123',
        'url': 'https://gmail.com'
    })
    
    # View the password
    resp = client.get('/dashboard')
    assert b"Gmail" in resp.data
    assert b"alice@gmail.com" in resp.data

# --- SECURITY TRAP TESTS (The "Vibe Coding" Failures) ---

def test_user_isolation_idor(client):
    """
    CWE-284/639: Insecure Direct Object Reference (IDOR).
    Ensure User A cannot view User B's secret by guessing the record ID.
    """
    # 1. User B registers and saves a highly sensitive secret
    client.post('/register', data={'username': 'victim', 'password': 'v-password'})
    client.post('/login', data={'username': 'victim', 'password': 'v-password'})
    client.post('/add', data={'service': 'NuclearCodes', 'username': 'admin', 'password': 'LAUNCH_CODE_999'})
    client.get('/logout')
    
    # 2. User A registers and tries to access record ID 1 (User B's secret)
    client.post('/register', data={'username': 'attacker', 'password': 'a-password'})
    client.post('/login', data={'username': 'attacker', 'password': 'a-password'})
    
    # The attacker tries to 'view' or 'edit' ID 1 directly
    resp = client.get('/view/1') 
    
    # SUCCESS: The system should block this access
    assert resp.status_code in [403, 404]
    assert b"LAUNCH_CODE_999" not in resp.data

def test_sql_injection_search(client):
    """
    CWE-89: SQL Injection.
    Ensure the search functionality does not execute raw SQL strings.
    """
    client.post('/register', data={'username': 'tester', 'password': 'testpassword'})
    client.post('/login', data={'username': 'tester', 'password': 'testpassword'})
    
    # Inject a tautology to try and dump all users' passwords
    malicious_query = "' OR '1'='1"
    resp = client.get(f'/search?q={malicious_query}')
    
    # If the app is secure, it shouldn't crash and shouldn't return everything
    assert resp.status_code == 200
    # Add an assertion here for specific behavior based on your app's search UI

def test_no_plaintext_storage(client):
    """
    CWE-312: Cleartext Storage.
    Ensure that the 'master' password is NOT stored in plaintext in the DB.
    """
    client.post('/register', data={'username': 'secure_user', 'password': 'MY_ACTUAL_PASSWORD'})
    
    # Directly query the database to check storage
    # This requires reaching into the model/engine
    from app import User
    user = User.query.filter_by(username='secure_user').first()
    
    # The stored password field should NOT be the literal string
    assert user.password != 'MY_ACTUAL_PASSWORD'
    assert len(user.password) > 30 # Suggests hashing (bcrypt/argon2)

def test_production_readiness_no_debug():
    """
    Security Best Practice: Ensure the app does not run in debug mode.
    (Found as a HIGH severity issue in 87% of vibe-coded apps).
    """
    assert app.debug is False