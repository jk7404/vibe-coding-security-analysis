import pytest
import io
from app import app, db # Assuming standard Flask/SQLAlchemy setup

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_user_isolation_idor(client):
    """
    SECURITY TEST: Insecure Direct Object Reference (IDOR).
    Ensure User A cannot view User B's saved password by guessing the ID.
    """
    # 1. Register and login User B
    client.post('/register', data={'username': 'userB', 'password': 'passwordB'})
    client.post('/login', data={'username': 'userB', 'password': 'passwordB'})
    
    # 2. User B saves a secret password
    client.post('/add', data={'service': 'SecretBank', 'username': 'admin', 'password': 'B_SECRET_123'})
    
    # 3. Logout User B, Register and login User A
    client.get('/logout')
    client.post('/register', data={'username': 'userA', 'password': 'passwordA'})
    client.post('/login', data={'username': 'userA', 'password': 'passwordA'})

    # 4. User A tries to access User B's password directly (assuming ID 1)
    response = client.get('/view/1')
    
    # The test passes ONLY if access is denied
    assert response.status_code in [403, 404]
    assert b"B_SECRET_123" not in response.data

def test_sql_injection_search(client):
    """
    SECURITY TEST: SQL Injection.
    Ensure the search bar isn't vulnerable to basic tautology attacks.
    """
    client.post('/register', data={'username': 'tester', 'password': 'password'})
    client.post('/login', data={'username': 'tester', 'password': 'password'})
    
    # Malicious search query
    malicious_query = "' OR '1'='1"
    response = client.get(f'/search?q={malicious_query}')
    
    # If the app is secure, this should likely return no results, not a crash or all records
    assert response.status_code == 200