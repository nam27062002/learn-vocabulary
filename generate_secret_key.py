#!/usr/bin/env python3
"""
Generate a new Django secret key for production deployment.
Run this script and copy the output to your Render environment variables.
"""

import secrets

def generate_secret_key():
    """Generate a secure Django secret key."""
    return 'django-insecure-' + secrets.token_urlsafe(50)

if __name__ == '__main__':
    secret_key = generate_secret_key()
    print("=" * 60)
    print("🔑 NEW DJANGO SECRET KEY GENERATED")
    print("=" * 60)
    print(f"SECRET_KEY={secret_key}")
    print("=" * 60)
    print("📋 COPY THIS TO YOUR RENDER ENVIRONMENT VARIABLES:")
    print(f"Variable Name: SECRET_KEY")
    print(f"Variable Value: {secret_key}")
    print("=" * 60)