import os
import re
import base64
import zlib

class OtherDeobf:
    def __init__(self, extractiondir, entries):
        self.extractiondir = extractiondir
        self.entries = entries
    
    def Deobfuscate(self):
        for entry in self.entries:
            try:
                with open(os.path.join(self.extractiondir, entry), 'rb') as f:
                    content = f.read()
                    webhook = self._analyze_content(content)
                    if webhook:
                        return webhook
            except:
                continue
        return None
    
    def _analyze_content(self, content):
        # Try common obfuscation patterns
        patterns = [
            rb'https://discord\.com/api/webhooks/\d+/[a-zA-Z0-9_-]+',
            rb'[A-Za-z0-9+/=]{80,}',
            rb'\x00[\x00-\xFF]{20,100}\x00'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                try:
                    decoded = match.decode('utf-8')
                    if 'discord.com/api/webhooks' in decoded:
                        return decoded
                except:
                    try:
                        decompressed = zlib.decompress(match)
                        decoded = decompressed.decode('utf-8')
                        if 'discord.com/api/webhooks' in decoded:
                            return decoded
                    except:
                        continue
        return None