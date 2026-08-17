import hashlib
import secrets

from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

password_hasher = PasswordHash.recommended()
API_KEY_PREFIX = "at_"


def hash_password(password: str) -> str:
    """Create a salted Argon2id hash for a plain-text password."""
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Return whether a plain-text password matches a stored hash."""
    try:
        return password_hasher.verify(password, password_hash)
    except UnknownHashError:
        return False


def generate_api_key() -> str:
    """Create a cryptographically secure API key."""
    return f"{API_KEY_PREFIX}{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Create the deterministic SHA-256 digest stored for an API key."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()
