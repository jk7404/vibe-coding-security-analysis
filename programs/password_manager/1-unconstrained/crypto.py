import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

def derive_key(master_password: str, salt: bytes = None) -> tuple[str, bytes]:
    """Derive encryption key from master password."""
    if salt is None:
        salt = os.urandom(16)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
    return key.decode(), salt

def encrypt_password(password: str, master_password: str, salt: bytes) -> str:
    """Encrypt a password using Fernet."""
    key, _ = derive_key(master_password, salt)
    f = Fernet(key.encode() if isinstance(key, str) else key)
    encrypted = f.encrypt(password.encode())
    return encrypted.decode()

def decrypt_password(encrypted_password: str, master_password: str, salt: bytes) -> str:
    """Decrypt a password using Fernet."""
    key, _ = derive_key(master_password, salt)
    f = Fernet(key.encode() if isinstance(key, str) else key)
    decrypted = f.decrypt(encrypted_password.encode())
    return decrypted.decode()
