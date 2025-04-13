import requests
import json

class Webhook:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.name = None
        self.channel_id = None
        self.guild_id = None
    
    def CheckValid(self, webhook_url=None):
        url = webhook_url or self.webhook_url
        try:
            r = requests.get(url)
            if r.status_code == 200:
                data = r.json()
                self.name = data.get('name')
                self.channel_id = data.get('channel_id')
                self.guild_id = data.get('guild_id')
                return True
            return False
        except:
            return False
    
    def GetInformations(self):
        try:
            r = requests.get(self.webhook_url)
            if r.status_code == 200:
                data = r.json()
                self.name = data.get('name')
                self.channel_id = data.get('channel_id')
                self.guild_id = data.get('guild_id')
                return data
            return None
        except:
            return None
    
    def DeleteWebhook(self):
        try:
            r = requests.delete(self.webhook_url)
            return r.status_code == 204
        except:
            return False
    
    def SendWebhook(self, message="Test message from ratters.rip"):
        try:
            data = {
                "content": message,
                "username": "ratters.rip"
            }
            r = requests.post(self.webhook_url, json=data)
            return r.status_code == 204
        except:
            return False