import os
import base64

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionService:
    def __init__(self, master_key_hex: str):
        self._key = bytes.fromhex(master_key_hex)
        self._aesgcm = AESGCM(self._key)

    def encrypt(self, plaintext: str) -> tuple[str, str, str]:
        """Returns (encrypted_key, nonce, tag) as base64 strings."""
        nonce = os.urandom(12)
        ciphertext_and_tag = self._aesgcm.encrypt(nonce, plaintext.encode(), None)
        ciphertext = ciphertext_and_tag[:-16]
        tag = ciphertext_and_tag[-16:]
        return (
            base64.b64encode(ciphertext).decode(),
            base64.b64encode(nonce).decode(),
            base64.b64encode(tag).decode(),
        )

    def decrypt(self, encrypted_key: str, nonce: str, tag: str) -> str:
        """Accepts base64 strings and returns decrypted plaintext."""
        ciphertext = base64.b64decode(encrypted_key)
        nonce_bytes = base64.b64decode(nonce)
        tag_bytes = base64.b64decode(tag)
        plaintext = self._aesgcm.decrypt(nonce_bytes, ciphertext + tag_bytes, None)
        return plaintext.decode()

    @staticmethod
    def mask(key: str) -> str:
        if len(key) <= 8:
            return f"{key[0]}...{key[-3:]}"
        return f"{key[:4]}...{key[-4:]}"
