"""Admin-only authentication and audit logging."""

from __future__ import annotations

from database.database import DatabaseManager
from models.admin import Admin


class AdminController:
    def __init__(self, database: DatabaseManager) -> None:
        self.database = database

    def login(self, username: str, password: str) -> Admin | None:
        admin = self.database.authenticate_admin(username, password)
        if admin:
            self.database.log_activity(admin.username, "Admin logged in", "Admin dashboard session started.")
        return admin

    def logout(self, admin: Admin) -> None:
        self.database.log_activity(admin.username, "Admin logged out", "Admin dashboard session ended.")
