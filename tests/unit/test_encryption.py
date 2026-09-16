"""Testa a criptografia de campos sensíveis em repouso (Fernet/AES-128).

Cobre o contrato que o resto do sistema depende: o que é escrito por
process_bind_param deve voltar idêntico via process_result_value, e uma
linha legada não criptografada não deve quebrar a leitura (fail-open).
"""

import pytest
from cryptography.fernet import Fernet

from infrastructure.utils.encryption import (
    EncryptedJSON,
    EncryptedText,
    decrypt,
    encrypt,
)


def test_encrypt_decrypt_round_trip():
    plaintext = "Flávio Henrique Madureira Bergamini"
    ciphertext = encrypt(plaintext)
    assert ciphertext != plaintext
    assert decrypt(ciphertext) == plaintext


def test_ciphertext_is_not_plaintext_and_not_predictable():
    ciphertext_a = encrypt("mesmo valor")
    ciphertext_b = encrypt("mesmo valor")
    # Fernet inclui IV/timestamp — duas cifragens do mesmo texto não são iguais
    assert ciphertext_a != ciphertext_b


def test_encrypted_text_bind_then_result_round_trip():
    field = EncryptedText()
    bound = field.process_bind_param("diagnóstico: TEA nível 2", dialect=None)
    assert bound != "diagnóstico: TEA nível 2"
    result = field.process_result_value(bound, dialect=None)
    assert result == "diagnóstico: TEA nível 2"


def test_encrypted_text_handles_none():
    field = EncryptedText()
    assert field.process_bind_param(None, dialect=None) is None
    assert field.process_result_value(None, dialect=None) is None


def test_encrypted_text_fails_open_on_legacy_plaintext_row():
    """Uma linha gravada antes da criptografia ser adotada não deve quebrar a
    leitura — o valor bruto (não descriptografável) é retornado como está."""
    field = EncryptedText()
    legacy_plaintext = "valor gravado antes da migração de criptografia"
    assert field.process_result_value(legacy_plaintext, dialect=None) == legacy_plaintext


def test_encrypted_json_round_trip():
    field = EncryptedJSON()
    payload = {"guardians": ["Ana", "Carlos"], "age": "8"}
    bound = field.process_bind_param(payload, dialect=None)
    assert bound != payload
    result = field.process_result_value(bound, dialect=None)
    assert result == payload


def test_decrypt_with_wrong_key_raises():
    other_key = Fernet.generate_key()
    ciphertext = Fernet(other_key).encrypt(b"segredo").decode()
    with pytest.raises(Exception):
        decrypt(ciphertext)
