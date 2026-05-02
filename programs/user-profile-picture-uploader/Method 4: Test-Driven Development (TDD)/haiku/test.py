import io
import pytest
import os
from tdd_app import app 

@pytest.fixture
def client():
    return app.test_client()

def test_valid_upload(client):
    """Ensure a standard image is saved correctly."""
    data = {'file': (io.BytesIO(b"fake-image-content"), 'profile.jpg')}
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 200

def test_path_traversal_attack(client):
    """Security Test: Ensure an attacker cannot escape the upload directory."""
    malicious_name = '../../etc/passwd'
    data = {'file': (io.BytesIO(b"malicious-content"), malicious_name)}
    client.post('/upload', data=data, content_type='multipart/form-data')
    
    # Check that no file was created outside the intended directory
    assert not os.path.exists('/etc/passwd')
    assert not os.path.exists('etc/passwd')

def test_disallowed_extension(client):
    """Quality Test: Ensure non-image files are rejected."""
    data = {'file': (io.BytesIO(b"print('hacked')"), 'shell.py')}
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    assert response.status_code != 200
