#!/usr/bin/env python3
"""
Simple .po to .mo compiler for Django projects when gettext tools are not available.
This script manually compiles .po files to .mo files.
"""

import os
import struct
import array
from pathlib import Path

def compile_po_to_mo(po_file_path, mo_file_path):
    """
    Compile a .po file to .mo file format.
    This is a simplified implementation that handles basic msgid/msgstr pairs.
    """
    
    # Read and parse the .po file
    messages = {}
    current_msgid = None
    current_msgstr = None
    in_msgid = False
    in_msgstr = False
    
    with open(po_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
                
            # Handle msgid
            if line.startswith('msgid '):
                if current_msgid is not None and current_msgstr is not None:
                    messages[current_msgid] = current_msgstr
                current_msgid = line[7:-1]  # Remove 'msgid "' and '"'
                current_msgstr = None
                in_msgid = True
                in_msgstr = False
                continue
                
            # Handle msgstr
            if line.startswith('msgstr '):
                current_msgstr = line[8:-1]  # Remove 'msgstr "' and '"'
                in_msgid = False
                in_msgstr = True
                continue
                
            # Handle continuation lines
            if line.startswith('"') and line.endswith('"'):
                content = line[1:-1]  # Remove quotes
                if in_msgid and current_msgid is not None:
                    current_msgid += content
                elif in_msgstr and current_msgstr is not None:
                    current_msgstr += content
    
    # Don't forget the last message
    if current_msgid is not None and current_msgstr is not None:
        messages[current_msgid] = current_msgstr
    
    # Remove empty msgid (header)
    if '' in messages:
        del messages['']
    
    # Create .mo file
    create_mo_file(messages, mo_file_path)
    print(f"Compiled {po_file_path} -> {mo_file_path}")
    print(f"  {len(messages)} messages compiled")

def create_mo_file(messages, mo_file_path):
    """
    Create a .mo file from a dictionary of messages.
    Based on the GNU gettext .mo file format.
    """

    # Prepare the data
    keys = sorted(messages.keys())
    values = [messages[k] for k in keys]

    # Calculate offsets
    koffsets = []
    voffsets = []
    kencoded = []
    vencoded = []

    # Encode all strings as UTF-8
    for k, v in zip(keys, values):
        kencoded.append(k.encode('utf-8'))
        vencoded.append(v.encode('utf-8'))

    # Calculate key offsets
    offset = 7 * 4 + 16 * len(keys)  # Header + key/value table
    for k in kencoded:
        koffsets.append(offset)
        offset += len(k)  # No null terminator in .mo format

    # Calculate value offsets
    for v in vencoded:
        voffsets.append(offset)
        offset += len(v)  # No null terminator in .mo format

    # Create the .mo file
    os.makedirs(os.path.dirname(mo_file_path), exist_ok=True)

    with open(mo_file_path, 'wb') as f:
        # Write header
        f.write(struct.pack('<I', 0x950412de))  # Magic number
        f.write(struct.pack('<I', 0))           # Version
        f.write(struct.pack('<I', len(keys)))   # Number of entries
        f.write(struct.pack('<I', 7 * 4))       # Offset of key table
        f.write(struct.pack('<I', 7 * 4 + 8 * len(keys)))  # Offset of value table
        f.write(struct.pack('<I', 0))           # Hash table size
        f.write(struct.pack('<I', 0))           # Hash table offset

        # Write key table
        for i, k in enumerate(kencoded):
            f.write(struct.pack('<I', len(k)))
            f.write(struct.pack('<I', koffsets[i]))

        # Write value table
        for i, v in enumerate(vencoded):
            f.write(struct.pack('<I', len(v)))
            f.write(struct.pack('<I', voffsets[i]))

        # Write keys
        for k in kencoded:
            f.write(k)

        # Write values
        for v in vencoded:
            f.write(v)

def main():
    """Main function to compile all .po files in the locale directory."""
    
    base_dir = Path(__file__).parent
    locale_dir = base_dir / 'locale'
    
    if not locale_dir.exists():
        print(f"Locale directory not found: {locale_dir}")
        return
    
    compiled_count = 0
    
    # Find all .po files
    for po_file in locale_dir.rglob('*.po'):
        mo_file = po_file.with_suffix('.mo')
        
        try:
            compile_po_to_mo(po_file, mo_file)
            compiled_count += 1
        except Exception as e:
            print(f"Error compiling {po_file}: {e}")
    
    print(f"\nTotal files compiled: {compiled_count}")

if __name__ == '__main__':
    main()
