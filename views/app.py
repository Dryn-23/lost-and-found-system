"""Tkinter application shell and top-level navigation."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from controllers.system_controller import LostFoundSystem
from models.admin import Admin
from views.ui import COLORS, setup_theme
from views.public_views import PublicHomeView
from views.admin_login import AdminLoginView
from views.admin_views import AdminDashboardView


class LostFoundApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Lost Today, Found Someday | School Lost & Found")
        self.geometry("1280x860")
        self.minsize(960, 700)
        self.configure(background=COLORS["background"])
        setup_theme(self)
        self.system = LostFoundSystem()
        self.current_admin: Admin | None = None
        self._active_view: ttk.Frame | None = None
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.show_public_home()

    def _show(self, view_type: type[ttk.Frame], *args: object) -> None:
        if self._active_view is not None:
            self._active_view.destroy()
        self._active_view = view_type(self.container, self, *args)
        self._active_view.pack(fill="both", expand=True)

    def show_public_home(self) -> None:
        self.current_admin = None
        self._show(PublicHomeView)

    def show_admin_login(self) -> None:
        self._show(AdminLoginView)

    def show_admin_dashboard(self, admin: Admin) -> None:
        self.current_admin = admin
        self._show(AdminDashboardView, admin)

    def logout_admin(self) -> None:
        if self.current_admin is not None:
            self.system.admin.logout(self.current_admin)
        self.current_admin = None
        self.show_public_home()

    def _on_close(self) -> None:
        if self.current_admin and not messagebox.askyesno(
            "Exit application", "Close the Lost & Found system?", parent=self
        ):
            return
        self.destroy()
