"""Composition root for application services."""

from __future__ import annotations

from database.database import DatabaseManager
from controllers.admin_controller import AdminController
from controllers.claim_controller import ClaimController
from controllers.item_controller import ItemController


class LostFoundSystem:
    """Facade wiring the database and focused application controllers."""

    def __init__(self, database_path: str | None = None) -> None:
        self.database = DatabaseManager(database_path)
        self.items = ItemController(self.database)
        self.claims = ClaimController(self.database)
        self.admin = AdminController(self.database)
