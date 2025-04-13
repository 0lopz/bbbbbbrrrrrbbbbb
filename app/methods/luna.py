import os
import re
import base64
import zlib

class LunaDeobf:
    def __init__(self, extractiondir, entries):
        self.extractiondir = extractiondir
        self.entries = entries
    
    def Deobfuscate(self):
        main_script = None
        for entry in self.entries:
            if 'main' in entry.lower():
                main_script = entry
                break
        
        if main_script:
            try:
                with open(os.path.join(self.extractiondir, main_script), 'rb') as f:
                    content = f.read()
                    return self._extract_luna_webhook(content)
            except:
                pass
        return None
    
    def _extract_luna_webhook(self, content):
        # Luna specific pattern
        pattern = rb'[\x00-\x7F]{30,100}'
        matches = re.findall(pattern, content)
        for match in matches:
            try:
                if b'discord' in match:
                    decoded = match.decode('utf-8')
                    if 'discord.com/api/webhooks' in decoded:
                        return decoded
            except:
                continue
        return None