"""Application rules for found-item catalog and admin maintenance."""

from __future__ import annotations

from typing import Any

from database.database import DatabaseManager
from models.finder import Finder
from models.item import Item
from utils.validators import validate_finder_record, validate_item_record


class ItemController:
    def __init__(self, database: DatabaseManager) -> None:
        self.database = database

    def public_catalog(
        self,
        search: str = "",
        category: str = "All",
        location: str = "All locations",
        date_found: str = "",
        status: str = "All statuses",
    ) -> list[dict[str, Any]]:
        return self.database.list_public_items(search, category, location, date_found, status)

    def public_item(self, item_id: int) -> dict[str, Any] | None:
        return self.database.get_public_item(item_id)

    def public_locations(self) -> list[str]:
        return self.database.get_public_locations()

    def admin_items(
        self, search: str = "", category: str = "All", status: str = "All statuses"
    ) -> list[dict[str, Any]]:
        return self.database.list_admin_items(search, category, status)

    def admin_item(self, item_id: int) -> dict[str, Any] | None:
        return self.database.get_admin_item(item_id)

    def possible_duplicate(self, item: Item) -> dict[str, Any] | None:
        data = item.to_record()
        return self.database.find_possible_duplicate_item(
            data["name"], data["date_found"], data["location_found"]
        )

    def add_found_item(self, finder: Finder, item: Item, admin_username: str) -> int:
        finder_record = validate_finder_record(finder.to_record())
        item_record = validate_item_record(item.to_record())
        return self.database.create_found_item(finder_record, item_record, admin_username)

    def update_item(self, item_id: int, values: dict[str, Any], admin_username: str) -> None:
        validated = validate_item_record(values)
        self.database.update_item(item_id, validated, admin_username)

    def archive_item(self, item_id: int, admin_username: str) -> None:
        self.database.archive_item(item_id, admin_username)

    def stats(self) -> dict[str, int]:
        return self.database.dashboard_stats()

    def report_summary(self) -> dict[str, list[dict[str, Any]]]:
        return self.database.report_summary()
