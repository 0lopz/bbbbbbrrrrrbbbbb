import os
import re
import base64
import json

class BenDeobf:
    def __init__(self, javadir):
        self.javadir = javadir
    
    def Deobfuscate(self):
        webhooks = []
        for root, _, files in os.walk(self.javadir):
            for file in files:
                if file.endswith('.class'):
                    try:
                        with open(os.path.join(root, file), 'rb') as f:
                            content = f.read().decode('latin-1')
                            webhook = self._extract_webhook(content)
                            if webhook:
                                webhooks.append(webhook)
                    except:
                        continue
        
        return webhooks[0] if len(webhooks) == 1 else webhooks
    
    def _extract_webhook(self, content):
        # Look for base64 encoded webhooks
        b64_matches = re.findall(r'(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?', content)
        for match in b64_matches:
            try:
                decoded = base64.b64decode(match).decode('utf-8')
                if 'discord.com/api/webhooks' in decoded:
                    return decoded
            except:
                continue
        
        # Look for plaintext webhooks
        plain_matches = re.findall(r'https://discord\.com/api/webhooks/\d+/[a-zA-Z0-9_-]+', content)
        if plain_matches:
            return plain_matches[0]
        
        return None