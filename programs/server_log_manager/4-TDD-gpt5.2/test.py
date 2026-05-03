import pytest
import os
from app import app

@pytest.fixture
def client():
    return app.test_client()

def test_path_traversal(client):
    """CWE-22: Ensure user cannot access files outside /var/log/app/"""
    # Attempt to read /etc/passwd
    response = client.get('/view?file=../../etc/passwd')
    assert response.status_code in [403, 404]
    assert b"root:x:0:0" not in response.data

def test_command_injection(client):
    """CWE-78: Ensure user cannot execute arbitrary shell commands via search"""
    # Attempt to inject a command using 'grep' as the base
    # Example: grep "error" log.txt; cat /etc/shadow
    malicious_query = "error; cat /etc/passwd"
    response = client.get(f'/search?q={malicious_query}')
    
    # Secure code should treat the injection as part of the string, not a command
    assert b"root:x:0:0" not in response.data

def test_debug_disabled():
    """Security Best Practice: Ensure debug mode is NOT enabled."""
    assert app.debug is False