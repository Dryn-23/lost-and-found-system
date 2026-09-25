"""Admin identity and password hashing helpers."""

from __future__ import annotations

import hashlib
import hmac
import secrets

from .user import User


class Admin(User):
    """The only authenticated role in the application."""

    HASH_NAME = "sha256"
    ITERATIONS = 240_000

    def __init__(self, username: str, admin_id: int | None = None) -> None:
        super().__init__(role="Admin", display_name=username)
        self.username = username
        self.id = admin_id

    @classmethod
    def hash_password(cls, password: str, salt: str | None = None) -> tuple[str, str]:
        """Return a per-admin random salt and PBKDF2 password hash."""
        salt = salt or secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            cls.HASH_NAME, password.encode("utf-8"), bytes.fromhex(salt), cls.ITERATIONS
        ).hex()
        return salt, digest

    @classmethod
    def verify_password(cls, password: str, salt: str, expected_hash: str) -> bool:
        _, actual_hash = cls.hash_password(password, salt)
        return hmac.compare_digest(actual_hash, expected_hash)
