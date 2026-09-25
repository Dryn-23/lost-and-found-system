"""Separate admin-only sign-in screen. Public visitors do not authenticate."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from views.ui import COLORS


class AdminLoginView(ttk.Frame):
    def __init__(self, master: tk.Misc, app: object) -> None:
        super().__init__(master)
        self.app = app
        header = ttk.Frame(self, style="White.TFrame", padding=(26, 15))
        header.pack(fill="x")
        ttk.Label(header, text="LF", background=COLORS["teal"], foreground="white", padding=(10, 7), font=("Segoe UI", 11, "bold")).pack(side="left")
        brand = ttk.Frame(header, style="White.TFrame")
        brand.pack(side="left", padx=(10, 0))
        ttk.Label(brand, text="LOST TODAY, FOUND SOMEDAY", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(brand, text="School Lost & Found", style="WhiteMuted.TLabel").pack(anchor="w")
        ttk.Button(header, text="← Back to public catalog", style="Link.TButton", command=app.show_public_home).pack(side="right")

        center = ttk.Frame(self)
        center.pack(fill="both", expand=True)
        card = ttk.Frame(center, style="Card.TFrame", padding=30)
        card.place(relx=0.5, rely=0.45, anchor="center", width=440)
        ttk.Label(card, text="Admin Office", style="CardHeading.TLabel").pack(anchor="w")
        ttk.Label(
            card,
            text="Sign in to manage found items and verify claims. Public browsing never requires an account.",
            style="Muted.TLabel",
            wraplength=370,
            justify="left",
        ).pack(anchor="w", pady=(5, 22))

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        ttk.Label(card, text="Username", style="White.TLabel").pack(anchor="w", pady=(0, 5))
        username_entry = ttk.Entry(card, textvariable=self.username_var)
        username_entry.pack(fill="x", pady=(0, 15))
        ttk.Label(card, text="Password", style="White.TLabel").pack(anchor="w", pady=(0, 5))
        password_entry = ttk.Entry(card, textvariable=self.password_var, show="•")
        password_entry.pack(fill="x", pady=(0, 18))
        password_entry.bind("<Return>", lambda _event: self._login())
        ttk.Button(card, text="LOGIN TO ADMIN", style="Primary.TButton", command=self._login).pack(fill="x")
        ttk.Label(
            card,
            text="First-run demo account: admin  /  admin123\nChange or remove demo credentials before any real deployment.",
            style="WhiteMuted.TLabel",
            justify="left",
        ).pack(anchor="w", pady=(18, 0))
        username_entry.focus_set()

    def _login(self) -> None:
        username = self.username_var.get().strip()
        password = self.password_var.get()
        if not username or not password:
            messagebox.showwarning("Missing details", "Enter both the admin username and password.", parent=self)
            return
        try:
            admin = self.app.system.admin.login(username, password)
        except Exception as exc:
            messagebox.showerror("Sign-in error", f"The admin sign-in could not be completed.\n\n{exc}", parent=self)
            return
        if admin is None:
            messagebox.showerror("Sign-in failed", "The username or password is incorrect.", parent=self)
            self.password_var.set("")
            return
        self.app.show_admin_dashboard(admin)
