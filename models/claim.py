"""Claim entity. A claim is a request for admin review, never an auto-release."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .person import SchoolPerson


CLAIM_STATUSES = ("Pending", "Verification Requested", "Approved", "Rejected", "Completed")


@dataclass
class Claim:
    item_id: int
    claimant: SchoolPerson
    last_seen_location: str
    last_seen_date: str
    item_description: str
    identifying_features: str
    additional_info: str = ""
    id: int | None = None
    claim_id: str = ""
    status: str = "Pending"

    def to_record(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            **self.claimant.to_record(),
            "last_seen_location": self.last_seen_location.strip(),
            "last_seen_date": self.last_seen_date.strip(),
            "item_description": self.item_description.strip(),
            "identifying_features": self.identifying_features.strip(),
            "additional_info": self.additional_info.strip(),
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> dict[str, Any]:
        """Return a plain representation for display without exposing secrets."""
        return dict(data)
