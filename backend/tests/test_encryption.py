import os

from app.services.encryption import EncryptionService


def test_encrypt_decrypt_roundtrip():
    master_key = os.urandom(32).hex()
    svc = EncryptionService(master_key)

    plaintext = "sk-test-api-key-1234567890"
    encrypted, nonce, tag = svc.encrypt(plaintext)

    assert encrypted != plaintext.encode()
    assert svc.decrypt(encrypted, nonce, tag) == plaintext


def test_decrypt_with_wrong_key_fails():
    key1 = os.urandom(32).hex()
    key2 = os.urandom(32).hex()
    svc1 = EncryptionService(key1)
    svc2 = EncryptionService(key2)

    encrypted, nonce, tag = svc1.encrypt("secret")
    try:
        svc2.decrypt(encrypted, nonce, tag)
        assert False, "Should have raised an error"
    except Exception:
        pass


def test_mask_key_long():
    assert EncryptionService.mask("sk-proj-abcdefghijklmnop") == "sk-p...mnop"


def test_mask_key_short():
    assert EncryptionService.mask("short") == "s...ort"


def test_mask_key_minimum():
    assert EncryptionService.mask("abcd") == "a...bcd"
