import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

def generate_salt():
    return os.urandom(16).hex()

def derive_key(master_password, salt_hex):
    salt = bytes.fromhex(salt_hex)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    derived = kdf.derive(master_password.encode())
    return base64.urlsafe_b64encode(derived)

def encrypt_password(plaintext, key):
    f = Fernet(key)
    encrypted = f.encrypt(plaintext.encode())
    return encrypted.decode()

def decrypt_password(token, key):
    f = Fernet(key)
    decrypted = f.decrypt(token.encode())
    return decrypted.decode()
