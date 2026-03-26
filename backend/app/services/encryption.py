import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionService:
    def __init__(self, master_key_hex: str):
        self._key = bytes.fromhex(master_key_hex)
        self._aesgcm = AESGCM(self._key)

    def encrypt(self, plaintext: str) -> tuple[bytes, bytes, bytes]:
        nonce = os.urandom(12)
        ciphertext_and_tag = self._aesgcm.encrypt(nonce, plaintext.encode(), None)
        ciphertext = ciphertext_and_tag[:-16]
        tag = ciphertext_and_tag[-16:]
        return ciphertext, nonce, tag

    def decrypt(self, ciphertext: bytes, nonce: bytes, tag: bytes) -> str:
        plaintext = self._aesgcm.decrypt(nonce, ciphertext + tag, None)
        return plaintext.decode()

    @staticmethod
    def mask(key: str) -> str:
        if len(key) <= 8:
            return f"{key[0]}...{key[-3:]}"
        return f"{key[:4]}...{key[-4:]}"
