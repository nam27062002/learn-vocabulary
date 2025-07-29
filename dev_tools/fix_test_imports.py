#!/usr/bin/env python
"""
Utility script to fix import paths in moved test files
"""
import os
import glob

def fix_test_file_imports():
    """Fix Django import paths in all test files"""
    
    # Get all test files
    test_files = glob.glob('../tests/test_*.py')
    
    old_import_block = '''import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learn_english_project.settings')
django.setup()'''

    new_import_block = '''import os
import sys
import django

# Add the parent directory to Python path so we can import Django modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learn_english_project.settings')
django.setup()'''

    fixed_files = []
    
    for test_file in test_files:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if old_import_block in content:
                new_content = content.replace(old_import_block, new_import_block)
                
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                fixed_files.append(test_file)
                print(f"✅ Fixed imports in {test_file}")
            else:
                print(f"⚠️ No standard import block found in {test_file}")
                
        except Exception as e:
            print(f"❌ Error processing {test_file}: {e}")
    
    print(f"\n🎉 Fixed imports in {len(fixed_files)} files")
    return fixed_files

if __name__ == '__main__':
    print("🔧 Fixing test file imports...")
    fix_test_file_imports()
