"""SQLite persistence layer for Lost Today, Found Someday.

All statements are parameterized. Public catalog queries deliberately select a
small allow-list of item columns and never join to the private finder table.
"""

from __future__ import annotations

import sqlite3
import secrets
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterator

from models.admin import Admin


class DuplicateClaimError(ValueError):
    """The same school ID already has an active claim for the item."""


class ItemUnavailableError(ValueError):
    """The item cannot accept the requested claim or status transition."""


class DatabaseManager:
    """Owns schema creation, demo seeding, and all SQLite operations."""

    def __init__(self, db_path: str | Path | None = None, seed_demo: bool = True) -> None:
        default_path = Path(__file__).resolve().parent / "lost_found.db"
        self.db_path = Path(db_path) if db_path else default_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()
        self._seed_default_admin()
        if seed_demo:
            self._seed_demo_items_if_empty()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path, timeout=8.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 8000")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    @staticmethod
    def _row_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
        return dict(row) if row is not None else None

    def _initialize_schema(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS finders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_type TEXT NOT NULL CHECK(person_type IN ('Student', 'Teacher', 'School Utility Personnel')),
            school_id TEXT NOT NULL,
            full_name TEXT NOT NULL,
            contact_number TEXT NOT NULL,
            affiliation TEXT NOT NULL,
            section TEXT NOT NULL DEFAULT '',
            where_found TEXT NOT NULL,
            date_found TEXT NOT NULL,
            time_found TEXT NOT NULL,
            circumstances TEXT NOT NULL,
            touched_related TEXT NOT NULL,
            additional_notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            public_description TEXT NOT NULL,
            color TEXT NOT NULL DEFAULT '',
            brand TEXT NOT NULL DEFAULT '',
            location_found TEXT NOT NULL,
            date_found TEXT NOT NULL,
            time_found TEXT NOT NULL,
            condition TEXT NOT NULL,
            storage_location TEXT NOT NULL,
            private_notes TEXT NOT NULL DEFAULT '',
            photo_path TEXT NOT NULL DEFAULT '',
            finder_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Available'
                CHECK(status IN ('Available', 'Pending Claim', 'Claim Approved', 'Returned', 'Archived')),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(finder_id) REFERENCES finders(id)
        );

        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id TEXT NOT NULL UNIQUE,
            item_id INTEGER NOT NULL,
            claimant_type TEXT NOT NULL CHECK(claimant_type IN ('Student', 'Teacher', 'School Utility Personnel')),
            school_id TEXT NOT NULL,
            full_name TEXT NOT NULL,
            contact_number TEXT NOT NULL,
            affiliation TEXT NOT NULL,
            section TEXT NOT NULL DEFAULT '',
            last_seen_location TEXT NOT NULL,
            last_seen_date TEXT NOT NULL,
            item_description TEXT NOT NULL,
            identifying_features TEXT NOT NULL,
            additional_info TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Pending'
                CHECK(status IN ('Pending', 'Verification Requested', 'Approved', 'Rejected', 'Completed')),
            submitted_at TEXT NOT NULL,
            admin_notes TEXT NOT NULL DEFAULT '',
            reviewed_by TEXT NOT NULL DEFAULT '',
            reviewed_at TEXT NOT NULL DEFAULT '',
            FOREIGN KEY(item_id) REFERENCES items(id)
        );

        CREATE TABLE IF NOT EXISTS claim_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id INTEGER NOT NULL,
            admin_username TEXT NOT NULL,
            action TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(claim_id) REFERENCES claims(id)
        );

        CREATE TABLE IF NOT EXISTS returns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            claim_id INTEGER NOT NULL UNIQUE,
            returned_date TEXT NOT NULL,
            returned_time TEXT NOT NULL,
            released_by TEXT NOT NULL,
            claimant_name TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(item_id) REFERENCES items(id),
            FOREIGN KEY(claim_id) REFERENCES claims(id)
        );

        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_username TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
        CREATE INDEX IF NOT EXISTS idx_items_date ON items(date_found);
        CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status);
        CREATE INDEX IF NOT EXISTS idx_claims_item ON claims(item_id);
        CREATE INDEX IF NOT EXISTS idx_finders_school_id ON finders(school_id);
        CREATE INDEX IF NOT EXISTS idx_activity_created ON activity_logs(created_at);
        """
        with self._connection() as connection:
            connection.executescript(schema)

    def _seed_default_admin(self) -> None:
        with self._connection() as connection:
            exists = connection.execute("SELECT 1 FROM admins LIMIT 1").fetchone()
            if exists:
                return
            salt, digest = Admin.hash_password("admin123")
            connection.execute(
                "INSERT INTO admins(username, password_salt, password_hash, created_at) VALUES (?, ?, ?, ?)",
                ("admin", salt, digest, self._now()),
            )

    def _seed_demo_items_if_empty(self) -> None:
        examples = [
            ("Black Samsung Smartphone", "Electronics", "DEMO SAMPLE — Black touchscreen smartphone in a protective case; identifying details withheld.", "Black", "Samsung", "Main Building", "Good"),
            ("Blue Water Bottle", "Other", "DEMO SAMPLE — Reusable blue bottle with a screw-top lid.", "Blue", "Unmarked", "Library", "Good"),
            ("Black Backpack", "Bags", "DEMO SAMPLE — Medium black backpack with multiple compartments.", "Black", "Unmarked", "Gymnasium", "Good"),
            ("Student ID", "ID", "DEMO SAMPLE — School identification card turned in; personal details are not displayed.", "Blue / White", "School-issued", "Cafeteria", "Good"),
            ("Scientific Calculator", "School Supplies", "DEMO SAMPLE — Scientific calculator with a protective slide cover.", "Black", "Casio", "Room 204", "Good"),
            ("USB Flash Drive", "Electronics", "DEMO SAMPLE — Small USB storage device; capacity and contents withheld.", "Silver", "Unmarked", "Computer Lab", "Fair"),
            ("House Keys", "Accessories", "DEMO SAMPLE — Small key ring with several keys; distinctive key details withheld.", "Silver", "Unmarked", "Covered Walkway", "Good"),
            ("Black Wallet", "Accessories", "DEMO SAMPLE — Compact black wallet; contents are private and not shown.", "Black", "Unmarked", "Admin Hallway", "Fair"),
            ("Notebook", "School Supplies", "DEMO SAMPLE — Spiral-bound lined notebook with a plain cover.", "Green", "Unmarked", "Science Wing", "Good"),
            ("Umbrella", "Other", "DEMO SAMPLE — Foldable umbrella with a dark canopy and curved handle.", "Navy", "Unmarked", "East Gate", "Good"),
        ]
        today = date.today()
        with self._connection() as connection:
            count = connection.execute("SELECT COUNT(*) AS count FROM items").fetchone()["count"]
            if count:
                return
            for index, sample in enumerate(examples):
                name, category, description, color, brand, location, condition = sample
                found_day = today - timedelta(days=(index % 6) + 1)
                finder_cursor = connection.execute(
                    """INSERT INTO finders(
                        person_type, school_id, full_name, contact_number, affiliation, section,
                        where_found, date_found, time_found, circumstances, touched_related,
                        additional_notes, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        "Student" if index % 3 == 0 else ("Teacher" if index % 3 == 1 else "School Utility Personnel"),
                        f"DEMO-{index + 1:03d}",
                        "Demo Finder (fictional)",
                        "000-000-0000",
                        "Demo department / grade",
                        "DEMO-SECTION" if index % 3 == 0 else "",
                        location,
                        found_day.isoformat(),
                        "10:15",
                        "Fictional sample record created automatically for demonstration.",
                        "Demo response: handled only to bring it to the office.",
                        "DEMO DATA ONLY — replace with an Admin Office interview after first launch.",
                        self._now(),
                    ),
                )
                connection.execute(
                    """INSERT INTO items(
                        name, category, public_description, color, brand, location_found,
                        date_found, time_found, condition, storage_location, private_notes,
                        photo_path, finder_id, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Available', ?, ?)""",
                    (
                        name,
                        category,
                        description,
                        color,
                        brand,
                        location,
                        found_day.isoformat(),
                        "10:15",
                        condition,
                        "Demo shelf — Lost & Found Office",
                        "Demo record; no real person or school item is represented.",
                        "",
                        finder_cursor.lastrowid,
                        self._now(),
                        self._now(),
                    ),
                )

    @staticmethod
    def _log(connection: sqlite3.Connection, username: str, action: str, details: str = "") -> None:
        connection.execute(
            "INSERT INTO activity_logs(admin_username, action, details, created_at) VALUES (?, ?, ?, ?)",
            (username, action, details, DatabaseManager._now()),
        )

    # --- Admin authentication -------------------------------------------------

    def authenticate_admin(self, username: str, password: str) -> Admin | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT id, username, password_salt, password_hash FROM admins WHERE username = ? COLLATE NOCASE",
                (username.strip(),),
            ).fetchone()
        if not row or not Admin.verify_password(password, row["password_salt"], row["password_hash"]):
            return None
        return Admin(username=row["username"], admin_id=row["id"])

    def log_activity(self, username: str, action: str, details: str = "") -> None:
        with self._connection() as connection:
            self._log(connection, username, action, details)

    # --- Public catalog: only safe, allow-listed columns ----------------------

    def list_public_items(
        self,
        search: str = "",
        category: str = "All",
        location: str = "All locations",
        date_found: str = "",
        status: str = "All statuses",
    ) -> list[dict[str, Any]]:
        sql = """SELECT id, name, category, public_description, color, brand,
                        location_found, date_found, condition, status, photo_path
                 FROM items WHERE status IN ('Available', 'Pending Claim')"""
        values: list[Any] = []
        if search.strip():
            pattern = f"%{search.strip()}%"
            sql += " AND (name LIKE ? OR category LIKE ? OR color LIKE ? OR brand LIKE ? OR location_found LIKE ?)"
            values.extend([pattern] * 5)
        if category and category != "All":
            sql += " AND category = ?"
            values.append(category)
        if location and location != "All locations":
            sql += " AND location_found = ?"
            values.append(location)
        if date_found:
            sql += " AND date_found = ?"
            values.append(date_found)
        if status and status != "All statuses":
            if status not in ("Available", "Pending Claim"):
                return []
            sql += " AND status = ?"
            values.append(status)
        sql += " ORDER BY date_found DESC, created_at DESC, id DESC"
        with self._connection() as connection:
            rows = connection.execute(sql, values).fetchall()
        return [dict(row) for row in rows]

    def get_public_item(self, item_id: int) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                """SELECT id, name, category, public_description, color, brand,
                          location_found, date_found, condition, status, photo_path
                   FROM items WHERE id = ? AND status IN ('Available', 'Pending Claim')""",
                (item_id,),
            ).fetchone()
        return self._row_dict(row)

    def get_public_locations(self) -> list[str]:
        with self._connection() as connection:
            rows = connection.execute(
                """SELECT DISTINCT location_found FROM items
                   WHERE status IN ('Available', 'Pending Claim') ORDER BY location_found COLLATE NOCASE"""
            ).fetchall()
        return [row["location_found"] for row in rows]

    # --- Admin item and finder management -------------------------------------

    def list_admin_items(
        self, search: str = "", category: str = "All", status: str = "All statuses"
    ) -> list[dict[str, Any]]:
        sql = """SELECT i.*, f.full_name AS finder_name, f.person_type AS finder_type,
                          f.school_id AS finder_school_id
                   FROM items i JOIN finders f ON f.id = i.finder_id WHERE 1 = 1"""
        values: list[Any] = []
        if search.strip():
            pattern = f"%{search.strip()}%"
            sql += " AND (i.name LIKE ? OR i.category LIKE ? OR i.location_found LIKE ? OR f.full_name LIKE ? OR f.school_id LIKE ?)"
            values.extend([pattern] * 5)
        if category and category != "All":
            sql += " AND i.category = ?"
            values.append(category)
        if status and status != "All statuses":
            sql += " AND i.status = ?"
            values.append(status)
        sql += " ORDER BY i.created_at DESC, i.id DESC"
        with self._connection() as connection:
            rows = connection.execute(sql, values).fetchall()
        return [dict(row) for row in rows]

    def get_admin_item(self, item_id: int) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                """SELECT i.*, f.person_type AS finder_type, f.school_id AS finder_school_id,
                          f.full_name AS finder_name, f.contact_number AS finder_contact,
                          f.affiliation AS finder_affiliation, f.section AS finder_section,
                          f.where_found AS finder_where_found, f.date_found AS finder_date_found,
                          f.time_found AS finder_time_found, f.circumstances AS finder_circumstances,
                          f.touched_related AS finder_touched_related,
                          f.additional_notes AS finder_additional_notes
                   FROM items i JOIN finders f ON f.id = i.finder_id WHERE i.id = ?""",
                (item_id,),
            ).fetchone()
        return self._row_dict(row)

    def find_possible_duplicate_item(self, name: str, date_found: str, location_found: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                """SELECT id, name, category, date_found, location_found, status FROM items
                   WHERE lower(name) = lower(?) AND date_found = ?
                     AND lower(location_found) = lower(?) AND status != 'Archived'
                   ORDER BY id DESC LIMIT 1""",
                (name.strip(), date_found.strip(), location_found.strip()),
            ).fetchone()
        return self._row_dict(row)

    def create_found_item(
        self, finder_data: dict[str, Any], item_data: dict[str, Any], admin_username: str
    ) -> int:
        now = self._now()
        with self._connection() as connection:
            finder_cursor = connection.execute(
                """INSERT INTO finders(
                    person_type, school_id, full_name, contact_number, affiliation, section,
                    where_found, date_found, time_found, circumstances, touched_related,
                    additional_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    finder_data["person_type"], finder_data["school_id"], finder_data["full_name"],
                    finder_data["contact_number"], finder_data["affiliation"], finder_data.get("section", ""),
                    finder_data["where_found"], finder_data["date_found"], finder_data["time_found"],
                    finder_data["circumstances"], finder_data["touched_related"],
                    finder_data.get("additional_notes", ""), now,
                ),
            )
            item_cursor = connection.execute(
                """INSERT INTO items(
                    name, category, public_description, color, brand, location_found, date_found,
                    time_found, condition, storage_location, private_notes, photo_path, finder_id,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Available', ?, ?)""",
                (
                    item_data["name"], item_data["category"], item_data["public_description"],
                    item_data.get("color", ""), item_data.get("brand", ""), item_data["location_found"],
                    item_data["date_found"], item_data["time_found"], item_data["condition"],
                    item_data["storage_location"], item_data.get("private_notes", ""),
                    item_data.get("photo_path", ""), finder_cursor.lastrowid, now, now,
                ),
            )
            item_id = int(item_cursor.lastrowid)
            self._log(
                connection,
                admin_username,
                "Received found item",
                f"Physical item for '{item_data['name']}' accepted at the Admin Office; finder interview recorded.",
            )
            self._log(
                connection,
                admin_username,
                "Added found item",
                f"Item #{item_id}: {item_data['name']} added to the public catalog.",
            )
        return item_id

    def update_item(self, item_id: int, item_data: dict[str, Any], admin_username: str) -> None:
        with self._connection() as connection:
            row = connection.execute("SELECT status, name FROM items WHERE id = ?", (item_id,)).fetchone()
            if not row:
                raise ValueError("Item record was not found.")
            if row["status"] in ("Returned", "Archived"):
                raise ItemUnavailableError("Returned or archived item records are read-only.")
            connection.execute(
                """UPDATE items SET name = ?, category = ?, public_description = ?, color = ?, brand = ?,
                   location_found = ?, date_found = ?, time_found = ?, condition = ?, storage_location = ?,
                   private_notes = ?, photo_path = ?, updated_at = ? WHERE id = ?""",
                (
                    item_data["name"], item_data["category"], item_data["public_description"],
                    item_data.get("color", ""), item_data.get("brand", ""), item_data["location_found"],
                    item_data["date_found"], item_data["time_found"], item_data["condition"],
                    item_data["storage_location"], item_data.get("private_notes", ""),
                    item_data.get("photo_path", ""), self._now(), item_id,
                ),
            )
            self._log(connection, admin_username, "Updated item", f"Item #{item_id}: {item_data['name']}.")

    def archive_item(self, item_id: int, admin_username: str) -> None:
        with self._connection() as connection:
            row = connection.execute("SELECT status, name FROM items WHERE id = ?", (item_id,)).fetchone()
            if not row:
                raise ValueError("Item record was not found.")
            if row["status"] != "Available":
                raise ItemUnavailableError(
                    "Only an available item can be archived. Resolve active claims or complete the return first."
                )
            connection.execute(
                "UPDATE items SET status = 'Archived', updated_at = ? WHERE id = ?",
                (self._now(), item_id),
            )
            self._log(connection, admin_username, "Archived item", f"Item #{item_id}: {row['name']}.")

    # --- Public claims and admin verification ---------------------------------

    def create_claim(self, claim_data: dict[str, Any]) -> str:
        now = self._now()
        with self._connection() as connection:
            item = connection.execute(
                "SELECT id, status, name FROM items WHERE id = ?", (claim_data["item_id"],)
            ).fetchone()
            if not item or item["status"] not in ("Available", "Pending Claim"):
                raise ItemUnavailableError("This item is no longer accepting claims. Please refresh the catalog.")
            duplicate = connection.execute(
                """SELECT 1 FROM claims WHERE item_id = ? AND lower(school_id) = lower(?)
                   AND status IN ('Pending', 'Verification Requested') LIMIT 1""",
                (claim_data["item_id"], claim_data["school_id"].strip()),
            ).fetchone()
            if duplicate:
                raise DuplicateClaimError("A pending claim for this item already exists under that school ID.")
            cursor = connection.execute(
                """INSERT INTO claims(
                    claim_id, item_id, claimant_type, school_id, full_name, contact_number,
                    affiliation, section, last_seen_location, last_seen_date, item_description,
                    identifying_features, additional_info, status, submitted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?)""",
                (
                    f"TMP-{secrets.token_hex(16)}", claim_data["item_id"], claim_data["person_type"],
                    claim_data["school_id"], claim_data["full_name"], claim_data["contact_number"],
                    claim_data["affiliation"], claim_data.get("section", ""),
                    claim_data["last_seen_location"], claim_data["last_seen_date"],
                    claim_data["item_description"], claim_data["identifying_features"],
                    claim_data.get("additional_info", ""), now,
                ),
            )
            internal_id = int(cursor.lastrowid)
            claim_code = f"CLAIM-{date.today().year}-{internal_id:05d}"
            connection.execute("UPDATE claims SET claim_id = ? WHERE id = ?", (claim_code, internal_id))
            if item["status"] == "Available":
                connection.execute(
                    "UPDATE items SET status = 'Pending Claim', updated_at = ? WHERE id = ?",
                    (now, claim_data["item_id"]),
                )
        return claim_code

    def list_claims(self, status: str = "All statuses", search: str = "") -> list[dict[str, Any]]:
        sql = """SELECT c.*, i.name AS item_name, i.category AS item_category,
                          i.status AS item_status
                   FROM claims c JOIN items i ON i.id = c.item_id WHERE 1 = 1"""
        values: list[Any] = []
        if status and status != "All statuses":
            sql += " AND c.status = ?"
            values.append(status)
        if search.strip():
            pattern = f"%{search.strip()}%"
            sql += " AND (c.claim_id LIKE ? OR c.full_name LIKE ? OR c.school_id LIKE ? OR i.name LIKE ?)"
            values.extend([pattern] * 4)
        sql += " ORDER BY c.submitted_at DESC, c.id DESC"
        with self._connection() as connection:
            rows = connection.execute(sql, values).fetchall()
        return [dict(row) for row in rows]

    def get_claim(self, claim_row_id: int) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                """SELECT c.*, i.name AS item_name, i.category AS item_category,
                          i.location_found AS item_location, i.status AS item_status
                   FROM claims c JOIN items i ON i.id = c.item_id WHERE c.id = ?""",
                (claim_row_id,),
            ).fetchone()
        return self._row_dict(row)

    def update_claim_status(
        self, claim_row_id: int, new_status: str, admin_username: str, notes: str = ""
    ) -> None:
        allowed = {"Verification Requested", "Approved", "Rejected"}
        if new_status not in allowed:
            raise ValueError("Unsupported claim decision.")
        now = self._now()
        with self._connection() as connection:
            claim = connection.execute(
                "SELECT id, item_id, claim_id, status, full_name FROM claims WHERE id = ?",
                (claim_row_id,),
            ).fetchone()
            if not claim:
                raise ValueError("Claim record was not found.")
            if claim["status"] not in ("Pending", "Verification Requested"):
                raise ValueError("Only pending claims can be reviewed. Refresh the claims list.")
            item = connection.execute("SELECT status FROM items WHERE id = ?", (claim["item_id"],)).fetchone()
            if not item:
                raise ValueError("The related item was not found.")
            if new_status == "Approved":
                if item["status"] not in ("Available", "Pending Claim"):
                    raise ItemUnavailableError("Another claim was approved or this item is no longer active.")
                connection.execute(
                    "UPDATE items SET status = 'Claim Approved', updated_at = ? WHERE id = ?",
                    (now, claim["item_id"]),
                )
            connection.execute(
                """UPDATE claims SET status = ?, admin_notes = ?, reviewed_by = ?, reviewed_at = ?
                   WHERE id = ?""",
                (new_status, notes.strip(), admin_username, now, claim_row_id),
            )
            if new_status == "Rejected" and item["status"] == "Pending Claim":
                remaining = connection.execute(
                    """SELECT COUNT(*) AS count FROM claims WHERE item_id = ?
                       AND status IN ('Pending', 'Verification Requested')""",
                    (claim["item_id"],),
                ).fetchone()["count"]
                next_status = "Pending Claim" if remaining else "Available"
                connection.execute(
                    "UPDATE items SET status = ?, updated_at = ? WHERE id = ?",
                    (next_status, now, claim["item_id"]),
                )
            self._log(
                connection,
                admin_username,
                {
                    "Verification Requested": "Requested claim verification",
                    "Approved": "Approved claim",
                    "Rejected": "Rejected claim",
                }[new_status],
                f"{claim['claim_id']} for item #{claim['item_id']} ({claim['full_name']}). {notes.strip()}".strip(),
            )
            connection.execute(
                """INSERT INTO claim_verifications(claim_id, admin_username, action, notes, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (claim_row_id, admin_username, new_status, notes.strip(), now),
            )

    def mark_returned(
        self, claim_row_id: int, return_data: dict[str, Any], admin_username: str
    ) -> None:
        now = self._now()
        with self._connection() as connection:
            claim = connection.execute(
                "SELECT id, item_id, claim_id, status, full_name FROM claims WHERE id = ?",
                (claim_row_id,),
            ).fetchone()
            if not claim:
                raise ValueError("Claim record was not found.")
            if claim["status"] != "Approved":
                raise ItemUnavailableError("Only an approved claim can be marked returned.")
            item = connection.execute("SELECT status FROM items WHERE id = ?", (claim["item_id"],)).fetchone()
            if not item or item["status"] != "Claim Approved":
                raise ItemUnavailableError("The item is not in an approved-for-release state.")
            connection.execute(
                """INSERT INTO returns(
                    item_id, claim_id, returned_date, returned_time, released_by,
                    claimant_name, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    claim["item_id"], claim_row_id, return_data["returned_date"],
                    return_data["returned_time"], return_data["released_by"],
                    return_data["claimant_name"], return_data.get("notes", ""), now,
                ),
            )
            connection.execute(
                "UPDATE items SET status = 'Returned', updated_at = ? WHERE id = ?",
                (now, claim["item_id"]),
            )
            connection.execute(
                "UPDATE claims SET status = 'Completed', reviewed_by = ?, reviewed_at = ? WHERE id = ?",
                (admin_username, now, claim_row_id),
            )
            self._log(
                connection,
                admin_username,
                "Marked item as returned",
                f"{claim['claim_id']} / item #{claim['item_id']} physically released to {return_data['claimant_name']}.",
            )

    # --- Private finder, return, dashboard, and reporting views ----------------

    def list_finders(self, search: str = "") -> list[dict[str, Any]]:
        sql = """SELECT f.id, f.person_type, f.school_id, f.full_name, f.contact_number,
                          f.affiliation, f.section, f.where_found, f.date_found, f.time_found,
                          f.created_at, COUNT(i.id) AS item_count,
                          GROUP_CONCAT(i.name, ', ') AS item_names
                   FROM finders f LEFT JOIN items i ON i.finder_id = f.id"""
        values: list[Any] = []
        if search.strip():
            pattern = f"%{search.strip()}%"
            sql += " WHERE (f.full_name LIKE ? OR f.school_id LIKE ? OR f.person_type LIKE ? OR f.affiliation LIKE ?)"
            values.extend([pattern] * 4)
        sql += " GROUP BY f.id ORDER BY f.created_at DESC, f.id DESC"
        with self._connection() as connection:
            rows = connection.execute(sql, values).fetchall()
        return [dict(row) for row in rows]

    def get_finder(self, finder_id: int) -> dict[str, Any] | None:
        with self._connection() as connection:
            finder = connection.execute("SELECT * FROM finders WHERE id = ?", (finder_id,)).fetchone()
            if not finder:
                return None
            result = dict(finder)
            result["items"] = [
                dict(row)
                for row in connection.execute(
                    "SELECT id, name, category, status, location_found, date_found FROM items WHERE finder_id = ? ORDER BY id DESC",
                    (finder_id,),
                ).fetchall()
            ]
        return result

    def list_returns(self, search: str = "") -> list[dict[str, Any]]:
        sql = """SELECT r.*, c.claim_id AS claim_code, i.name AS item_name, c.claimant_type,
                          c.school_id AS claimant_school_id
                   FROM returns r JOIN items i ON i.id = r.item_id
                   JOIN claims c ON c.id = r.claim_id WHERE 1 = 1"""
        values: list[Any] = []
        if search.strip():
            pattern = f"%{search.strip()}%"
            sql += " AND (c.claim_id LIKE ? OR i.name LIKE ? OR r.claimant_name LIKE ? OR r.released_by LIKE ?)"
            values.extend([pattern] * 4)
        sql += " ORDER BY r.returned_date DESC, r.returned_time DESC, r.id DESC"
        with self._connection() as connection:
            rows = connection.execute(sql, values).fetchall()
        return [dict(row) for row in rows]

    def list_activity(self, search: str = "") -> list[dict[str, Any]]:
        sql = "SELECT * FROM activity_logs"
        values: list[Any] = []
        if search.strip():
            pattern = f"%{search.strip()}%"
            sql += " WHERE admin_username LIKE ? OR action LIKE ? OR details LIKE ?"
            values.extend([pattern] * 3)
        sql += " ORDER BY created_at DESC, id DESC LIMIT 1000"
        with self._connection() as connection:
            rows = connection.execute(sql, values).fetchall()
        return [dict(row) for row in rows]

    def dashboard_stats(self) -> dict[str, int]:
        today = date.today().isoformat()
        with self._connection() as connection:
            total = connection.execute("SELECT COUNT(*) AS n FROM items WHERE status != 'Archived'").fetchone()["n"]
            available = connection.execute("SELECT COUNT(*) AS n FROM items WHERE status = 'Available'").fetchone()["n"]
            pending = connection.execute(
                "SELECT COUNT(*) AS n FROM claims WHERE status IN ('Pending', 'Verification Requested')"
            ).fetchone()["n"]
            returned = connection.execute("SELECT COUNT(*) AS n FROM items WHERE status = 'Returned'").fetchone()["n"]
            added_today = connection.execute(
                "SELECT COUNT(*) AS n FROM items WHERE substr(created_at, 1, 10) = ?", (today,)
            ).fetchone()["n"]
        return {
            "total_items": int(total),
            "available_items": int(available),
            "pending_claims": int(pending),
            "returned_items": int(returned),
            "added_today": int(added_today),
        }

    def report_summary(self) -> dict[str, list[dict[str, Any]]]:
        with self._connection() as connection:
            categories = [
                dict(row)
                for row in connection.execute(
                    "SELECT category AS label, COUNT(*) AS count FROM items WHERE status != 'Archived' GROUP BY category ORDER BY category"
                ).fetchall()
            ]
            item_statuses = [
                dict(row)
                for row in connection.execute(
                    "SELECT status AS label, COUNT(*) AS count FROM items GROUP BY status ORDER BY status"
                ).fetchall()
            ]
            claim_statuses = [
                dict(row)
                for row in connection.execute(
                    "SELECT status AS label, COUNT(*) AS count FROM claims GROUP BY status ORDER BY status"
                ).fetchall()
            ]
        return {"categories": categories, "item_statuses": item_statuses, "claim_statuses": claim_statuses}
