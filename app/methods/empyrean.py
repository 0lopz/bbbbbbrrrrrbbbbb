import os
import re
import base64
import zlib

class VespyDeobf:
    def __init__(self, extractiondir, entries):
        self.extractiondir = extractiondir
        self.entries = entries
    
    def Deobfuscate(self):
        for entry in self.entries:
            if entry.endswith('.pyc'):
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
        # Look for compressed base64 strings
        matches = re.findall(b'[A-Za-z0-9+/=]{20,}', content)
        for match in matches:
            try:
                decompressed = zlib.decompress(base64.b64decode(match))
                decoded = decompressed.decode('utf-8')
                if 'discord.com/api/webhooks' in decoded:
                    return decoded
            except:
                continue
        return None