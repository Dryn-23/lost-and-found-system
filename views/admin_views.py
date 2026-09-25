"""Admin dashboard and management sections."""

from __future__ import annotations

import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Any, Callable

from database.database import ItemUnavailableError
from models.admin import Admin
from models.finder import Finder
from models.item import CATEGORIES, Item
from models.person import make_school_person
from utils.helpers import display_date, display_time, now_time, today_iso
from utils.validators import ValidationError
from views.admin_dialogs import (
    AdminItemDetailsDialog,
    ClaimReviewDialog,
    FinderDetailsDialog,
    ItemEditDialog,
)
from views.ui import (
    COLORS,
    ScrollableFrame,
    build_tree,
    section_heading,
    set_text,
    text_value,
    text_widget,
)


NAV_ITEMS = (
    ("dashboard", "Dashboard"),
    ("items", "Items"),
    ("add_item", "Add Found Item"),
    ("claims", "Claims"),
    ("returned", "Returned Items"),
    ("finders", "Finders"),
    ("reports", "Reports"),
    ("activity", "Activity Log"),
)


class AdminDashboardView(ttk.Frame):
    """Authenticated admin shell with a persistent sidebar and section router."""

    def __init__(self, master: tk.Misc, app: object, admin: Admin) -> None:
        super().__init__(master)
        self.app = app
        self.admin = admin
        self.current_section = "dashboard"
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=220)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)
        self.main = ttk.Frame(self)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.rowconfigure(1, weight=1)
        self.main.columnconfigure(0, weight=1)

        self._build_sidebar()
        toolbar = ttk.Frame(self.main, style="White.TFrame", padding=(22, 13))
        toolbar.grid(row=0, column=0, sticky="ew")
        ttk.Label(toolbar, text="ADMIN WORKSPACE", style="CardTitle.TLabel").pack(side="left")
        right = ttk.Frame(toolbar, style="White.TFrame")
        right.pack(side="right")
        ttk.Label(right, text=f"Signed in as {admin.username}", style="WhiteMuted.TLabel").pack(side="left", padx=(0, 12))
        ttk.Button(right, text="Logout", style="Secondary.TButton", command=self._logout).pack(side="left")

        self.content = ttk.Frame(self.main, padding=(22, 20))
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)
        self.show_section("dashboard")

    def _build_sidebar(self) -> None:
        brand = ttk.Frame(self.sidebar, style="Sidebar.TFrame", padding=(17, 20, 15, 17))
        brand.pack(fill="x")
        ttk.Label(brand, text="LF  /  ADMIN", style="SidebarTitle.TLabel").pack(anchor="w")
        ttk.Label(brand, text="Lost Today, Found Someday", style="SidebarSub.TLabel").pack(anchor="w", pady=(4, 0))
        ttk.Separator(self.sidebar, orient="horizontal").pack(fill="x", padx=15, pady=(0, 13))
        ttk.Label(self.sidebar, text="MANAGEMENT", style="SidebarSection.TLabel", padding=(17, 4)).pack(anchor="w")
        self.nav_frame = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        self.nav_frame.pack(fill="x", padx=8, pady=(4, 0))
        self.nav_buttons: dict[str, ttk.Button] = {}
        for key, label in NAV_ITEMS:
            button = ttk.Button(
                self.nav_frame,
                text=label,
                style="Nav.TButton",
                command=lambda section=key: self.show_section(section),
            )
            button.pack(fill="x", pady=2)
            self.nav_buttons[key] = button
        bottom = ttk.Frame(self.sidebar, style="Sidebar.TFrame", padding=(16, 12))
        bottom.pack(side="bottom", fill="x")
        ttk.Label(bottom, text="Private admin records\nare not shown publicly.", style="SidebarSub.TLabel", justify="left").pack(anchor="w")

    def show_section(self, section: str) -> None:
        self.current_section = section
        for key, button in self.nav_buttons.items():
            button.configure(style="NavActive.TButton" if key == section else "Nav.TButton")
        for child in self.content.winfo_children():
            child.destroy()
        pages: dict[str, Callable[..., ttk.Frame]] = {
            "dashboard": DashboardSection,
            "items": ItemManagementSection,
            "add_item": AddItemSection,
            "claims": ClaimsSection,
            "returned": ReturnedItemsSection,
            "finders": FinderManagementSection,
            "reports": ReportsSection,
            "activity": ActivityLogSection,
        }
        page_type = pages.get(section, DashboardSection)
        page = page_type(self.content, self.app, self)
        page.grid(row=0, column=0, sticky="nsew")

    def _logout(self) -> None:
        if messagebox.askyesno("Log out", "End the admin session and return to the public catalog?", parent=self):
            self.app.logout_admin()


class DashboardSection(ttk.Frame):
    def __init__(self, master: tk.Misc, app: object, dashboard: AdminDashboardView) -> None:
        super().__init__(master)
        self.app = app
        self.dashboard = dashboard
        top = ttk.Frame(self)
        top.pack(fill="x")
        ttk.Label(top, text="Dashboard", style="Title.TLabel").pack(side="left")
        ttk.Button(top, text="Refresh", style="Secondary.TButton", command=self._refresh).pack(side="right")
        ttk.Label(self, text="A quick overview of items received and claims awaiting an Admin decision.", style="Muted.TLabel").pack(anchor="w", pady=(3, 15))

        self.metrics = ttk.Frame(self)
        self.metrics.pack(fill="x", pady=(0, 18))
        for index in range(5):
            self.metrics.columnconfigure(index, weight=1, uniform="metrics")
        self.metric_vars: dict[str, tk.StringVar] = {}
        metric_items = (
            ("total_items", "TOTAL ITEMS", "All active and returned records"),
            ("available_items", "AVAILABLE", "Visible in public catalog"),
            ("pending_claims", "PENDING CLAIMS", "Need Admin review"),
            ("returned_items", "RETURNED ITEMS", "Physically handed over"),
            ("added_today", "ADDED TODAY", "New intake records"),
        )
        for column, (key, label, detail) in enumerate(metric_items):
            card = ttk.Frame(self.metrics, style="Card.TFrame", padding=(14, 13))
            card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 6 if column < 4 else 0))
            ttk.Label(card, text=label, style="WhiteMuted.TLabel").pack(anchor="w")
            var = tk.StringVar(value="—")
            self.metric_vars[key] = var
            ttk.Label(card, textvariable=var, style="BigNumber.TLabel").pack(anchor="w", pady=(7, 2))
            ttk.Label(card, text=detail, style="WhiteMuted.TLabel", wraplength=150).pack(anchor="w")

        notice = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        notice.pack(fill="x", pady=(0, 18))
        ttk.Label(notice, text="Admin-controlled intake", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(
            notice,
            text="Only list items after they have been physically surrendered to the Admin Office. Claims remain requests until a staff member checks the claimant and the physical property in person.",
            style="WhiteMuted.TLabel",
            wraplength=920,
        ).pack(anchor="w", pady=(4, 0))
        quick = ttk.Frame(self)
        quick.pack(fill="x", pady=(0, 18))
        ttk.Button(quick, text="＋  Add found item", style="Primary.TButton", command=lambda: dashboard.show_section("add_item")).pack(side="left")
        ttk.Button(quick, text="Review pending claims", style="Secondary.TButton", command=lambda: dashboard.show_section("claims")).pack(side="left", padx=8)

        tables = ttk.Frame(self)
        tables.pack(fill="both", expand=True)
        tables.columnconfigure(0, weight=1)
        tables.columnconfigure(1, weight=1)
        ttk.Label(tables, text="Recent activity", style="Heading.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8), padx=(0, 8))
        ttk.Label(tables, text="Recently received items", style="Heading.TLabel").grid(row=0, column=1, sticky="w", pady=(0, 8), padx=(8, 0))
        self.activity_tree, activity_wrap = build_tree(
            tables,
            (("time", "TIME", 145, "w"), ("admin", "ADMIN", 90, "w"), ("action", "ACTIVITY", 180, "w")),
            height=8,
        )
        activity_wrap.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        self.recent_tree, recent_wrap = build_tree(
            tables,
            (("id", "ID", 55, "center"), ("name", "ITEM", 180, "w"), ("category", "CATEGORY", 110, "w"), ("status", "STATUS", 120, "w")),
            height=8,
        )
        recent_wrap.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        tables.rowconfigure(1, weight=1)
        self._refresh()

    def _refresh(self) -> None:
        stats = self.app.system.items.stats()
        for key, variable in self.metric_vars.items():
            variable.set(str(stats.get(key, 0)))
        for tree in (self.activity_tree, self.recent_tree):
            for iid in tree.get_children():
                tree.delete(iid)
        for row in self.app.system.database.list_activity()[:8]:
            self.activity_tree.insert("", "end", values=(row["created_at"], row["admin_username"], row["action"]))
        for row in self.app.system.items.admin_items()[:8]:
            self.recent_tree.insert("", "end", values=(row["id"], row["name"], row["category"], row["status"]))


class ItemManagementSection(ttk.Frame):
    def __init__(self, master: tk.Misc, app: object, dashboard: AdminDashboardView) -> None:
        super().__init__(master)
        self.app = app
        self.dashboard = dashboard
        self.search_var = tk.StringVar()
        self.category_var = tk.StringVar(value="All")
        self.status_var = tk.StringVar(value="All statuses")
        header = ttk.Frame(self)
        header.pack(fill="x")
        left = ttk.Frame(header)
        left.pack(side="left", fill="x", expand=True)
        ttk.Label(left, text="Items", style="Title.TLabel").pack(anchor="w")
        ttk.Label(left, text="Admin-only item records include private finder and storage information.", style="Muted.TLabel").pack(anchor="w", pady=(3, 0))
        ttk.Button(header, text="＋ Add Found Item", style="Primary.TButton", command=lambda: dashboard.show_section("add_item")).pack(side="right", padx=(10, 0))

        filter_card = ttk.Frame(self, style="Card.TFrame", padding=12)
        filter_card.pack(fill="x", pady=(15, 12))
        filter_card.columnconfigure(0, weight=1)
        search = ttk.Entry(filter_card, textvariable=self.search_var)
        search.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        search.bind("<Return>", lambda _event: self._refresh())
        category = ttk.Combobox(filter_card, textvariable=self.category_var, state="readonly", values=("All", *CATEGORIES), width=20)
        category.grid(row=0, column=1, padx=5)
        category.bind("<<ComboboxSelected>>", lambda _event: self._refresh())
        status = ttk.Combobox(filter_card, textvariable=self.status_var, state="readonly", values=("All statuses", "Available", "Pending Claim", "Claim Approved", "Returned", "Archived"), width=20)
        status.grid(row=0, column=2, padx=5)
        status.bind("<<ComboboxSelected>>", lambda _event: self._refresh())
        ttk.Button(filter_card, text="Search", style="Secondary.TButton", command=self._refresh).grid(row=0, column=3, padx=(6, 0))
        ttk.Button(filter_card, text="Clear", style="Link.TButton", command=self._clear).grid(row=0, column=4)

        columns = (
            ("id", "ID", 55, "center"),
            ("name", "ITEM", 205, "w"),
            ("category", "CATEGORY", 120, "w"),
            ("location", "FOUND AT", 155, "w"),
            ("date", "DATE FOUND", 115, "w"),
            ("status", "STATUS", 135, "w"),
            ("finder", "FINDER · PRIVATE", 180, "w"),
        )
        self.tree, tree_wrap = build_tree(self, columns, height=15)
        tree_wrap.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda _event: self._view())
        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(10, 0))
        ttk.Button(actions, text="View private record", style="Secondary.TButton", command=self._view).pack(side="left")
        ttk.Button(actions, text="Edit item", style="Secondary.TButton", command=self._edit).pack(side="left", padx=7)
        ttk.Button(actions, text="Archive", style="Danger.TButton", command=self._archive).pack(side="left")
        self._refresh()

    def _refresh(self) -> None:
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        rows = self.app.system.items.admin_items(self.search_var.get(), self.category_var.get(), self.status_var.get())
        for row in rows:
            self.tree.insert(
                "", "end", iid=str(row["id"]),
                values=(row["id"], row["name"], row["category"], row["location_found"], display_date(row["date_found"]), row["status"], row["finder_name"]),
            )

    def _selected(self) -> dict[str, Any] | None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Select an item", "Choose an item record first.", parent=self)
            return None
        return self.app.system.items.admin_item(int(selection[0]))

    def _view(self) -> None:
        item = self._selected()
        if item:
            AdminItemDetailsDialog(self, self.app, item)

    def _edit(self) -> None:
        item = self._selected()
        if not item:
            return
        if item["status"] in ("Returned", "Archived"):
            messagebox.showwarning("Read-only record", "Returned and archived historical item records cannot be edited.", parent=self)
            return
        ItemEditDialog(self, self.app, item, self._refresh)

    def _archive(self) -> None:
        item = self._selected()
        if not item:
            return
        if not messagebox.askyesno(
            "Archive item",
            f"Archive '{item['name']}'? It will leave the public catalog, but its history will remain in the database.",
            parent=self,
        ):
            return
        try:
            self.app.system.items.archive_item(int(item["id"]), self.app.current_admin.username)
        except Exception as exc:
            messagebox.showwarning("Item not archived", str(exc), parent=self)
            return
        messagebox.showinfo("Item archived", "The item was archived; its record was not permanently deleted.", parent=self)
        self._refresh()

    def _clear(self) -> None:
        self.search_var.set("")
        self.category_var.set("All")
        self.status_var.set("All statuses")
        self._refresh()


class AddItemSection(ttk.Frame):
    """Admin intake flow: record a finder interview and a physically received item."""

    def __init__(self, master: tk.Misc, app: object, dashboard: AdminDashboardView) -> None:
        super().__init__(master)
        self.app = app
        self.dashboard = dashboard
        self.finder_role = tk.StringVar(value="Student")
        self.finder_vars = {
            key: tk.StringVar() for key in (
                "school_id", "full_name", "contact_number", "grade_course", "section", "department", "assigned_area",
                "where_found", "date_found", "time_found",
            )
        }
        self.finder_vars["date_found"].set(today_iso())
        self.finder_vars["time_found"].set(now_time())
        self.finder_texts: dict[str, tk.Text] = {}
        self.item_vars = {
            key: tk.StringVar() for key in (
                "name", "category", "color", "brand", "location_found", "date_found", "time_found",
                "condition", "storage_location", "photo_path",
            )
        }
        self.item_vars["category"].set(CATEGORIES[0])
        self.item_vars["date_found"].set(today_iso())
        self.item_vars["time_found"].set(now_time())
        self.item_texts: dict[str, tk.Text] = {}
        self.received_var = tk.BooleanVar(value=False)
        self._build()

    def _build(self) -> None:
        top = ttk.Frame(self)
        top.pack(fill="x")
        ttk.Label(top, text="Add Found Item", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            top,
            text="Complete the finder interview and item record only after the physical item has been handed to the Admin Office.",
            style="Muted.TLabel",
            wraplength=950,
        ).pack(anchor="w", pady=(3, 12))
        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True)
        body = scroll.inner
        body.configure(padding=(2, 2, 10, 12))

        finder_box = ttk.LabelFrame(body, text="1 · Finder interview — private Admin record", padding=14)
        finder_box.pack(fill="x", pady=(0, 12))
        ttk.Label(finder_box, text="Finder's school role", style="White.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 12), pady=5)
        role_combo = ttk.Combobox(finder_box, textvariable=self.finder_role, state="readonly", values=("Student", "Teacher", "School Utility Personnel"), width=30)
        role_combo.grid(row=0, column=1, sticky="w", pady=5)
        role_combo.bind("<<ComboboxSelected>>", lambda _event: self._render_finder_identity())
        self.identity_frame = ttk.Frame(finder_box, style="White.TFrame")
        self.identity_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(4, 5))
        for col in (1, 3):
            self.identity_frame.columnconfigure(col, weight=1)
        self._render_finder_identity()

        interview = ttk.LabelFrame(finder_box, text="Finder's account of finding the item", padding=11)
        interview.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(7, 0))
        for col in (1, 3):
            interview.columnconfigure(col, weight=1)
        self._labeled_entry(interview, 0, 0, "Where did you find it?", "where_found", self.finder_vars)
        self._labeled_entry(interview, 0, 2, "Date found (YYYY-MM-DD)", "date_found", self.finder_vars)
        self._labeled_entry(interview, 1, 0, "Time found (HH:MM)", "time_found", self.finder_vars)
        self._labeled_text(interview, 2, "What were you doing when you found it?", "circumstances", 3, self.finder_texts)
        self._labeled_text(interview, 3, "Did you touch, open, or move anything related to it?", "touched_related", 2, self.finder_texts)
        self._labeled_text(interview, 4, "Additional finder notes (optional)", "additional_notes", 2, self.finder_texts)

        item_box = ttk.LabelFrame(body, text="2 · Found item record", padding=14)
        item_box.pack(fill="x", pady=(0, 12))
        ttk.Label(
            item_box,
            text="Public fields appear in the catalog. Storage location and Admin notes stay private. Avoid putting serial numbers, wallet contents, or private identifying marks in the public description.",
            style="WhiteMuted.TLabel",
            wraplength=900,
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))
        self._labeled_entry(item_box, 1, 0, "Item name", "name", self.item_vars, span=3)
        ttk.Label(item_box, text="Category", style="White.TLabel").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=5)
        ttk.Combobox(item_box, textvariable=self.item_vars["category"], state="readonly", values=CATEGORIES).grid(row=2, column=1, sticky="ew", padx=(0, 14), pady=5)
        self._labeled_entry(item_box, 2, 2, "Color (optional)", "color", self.item_vars)
        self._labeled_entry(item_box, 3, 0, "Brand (optional)", "brand", self.item_vars)
        self._labeled_entry(item_box, 3, 2, "Condition", "condition", self.item_vars)
        self._labeled_entry(item_box, 4, 0, "General location found", "location_found", self.item_vars)
        self._labeled_entry(item_box, 4, 2, "Date found (YYYY-MM-DD)", "date_found", self.item_vars)
        self._labeled_entry(item_box, 5, 0, "Time found (HH:MM)", "time_found", self.item_vars)
        self._labeled_entry(item_box, 5, 2, "Private storage location", "storage_location", self.item_vars)
        self._labeled_text(item_box, 6, "Public general description", "public_description", 3, self.item_texts)
        photo_label = ttk.Label(item_box, text="Optional photo (PNG/GIF)", style="White.TLabel")
        photo_label.grid(row=7, column=0, sticky="w", padx=(0, 8), pady=5)
        photo_row = ttk.Frame(item_box, style="White.TFrame")
        photo_row.grid(row=7, column=1, columnspan=3, sticky="ew", pady=5)
        ttk.Entry(photo_row, textvariable=self.item_vars["photo_path"]).pack(side="left", fill="x", expand=True)
        ttk.Button(photo_row, text="Browse", style="Secondary.TButton", command=self._choose_photo).pack(side="left", padx=(7, 0))
        self._labeled_text(item_box, 8, "Private Admin notes", "private_notes", 3, self.item_texts)
        for col in (1, 3):
            item_box.columnconfigure(col, weight=1)

        confirm_box = ttk.Frame(body, style="Card.TFrame", padding=12)
        confirm_box.pack(fill="x")
        ttk.Checkbutton(
            confirm_box,
            text="I confirm the physical item has been surrendered to and is being kept by the Admin / Lost & Found Office.",
            variable=self.received_var,
        ).pack(anchor="w")
        actions = ttk.Frame(body)
        actions.pack(fill="x", pady=(12, 2))
        ttk.Button(actions, text="Clear form", style="Secondary.TButton", command=self._clear).pack(side="right")
        ttk.Button(actions, text="ADD ITEM TO LOST & FOUND", style="Primary.TButton", command=self._submit).pack(side="right", padx=(0, 8))

    def _render_finder_identity(self) -> None:
        for child in self.identity_frame.winfo_children():
            child.destroy()
        role = self.finder_role.get()
        if role == "Student":
            fields = (("Student ID", "school_id"), ("Full name", "full_name"), ("Contact number", "contact_number"), ("Course / Grade", "grade_course"), ("Section", "section"))
        elif role == "Teacher":
            fields = (("Employee ID", "school_id"), ("Full name", "full_name"), ("Contact number", "contact_number"), ("Department", "department"))
        else:
            fields = (("Employee ID", "school_id"), ("Full name", "full_name"), ("Contact number", "contact_number"), ("Assigned department / area", "assigned_area"))
        for index, (label, key) in enumerate(fields):
            row, pair = divmod(index, 2)
            self._labeled_entry(self.identity_frame, row, pair * 2, label, key, self.finder_vars)

    def _labeled_entry(
        self,
        parent: tk.Misc,
        row: int,
        label_column: int,
        label: str,
        key: str,
        variables: dict[str, tk.StringVar],
        span: int = 1,
    ) -> None:
        ttk.Label(parent, text=label, style="White.TLabel").grid(row=row, column=label_column, sticky="w", padx=(0, 7), pady=5)
        entry = ttk.Entry(parent, textvariable=variables[key])
        entry.grid(row=row, column=label_column + 1, columnspan=span, sticky="ew", padx=(0, 14), pady=5)

    def _labeled_text(
        self,
        parent: tk.Misc,
        row: int,
        label: str,
        key: str,
        height: int,
        target: dict[str, tk.Text],
    ) -> None:
        ttk.Label(parent, text=label, style="White.TLabel").grid(row=row, column=0, sticky="nw", padx=(0, 8), pady=6)
        widget = text_widget(parent, height=height, width=70)
        widget.grid(row=row, column=1, columnspan=3, sticky="ew", pady=5)
        target[key] = widget
        for column in (1, 3):
            parent.columnconfigure(column, weight=1)

    def _choose_photo(self) -> None:
        path = filedialog.askopenfilename(
            parent=self,
            title="Choose a catalog-safe item photo",
            filetypes=(("PNG and GIF images", "*.png *.gif"), ("All files", "*.*")),
        )
        if path:
            self.item_vars["photo_path"].set(path)

    def _build_finder(self) -> Finder:
        role = self.finder_role.get()
        person_data: dict[str, Any] = {
            "school_id": self.finder_vars["school_id"].get(),
            "full_name": self.finder_vars["full_name"].get(),
            "contact_number": self.finder_vars["contact_number"].get(),
        }
        if role == "Student":
            person_data.update(grade_course=self.finder_vars["grade_course"].get(), section=self.finder_vars["section"].get())
        elif role == "Teacher":
            person_data["department"] = self.finder_vars["department"].get()
        else:
            person_data["assigned_area"] = self.finder_vars["assigned_area"].get()
        person = make_school_person(role, person_data)
        return Finder(
            person=person,
            where_found=self.finder_vars["where_found"].get(),
            date_found=self.finder_vars["date_found"].get(),
            time_found=self.finder_vars["time_found"].get(),
            circumstances=text_value(self.finder_texts["circumstances"]),
            touched_related=text_value(self.finder_texts["touched_related"]),
            additional_notes=text_value(self.finder_texts["additional_notes"]),
        )

    def _build_item(self) -> Item:
        return Item(
            name=self.item_vars["name"].get(),
            category=self.item_vars["category"].get(),
            public_description=text_value(self.item_texts["public_description"]),
            color=self.item_vars["color"].get(),
            brand=self.item_vars["brand"].get(),
            location_found=self.item_vars["location_found"].get(),
            date_found=self.item_vars["date_found"].get(),
            time_found=self.item_vars["time_found"].get(),
            condition=self.item_vars["condition"].get(),
            storage_location=self.item_vars["storage_location"].get(),
            private_notes=text_value(self.item_texts["private_notes"]),
            photo_path=self.item_vars["photo_path"].get(),
        )

    def _submit(self) -> None:
        if not self.received_var.get():
            messagebox.showwarning(
                "Physical item not confirmed",
                "Confirm that the item has been physically surrendered to the Admin Office before adding it to the catalog.",
                parent=self,
            )
            return
        try:
            finder = self._build_finder()
            item = self._build_item()
            duplicate = self.app.system.items.possible_duplicate(item)
            if duplicate and not messagebox.askyesno(
                "Possible duplicate item",
                f"A similar active record already exists:\n\n#{duplicate['id']} · {duplicate['name']} · {duplicate['location_found']} · {display_date(duplicate['date_found'])}\n\nAdd another record anyway?",
                parent=self,
            ):
                return
            item_id = self.app.system.items.add_found_item(finder, item, self.app.current_admin.username)
        except ValidationError as exc:
            messagebox.showwarning("Check the intake form", str(exc), parent=self)
            return
        except Exception as exc:
            messagebox.showerror("Item not added", f"The item intake could not be saved.\n\n{exc}", parent=self)
            return
        messagebox.showinfo(
            "Found item added",
            f"Item #{item_id} has been recorded. It is now visible in the public catalog. The finder interview remains private to Admin staff.",
            parent=self,
        )
        self.dashboard.show_section("items")

    def _clear(self) -> None:
        if not messagebox.askyesno("Clear form", "Clear the finder interview and item fields?", parent=self):
            return
        for key, variable in self.finder_vars.items():
            variable.set(today_iso() if key == "date_found" else now_time() if key == "time_found" else "")
        self.finder_role.set("Student")
        for widget in (*self.finder_texts.values(), *self.item_texts.values()):
            widget.delete("1.0", "end")
        for key, variable in self.item_vars.items():
            if key == "category":
                variable.set(CATEGORIES[0])
            elif key == "date_found":
                variable.set(today_iso())
            elif key == "time_found":
                variable.set(now_time())
            else:
                variable.set("")
        self.received_var.set(False)
        self._render_finder_identity()


class ClaimsSection(ttk.Frame):
    def __init__(self, master: tk.Misc, app: object, dashboard: AdminDashboardView) -> None:
        super().__init__(master)
        self.app = app
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="All statuses")
        ttk.Label(self, text="Claims", style="Title.TLabel").pack(anchor="w")
        ttk.Label(self, text="Review private claimant answers and record an in-person Admin decision.", style="Muted.TLabel").pack(anchor="w", pady=(3, 12))
        filters = ttk.Frame(self, style="Card.TFrame", padding=12)
        filters.pack(fill="x", pady=(0, 12))
        filters.columnconfigure(0, weight=1)
        search = ttk.Entry(filters, textvariable=self.search_var)
        search.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        search.bind("<Return>", lambda _event: self._refresh())
        statuses = ("All statuses", "Pending", "Verification Requested", "Approved", "Rejected", "Completed")
        combo = ttk.Combobox(filters, textvariable=self.status_var, values=statuses, state="readonly", width=24)
        combo.grid(row=0, column=1, padx=5)
        combo.bind("<<ComboboxSelected>>", lambda _event: self._refresh())
        ttk.Button(filters, text="Search", style="Secondary.TButton", command=self._refresh).grid(row=0, column=2, padx=(6, 0))
        columns = (
            ("claim_id", "CLAIM ID", 145, "w"),
            ("item", "ITEM", 190, "w"),
            ("claimant", "CLAIMANT · PRIVATE", 160, "w"),
            ("type", "TYPE", 160, "w"),
            ("school_id", "SCHOOL ID · PRIVATE", 145, "w"),
            ("submitted", "SUBMITTED", 155, "w"),
            ("status", "STATUS", 155, "w"),
        )
        self.tree, wrapper = build_tree(self, columns, height=16)
        wrapper.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda _event: self._open())
        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(10, 0))
        ttk.Button(actions, text="Open selected claim", style="Primary.TButton", command=self._open).pack(side="left")
        ttk.Button(actions, text="Refresh", style="Secondary.TButton", command=self._refresh).pack(side="left", padx=8)
        self._refresh()

    def _refresh(self) -> None:
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        rows = self.app.system.claims.list_claims(self.status_var.get(), self.search_var.get())
        for row in rows:
            self.tree.insert(
                "", "end", iid=str(row["id"]),
                values=(row["claim_id"], row["item_name"], row["full_name"], row["claimant_type"], row["school_id"], row["submitted_at"], row["status"]),
            )

    def _open(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Select a claim", "Choose a claim to review.", parent=self)
            return
        ClaimReviewDialog(self, self.app, int(selection[0]), self._refresh)


class ReturnedItemsSection(ttk.Frame):
    def __init__(self, master: tk.Misc, app: object, dashboard: AdminDashboardView) -> None:
        super().__init__(master)
        self.app = app
        self.search_var = tk.StringVar()
        ttk.Label(self, text="Returned Items", style="Title.TLabel").pack(anchor="w")
        ttk.Label(self, text="Historical record of items physically handed to verified claimants.", style="Muted.TLabel").pack(anchor="w", pady=(3, 12))
        search_card = ttk.Frame(self, style="Card.TFrame", padding=12)
        search_card.pack(fill="x", pady=(0, 12))
        search_card.columnconfigure(0, weight=1)
        entry = ttk.Entry(search_card, textvariable=self.search_var)
        entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        entry.bind("<Return>", lambda _event: self._refresh())
        ttk.Button(search_card, text="Search", style="Secondary.TButton", command=self._refresh).grid(row=0, column=1)
        columns = (
            ("claim_id", "CLAIM ID", 145, "w"),
            ("item", "ITEM", 200, "w"),
            ("claimant", "CLAIMANT · PRIVATE", 180, "w"),
            ("school_id", "SCHOOL ID · PRIVATE", 145, "w"),
            ("date", "RETURNED DATE", 125, "w"),
            ("time", "RETURNED TIME", 125, "w"),
            ("released_by", "RELEASED BY", 130, "w"),
        )
        self.tree, wrapper = build_tree(self, columns, height=16)
        wrapper.pack(fill="both", expand=True)
        self._refresh()

    def _refresh(self) -> None:
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        for row in self.app.system.database.list_returns(self.search_var.get()):
            self.tree.insert("", "end", values=(row["claim_code"], row["item_name"], row["claimant_name"], row["claimant_school_id"], display_date(row["returned_date"]), display_time(row["returned_time"]), row["released_by"]))


class FinderManagementSection(ttk.Frame):
    def __init__(self, master: tk.Misc, app: object, dashboard: AdminDashboardView) -> None:
        super().__init__(master)
        self.app = app
        self.search_var = tk.StringVar()
        ttk.Label(self, text="Finders", style="Title.TLabel").pack(anchor="w")
        ttk.Label(self, text="Finder identity and contact details are private Admin records and are never part of the public catalog.", style="Muted.TLabel", wraplength=900).pack(anchor="w", pady=(3, 12))
        filter_card = ttk.Frame(self, style="Card.TFrame", padding=12)
        filter_card.pack(fill="x", pady=(0, 12))
        filter_card.columnconfigure(0, weight=1)
        entry = ttk.Entry(filter_card, textvariable=self.search_var)
        entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        entry.bind("<Return>", lambda _event: self._refresh())
        ttk.Button(filter_card, text="Search", style="Secondary.TButton", command=self._refresh).grid(row=0, column=1)
        columns = (
            ("name", "FINDER · PRIVATE", 190, "w"),
            ("type", "SCHOOL ROLE", 175, "w"),
            ("school_id", "SCHOOL ID · PRIVATE", 150, "w"),
            ("affiliation", "AFFILIATION", 170, "w"),
            ("location", "FOUND AT", 165, "w"),
            ("date", "DATE FOUND", 120, "w"),
            ("items", "ITEMS", 70, "center"),
        )
        self.tree, wrapper = build_tree(self, columns, height=16)
        wrapper.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda _event: self._open())
        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(10, 0))
        ttk.Button(actions, text="View private finder interview", style="Primary.TButton", command=self._open).pack(side="left")
        self._refresh()

    def _refresh(self) -> None:
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        for row in self.app.system.database.list_finders(self.search_var.get()):
            self.tree.insert("", "end", iid=str(row["id"]), values=(row["full_name"], row["person_type"], row["school_id"], row["affiliation"], row["where_found"], display_date(row["date_found"]), row["item_count"]))

    def _open(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Select a finder", "Choose a finder record to view.", parent=self)
            return
        finder = self.app.system.database.get_finder(int(selection[0]))
        if finder:
            FinderDetailsDialog(self, finder)


class ReportsSection(ttk.Frame):
    def __init__(self, master: tk.Misc, app: object, dashboard: AdminDashboardView) -> None:
        super().__init__(master)
        self.app = app
        header = ttk.Frame(self)
        header.pack(fill="x")
        ttk.Label(header, text="Reports", style="Title.TLabel").pack(side="left")
        ttk.Button(header, text="Export summary CSV", style="Primary.TButton", command=self._export).pack(side="right")
        ttk.Label(self, text="Aggregate counts for school reporting. Claimant and finder contact data are not included in this summary.", style="Muted.TLabel", wraplength=900).pack(anchor="w", pady=(3, 15))
        self.summary = self.app.system.items.report_summary()
        boxes = ttk.Frame(self)
        boxes.pack(fill="both", expand=True)
        boxes.columnconfigure(0, weight=1)
        boxes.columnconfigure(1, weight=1)
        boxes.rowconfigure(0, weight=1)
        boxes.rowconfigure(1, weight=1)
        self._report_box(boxes, "Items by category", self.summary["categories"], 0, 0)
        self._report_box(boxes, "Items by status", self.summary["item_statuses"], 0, 1)
        self._report_box(boxes, "Claims by status", self.summary["claim_statuses"], 1, 0)
        note = ttk.Frame(boxes, style="Card.TFrame", padding=18)
        note.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(8, 0))
        ttk.Label(note, text="Process reminders", style="CardTitle.TLabel").pack(anchor="w")
        for message in (
            "Found items are entered only by an Admin after physical receipt.",
            "Claims are manually verified; approval does not mean the item is already returned.",
            "Returned records are preserved for audit and removed from normal public browsing.",
        ):
            ttk.Label(note, text="•  " + message, style="WhiteMuted.TLabel", wraplength=360, justify="left").pack(anchor="w", pady=(10, 0))

    @staticmethod
    def _report_box(parent: tk.Misc, title: str, rows: list[dict[str, Any]], row: int, column: int) -> None:
        box = ttk.Frame(parent, style="Card.TFrame", padding=15)
        box.grid(row=row, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 8 if column == 0 else 0), pady=(0 if row == 0 else 8, 8 if row == 0 else 0))
        ttk.Label(box, text=title, style="CardTitle.TLabel").pack(anchor="w", pady=(0, 8))
        if not rows:
            ttk.Label(box, text="No records yet.", style="WhiteMuted.TLabel").pack(anchor="w")
        for item in rows:
            line = ttk.Frame(box, style="White.TFrame")
            line.pack(fill="x", pady=3)
            ttk.Label(line, text=item["label"], style="White.TLabel").pack(side="left")
            ttk.Label(line, text=str(item["count"]), style="WhiteAccent.TLabel").pack(side="right")

    def _export(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export aggregate report",
            defaultextension=".csv",
            filetypes=(("CSV file", "*.csv"),),
            initialfile="lost_found_summary.csv",
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.writer(handle)
                writer.writerow(("Lost Today, Found Someday — Aggregate Report",))
                writer.writerow(("Report generated", today_iso()))
                for heading, key in (("Items by category", "categories"), ("Items by status", "item_statuses"), ("Claims by status", "claim_statuses")):
                    writer.writerow(())
                    writer.writerow((heading, "Count"))
                    for row in self.summary[key]:
                        writer.writerow((row["label"], row["count"]))
        except OSError as exc:
            messagebox.showerror("Export failed", f"The CSV could not be saved.\n\n{exc}", parent=self)
            return
        messagebox.showinfo("Report exported", f"Aggregate report saved to:\n{path}", parent=self)


class ActivityLogSection(ttk.Frame):
    def __init__(self, master: tk.Misc, app: object, dashboard: AdminDashboardView) -> None:
        super().__init__(master)
        self.app = app
        self.search_var = tk.StringVar()
        ttk.Label(self, text="Activity Log", style="Title.TLabel").pack(anchor="w")
        ttk.Label(self, text="Administrative actions and claim decisions are retained for accountability.", style="Muted.TLabel").pack(anchor="w", pady=(3, 12))
        search_card = ttk.Frame(self, style="Card.TFrame", padding=12)
        search_card.pack(fill="x", pady=(0, 12))
        search_card.columnconfigure(0, weight=1)
        entry = ttk.Entry(search_card, textvariable=self.search_var)
        entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        entry.bind("<Return>", lambda _event: self._refresh())
        ttk.Button(search_card, text="Search", style="Secondary.TButton", command=self._refresh).grid(row=0, column=1)
        columns = (
            ("time", "DATE / TIME", 185, "w"),
            ("admin", "ADMIN", 125, "w"),
            ("action", "ACTION", 215, "w"),
            ("details", "DETAILS", 500, "w"),
        )
        self.tree, wrapper = build_tree(self, columns, height=18)
        wrapper.pack(fill="both", expand=True)
        self._refresh()

    def _refresh(self) -> None:
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        for row in self.app.system.database.list_activity(self.search_var.get()):
            self.tree.insert("", "end", values=(row["created_at"], row["admin_username"], row["action"], row["details"]))
