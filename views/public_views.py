"""Public catalog, safe item details, and anonymous claim form."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Any

from models.claim import Claim
from models.item import CATEGORIES
from models.person import make_school_person
from utils.helpers import display_date, today_iso
from utils.validators import ValidationError
from database.database import DuplicateClaimError, ItemUnavailableError
from views.ui import (
    COLORS,
    ScrollableFrame,
    section_heading,
    text_value,
    text_widget,
)


PUBLIC_CATEGORIES = ("All", "Electronics", "ID", "Bags", "Clothing", "School Supplies", "Accessories", "Other")


class PublicHomeView(ttk.Frame):
    """The application opens here. Browsing and claiming require no account."""

    def __init__(self, master: tk.Misc, app: object) -> None:
        super().__init__(master)
        self.app = app
        self.photo_refs: dict[str, tk.PhotoImage] = {}
        self.search_var = tk.StringVar()
        self.category_var = tk.StringVar(value="All")
        self.location_var = tk.StringVar(value="All locations")
        self.date_var = tk.StringVar()
        self.status_var = tk.StringVar(value="All statuses")

        self._build_header()
        self.page = ScrollableFrame(self)
        self.page.pack(fill="both", expand=True)
        self.body = self.page.inner
        self.body.configure(padding=(34, 24, 34, 22))
        self.body.columnconfigure(0, weight=1)
        self._build_content()
        self._load_items()

    def _build_header(self) -> None:
        header = ttk.Frame(self, style="White.TFrame", padding=(30, 12))
        header.pack(fill="x")
        brand = ttk.Frame(header, style="White.TFrame")
        brand.pack(side="left")
        ttk.Label(brand, text="LF", background=COLORS["teal"], foreground=COLORS["white"], padding=(10, 8), font=("Segoe UI", 11, "bold")).pack(side="left")
        title = ttk.Frame(brand, style="White.TFrame")
        title.pack(side="left", padx=(10, 0))
        ttk.Label(title, text="BackToU", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(title, text="A School-Based Lost & Found Catalog", style="WhiteMuted.TLabel").pack(anchor="w")

        nav = ttk.Frame(header, style="White.TFrame")
        nav.pack(side="right")
        self.nav_buttons: list[ttk.Button] = []
        nav_items = (
            ("Home", "hero_target"),
            ("Found Items", "catalog_target"),
            ("Categories", "categories_target"),
            ("How It Works", "how_target"),
            ("About", "about_target"),
        )
        for label, target in nav_items:
            button = ttk.Button(nav, text=label, style="SmallLink.TButton", command=lambda name=target: self._scroll_to(name))
            button.pack(side="left", padx=2)
            self.nav_buttons.append(button)

    def _build_content(self) -> None:
        self.hero = ttk.Frame(self.body, style="Hero.TFrame", padding=(28, 28))
        self.hero.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.hero.columnconfigure(0, weight=1)
        self.hero_target = self.hero
        ttk.Label(self.hero, text="SCHOOL LOST & FOUND", style="HeroEyebrow.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(self.hero, text="Lost today, found someday.", style="HeroTitle.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 5))
        ttk.Label(
            self.hero,
            text="Browse items turned in to the Admin Office. Think you found yours? Send a claim for review—\nitems are released only after in-person identity and ownership verification.",
            style="HeroSubtitle.TLabel",
            justify="left",
            wraplength=900,
        ).grid(row=2, column=0, sticky="w")
        trust = ttk.Frame(self.hero, style="Hero.TFrame")
        trust.grid(row=0, column=1, rowspan=3, sticky="e", padx=(30, 2))
        ttk.Label(trust, text="PUBLIC TO BROWSE", background=COLORS["navy"], foreground="#8FE0D7", font=("Segoe UI", 9, "bold")).pack(anchor="e")
        ttk.Label(trust, text="No account needed", style="HeroSubtitle.TLabel").pack(anchor="e", pady=(5, 0))

        self.search_panel = ttk.Frame(self.body, style="Card.TFrame", padding=18)
        self.search_panel.grid(row=1, column=0, sticky="ew", pady=(0, 22))
        self.search_panel.columnconfigure(0, weight=1)
        search_row = ttk.Frame(self.search_panel, style="White.TFrame")
        search_row.grid(row=0, column=0, sticky="ew")
        search_row.columnconfigure(0, weight=1)
        search = ttk.Entry(search_row, textvariable=self.search_var, font=("Segoe UI", 11))
        search.grid(row=0, column=0, sticky="ew", ipady=3)
        search.insert(0, "")
        search.bind("<Return>", lambda _event: self._load_items())
        ttk.Button(search_row, text="Search items", style="Primary.TButton", command=self._load_items).grid(row=0, column=1, padx=(9, 0))
        ttk.Label(
            self.search_panel,
            text="Search by item name, category, color, brand, or general location found.",
            style="WhiteMuted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 12))

        filters = ttk.Frame(self.search_panel, style="White.TFrame")
        filters.grid(row=2, column=0, sticky="ew")
        for column in (1, 3, 5):
            filters.columnconfigure(column, weight=1)
        ttk.Label(filters, text="Location", style="WhiteMuted.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.location_combo = ttk.Combobox(filters, textvariable=self.location_var, state="readonly", width=21)
        self.location_combo.grid(row=0, column=1, sticky="ew", padx=(0, 16))
        self.location_combo.bind("<<ComboboxSelected>>", lambda _event: self._load_items())
        ttk.Label(filters, text="Date found", style="WhiteMuted.TLabel").grid(row=0, column=2, sticky="w", padx=(0, 6))
        ttk.Entry(filters, textvariable=self.date_var, width=16).grid(row=0, column=3, sticky="ew", padx=(0, 16))
        ttk.Label(filters, text="Status", style="WhiteMuted.TLabel").grid(row=0, column=4, sticky="w", padx=(0, 6))
        status_combo = ttk.Combobox(
            filters,
            textvariable=self.status_var,
            state="readonly",
            values=("All statuses", "Available", "Pending Claim"),
            width=17,
        )
        status_combo.grid(row=0, column=5, sticky="ew", padx=(0, 12))
        status_combo.bind("<<ComboboxSelected>>", lambda _event: self._load_items())
        ttk.Button(filters, text="Apply", style="Secondary.TButton", command=self._load_items).grid(row=0, column=6, padx=(0, 6))
        ttk.Button(filters, text="Reset", style="Link.TButton", command=self._reset_filters).grid(row=0, column=7)

        self.categories_section = ttk.Frame(self.body)
        self.categories_section.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        self.categories_target = self.categories_section
        ttk.Label(self.categories_section, text="Browse by category", style="Heading.TLabel").pack(anchor="w", pady=(0, 9))
        self.category_buttons = ttk.Frame(self.categories_section)
        self.category_buttons.pack(anchor="w", fill="x")
        self._render_category_buttons()

        self.catalog_section = ttk.Frame(self.body)
        self.catalog_section.grid(row=3, column=0, sticky="ew", pady=(0, 30))
        self.catalog_target = self.catalog_section
        catalog_header = ttk.Frame(self.catalog_section)
        catalog_header.pack(fill="x", pady=(0, 12))
        ttk.Label(catalog_header, text="Recently added items", style="Heading.TLabel").pack(side="left")
        self.result_count = ttk.Label(catalog_header, text="", style="Muted.TLabel")
        self.result_count.pack(side="right", anchor="e")
        self.items_grid = ttk.Frame(self.catalog_section)
        self.items_grid.pack(fill="x")
        for column in range(3):
            self.items_grid.columnconfigure(column, weight=1, uniform="catalog")

        self.how_section = ttk.Frame(self.body)
        self.how_section.grid(row=4, column=0, sticky="ew", pady=(5, 30))
        self.how_target = self.how_section
        section_heading(self.how_section, "How the system works", "A clear process protects both the owner and the person who turned an item in.")
        steps = ttk.Frame(self.how_section)
        steps.pack(fill="x")
        instructions = [
            ("01", "Browse the catalog", "Search or filter the items the Admin Office has physically received."),
            ("02", "Submit a claim", "Share your school ID details and private ownership information. No account is created."),
            ("03", "Meet the Admin", "Bring your claim ID and school ID for in-person verification. Nothing is released automatically."),
        ]
        for index, (number, title, description) in enumerate(instructions):
            card = ttk.Frame(steps, style="Card.TFrame", padding=17)
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 8, 8 if index < 2 else 0))
            steps.columnconfigure(index, weight=1, uniform="steps")
            ttk.Label(card, text=number, background=COLORS["teal_soft"], foreground=COLORS["teal"], padding=(8, 4), font=("Segoe UI", 9, "bold")).pack(anchor="w")
            ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w", pady=(11, 5))
            ttk.Label(card, text=description, style="WhiteMuted.TLabel", wraplength=300, justify="left").pack(anchor="w")

        self.about_section = ttk.Frame(self.body, style="Card.TFrame", padding=20)
        self.about_section.grid(row=5, column=0, sticky="ew", pady=(0, 20))
        self.about_target = self.about_section
        about_content = ttk.Frame(self.about_section, style="White.TFrame")
        about_content.pack(fill="x")
        about_content.columnconfigure(0, weight=1)
        ttk.Label(about_content, text="A school office-managed service", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            about_content,
            text="Found property is accepted, documented, and stored by the Admin Office. Finder contact details, storage locations, and private notes are never shown in the public catalog. To turn in an item, bring it directly to the Admin / Lost & Found Office.",
            style="WhiteMuted.TLabel",
            wraplength=900,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(7, 0))
        ttk.Label(
            about_content,
            text="Claimants must present their official school identification and Claim ID to the Admin Office. The Admin makes the final ownership decision and records the physical handover.",
            style="WhiteMuted.TLabel",
            wraplength=900,
            justify="left",
        ).grid(row=2, column=0, sticky="w", pady=(7, 0))

        footer = ttk.Frame(self.body, padding=(0, 10, 0, 4))
        footer.grid(row=6, column=0, sticky="ew")
        ttk.Label(footer, text="Lost Today, Found Someday  ·  Browse publicly, verify in person.", style="Muted.TLabel").pack(side="left")
        ttk.Button(footer, text="Admin", style="SmallLink.TButton", command=self.app.show_admin_login).pack(side="right")

    def _render_category_buttons(self) -> None:
        for child in self.category_buttons.winfo_children():
            child.destroy()
        for category in PUBLIC_CATEGORIES:
            style = "SelectedChip.TButton" if self.category_var.get() == category else "Chip.TButton"
            ttk.Button(
                self.category_buttons,
                text=category,
                style=style,
                command=lambda value=category: self._set_category(value),
            ).pack(side="left", padx=(0, 7), pady=(0, 3))

    def _set_category(self, category: str) -> None:
        self.category_var.set(category)
        self._render_category_buttons()
        self._load_items()
        self.page.scroll_to(self.catalog_target)

    def _scroll_to(self, target_name: str) -> None:
        target = getattr(self, target_name, None)
        if target is not None:
            self.page.scroll_to(target)

    def _reset_filters(self) -> None:
        self.search_var.set("")
        self.category_var.set("All")
        self.location_var.set("All locations")
        self.date_var.set("")
        self.status_var.set("All statuses")
        self._render_category_buttons()
        self._load_items()

    def _load_items(self) -> None:
        date_filter = self.date_var.get().strip()
        if date_filter:
            from utils.validators import validate_date, ValidationError

            try:
                validate_date(date_filter, "Date found")
            except ValidationError as exc:
                messagebox.showwarning("Check the date filter", str(exc), parent=self)
                return
        try:
            locations = ["All locations", *self.app.system.items.public_locations()]
            self.location_combo.configure(values=locations)
            if self.location_var.get() not in locations:
                self.location_var.set("All locations")
            items = self.app.system.items.public_catalog(
                search=self.search_var.get().strip(),
                category=self.category_var.get(),
                location=self.location_var.get(),
                date_found=date_filter,
                status=self.status_var.get(),
            )
        except Exception as exc:
            messagebox.showerror("Catalog error", f"The public catalog could not be loaded.\n\n{exc}", parent=self)
            return
        for child in self.items_grid.winfo_children():
            child.destroy()
        self.photo_refs.clear()
        self.result_count.configure(text=f"{len(items)} item{'s' if len(items) != 1 else ''}")
        if not items:
            empty = ttk.Frame(self.items_grid, style="Card.TFrame", padding=24)
            empty.grid(row=0, column=0, columnspan=3, sticky="ew")
            ttk.Label(empty, text="No matching items", style="CardTitle.TLabel").pack(anchor="w")
            ttk.Label(empty, text="Try a different search or clear one of the filters.", style="WhiteMuted.TLabel").pack(anchor="w", pady=(4, 0))
            return
        for index, item in enumerate(items):
            row, column = divmod(index, 3)
            self._item_card(item, row, column)

    def _item_card(self, item: dict[str, Any], row: int, column: int) -> None:
        card = ttk.Frame(self.items_grid, style="Card.TFrame", padding=0)
        card.grid(row=row, column=column, sticky="nsew", padx=7, pady=7)
        image_area = ttk.Frame(card, style="Placeholder.TFrame", height=118)
        image_area.pack(fill="x")
        image_area.pack_propagate(False)
        photo = self._load_photo(item.get("photo_path", ""), max_width=260, max_height=112)
        if photo:
            self.photo_refs[f"card-{item['id']}"] = photo
            ttk.Label(image_area, image=photo, style="Placeholder.TLabel").pack(expand=True)
        else:
            ttk.Label(image_area, text="NO PHOTO PROVIDED", style="Placeholder.TLabel").pack(expand=True)

        details = ttk.Frame(card, style="White.TFrame", padding=(15, 13, 15, 14))
        details.pack(fill="both", expand=True)
        ttk.Label(details, text=item["name"], style="CardTitle.TLabel", wraplength=280).pack(anchor="w")
        meta = ttk.Frame(details, style="White.TFrame")
        meta.pack(fill="x", pady=(7, 4))
        category_label = item["category"]
        if str(item.get("public_description", "")).startswith("DEMO SAMPLE —"):
            category_label += "  ·  DEMO"
        ttk.Label(meta, text=category_label, style="WhiteAccent.TLabel").pack(side="left")
        status_style = "Pending.TLabel" if item["status"] == "Pending Claim" else "Status.TLabel"
        ttk.Label(meta, text=item["status"], style=status_style).pack(side="right")
        ttk.Label(details, text=f"Found: {item['location_found']}", style="WhiteMuted.TLabel").pack(anchor="w", pady=(5, 1))
        ttk.Label(details, text=f"Date: {display_date(item['date_found'])}", style="WhiteMuted.TLabel").pack(anchor="w")
        ttk.Button(details, text="View details", style="Secondary.TButton", command=lambda row=item: ItemDetailsDialog(self, self.app, row, self._on_claimed)).pack(fill="x", pady=(11, 0))

    @staticmethod
    def _load_photo(path: str, max_width: int, max_height: int) -> tk.PhotoImage | None:
        if not path or not Path(path).is_file():
            return None
        try:
            image = tk.PhotoImage(file=path)
            divisor = max(1, (image.width() + max_width - 1) // max_width, (image.height() + max_height - 1) // max_height)
            return image.subsample(divisor, divisor) if divisor > 1 else image
        except (tk.TclError, OSError):
            return None

    def _on_claimed(self) -> None:
        self._load_items()


class ItemDetailsDialog(tk.Toplevel):
    """Only catalog-safe item fields are rendered in this public dialog."""

    def __init__(self, parent: tk.Misc, app: object, item: dict[str, Any], on_claimed: object) -> None:
        super().__init__(parent)
        self.app = app
        self.item = item
        self.on_claimed = on_claimed
        self.title("Found item details")
        self.geometry("610x680")
        self.minsize(540, 560)
        self.configure(background=COLORS["background"])
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        top = ttk.Frame(self, style="White.TFrame", padding=(22, 18))
        top.pack(fill="x")
        ttk.Label(top, text="ITEM DETAILS", style="WhiteAccent.TLabel").pack(anchor="w")
        ttk.Label(top, text=item["name"], style="CardHeading.TLabel", wraplength=520).pack(anchor="w", pady=(5, 0))
        ttk.Label(top, text=f"{item['category']}  ·  {item['status']}", style="WhiteMuted.TLabel").pack(anchor="w", pady=(5, 0))

        content = ScrollableFrame(self)
        content.pack(fill="both", expand=True, padx=20, pady=12)
        body = content.inner
        body.configure(padding=17)
        photo = PublicHomeView._load_photo(item.get("photo_path", ""), 520, 220)
        if photo:
            self.photo = photo
            ttk.Label(body, image=photo, style="White.TLabel").pack(fill="x", pady=(0, 14))
        info = ttk.Frame(body, style="Card.TFrame", padding=17)
        info.pack(fill="x")
        self._detail(info, "General description", item.get("public_description", "—"), 0)
        self._detail(info, "Color", item.get("color") or "Not specified", 1)
        self._detail(info, "Brand", item.get("brand") or "Not specified", 2)
        self._detail(info, "General location found", item.get("location_found", "—"), 3)
        self._detail(info, "Date found", display_date(item.get("date_found")), 4)
        self._detail(info, "Condition", item.get("condition", "—"), 5)
        self._detail(info, "Status", item.get("status", "—"), 6)

        reminder = ttk.Frame(body, style="Card.TFrame", padding=14)
        reminder.pack(fill="x", pady=(12, 0))
        ttk.Label(reminder, text="Privacy & verification", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(
            reminder,
            text="Some identifying details are intentionally withheld. Submit a claim only if you can describe the item; the Admin Office will compare your answers with the physical property.",
            style="WhiteMuted.TLabel",
            wraplength=490,
            justify="left",
        ).pack(anchor="w", pady=(5, 0))

        actions = ttk.Frame(self, padding=(20, 12))
        actions.pack(fill="x")
        ttk.Button(actions, text="Close", style="Secondary.TButton", command=self.destroy).pack(side="right")
        if item.get("status") in ("Available", "Pending Claim"):
            ttk.Button(actions, text="CLAIM THIS ITEM", style="Primary.TButton", command=self._open_claim).pack(side="right", padx=(0, 9))

    @staticmethod
    def _detail(parent: ttk.Frame, label: str, value: str, row: int) -> None:
        ttk.Label(parent, text=label, style="WhiteMuted.TLabel").grid(row=row, column=0, sticky="nw", padx=(0, 22), pady=5)
        ttk.Label(parent, text=value, style="White.TLabel", wraplength=330, justify="left").grid(row=row, column=1, sticky="nw", pady=5)
        parent.columnconfigure(1, weight=1)

    def _open_claim(self) -> None:
        latest = self.app.system.items.public_item(int(self.item["id"]))
        if not latest:
            messagebox.showwarning("Item unavailable", "This item is no longer accepting claims.", parent=self)
            self.destroy()
            return
        ClaimFormDialog(self, self.app, latest, self.on_claimed)


class ClaimFormDialog(tk.Toplevel):
    """Anonymous public request form; the Admin Office decides ownership."""

    def __init__(self, parent: tk.Misc, app: object, item: dict[str, Any], on_submitted: object) -> None:
        super().__init__(parent)
        self.app = app
        self.item = item
        self.on_submitted = on_submitted
        self.title("Submit an item claim")
        self.geometry("680x780")
        self.minsize(590, 650)
        self.configure(background=COLORS["background"])
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.role_var = tk.StringVar(value="Student")
        self.vars: dict[str, tk.StringVar] = {
            key: tk.StringVar() for key in (
                "school_id", "full_name", "contact_number", "grade_course", "section",
                "department", "assigned_area", "last_seen_location", "last_seen_date",
            )
        }
        self.question_texts: dict[str, tk.Text] = {}
        self._build()

    def _build(self) -> None:
        header = ttk.Frame(self, style="White.TFrame", padding=(20, 15))
        header.pack(fill="x")
        ttk.Label(header, text="CLAIM REQUEST", style="WhiteAccent.TLabel").pack(anchor="w")
        ttk.Label(header, text=self.item["name"], style="CardHeading.TLabel", wraplength=590).pack(anchor="w", pady=(4, 0))
        ttk.Label(header, text="This form is private and goes to the Admin Office for review.", style="WhiteMuted.TLabel").pack(anchor="w", pady=(4, 0))

        self.scroll = ScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=16, pady=(8, 0))
        body = self.scroll.inner
        body.configure(padding=15)
        notice = ttk.Frame(body, style="Card.TFrame", padding=12)
        notice.pack(fill="x", pady=(0, 12))
        ttk.Label(
            notice,
            text="A claim is not an automatic approval. Bring your Claim ID and official school ID to the Admin Office for in-person identity and ownership verification.",
            style="WhiteMuted.TLabel",
            wraplength=570,
            justify="left",
        ).pack(anchor="w")

        role_box = ttk.LabelFrame(body, text="I am a:", padding=12)
        role_box.pack(fill="x", pady=(0, 12))
        role_row = ttk.Frame(role_box, style="White.TFrame")
        role_row.pack(anchor="w")
        for role in ("Student", "Teacher", "School Utility Personnel"):
            ttk.Radiobutton(role_row, text=role, variable=self.role_var, value=role, command=self._render_person_fields).pack(side="left", padx=(0, 18))
        self.person_fields = ttk.Frame(role_box, style="White.TFrame")
        self.person_fields.pack(fill="x", pady=(12, 0))
        self._render_person_fields()

        questions = ttk.LabelFrame(body, text="Ownership verification questions", padding=12)
        questions.pack(fill="x")
        self._entry_row(questions, 0, "Where do you believe you lost the item?", "last_seen_location", width=56)
        self._entry_row(questions, 1, "When did you last have it? (YYYY-MM-DD)", "last_seen_date", width=22)
        self._text_row(questions, 2, "Describe the item", "item_description", 3)
        self._text_row(questions, 3, "What makes it identifiable as yours?", "identifying_features", 3)
        self._text_row(questions, 4, "Additional information (optional)", "additional_info", 2)
        ttk.Label(
            body,
            text="Your name, school ID, contact details, and answers are visible only to Admin staff for verification.",
            style="Muted.TLabel",
            wraplength=570,
        ).pack(anchor="w", pady=(10, 0))

        actions = ttk.Frame(self, padding=(16, 12))
        actions.pack(fill="x")
        ttk.Button(actions, text="Cancel", style="Secondary.TButton", command=self.destroy).pack(side="right")
        ttk.Button(actions, text="Submit claim for review", style="Primary.TButton", command=self._submit).pack(side="right", padx=(0, 8))

    def _render_person_fields(self) -> None:
        for child in self.person_fields.winfo_children():
            child.destroy()
        role = self.role_var.get()
        if role == "Student":
            fields = (("Student ID", "school_id"), ("Full name", "full_name"), ("Contact number", "contact_number"), ("Course / Grade", "grade_course"), ("Section", "section"))
        elif role == "Teacher":
            fields = (("Employee ID", "school_id"), ("Full name", "full_name"), ("Contact number", "contact_number"), ("Department", "department"))
        else:
            fields = (("Employee ID", "school_id"), ("Full name", "full_name"), ("Contact number", "contact_number"), ("Assigned department / area", "assigned_area"))
        for row, (label, key) in enumerate(fields):
            self._entry_row(self.person_fields, row, label, key, width=52)

    def _entry_row(self, parent: tk.Misc, row: int, label: str, key: str, width: int = 42) -> None:
        ttk.Label(parent, text=label, style="White.TLabel").grid(row=row, column=0, sticky="nw", padx=(0, 12), pady=5)
        entry = ttk.Entry(parent, textvariable=self.vars[key], width=width)
        entry.grid(row=row, column=1, sticky="ew", pady=5)
        parent.columnconfigure(1, weight=1)

    def _text_row(self, parent: tk.Misc, row: int, label: str, key: str, height: int) -> None:
        ttk.Label(parent, text=label, style="White.TLabel").grid(row=row, column=0, sticky="nw", padx=(0, 12), pady=6)
        widget = text_widget(parent, height=height, width=45)
        widget.grid(row=row, column=1, sticky="ew", pady=5)
        self.question_texts[key] = widget
        parent.columnconfigure(1, weight=1)

    def _submit(self) -> None:
        role = self.role_var.get()
        person_data: dict[str, Any] = {
            "school_id": self.vars["school_id"].get(),
            "full_name": self.vars["full_name"].get(),
            "contact_number": self.vars["contact_number"].get(),
        }
        if role == "Student":
            person_data.update(grade_course=self.vars["grade_course"].get(), section=self.vars["section"].get())
        elif role == "Teacher":
            person_data["department"] = self.vars["department"].get()
        else:
            person_data["assigned_area"] = self.vars["assigned_area"].get()
        try:
            person = make_school_person(role, person_data)
            claim = Claim(
                item_id=int(self.item["id"]),
                claimant=person,
                last_seen_location=self.vars["last_seen_location"].get(),
                last_seen_date=self.vars["last_seen_date"].get(),
                item_description=text_value(self.question_texts["item_description"]),
                identifying_features=text_value(self.question_texts["identifying_features"]),
                additional_info=text_value(self.question_texts["additional_info"]),
            )
            claim_code = self.app.system.claims.submit_claim(claim)
        except (ValidationError, DuplicateClaimError, ItemUnavailableError) as exc:
            messagebox.showwarning("Claim not submitted", str(exc), parent=self)
            return
        except Exception as exc:
            messagebox.showerror("Claim error", f"The claim could not be submitted.\n\n{exc}", parent=self)
            return
        messagebox.showinfo(
            "Claim submitted successfully",
            f"Your claim has been submitted for Admin review.\n\nClaim ID: {claim_code}\n\nPlease present this Claim ID and your official school identification at the Admin Office. The item will not be released automatically.",
            parent=self,
        )
        if callable(self.on_submitted):
            self.on_submitted()
        self.destroy()
