# tests/unit/test_security.py

from app.core.security import hash_password, verify_password, create_access_token, decode_access_token


def test_hash_password_produces_different_hash_each_time():
    password = "MotDePasse123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    assert hash1 != hash2  # Argon2 inclut un sel aléatoire


def test_verify_password_correct():
    password = "MotDePasse123"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    hashed = hash_password("MotDePasse123")
    assert verify_password("MauvaisMotDePasse", hashed) is False


def test_access_token_roundtrip():
    token = create_access_token(subject="user-id-123")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user-id-123"
    assert payload["type"] == "access"


def test_decode_invalid_token_returns_none():
    payload = decode_access_token("token.invalide.xyz")
    assert payload is None