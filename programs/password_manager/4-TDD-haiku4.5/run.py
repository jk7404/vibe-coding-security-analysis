#!/usr/bin/env python
"""Simple startup script for the password manager."""
import sys
from app import app, db

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database initialized.")

    print("\n" + "="*60)
    print("🔐 Password Manager Starting")
    print("="*60)
    print("\nServer running at: http://localhost:5000")
    print("\nDefault test credentials:")
    print("  - Register a new account at /register")
    print("  - Or use: username='test', password='test123'")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")

    app.run(host='127.0.0.1', port=5000, debug=False)
