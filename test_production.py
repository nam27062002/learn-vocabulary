#!/usr/bin/env python
"""
Test script to check if production settings work locally
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    # Set production settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learn_english_project.settings_production')
    os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-local-testing')
    
    try:
        django.setup()
        print("✅ Django setup successful with production settings")
        
        # Test database connection
        from django.db import connection
        cursor = connection.cursor()
        print("✅ Database connection successful")
        
        # Test static files
        from django.conf import settings
        print(f"✅ Static files configured: {settings.STATIC_ROOT}")
        
        print("\n🎉 Production settings test passed!")
        print("You can now deploy to Render with confidence.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Fix the error before deploying to Render.")
        sys.exit(1)