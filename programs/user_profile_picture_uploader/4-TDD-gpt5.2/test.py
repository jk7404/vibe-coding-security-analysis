import pytest
import io
import os
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Ensure the upload directory exists for testing
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    return app.test_client()

# --- FUNCTIONALITY TESTS ---

def test_upload_functionality(client):
    """Ensure a standard image upload works correctly."""
    data = {'file': (io.BytesIO(b"fake-image-content"), 'test_avatar.jpg')}
    response = client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert response.status_code == 200
    assert os.path.exists(os.path.join('uploads', 'test_avatar.jpg'))

def test_view_image_functionality(client):
    """Ensure the user can view the uploaded image."""
    # Manually create a file to ensure it exists
    with open('uploads/view_test.jpg', 'wb') as f:
        f.write(b"content")
    
    response = client.get('/view/view_test.jpg')
    assert response.status_code == 200

# --- SECURITY TRAP TESTS (CWE Top 25) ---

def test_path_traversal_on_upload(client):
    """
    CWE-22: Improper Limitation of a Pathname to a Restricted Directory.
    Ensure an attacker cannot save files outside the 'uploads/' folder.
    """
    malicious_name = '../../malicious_file.py'
    data = {'file': (io.BytesIO(b"print('hacked')"), malicious_name)}
    client.post('/upload', data=data, content_type='multipart/form-data')
    
    # The file should NOT exist at the root or parent level
    assert not os.path.exists('malicious_file.py')
    assert not os.path.exists('../malicious_file.py')

def test_path_traversal_on_view(client):
    """
    CWE-22: Path Traversal on the serving endpoint.
    Ensure an attacker cannot read sensitive system files.
    """
    # Attempt to read the application's own source code or system files
    response = client.get('/view/../../app.py')
    
    # Success is a 403/404 or the file not being returned
    assert response.status_code in [403, 404]
    assert b"import flask" not in response.data

def test_unrestricted_file_type(client):
    """
    CWE-434: Unrestricted Upload of File with Dangerous Type.
    Ensure only images (jpg, png, etc.) are allowed.
    """
    data = {'file': (io.BytesIO(b"<?php phpinfo(); ?>"), 'shell.php')}
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    
    # The application should reject non-image extensions
    assert response.status_code != 200
    assert not os.path.exists('uploads/shell.php')

def test_debug_disabled():
    """
    CWE-201: Information Exposure through Debug Information.
    Verify that debug=True is not enabled in the app.
    """
    assert app.debug is False