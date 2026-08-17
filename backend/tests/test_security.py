from app.core.security import (
    generate_api_key,
    hash_api_key,
    hash_password,
    verify_password,
)


def test_hash_password_uses_argon2id_and_hides_plain_text() -> None:
    password = "correct-horse-battery-staple"

    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$argon2id$")


def test_verify_password_accepts_correct_password() -> None:
    password_hash = hash_password("a-secure-test-password")

    assert verify_password("a-secure-test-password", password_hash) is True


def test_verify_password_rejects_wrong_password() -> None:
    password_hash = hash_password("a-secure-test-password")

    assert verify_password("wrong-password", password_hash) is False


def test_hashing_same_password_twice_produces_different_hashes() -> None:
    password = "same-password-with-random-salts"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash
    assert verify_password(password, first_hash) is True
    assert verify_password(password, second_hash) is True


def test_verify_password_rejects_unrecognized_hash() -> None:
    assert verify_password("password", "not-a-valid-password-hash") is False


def test_generate_api_key_creates_distinct_random_values() -> None:
    first_api_key = generate_api_key()
    second_api_key = generate_api_key()

    assert first_api_key.startswith("at_")
    assert second_api_key.startswith("at_")
    assert first_api_key != second_api_key
    assert len(first_api_key) >= 40


def test_hash_api_key_returns_deterministic_sha256_digest() -> None:
    api_key = generate_api_key()

    first_hash = hash_api_key(api_key)
    second_hash = hash_api_key(api_key)

    assert first_hash == second_hash
    assert len(first_hash) == 64
    assert api_key not in first_hash
