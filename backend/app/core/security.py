from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Create a salted Argon2id hash for a plain-text password."""
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Return whether a plain-text password matches a stored hash."""
    try:
        return password_hasher.verify(password, password_hash)
    except UnknownHashError:
        return False

