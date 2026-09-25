"""Reusable ttk theme and widget helpers."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Iterable


COLORS = {
    "navy": "#18324B",
    "navy_dark": "#102438",
    "teal": "#087F78",
    "teal_dark": "#066B65",
    "teal_soft": "#E4F4F2",
    "ink": "#203247",
    "muted": "#687B8D",
    "background": "#F4F7FA",
    "white": "#FFFFFF",
    "line": "#DFE7ED",
    "amber": "#9A6200",
    "amber_soft": "#FFF3D9",
    "red": "#A33A3A",
    "red_soft": "#FCEBEC",
    "green": "#24734B",
    "green_soft": "#E9F5ED",
    "blue_soft": "#EAF1F8",
}


def setup_theme(root: tk.Misc) -> ttk.Style:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("TFrame", background=COLORS["background"])
    style.configure("White.TFrame", background=COLORS["white"])
    style.configure("Card.TFrame", background=COLORS["white"], relief="solid", borderwidth=1)
    style.configure("Sidebar.TFrame", background=COLORS["navy_dark"])
    style.configure("SidebarTitle.TLabel", background=COLORS["navy_dark"], foreground=COLORS["white"], font=("Segoe UI", 12, "bold"))
    style.configure("SidebarSub.TLabel", background=COLORS["navy_dark"], foreground="#AFC3D2", font=("Segoe UI", 8))
    style.configure("SidebarSection.TLabel", background=COLORS["navy_dark"], foreground="#87A1B6", font=("Segoe UI", 8, "bold"))
    style.configure("Hero.TFrame", background=COLORS["navy"])
    style.configure("TLabel", background=COLORS["background"], foreground=COLORS["ink"], font=("Segoe UI", 10))
    style.configure("White.TLabel", background=COLORS["white"], foreground=COLORS["ink"], font=("Segoe UI", 10))
    style.configure("Muted.TLabel", background=COLORS["background"], foreground=COLORS["muted"], font=("Segoe UI", 9))
    style.configure("WhiteMuted.TLabel", background=COLORS["white"], foreground=COLORS["muted"], font=("Segoe UI", 9))
    style.configure("WhiteAccent.TLabel", background=COLORS["white"], foreground=COLORS["teal"], font=("Segoe UI", 10, "bold"))
    style.configure("Placeholder.TFrame", background="#EDF2F6")
    style.configure("Placeholder.TLabel", background="#EDF2F6", foreground="#8594A1", font=("Segoe UI", 9, "bold"))
    style.configure("HeroTitle.TLabel", background=COLORS["navy"], foreground=COLORS["white"], font=("Segoe UI", 27, "bold"))
    style.configure("HeroSubtitle.TLabel", background=COLORS["navy"], foreground="#DCE8F0", font=("Segoe UI", 11))
    style.configure("Title.TLabel", background=COLORS["background"], foreground=COLORS["navy"], font=("Segoe UI", 21, "bold"))
    style.configure("Heading.TLabel", background=COLORS["background"], foreground=COLORS["navy"], font=("Segoe UI", 15, "bold"))
    style.configure("CardTitle.TLabel", background=COLORS["white"], foreground=COLORS["navy"], font=("Segoe UI", 11, "bold"))
    style.configure("CardHeading.TLabel", background=COLORS["white"], foreground=COLORS["navy"], font=("Segoe UI", 21, "bold"))
    style.configure("BigNumber.TLabel", background=COLORS["white"], foreground=COLORS["navy"], font=("Segoe UI", 24, "bold"))
    style.configure("Accent.TLabel", background=COLORS["background"], foreground=COLORS["teal"], font=("Segoe UI", 10, "bold"))
    style.configure("HeroEyebrow.TLabel", background=COLORS["navy"], foreground="#8FE0D7", font=("Segoe UI", 9, "bold"))
    style.configure("Status.TLabel", background=COLORS["teal_soft"], foreground=COLORS["teal_dark"], padding=(8, 3), font=("Segoe UI", 8, "bold"))
    style.configure("Pending.TLabel", background=COLORS["amber_soft"], foreground=COLORS["amber"], padding=(8, 3), font=("Segoe UI", 8, "bold"))
    style.configure("DangerText.TLabel", background=COLORS["red_soft"], foreground=COLORS["red"], padding=(8, 3), font=("Segoe UI", 8, "bold"))

    style.configure("TButton", font=("Segoe UI", 9), padding=(12, 8), foreground=COLORS["ink"])
    style.map("TButton", foreground=[("disabled", "#98A5B0")])
    style.configure("Primary.TButton", background=COLORS["teal"], foreground=COLORS["white"], borderwidth=0, font=("Segoe UI", 9, "bold"), padding=(14, 9))
    style.map("Primary.TButton", background=[("active", COLORS["teal_dark"]), ("disabled", "#A9C8C4")], foreground=[("disabled", "#F8FFFF")])
    style.configure("Secondary.TButton", background=COLORS["white"], foreground=COLORS["navy"], bordercolor=COLORS["line"], padding=(12, 8))
    style.map("Secondary.TButton", background=[("active", "#EEF4F7")])
    style.configure("Danger.TButton", background=COLORS["red"], foreground=COLORS["white"], borderwidth=0, font=("Segoe UI", 9, "bold"), padding=(12, 8))
    style.map("Danger.TButton", background=[("active", "#842D31")])
    style.configure("Link.TButton", background=COLORS["white"], foreground=COLORS["teal"], borderwidth=0, padding=(8, 6), font=("Segoe UI", 9, "bold"))
    style.map("Link.TButton", background=[("active", COLORS["teal_soft"])])
    style.configure("SmallLink.TButton", background=COLORS["background"], foreground=COLORS["muted"], borderwidth=0, padding=(5, 3), font=("Segoe UI", 8))
    style.map("SmallLink.TButton", foreground=[("active", COLORS["teal"])])
    style.configure("Chip.TButton", background=COLORS["white"], foreground=COLORS["muted"], bordercolor=COLORS["line"], padding=(10, 6), font=("Segoe UI", 9))
    style.map("Chip.TButton", background=[("active", COLORS["teal_soft"])], foreground=[("active", COLORS["teal_dark"])])
    style.configure("SelectedChip.TButton", background=COLORS["teal"], foreground=COLORS["white"], borderwidth=0, padding=(10, 6), font=("Segoe UI", 9, "bold"))
    style.map("SelectedChip.TButton", background=[("active", COLORS["teal_dark"])])
    style.configure("Nav.TButton", background=COLORS["navy_dark"], foreground="#D7E4EE", borderwidth=0, anchor="w", padding=(14, 11), font=("Segoe UI", 9))
    style.map("Nav.TButton", background=[("active", "#1C3851")], foreground=[("active", COLORS["white"])])
    style.configure("NavActive.TButton", background=COLORS["teal"], foreground=COLORS["white"], borderwidth=0, anchor="w", padding=(14, 11), font=("Segoe UI", 9, "bold"))
    style.map("NavActive.TButton", background=[("active", COLORS["teal_dark"])])

    style.configure("TEntry", padding=(8, 7), fieldbackground=COLORS["white"], foreground=COLORS["ink"])
    style.configure("TCombobox", padding=(7, 6), fieldbackground=COLORS["white"], foreground=COLORS["ink"])
    style.map("TCombobox", fieldbackground=[("readonly", COLORS["white"])])
    style.configure("TLabelframe", background=COLORS["white"], bordercolor=COLORS["line"], relief="solid", borderwidth=1)
    style.configure("TLabelframe.Label", background=COLORS["white"], foreground=COLORS["navy"], font=("Segoe UI", 10, "bold"))
    style.configure("Treeview", background=COLORS["white"], fieldbackground=COLORS["white"], foreground=COLORS["ink"], rowheight=32, font=("Segoe UI", 9), borderwidth=0)
    style.configure("Treeview.Heading", background="#EAF0F5", foreground=COLORS["navy"], font=("Segoe UI", 9, "bold"), padding=(8, 8), relief="flat")
    style.map("Treeview", background=[("selected", COLORS["teal_soft"])], foreground=[("selected", COLORS["navy"])])
    style.configure("TNotebook", background=COLORS["background"], borderwidth=0)
    style.configure("TNotebook.Tab", padding=(14, 8), font=("Segoe UI", 9))
    style.configure("TRadiobutton", background=COLORS["white"], foreground=COLORS["ink"], font=("Segoe UI", 9))
    style.configure("TCheckbutton", background=COLORS["white"], foreground=COLORS["ink"], font=("Segoe UI", 9))
    return style


class ScrollableFrame(ttk.Frame):
    """A ttk content frame with a standard Tk canvas and vertical scrollbar."""

    def __init__(self, master: tk.Misc, background: str | None = None, **kwargs: object) -> None:
        super().__init__(master, **kwargs)
        self.canvas = tk.Canvas(
            self,
            background=background or COLORS["background"],
            highlightthickness=0,
            borderwidth=0,
        )
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self)
        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.inner.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_inner)
        self.canvas.bind("<Enter>", self._enable_wheel)
        self.canvas.bind("<Leave>", self._disable_wheel)
        self.bind("<Destroy>", self._on_destroy, add="+")

    def _update_scroll_region(self, _event: tk.Event | None = None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_inner(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _enable_wheel(self, _event: tk.Event | None = None) -> None:
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_linux_wheel)
        self.canvas.bind_all("<Button-5>", self._on_linux_wheel)

    def _disable_wheel(self, _event: tk.Event | None = None) -> None:
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event: tk.Event) -> None:
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_linux_wheel(self, event: tk.Event) -> None:
        self.canvas.yview_scroll(-1 if event.num == 4 else 1, "units")

    def _on_destroy(self, event: tk.Event) -> None:
        if event.widget is self:
            self._disable_wheel()

    def scroll_to(self, widget: tk.Widget) -> None:
        self.update_idletasks()
        total = max(self.inner.winfo_height(), 1)
        self.canvas.yview_moveto(max(0.0, min(widget.winfo_y() / total, 1.0)))


def section_heading(parent: ttk.Frame, title: str, subtitle: str = "") -> ttk.Frame:
    header = ttk.Frame(parent)
    header.pack(fill="x", pady=(0, 16))
    ttk.Label(header, text=title, style="Title.TLabel").pack(anchor="w")
    if subtitle:
        ttk.Label(header, text=subtitle, style="Muted.TLabel", wraplength=1000).pack(anchor="w", pady=(4, 0))
    return header


def build_tree(
    parent: tk.Misc,
    columns: Iterable[tuple[str, str, int, str]],
    height: int = 14,
) -> tuple[ttk.Treeview, ttk.Frame]:
    """Create a headed treeview with the supplied (key, title, width, anchor) columns."""
    wrapper = ttk.Frame(parent, style="White.TFrame")
    keys = [column[0] for column in columns]
    tree = ttk.Treeview(wrapper, columns=keys, show="headings", height=height, selectmode="browse")
    for key, title, width, anchor in columns:
        tree.heading(key, text=title, anchor=anchor)
        tree.column(key, width=width, minwidth=max(50, min(width, 80)), anchor=anchor, stretch=True)
    vertical = ttk.Scrollbar(wrapper, orient="vertical", command=tree.yview)
    horizontal = ttk.Scrollbar(wrapper, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vertical.grid(row=0, column=1, sticky="ns")
    horizontal.grid(row=1, column=0, sticky="ew")
    wrapper.rowconfigure(0, weight=1)
    wrapper.columnconfigure(0, weight=1)
    return tree, wrapper


def text_widget(parent: tk.Misc, height: int = 4, width: int = 40) -> tk.Text:
    return tk.Text(
        parent,
        height=height,
        width=width,
        wrap="word",
        undo=True,
        font=("Segoe UI", 9),
        background=COLORS["white"],
        foreground=COLORS["ink"],
        insertbackground=COLORS["ink"],
        relief="solid",
        borderwidth=1,
        highlightthickness=1,
        highlightbackground=COLORS["line"],
        highlightcolor=COLORS["teal"],
        padx=8,
        pady=6,
    )


def text_value(widget: tk.Text) -> str:
    return widget.get("1.0", "end-1c").strip()


def set_text(widget: tk.Text, value: str) -> None:
    widget.delete("1.0", "end")
    widget.insert("1.0", value or "")
