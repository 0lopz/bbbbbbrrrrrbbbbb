#!/usr/bin/env python3
import sys
import re
import base64

def deobfuscate_python(filepath):
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        
        # Look for common obfuscation patterns
        patterns = [
            (b'exec\(.*?\)', 'exec() call found'),
            (b'eval\(.*?\)', 'eval() call found'),
            (b'base64\.b64decode\(.*?\)', 'base64 encoded payload found'),
            (b'compile\(.*?\)', 'compile() call found')
        ]
        
        results = []
        for pattern, desc in patterns:
            matches = re.findall(pattern, data)
            if matches:
                results.append(f"{desc} ({len(matches)} occurrences)")
                
                # Try to decode base64 if found
                if b'base64' in pattern:
                    for match in matches[:3]:  # Limit to first 3
                        try:
                            decoded = base64.b64decode(match.split(b'(')[1].split(b')')[0])
                            results.append(f"Decoded: {decoded[:200]}...")
                        except:
                            pass
        
        return "\n".join(results) if results else "No common obfuscation patterns detected"
    except Exception as e:
        return f"Deobfuscation error: {str(e)}"

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: deobfuscate.py <filepath>")
        sys.exit(1)
    
    print(deobfuscate_python(sys.argv[1]))