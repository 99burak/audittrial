from app.core.security import hash_password, verify_password


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

