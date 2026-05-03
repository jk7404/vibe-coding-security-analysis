"""
Test script to verify Password Manager functionality
Run this after starting the server to test all features
"""

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:5000"

def get_csrf_token(session, url):
    """Extract CSRF token from HTML form."""
    response = session.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    token = soup.find('input', {'name': 'csrf_token'})
    return token['value'] if token else None

def test_registration():
    """Test user registration."""
    print("\n[TEST 1] User Registration")
    print("-" * 50)

    session = requests.Session()

    # Get registration page
    response = session.get(f"{BASE_URL}/register")
    csrf_token = get_csrf_token(session, f"{BASE_URL}/register")

    # Submit registration form
    data = {
        'username': 'testuser123',
        'email': 'testuser@example.com',
        'password': 'SecurePass123!',
        'confirm_password': 'SecurePass123!',
        'csrf_token': csrf_token
    }

    response = session.post(f"{BASE_URL}/register", data=data, allow_redirects=False)

    if response.status_code == 302:  # Redirect to login
        print("✓ Registration successful - user redirected to login")
        return session
    else:
        print("✗ Registration failed")
        print(f"Status code: {response.status_code}")
        return None

def test_login(session):
    """Test user login."""
    print("\n[TEST 2] User Login")
    print("-" * 50)

    # Get login page and CSRF token
    csrf_token = get_csrf_token(session, f"{BASE_URL}/login")

    # Submit login form
    data = {
        'username': 'testuser123',
        'password': 'SecurePass123!',
        'csrf_token': csrf_token
    }

    response = session.post(f"{BASE_URL}/login", data=data, allow_redirects=False)

    if response.status_code == 302:  # Redirect to dashboard
        print("✓ Login successful - user redirected to dashboard")
        return True
    else:
        print("✗ Login failed")
        return False

def test_add_credential(session):
    """Test adding a credential."""
    print("\n[TEST 3] Add Credential")
    print("-" * 50)

    # Get add credential form
    response = session.get(f"{BASE_URL}/credential/add")
    csrf_token = get_csrf_token(session, f"{BASE_URL}/credential/add")

    # Submit credential form
    data = {
        'service_name': 'Gmail',
        'username': 'myemail@gmail.com',
        'password': 'MyGmailPassword123!',
        'url': 'https://gmail.com',
        'csrf_token': csrf_token
    }

    response = session.post(f"{BASE_URL}/credential/add", data=data, allow_redirects=False)

    if response.status_code == 302:  # Redirect to dashboard
        print("✓ Credential added successfully")
        return True
    else:
        print("✗ Failed to add credential")
        print(f"Status code: {response.status_code}")
        return False

def test_dashboard(session):
    """Test viewing dashboard with credentials."""
    print("\n[TEST 4] View Dashboard")
    print("-" * 50)

    response = session.get(f"{BASE_URL}/dashboard")

    if "Gmail" in response.text and "myemail@gmail.com" in response.text:
        print("✓ Dashboard displays credentials correctly")
        return True
    else:
        print("✗ Credentials not found on dashboard")
        return False

def test_search(session):
    """Test search functionality."""
    print("\n[TEST 5] Search Credentials")
    print("-" * 50)

    # Add another credential
    csrf_token = get_csrf_token(session, f"{BASE_URL}/credential/add")
    data = {
        'service_name': 'GitHub',
        'username': 'myusername',
        'password': 'MyGitHubPassword456!',
        'url': 'https://github.com',
        'csrf_token': csrf_token
    }
    session.post(f"{BASE_URL}/credential/add", data=data, allow_redirects=False)

    # Search for Gmail
    response = session.get(f"{BASE_URL}/dashboard?search_query=Gmail")

    if "Gmail" in response.text and "GitHub" not in response.text:
        print("✓ Search filters credentials correctly")
        return True
    else:
        print("✗ Search functionality not working properly")
        return False

def test_invalid_login():
    """Test invalid login attempt."""
    print("\n[TEST 6] Invalid Login Attempt")
    print("-" * 50)

    session = requests.Session()
    csrf_token = get_csrf_token(session, f"{BASE_URL}/login")

    data = {
        'username': 'wronguser',
        'password': 'wrongpassword',
        'csrf_token': csrf_token
    }

    response = session.post(f"{BASE_URL}/login", data=data)

    if "Invalid username or password" in response.text:
        print("✓ Generic error message shown (no user enumeration)")
        return True
    else:
        print("✗ Error handling may be insecure")
        return False

def test_xss_prevention():
    """Test XSS prevention."""
    print("\n[TEST 7] XSS Prevention")
    print("-" * 50)

    session = requests.Session()

    # Login first
    csrf_token = get_csrf_token(session, f"{BASE_URL}/login")
    data = {
        'username': 'testuser123',
        'password': 'SecurePass123!',
        'csrf_token': csrf_token
    }
    session.post(f"{BASE_URL}/login", data=data)

    # Try to add credential with XSS payload
    csrf_token = get_csrf_token(session, f"{BASE_URL}/credential/add")
    data = {
        'service_name': '<script>alert("XSS")</script>',
        'username': 'test',
        'password': 'test123!',
        'url': '',
        'csrf_token': csrf_token
    }

    response = session.post(f"{BASE_URL}/credential/add", data=data, allow_redirects=False)

    # Check if the dashboard escapes the script tag
    response = session.get(f"{BASE_URL}/dashboard")

    if "&lt;script&gt;" in response.text or "&lt;" in response.text:
        print("✓ XSS payload properly escaped in HTML output")
        return True
    else:
        print("⚠ Verify XSS escaping manually")
        return False

def test_unauthorized_access():
    """Test that users cannot access other users' credentials."""
    print("\n[TEST 8] Authorization Check")
    print("-" * 50)

    # Create two sessions
    session1 = requests.Session()
    session2 = requests.Session()

    # Register user 1
    csrf_token = get_csrf_token(session1, f"{BASE_URL}/register")
    data = {
        'username': 'user1test',
        'email': 'user1test@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!',
        'csrf_token': csrf_token
    }
    session1.post(f"{BASE_URL}/register", data=data)

    # Register user 2
    csrf_token = get_csrf_token(session2, f"{BASE_URL}/register")
    data = {
        'username': 'user2test',
        'email': 'user2test@example.com',
        'password': 'Password456!',
        'confirm_password': 'Password456!',
        'csrf_token': csrf_token
    }
    session2.post(f"{BASE_URL}/register", data=data)

    # User 1 login and add credential
    csrf_token = get_csrf_token(session1, f"{BASE_URL}/login")
    data = {
        'username': 'user1test',
        'password': 'Password123!',
        'csrf_token': csrf_token
    }
    session1.post(f"{BASE_URL}/login", data=data)

    # User 1 adds a credential
    csrf_token = get_csrf_token(session1, f"{BASE_URL}/credential/add")
    data = {
        'service_name': 'User1Secret',
        'username': 'user1secret',
        'password': 'secret123!',
        'url': '',
        'csrf_token': csrf_token
    }
    session1.post(f"{BASE_URL}/credential/add", data=data)

    # User 2 login
    csrf_token = get_csrf_token(session2, f"{BASE_URL}/login")
    data = {
        'username': 'user2test',
        'password': 'Password456!',
        'csrf_token': csrf_token
    }
    session2.post(f"{BASE_URL}/login", data=data)

    # User 2 tries to access credential ID 1
    response = session2.get(f"{BASE_URL}/credential/1/edit")

    if response.status_code == 403 or "do not have permission" in response.text:
        print("✓ Users cannot access other users' credentials")
        return True
    else:
        print("⚠ Authorization may need review")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*50)
    print("  PASSWORD MANAGER - SECURITY TEST SUITE")
    print("="*50)

    print("\nNote: Ensure the server is running on http://localhost:5000")

    try:
        # Check if server is running
        requests.get(BASE_URL, timeout=2)
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Cannot connect to server on http://localhost:5000")
        print("Please start the server first (python app.py)")
        return

    session = test_registration()
    if not session:
        print("\n✗ Registration test failed. Aborting.")
        return

    if not test_login(session):
        print("\n✗ Login test failed. Aborting.")
        return

    if not test_add_credential(session):
        print("\n✗ Add credential test failed. Aborting.")
        return

    test_dashboard(session)
    test_search(session)
    test_invalid_login()
    test_xss_prevention()
    test_unauthorized_access()

    print("\n" + "="*50)
    print("  TEST SUITE COMPLETE")
    print("="*50)
    print("\nManual Testing Checklist:")
    print("  [ ] Register with weak password - should be rejected")
    print("  [ ] Try SQL injection in search - should be parameterized")
    print("  [ ] Check password field is 'password' type (hidden)")
    print("  [ ] Check CSRF tokens in all forms")
    print("  [ ] Verify session expires after 24 hours")
    print("  [ ] Test rate limiting on login (5 attempts/min)")
    print()

if __name__ == '__main__':
    main()
