from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def labeled_combobox(
    parent: tk.Misc,
    label: str,
    values: list[str],
    *,
    width: int = 28,
) -> tuple[ttk.Label, ttk.Combobox]:
    frame = ttk.Frame(parent)
    lbl = ttk.Label(frame, text=label)
    lbl.pack(side=tk.LEFT, padx=(0, 6))
    combo = ttk.Combobox(frame, values=values, width=width, state="readonly")
    combo.pack(side=tk.LEFT)
    frame.pack(side=tk.LEFT, padx=4, pady=4)
    return lbl, combo


def labeled_entry(
    parent: tk.Misc,
    label: str,
    *,
    width: int = 40,
) -> tuple[ttk.Label, ttk.Entry]:
    frame = ttk.Frame(parent)
    lbl = ttk.Label(frame, text=label)
    lbl.pack(side=tk.LEFT, padx=(0, 6))
    entry = ttk.Entry(frame, width=width)
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    frame.pack(side=tk.LEFT, padx=4, pady=4, fill=tk.X, expand=True)
    return lbl, entry


def make_treeview(parent: tk.Misc, columns: list[str]) -> ttk.Treeview:
    tree = ttk.Treeview(parent, columns=columns, show="headings", height=18)
    for col in columns:
        tree.heading(col, text=col)
        width = 90
        if col == "Name":
            width = 200
        elif col in ("Dates", "Location", "Deadline"):
            width = 120
        elif col == "Prestige":
            width = 110
        elif col in ("Submit", "Attend"):
            width = 95
        tree.column(col, width=width, anchor=tk.W)
    vsb = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    return tree
