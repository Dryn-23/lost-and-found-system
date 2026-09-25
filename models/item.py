"""Found-property item entity and its public/private field boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


ITEM_STATUSES = (
    "Available",
    "Pending Claim",
    "Claim Approved",
    "Returned",
    "Archived",
)

CATEGORIES = (
    "Electronics",
    "ID",
    "Bags",
    "Clothing",
    "School Supplies",
    "Accessories",
    "Other",
)


@dataclass
class Item:
    name: str
    category: str
    public_description: str
    color: str
    brand: str
    location_found: str
    date_found: str
    time_found: str
    condition: str
    storage_location: str
    private_notes: str = ""
    photo_path: str = ""
    status: str = "Available"
    id: int | None = None
    finder_id: int | None = None

    def to_record(self) -> dict[str, Any]:
        return {
            "name": self.name.strip(),
            "category": self.category.strip(),
            "public_description": self.public_description.strip(),
            "color": self.color.strip(),
            "brand": self.brand.strip(),
            "location_found": self.location_found.strip(),
            "date_found": self.date_found.strip(),
            "time_found": self.time_found.strip(),
            "condition": self.condition.strip(),
            "storage_location": self.storage_location.strip(),
            "private_notes": self.private_notes.strip(),
            "photo_path": self.photo_path.strip(),
            "status": self.status,
        }

    def public_record(self) -> dict[str, Any]:
        """Return only catalog-safe details; never expose finder/storage/notes."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "public_description": self.public_description,
            "color": self.color,
            "brand": self.brand,
            "location_found": self.location_found,
            "date_found": self.date_found,
            "condition": self.condition,
            "status": self.status,
            "photo_path": self.photo_path,
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "Item":
        keys = cls.__dataclass_fields__.keys()
        return cls(**{key: data[key] for key in keys if key in data})
