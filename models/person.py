"""School-associated people used for finder interviews and claim forms.

These classes represent a person's stated school affiliation only. They do not
create application accounts and never grant access to the admin area.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SchoolPerson(ABC):
    """Abstract base class shared by students, teachers, and utility staff."""

    def __init__(self, full_name: str, school_id: str, contact_number: str) -> None:
        self._full_name = full_name.strip()
        self._school_id = school_id.strip()
        self._contact_number = contact_number.strip()

    @property
    def full_name(self) -> str:
        return self._full_name

    @property
    def school_id(self) -> str:
        return self._school_id

    @property
    def contact_number(self) -> str:
        return self._contact_number

    @property
    @abstractmethod
    def role(self) -> str:
        """Human-readable school affiliation type."""

    @property
    @abstractmethod
    def affiliation(self) -> str:
        """Course/grade, department, or assigned area."""

    @property
    def section(self) -> str | None:
        return None

    def to_record(self) -> dict[str, Any]:
        """Polymorphic common record shape used by finder and claim storage."""
        return {
            "person_type": self.role,
            "school_id": self.school_id,
            "full_name": self.full_name,
            "contact_number": self.contact_number,
            "affiliation": self.affiliation,
            "section": self.section,
        }


class Student(SchoolPerson):
    def __init__(
        self,
        full_name: str,
        school_id: str,
        contact_number: str,
        grade_course: str,
        section: str,
    ) -> None:
        super().__init__(full_name, school_id, contact_number)
        self._grade_course = grade_course.strip()
        self._section = section.strip()

    @property
    def role(self) -> str:
        return "Student"

    @property
    def affiliation(self) -> str:
        return self._grade_course

    @property
    def section(self) -> str:
        return self._section


class Teacher(SchoolPerson):
    def __init__(
        self,
        full_name: str,
        school_id: str,
        contact_number: str,
        department: str,
    ) -> None:
        super().__init__(full_name, school_id, contact_number)
        self._department = department.strip()

    @property
    def role(self) -> str:
        return "Teacher"

    @property
    def affiliation(self) -> str:
        return self._department


class UtilityStaff(SchoolPerson):
    def __init__(
        self,
        full_name: str,
        school_id: str,
        contact_number: str,
        assigned_area: str,
    ) -> None:
        super().__init__(full_name, school_id, contact_number)
        self._assigned_area = assigned_area.strip()

    @property
    def role(self) -> str:
        return "School Utility Personnel"

    @property
    def affiliation(self) -> str:
        return self._assigned_area


def make_school_person(role: str, data: dict[str, Any]) -> SchoolPerson:
    """Factory that returns the appropriate polymorphic school-person type."""
    common = {
        "full_name": str(data.get("full_name", "")),
        "school_id": str(data.get("school_id", data.get("employee_id", ""))),
        "contact_number": str(data.get("contact_number", "")),
    }
    if role == "Student":
        return Student(
            **common,
            grade_course=str(data.get("grade_course", data.get("affiliation", ""))),
            section=str(data.get("section", "")),
        )
    if role == "Teacher":
        return Teacher(
            **common,
            department=str(data.get("department", data.get("affiliation", ""))),
        )
    if role == "School Utility Personnel":
        return UtilityStaff(
            **common,
            assigned_area=str(data.get("assigned_area", data.get("affiliation", ""))),
        )
    raise ValueError("Choose Student, Teacher, or School Utility Personnel.")
