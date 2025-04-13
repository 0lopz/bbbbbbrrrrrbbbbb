#!/usr/bin/env python3
import sys
import re
import pefile

def extract_strings(filepath):
    try:
        pe = pefile.PE(filepath)
        strings = []
        for section in pe.sections:
            data = section.get_data()
            # Extract ASCII strings
            strings.extend(re.findall(b'[ -~]{4,}', data))
        return [s.decode('ascii', errors='ignore') for s in strings]
    except Exception as e:
        return [f"Error extracting strings: {str(e)}"]

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: extract_strings.py <filepath>")
        sys.exit(1)
    
    strings = extract_strings(sys.argv[1])
    print("\n".join(strings[:1000]))  # Limit output