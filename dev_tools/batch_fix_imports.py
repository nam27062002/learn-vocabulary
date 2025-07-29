#!/usr/bin/env python
"""
Batch fix imports in all test files
"""
import os
import sys

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_all_test_files():
    """Fix imports in all test files"""
    
    test_files = [
        'test_api_fix.py',
        'test_audio_stats_fix.py', 
        'test_current_audio_ui_fixes.py',
        'test_enhanced_audio_fixes.py',
        'test_enhanced_audio_ux.py',
        'test_favorites.py',
        'test_favorites_implementation.py',
        'test_notification_ui_fixes.py'
    ]
    
    tests_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tests')
    
    for filename in test_files:
        filepath = os.path.join(tests_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"⚠️ File not found: {filepath}")
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for the Django setup pattern and fix it
            lines = content.split('\n')
            new_lines = []
            i = 0
            
            while i < len(lines):
                line = lines[i]
                
                # Check if this is the start of Django setup block
                if 'import django' in line and i > 0:
                    # Add the current line
                    new_lines.append(line)
                    i += 1
                    
                    # Add empty line if it exists
                    if i < len(lines) and lines[i].strip() == '':
                        new_lines.append(lines[i])
                        i += 1
                    
                    # Check for Django setup comment
                    if i < len(lines) and 'Setup Django environment' in lines[i]:
                        # Add the path insertion before Django setup
                        new_lines.append('')
                        new_lines.append('# Add the parent directory to Python path so we can import Django modules')
                        new_lines.append('sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))')
                        new_lines.append('')
                        new_lines.append(lines[i])  # Add the comment
                        i += 1
                    else:
                        # Add the path insertion anyway
                        new_lines.append('')
                        new_lines.append('# Add the parent directory to Python path so we can import Django modules')
                        new_lines.append('sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))')
                        new_lines.append('')
                        new_lines.append('# Setup Django environment')
                else:
                    new_lines.append(line)
                    i += 1
            
            # Write the fixed content back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            
            print(f"✅ Fixed imports in {filename}")
            
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

if __name__ == '__main__':
    print("🔧 Batch fixing test file imports...")
    fix_all_test_files()
    print("🎉 Batch import fixing completed!")
