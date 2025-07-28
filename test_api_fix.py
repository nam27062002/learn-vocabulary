#!/usr/bin/env python3
"""
Test script to verify that the incorrect words count API endpoint is working correctly.
This script tests the fix for the 404 error in the study interface.
"""

import os
import sys
import django
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learn_english_project.settings')
django.setup()

def test_api_endpoint():
    """Test the incorrect words count API endpoint."""
    print("Testing API endpoint fix...")
    
    # Create a test client
    client = Client()
    
    # Create a test user
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    # Log in the test user
    client.login(username='testuser', password='testpass123')
    
    # Test the API endpoint without language prefix
    print("Testing /api/incorrect-words/count/ (without language prefix)...")
    response = client.get('/api/incorrect-words/count/')
    
    print(f"Response status code: {response.status_code}")
    print(f"Response content type: {response.get('Content-Type', 'Not specified')}")
    
    if response.status_code == 200:
        print("✅ SUCCESS: API endpoint is working correctly!")
        try:
            data = response.json()
            print(f"Response data: {data}")
            if 'success' in data and 'counts' in data:
                print("✅ SUCCESS: API response has correct structure!")
                return True
            else:
                print("❌ ERROR: API response structure is incorrect")
                return False
        except Exception as e:
            print(f"❌ ERROR: Failed to parse JSON response: {e}")
            return False
    else:
        print(f"❌ ERROR: API endpoint returned status {response.status_code}")
        print(f"Response content: {response.content.decode()}")
        return False

def test_old_endpoint():
    """Test that the old endpoint with language prefix returns 404."""
    print("\nTesting old endpoint with language prefix...")
    
    client = Client()
    
    # Create and login test user
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    client.login(username='testuser', password='testpass123')
    
    # Test the old endpoint with language prefix (should return 404)
    print("Testing /en/api/incorrect-words/count/ (with language prefix)...")
    response = client.get('/en/api/incorrect-words/count/')
    
    print(f"Response status code: {response.status_code}")
    
    if response.status_code == 404:
        print("✅ SUCCESS: Old endpoint correctly returns 404 (as expected)")
        return True
    else:
        print(f"❌ UNEXPECTED: Old endpoint returned status {response.status_code}")
        return False

def test_url_patterns():
    """Test that URL patterns are correctly configured."""
    print("\nTesting URL pattern configuration...")
    
    try:
        # Test that the API URL name resolves correctly
        from django.urls import reverse
        url = reverse('api_get_incorrect_words_count')
        print(f"✅ SUCCESS: URL pattern resolves to: {url}")
        return True
    except Exception as e:
        print(f"❌ ERROR: URL pattern resolution failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("API ENDPOINT FIX VERIFICATION")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: New API endpoint
    if test_api_endpoint():
        tests_passed += 1
    
    # Test 2: Old endpoint (should fail)
    if test_old_endpoint():
        tests_passed += 1
    
    # Test 3: URL patterns
    if test_url_patterns():
        tests_passed += 1
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {tests_passed}/{total_tests} tests passed")
    print("=" * 60)
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED! The API fix is working correctly.")
        print("\nThe study interface should now be able to:")
        print("- Load incorrect words count without 404 errors")
        print("- Display the review mode option properly")
        print("- Allow users to review incorrect words")
    else:
        print("❌ Some tests failed. Please check the configuration.")
    
    return tests_passed == total_tests

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
