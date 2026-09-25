"""Private finder interview record, composed with a SchoolPerson."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .person import SchoolPerson


@dataclass
class Finder:
    person: SchoolPerson
    where_found: str
    date_found: str
    time_found: str
    circumstances: str
    touched_related: str
    additional_notes: str = ""

    def to_record(self) -> dict[str, Any]:
        """Flatten the person and interview answers for the private DB table."""
        return {
            **self.person.to_record(),
            "where_found": self.where_found.strip(),
            "date_found": self.date_found.strip(),
            "time_found": self.time_found.strip(),
            "circumstances": self.circumstances.strip(),
            "touched_related": self.touched_related.strip(),
            "additional_notes": self.additional_notes.strip(),
        }
