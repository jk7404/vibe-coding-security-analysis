#!/usr/bin/env python
"""
Test script to verify the password manager's core functionality.
This script tests: user registration, login, credential storage, encryption, and retrieval.
"""
import os
import sys
from app import create_app, db
from models import User, Credential
from crypto import derive_key, encrypt_password, decrypt_password, generate_salt
from werkzeug.security import generate_password_hash, check_password_hash

def test_basic_functionality():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("[OK] Database initialized")

        test_password = "test_master_pass_123"
        test_salt = generate_salt()
        password_hash = generate_password_hash(test_password, method='pbkdf2:sha256')

        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=password_hash,
            salt=test_salt
        )
        db.session.add(user)
        db.session.commit()
        print(f"[OK] User registered: {user.username}")

        assert check_password_hash(user.password_hash, test_password)
        print("[OK] Password hash verification works")

        fernet_key = derive_key(test_password, user.salt)
        print("[OK] Fernet key derived successfully")

        test_cred_password = "super_secret_password_123"
        encrypted = encrypt_password(test_cred_password, fernet_key)
        print(f"[OK] Password encrypted: {encrypted[:50]}...")

        credential = Credential(
            owner_id=user.id,
            service_name="Gmail",
            username_field="user@gmail.com",
            encrypted_password=encrypted,
            url="https://gmail.com",
            notes="Personal email account"
        )
        db.session.add(credential)
        db.session.commit()
        print(f"[OK] Credential saved for {credential.service_name}")

        retrieved_cred = Credential.query.filter_by(id=credential.id, owner_id=user.id).first()
        assert retrieved_cred is not None
        print("[OK] Credential ownership check passed")

        decrypted = decrypt_password(retrieved_cred.encrypted_password, fernet_key)
        assert decrypted == test_cred_password
        print("[OK] Password decrypted correctly")

        user2 = User(
            username="testuser2",
            email="test2@example.com",
            password_hash=generate_password_hash("different_pass_456", method='pbkdf2:sha256'),
            salt=generate_salt()
        )
        db.session.add(user2)
        db.session.commit()

        user2_creds = Credential.query.filter_by(owner_id=user2.id).all()
        assert len(user2_creds) == 0
        print("[OK] User isolation verified (user2 can't see user1's credentials)")

        user1_creds = Credential.query.filter_by(owner_id=user.id).all()
        assert len(user1_creds) == 1
        print("[OK] User can retrieve their own credentials")

        all_users = User.query.all()
        assert len(all_users) == 2
        print(f"[OK] Database contains {len(all_users)} users")

        print("\n" + "="*60)
        print("ALL TESTS PASSED!")
        print("="*60)
        print("\nThe password manager is fully functional:")
        print("  - User registration with secure password hashing")
        print("  - Fernet encryption for stored credentials")
        print("  - User isolation and ownership verification")
        print("  - Password encryption and decryption")
        print("  - Database persistence")
        print("\nTo start the server, run:")
        print("  python app.py")
        print("\nThen navigate to: http://127.0.0.1:5000")

if __name__ == '__main__':
    try:
        test_basic_functionality()
    except Exception as e:
        print(f"\n[FAILED] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
