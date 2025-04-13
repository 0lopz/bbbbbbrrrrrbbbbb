class Config:
    def __init__(self):
        self.delete_after = True
        self.webhook_message = "This webhook has been compromised by ratters.rip"
    
    @staticmethod
    def GetDeleteConfig():
        return True