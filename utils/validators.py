"""Input validation shared by Tkinter views and application controllers."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any


class ValidationError(ValueError):
    """A user-correctable form validation error."""


CONTACT_RE = re.compile(r"^[+0-9][0-9\s().-]{5,19}$")


def required(value: Any, label: str, max_length: int = 500) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValidationError(f"{label} is required.")
    if len(text) > max_length:
        raise ValidationError(f"{label} must be {max_length} characters or fewer.")
    return text


def optional(value: Any, label: str, max_length: int = 500) -> str:
    text = str(value or "").strip()
    if len(text) > max_length:
        raise ValidationError(f"{label} must be {max_length} characters or fewer.")
    return text


def validate_school_id(value: Any, label: str = "Student/Employee ID") -> str:
    text = required(value, label, 40)
    if len(text) < 2:
        raise ValidationError(f"{label} must contain at least 2 characters.")
    if any(ord(char) < 32 for char in text):
        raise ValidationError(f"{label} contains an invalid character.")
    return text


def validate_contact(value: Any) -> str:
    text = required(value, "Contact number", 30)
    digits = sum(character.isdigit() for character in text)
    if not CONTACT_RE.fullmatch(text) or not 7 <= digits <= 15:
        raise ValidationError(
            "Enter a valid contact number with 7 to 15 digits (spaces, +, -, and parentheses are allowed)."
        )
    return text


def validate_date(value: Any, label: str) -> str:
    text = required(value, label, 10)
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError as exc:
        raise ValidationError(f"{label} must use YYYY-MM-DD format (for example, 2026-09-20).") from exc
    return text


def validate_time(value: Any, label: str) -> str:
    text = required(value, label, 5)
    try:
        datetime.strptime(text, "%H:%M")
    except ValueError as exc:
        raise ValidationError(f"{label} must use 24-hour HH:MM format (for example, 14:30).") from exc
    return text


def validate_person_record(data: dict[str, Any]) -> dict[str, Any]:
    role = required(data.get("person_type"), "School role", 50)
    if role not in ("Student", "Teacher", "School Utility Personnel"):
        raise ValidationError("Choose Student, Teacher, or School Utility Personnel.")
    label = "Student ID" if role == "Student" else "Employee ID"
    result = {
        "person_type": role,
        "school_id": validate_school_id(data.get("school_id"), label),
        "full_name": required(data.get("full_name"), "Full name", 120),
        "contact_number": validate_contact(data.get("contact_number")),
        "affiliation": required(data.get("affiliation"), "Course/grade, department, or assigned area", 120),
        "section": optional(data.get("section"), "Section", 80),
    }
    if role == "Student" and not result["section"]:
        raise ValidationError("Section is required for a student.")
    return result


def validate_finder_record(data: dict[str, Any]) -> dict[str, Any]:
    result = validate_person_record(data)
    result.update(
        {
            "where_found": required(data.get("where_found"), "Where the item was found", 180),
            "date_found": validate_date(data.get("date_found"), "Date found"),
            "time_found": validate_time(data.get("time_found"), "Time found"),
            "circumstances": required(data.get("circumstances"), "Circumstances when found", 600),
            "touched_related": required(data.get("touched_related"), "Handling details", 300),
            "additional_notes": optional(data.get("additional_notes"), "Finder notes", 1000),
        }
    )
    return result


def validate_item_record(data: dict[str, Any]) -> dict[str, Any]:
    category = required(data.get("category"), "Category", 60)
    from models.item import CATEGORIES

    if category not in CATEGORIES:
        raise ValidationError("Choose a category from the list.")
    result = {
        "name": required(data.get("name"), "Item name", 120),
        "category": category,
        "public_description": required(data.get("public_description"), "Public description", 500),
        "color": optional(data.get("color"), "Color", 80),
        "brand": optional(data.get("brand"), "Brand", 100),
        "location_found": required(data.get("location_found"), "General location found", 180),
        "date_found": validate_date(data.get("date_found"), "Date found"),
        "time_found": validate_time(data.get("time_found"), "Time found"),
        "condition": required(data.get("condition"), "Condition", 80),
        "storage_location": required(data.get("storage_location"), "Private storage location", 180),
        "private_notes": optional(data.get("private_notes"), "Private notes", 2000),
        "photo_path": optional(data.get("photo_path"), "Photo path", 1000),
    }
    return result


def validate_claim_record(data: dict[str, Any]) -> dict[str, Any]:
    result = validate_person_record(data)
    result.update(
        {
            "item_id": int(data.get("item_id", 0)),
            "last_seen_location": required(data.get("last_seen_location"), "Where the item was last seen", 180),
            "last_seen_date": validate_date(data.get("last_seen_date"), "Date last seen"),
            "item_description": required(data.get("item_description"), "Item description", 800),
            "identifying_features": required(data.get("identifying_features"), "Ownership/identifying details", 800),
            "additional_info": optional(data.get("additional_info"), "Additional information", 1200),
        }
    )
    if result["item_id"] <= 0:
        raise ValidationError("The selected item is not valid. Please reopen its details and try again.")
    return result


def validate_return_record(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "returned_date": validate_date(data.get("returned_date"), "Returned date"),
        "returned_time": validate_time(data.get("returned_time"), "Returned time"),
        "released_by": required(data.get("released_by"), "Released by", 120),
        "claimant_name": required(data.get("claimant_name"), "Claimant name", 120),
        "notes": optional(data.get("notes"), "Return notes", 1000),
    }
