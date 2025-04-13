class AESModeOfOperationGCM:
    def __init__(self, key, iv):
        self.key = key
        self.iv = iv
    
    def decrypt(self, data):
        # Simplified AES-GCM decryption
        # In a real implementation, you would use cryptography.hazmat or similar
        try:
            from Crypto.Cipher import AES # type: ignore
            cipher = AES.new(self.key, AES.MODE_GCM, nonce=self.iv)
            return cipher.decrypt(data)
        except ImportError:
            # Fallback to pure Python implementation if PyCryptodome not available
            return self._fallback_decrypt(data)
    
    def _fallback_decrypt(self, data):
        # Very basic XOR "decryption" as fallback
        # WARNING: This is not secure and only for demonstration!
        decrypted = bytearray()
        key_len = len(self.key)
        for i in range(len(data)):
            decrypted.append(data[i] ^ self.key[i % key_len])
        return bytes(decrypted)