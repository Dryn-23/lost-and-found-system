"""Small identity abstractions for the two application roles.

Public visitors are guests by design: they browse and submit a claim without
an account. Only Admin objects are authenticated.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    role: str
    display_name: str


class PublicUser(User):
    """An unauthenticated public visitor; this class has no registration flow."""

    def __init__(self) -> None:
        super().__init__(role="Public User", display_name="Visitor")
