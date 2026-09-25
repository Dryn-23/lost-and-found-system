"""Admin-only dialogs for item records, finder interviews, and claim decisions."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Any, Callable

from models.item import CATEGORIES
from utils.helpers import display_date, display_time, now_time, today_iso
from utils.validators import ValidationError
from views.ui import COLORS, ScrollableFrame, set_text, text_value, text_widget


class ItemEditDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, app: object, item: dict[str, Any], on_saved: Callable[[], None]) -> None:
        super().__init__(parent)
        self.app = app
        self.item = item
        self.on_saved = on_saved
        self.title(f"Edit item #{item['id']}")
        self.geometry("760x790")
        self.minsize(630, 650)
        self.configure(background=COLORS["background"])
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.vars: dict[str, tk.StringVar] = {
            key: tk.StringVar(value=str(item.get(key, "") or ""))
            for key in (
                "name", "category", "color", "brand", "location_found", "date_found",
                "time_found", "condition", "storage_location", "photo_path",
            )
        }
        self.texts: dict[str, tk.Text] = {}
        self._build()

    def _build(self) -> None:
        header = ttk.Frame(self, style="White.TFrame", padding=(20, 15))
        header.pack(fill="x")
        ttk.Label(header, text="EDIT FOUND ITEM", style="WhiteAccent.TLabel").pack(anchor="w")
        ttk.Label(header, text=self.item.get("name", "Item"), style="CardHeading.TLabel").pack(anchor="w", pady=(4, 0))
        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=14, pady=10)
        body = scroll.inner
        body.configure(padding=15)
        form = ttk.LabelFrame(body, text="Catalog and private item record", padding=14)
        form.pack(fill="x")
        row = 0
        self._entry(form, row, "Item name", "name"); row += 1
        ttk.Label(form, text="Category", style="White.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 12), pady=5)
        ttk.Combobox(form, textvariable=self.vars["category"], state="readonly", values=CATEGORIES).grid(row=row, column=1, sticky="ew", pady=5); row += 1
        self._text_row(form, row, "Public description", "public_description", str(self.item.get("public_description", "")), 3); row += 1
        self._entry(form, row, "Color (optional)", "color"); row += 1
        self._entry(form, row, "Brand (optional)", "brand"); row += 1
        self._entry(form, row, "General location found", "location_found"); row += 1
        self._entry(form, row, "Date found (YYYY-MM-DD)", "date_found"); row += 1
        self._entry(form, row, "Time found (HH:MM)", "time_found"); row += 1
        self._entry(form, row, "Condition", "condition"); row += 1
        self._entry(form, row, "Private storage location", "storage_location"); row += 1
        ttk.Label(form, text="Item photo (PNG/GIF)", style="White.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 12), pady=5)
        photo_row = ttk.Frame(form, style="White.TFrame")
        photo_row.grid(row=row, column=1, sticky="ew", pady=5)
        ttk.Entry(photo_row, textvariable=self.vars["photo_path"]).pack(side="left", fill="x", expand=True)
        ttk.Button(photo_row, text="Browse", style="Secondary.TButton", command=self._choose_photo).pack(side="left", padx=(7, 0)); row += 1
        self._text_row(form, row, "Private Admin notes", "private_notes", str(self.item.get("private_notes", "")), 3)
        form.columnconfigure(1, weight=1)
        actions = ttk.Frame(self, padding=(14, 10))
        actions.pack(fill="x")
        ttk.Button(actions, text="Cancel", style="Secondary.TButton", command=self.destroy).pack(side="right")
        ttk.Button(actions, text="Save changes", style="Primary.TButton", command=self._save).pack(side="right", padx=(0, 8))

    def _entry(self, parent: tk.Misc, row: int, label: str, key: str) -> None:
        ttk.Label(parent, text=label, style="White.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 12), pady=5)
        ttk.Entry(parent, textvariable=self.vars[key]).grid(row=row, column=1, sticky="ew", pady=5)

    def _text_row(self, parent: tk.Misc, row: int, label: str, key: str, value: str, height: int) -> None:
        ttk.Label(parent, text=label, style="White.TLabel").grid(row=row, column=0, sticky="nw", padx=(0, 12), pady=5)
        text = text_widget(parent, height=height, width=50)
        text.grid(row=row, column=1, sticky="ew", pady=5)
        set_text(text, value)
        self.texts[key] = text

    def _choose_photo(self) -> None:
        path = filedialog.askopenfilename(
            parent=self,
            title="Choose an item photo",
            filetypes=(("PNG and GIF images", "*.png *.gif"), ("All files", "*.*")),
        )
        if path:
            self.vars["photo_path"].set(path)

    def _save(self) -> None:
        values = {key: variable.get().strip() for key, variable in self.vars.items()}
        values["public_description"] = text_value(self.texts["public_description"])
        values["private_notes"] = text_value(self.texts["private_notes"])
        try:
            self.app.system.items.update_item(
                int(self.item["id"]), values, self.app.current_admin.username
            )
        except ValidationError as exc:
            messagebox.showwarning("Check the item details", str(exc), parent=self)
            return
        except Exception as exc:
            messagebox.showerror("Update failed", f"The item was not updated.\n\n{exc}", parent=self)
            return
        messagebox.showinfo("Item updated", "The item record has been updated.", parent=self)
        self.on_saved()
        self.destroy()


class AdminItemDetailsDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, app: object, item: dict[str, Any]) -> None:
        super().__init__(parent)
        self.app = app
        self.item = item
        self.title(f"Admin item record #{item['id']}")
        self.geometry("700x760")
        self.minsize(600, 620)
        self.configure(background=COLORS["background"])
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        header = ttk.Frame(self, style="White.TFrame", padding=(20, 15))
        header.pack(fill="x")
        ttk.Label(header, text="PRIVATE ADMIN RECORD", style="WhiteAccent.TLabel").pack(anchor="w")
        ttk.Label(header, text=item.get("name", "Item"), style="CardHeading.TLabel", wraplength=610).pack(anchor="w", pady=(4, 0))
        ttk.Label(header, text=f"Item #{item['id']}  ·  {item.get('status', '')}", style="WhiteMuted.TLabel").pack(anchor="w", pady=(4, 0))
        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=14, pady=10)
        body = scroll.inner
        body.configure(padding=14)
        item_box = ttk.LabelFrame(body, text="Item information", padding=12)
        item_box.pack(fill="x", pady=(0, 10))
        fields = [
            ("Category", item.get("category")),
            ("Public description", item.get("public_description")),
            ("Color / brand", f"{item.get('color') or 'Not specified'} / {item.get('brand') or 'Not specified'}"),
            ("Location found", item.get("location_found")),
            ("Date / time found", f"{display_date(item.get('date_found'))} · {display_time(item.get('time_found'))}"),
            ("Condition", item.get("condition")),
            ("Private storage location", item.get("storage_location")),
            ("Private notes", item.get("private_notes") or "—"),
            ("Photo path", item.get("photo_path") or "—"),
        ]
        for row, (label, value) in enumerate(fields):
            self._detail(item_box, label, value, row)
        finder_box = ttk.LabelFrame(body, text="Finder information — Admin only", padding=12)
        finder_box.pack(fill="x")
        finder_fields = [
            ("Finder", f"{item.get('finder_name')} · {item.get('finder_type')}"),
            ("School ID", item.get("finder_school_id")),
            ("Contact", item.get("finder_contact")),
            ("Affiliation / section", f"{item.get('finder_affiliation') or '—'} · {item.get('finder_section') or '—'}"),
            ("Where / when found", f"{item.get('finder_where_found')} · {display_date(item.get('finder_date_found'))} {display_time(item.get('finder_time_found'))}"),
            ("Circumstances", item.get("finder_circumstances")),
            ("Handling details", item.get("finder_touched_related")),
            ("Finder notes", item.get("finder_additional_notes") or "—"),
        ]
        for row, (label, value) in enumerate(finder_fields):
            self._detail(finder_box, label, value, row)
        ttk.Button(self, text="Close", style="Secondary.TButton", command=self.destroy).pack(anchor="e", padx=18, pady=(0, 14))

    @staticmethod
    def _detail(parent: ttk.Frame, label: str, value: Any, row: int) -> None:
        ttk.Label(parent, text=label, style="WhiteMuted.TLabel").grid(row=row, column=0, sticky="nw", padx=(0, 16), pady=4)
        ttk.Label(parent, text=str(value or "—"), style="White.TLabel", wraplength=420, justify="left").grid(row=row, column=1, sticky="nw", pady=4)
        parent.columnconfigure(1, weight=1)


class FinderDetailsDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, finder: dict[str, Any]) -> None:
        super().__init__(parent)
        self.finder = finder
        self.title("Private finder interview")
        self.geometry("640x690")
        self.minsize(540, 560)
        self.configure(background=COLORS["background"])
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        header = ttk.Frame(self, style="White.TFrame", padding=(20, 14))
        header.pack(fill="x")
        ttk.Label(header, text="FINDER INTERVIEW · ADMIN ONLY", style="WhiteAccent.TLabel").pack(anchor="w")
        ttk.Label(header, text=finder.get("full_name", "Finder"), style="CardHeading.TLabel").pack(anchor="w", pady=(4, 0))
        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=14, pady=10)
        body = scroll.inner
        body.configure(padding=14)
        details = ttk.LabelFrame(body, text="Private information", padding=12)
        details.pack(fill="x", pady=(0, 10))
        fields = [
            ("Role", finder.get("person_type")),
            ("Student / employee ID", finder.get("school_id")),
            ("Contact number", finder.get("contact_number")),
            ("Course / grade or department", finder.get("affiliation")),
            ("Section", finder.get("section") or "—"),
            ("Where found", finder.get("where_found")),
            ("Date / time found", f"{display_date(finder.get('date_found'))} · {display_time(finder.get('time_found'))}"),
            ("What finder was doing", finder.get("circumstances")),
            ("Whether item was handled", finder.get("touched_related")),
            ("Additional notes", finder.get("additional_notes") or "—"),
        ]
        for row, (label, value) in enumerate(fields):
            AdminItemDetailsDialog._detail(details, label, value, row)
        items_box = ttk.LabelFrame(body, text="Associated item record(s)", padding=12)
        items_box.pack(fill="x")
        items = finder.get("items", [])
        if not items:
            ttk.Label(items_box, text="No associated item records.", style="WhiteMuted.TLabel").pack(anchor="w")
        for item in items:
            ttk.Label(
                items_box,
                text=f"#{item['id']}  {item['name']}  ·  {item['status']}  ·  {item['location_found']}  ·  {display_date(item['date_found'])}",
                style="White.TLabel",
                wraplength=520,
            ).pack(anchor="w", pady=3)
        ttk.Button(self, text="Close", style="Secondary.TButton", command=self.destroy).pack(anchor="e", padx=18, pady=(0, 14))


class ClaimReviewDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Misc,
        app: object,
        claim_row_id: int,
        on_changed: Callable[[], None],
    ) -> None:
        super().__init__(parent)
        self.app = app
        self.claim_row_id = claim_row_id
        self.on_changed = on_changed
        self.claim = self.app.system.claims.claim(claim_row_id)
        if not self.claim:
            messagebox.showerror("Claim not found", "The claim record no longer exists.", parent=parent)
            self.destroy()
            return
        self.title(f"Review {self.claim['claim_id']}")
        self.geometry("820x820")
        self.minsize(690, 650)
        self.configure(background=COLORS["background"])
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.notes_text: tk.Text | None = None
        self._build()

    def _build(self) -> None:
        claim = self.claim
        header = ttk.Frame(self, style="White.TFrame", padding=(20, 14))
        header.pack(fill="x")
        ttk.Label(header, text="CLAIM REVIEW · ADMIN ONLY", style="WhiteAccent.TLabel").pack(anchor="w")
        ttk.Label(header, text=claim["claim_id"], style="CardHeading.TLabel").pack(anchor="w", pady=(4, 0))
        ttk.Label(header, text=f"Item: {claim['item_name']}  ·  Status: {claim['status']}", style="WhiteMuted.TLabel").pack(anchor="w", pady=(4, 0))

        scroll = ScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=14, pady=10)
        body = scroll.inner
        body.configure(padding=14)
        claimant_box = ttk.LabelFrame(body, text="Claimant identity — private", padding=12)
        claimant_box.pack(fill="x", pady=(0, 10))
        claim_fields = [
            ("Claimant", claim.get("full_name")),
            ("Claimant type", claim.get("claimant_type")),
            ("Student / employee ID", claim.get("school_id")),
            ("Contact number", claim.get("contact_number")),
            ("Course / grade or department", claim.get("affiliation")),
            ("Section", claim.get("section") or "—"),
            ("Submitted", claim.get("submitted_at")),
            ("Last seen location", claim.get("last_seen_location")),
            ("Date last seen", display_date(claim.get("last_seen_date"))),
        ]
        for row, (label, value) in enumerate(claim_fields):
            AdminItemDetailsDialog._detail(claimant_box, label, value, row)
        answers = ttk.LabelFrame(body, text="Claimant's ownership answers", padding=12)
        answers.pack(fill="x", pady=(0, 10))
        self._question(answers, "Description provided", claim.get("item_description"), 0)
        self._question(answers, "Identifying characteristics / ownership explanation", claim.get("identifying_features"), 1)
        self._question(answers, "Additional information", claim.get("additional_info") or "—", 2)
        ttk.Label(
            body,
            text="Final ownership verification must be performed by Admin staff in person. The software does not decide ownership.",
            style="Muted.TLabel",
            wraplength=700,
        ).pack(anchor="w", pady=(0, 8))
        notes_box = ttk.LabelFrame(body, text="Admin verification / decision notes", padding=10)
        notes_box.pack(fill="x")
        self.notes_text = text_widget(notes_box, height=4, width=60)
        self.notes_text.pack(fill="x")
        set_text(self.notes_text, claim.get("admin_notes", ""))

        actions = ttk.Frame(self, padding=(14, 10))
        actions.pack(fill="x")
        ttk.Button(actions, text="Close", style="Secondary.TButton", command=self.destroy).pack(side="right")
        status = claim.get("status")
        if status in ("Pending", "Verification Requested"):
            ttk.Button(actions, text="REJECT CLAIM", style="Danger.TButton", command=lambda: self._decide("Rejected")).pack(side="right", padx=(0, 8))
            ttk.Button(actions, text="APPROVE CLAIM", style="Primary.TButton", command=lambda: self._decide("Approved")).pack(side="right", padx=(0, 8))
            ttk.Button(actions, text="REQUEST VERIFICATION", style="Secondary.TButton", command=lambda: self._decide("Verification Requested")).pack(side="right", padx=(0, 8))
        elif status == "Approved":
            ttk.Button(actions, text="MARK AS RETURNED", style="Primary.TButton", command=self._open_return_form).pack(side="right", padx=(0, 8))
        elif status == "Completed":
            ttk.Label(actions, text="Physical return recorded", style="Accent.TLabel").pack(side="right", padx=(0, 8))
        else:
            ttk.Label(actions, text=f"Claim is {status.lower()} and is read-only.", style="Muted.TLabel").pack(side="right", padx=(0, 8))

    @staticmethod
    def _question(parent: ttk.LabelFrame, label: str, value: Any, row: int) -> None:
        ttk.Label(parent, text=label, style="WhiteMuted.TLabel").grid(row=row, column=0, sticky="nw", padx=(0, 15), pady=5)
        ttk.Label(parent, text=str(value or "—"), style="White.TLabel", wraplength=530, justify="left").grid(row=row, column=1, sticky="nw", pady=5)
        parent.columnconfigure(1, weight=1)

    def _notes(self) -> str:
        return text_value(self.notes_text) if self.notes_text else ""

    def _decide(self, status: str) -> None:
        if status == "Approved":
            confirmed = messagebox.askyesno(
                "Confirm in-person verification",
                "Confirm that you personally checked the claimant's official school identification and ownership answers against the physical item at the Admin Office.\n\nThis will approve the claim but will NOT mark the item as returned.",
                parent=self,
            )
            if not confirmed:
                return
        elif status == "Rejected":
            if not self._notes():
                messagebox.showwarning("Add a decision note", "Please record a brief reason for rejecting this claim.", parent=self)
                return
            if not messagebox.askyesno("Reject claim", "Reject this claim? The decision will be recorded in the activity log.", parent=self):
                return
        elif status == "Verification Requested":
            if not messagebox.askyesno(
                "Request in-person verification",
                "Set this claim to Verification Requested. The claimant must visit the Admin Office with their school ID and Claim ID; this app does not send an external notification.",
                parent=self,
            ):
                return
        try:
            self.app.system.claims.review(
                self.claim_row_id,
                status,
                self.app.current_admin.username,
                self._notes(),
            )
        except Exception as exc:
            messagebox.showerror("Claim update failed", f"The claim status was not changed.\n\n{exc}", parent=self)
            return
        messagebox.showinfo("Claim updated", f"{self.claim['claim_id']} is now marked {status}.", parent=self)
        self.on_changed()
        self.destroy()

    def _open_return_form(self) -> None:
        ReturnFormDialog(self, self.app, self.claim, self._returned)

    def _returned(self) -> None:
        self.on_changed()
        self.destroy()


class ReturnFormDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, app: object, claim: dict[str, Any], on_saved: Callable[[], None]) -> None:
        super().__init__(parent)
        self.app = app
        self.claim = claim
        self.on_saved = on_saved
        self.title("Record physical item return")
        self.geometry("570x560")
        self.minsize(500, 480)
        self.configure(background=COLORS["background"])
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.vars = {
            "returned_date": tk.StringVar(value=today_iso()),
            "returned_time": tk.StringVar(value=now_time()),
            "released_by": tk.StringVar(value=self.app.current_admin.username),
            "claimant_name": tk.StringVar(value=claim.get("full_name", "")),
        }
        self._build()

    def _build(self) -> None:
        header = ttk.Frame(self, style="White.TFrame", padding=(20, 15))
        header.pack(fill="x")
        ttk.Label(header, text="PHYSICAL HANDOVER", style="WhiteAccent.TLabel").pack(anchor="w")
        ttk.Label(header, text=self.claim["item_name"], style="CardHeading.TLabel").pack(anchor="w", pady=(4, 0))
        ttk.Label(header, text=f"Claim ID: {self.claim['claim_id']} · claimant: {self.claim['full_name']}", style="WhiteMuted.TLabel").pack(anchor="w", pady=(4, 0))
        body = ttk.Frame(self, padding=18)
        body.pack(fill="both", expand=True)
        notice = ttk.Frame(body, style="Card.TFrame", padding=12)
        notice.pack(fill="x", pady=(0, 12))
        ttk.Label(notice, text="Only record this after the item has actually been handed to the verified claimant.", style="WhiteMuted.TLabel", wraplength=480).pack(anchor="w")
        form = ttk.LabelFrame(body, text="Return record", padding=12)
        form.pack(fill="x")
        labels = (("Return date (YYYY-MM-DD)", "returned_date"), ("Return time (HH:MM)", "returned_time"), ("Released by", "released_by"), ("Claimant receiving item", "claimant_name"))
        for row, (label, key) in enumerate(labels):
            ttk.Label(form, text=label, style="White.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 10), pady=6)
            ttk.Entry(form, textvariable=self.vars[key]).grid(row=row, column=1, sticky="ew", pady=6)
        ttk.Label(form, text="Notes (optional)", style="White.TLabel").grid(row=4, column=0, sticky="nw", padx=(0, 10), pady=6)
        self.notes = text_widget(form, height=3, width=38)
        self.notes.grid(row=4, column=1, sticky="ew", pady=6)
        form.columnconfigure(1, weight=1)
        actions = ttk.Frame(self, padding=(18, 10))
        actions.pack(fill="x")
        ttk.Button(actions, text="Cancel", style="Secondary.TButton", command=self.destroy).pack(side="right")
        ttk.Button(actions, text="Confirm item was returned", style="Primary.TButton", command=self._save).pack(side="right", padx=(0, 8))

    def _save(self) -> None:
        if not messagebox.askyesno(
            "Confirm physical handover",
            "Confirm the item has been physically released to the claimant and this return record is accurate.",
            parent=self,
        ):
            return
        values = {key: var.get().strip() for key, var in self.vars.items()}
        values["notes"] = text_value(self.notes)
        try:
            self.app.system.claims.mark_returned(
                int(self.claim["id"]), values, self.app.current_admin.username
            )
        except ValidationError as exc:
            messagebox.showwarning("Check return details", str(exc), parent=self)
            return
        except Exception as exc:
            messagebox.showerror("Return not recorded", f"The item was not marked returned.\n\n{exc}", parent=self)
            return
        messagebox.showinfo("Return recorded", "The item is now marked Returned and will not appear in the public catalog.", parent=self)
        self.on_saved()
        self.destroy()
