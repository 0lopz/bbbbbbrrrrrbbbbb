import requests

class Telegram:
    def __init__(self, token):
        self.token = token
        self.username = None
        self.firstName = None
        self.dump = False
    
    @staticmethod
    def CheckValid(token):
        try:
            r = requests.get(f"https://api.telegram.org/bot{token}/getMe")
            return r.status_code == 200
        except:
            return False
    
    def GetInformations(self):
        try:
            r = requests.get(f"https://api.telegram.org/bot{self.token}/getMe")
            if r.status_code == 200:
                data = r.json()
                if data.get('ok'):
                    result = data.get('result', {})
                    self.username = result.get('username')
                    self.firstName = result.get('first_name')
                    return True
            return False
        except:
            return False
    
    def CheckDump(self, chat_id):
        try:
            r = requests.post(f"https://api.telegram.org/bot{self.token}/getChat", json={"chat_id": chat_id})
            self.dump = r.status_code == 200
            return self.dump
        except:
            return False