"""Application rules for anonymous claim submission and admin review."""

from __future__ import annotations

from typing import Any

from database.database import DatabaseManager
from models.claim import Claim
from utils.validators import validate_claim_record, validate_return_record


class ClaimController:
    def __init__(self, database: DatabaseManager) -> None:
        self.database = database

    def submit_claim(self, claim: Claim) -> str:
        validated = validate_claim_record(claim.to_record())
        return self.database.create_claim(validated)

    def list_claims(self, status: str = "All statuses", search: str = "") -> list[dict[str, Any]]:
        return self.database.list_claims(status=status, search=search)

    def claim(self, claim_row_id: int) -> dict[str, Any] | None:
        return self.database.get_claim(claim_row_id)

    def review(self, claim_row_id: int, status: str, admin_username: str, notes: str = "") -> None:
        self.database.update_claim_status(claim_row_id, status, admin_username, notes)

    def mark_returned(
        self, claim_row_id: int, values: dict[str, Any], admin_username: str
    ) -> None:
        validated = validate_return_record(values)
        self.database.mark_returned(claim_row_id, validated, admin_username)

    def stats(self) -> dict[str, int]:
        return self.database.dashboard_stats()
