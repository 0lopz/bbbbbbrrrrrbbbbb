import os
import re

class NotObfuscated:
    def __init__(self, extractiondir, entries):
        self.extractiondir = extractiondir
        self.entries = entries
    
    def Deobfuscate(self):
        for entry in self.entries:
            if entry.endswith('.pyc') or entry.endswith('.py'):
                try:
                    with open(os.path.join(self.extractiondir, entry), 'rb') as f:
                        content = f.read().decode('utf-8', errors='ignore')
                        webhook = self._find_webhook(content)
                        if webhook:
                            return webhook
                except:
                    continue
        return None
    
    def _find_webhook(self, content):
        matches = re.findall(r'https://discord\.com/api/webhooks/\d+/[a-zA-Z0-9_-]+', content)
        if matches:
            return matches[0]
        return None