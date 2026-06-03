from __future__ import annotations

import threading
import webbrowser
from datetime import datetime
from tkinter import messagebox, ttk
import tkinter as tk
from typing import List, Optional

from src.filters.conference_status import (
    attend_link_enabled,
    attendance_status_label,
    submit_link_enabled,
    submission_status_label,
)
from src.models import Conference
from src.search.orchestrator import SearchOrchestrator, SearchResult
from src.search.topics import TOPIC_CHOICES
from src.ui.widgets import labeled_combobox, labeled_entry, make_treeview


class ConferenceFinderApp:
    COLUMNS = (
        "Rank",
        "Name",
        "Dates",
        "Location",
        "Deadline",
        "Prestige",
        "Submit",
        "Attend",
    )

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("US CS Conference Finder")
        self.root.minsize(1000, 550)

        self.orchestrator = SearchOrchestrator()
        self._results: List[Conference] = []
        self._row_links: dict[str, tuple[str, str, bool, bool]] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill=tk.X)

        _, self.topic_combo = labeled_combobox(top, "Topic:", TOPIC_CHOICES, width=26)
        self.topic_combo.set(TOPIC_CHOICES[0])

        _, self.query_entry = labeled_entry(top, "Semantic search:", width=36)

        self.search_btn = ttk.Button(top, text="Search", command=self._on_search)
        self.search_btn.pack(side=tk.LEFT, padx=8)

        self.status_var = tk.StringVar(
            value="Ready. Submit/Attend Open/Closed compared to today's date."
        )
        status = ttk.Label(self.root, textvariable=self.status_var, padding=(8, 0))
        status.pack(fill=tk.X)

        mid = ttk.Frame(self.root, padding=8)
        mid.pack(fill=tk.BOTH, expand=True)

        self.tree = make_treeview(mid, list(self.COLUMNS))
        self.tree.bind("<Double-1>", self._on_double_click)

        bottom = ttk.Frame(self.root, padding=8)
        bottom.pack(fill=tk.X)
        self._configure_progress_styles()
        self.progress = ttk.Progressbar(
            bottom,
            mode="determinate",
            maximum=100,
            value=0,
            style="Idle.Horizontal.TProgressbar",
        )
        self.progress.pack(fill=tk.X)
        ttk.Label(
            bottom,
            text=(
                "Submit/Attend show Open only if deadline or conference date is today or later. "
                "Double-click Open to open the link."
            ),
        ).pack(anchor=tk.W, pady=(4, 0))

        self.query_entry.bind("<Return>", lambda _: self._on_search())

    def _on_search(self) -> None:
        topic = self.topic_combo.get()
        query = self.query_entry.get().strip()
        self.search_btn.config(state=tk.DISABLED)
        self.status_var.set("Fetching conferences…")
        self._start_loading_progress()

        def worker():
            try:
                result = self.orchestrator.search(topic, query)
                self.root.after(0, lambda: self._show_results(result, None))
            except Exception as exc:
                self.root.after(0, lambda: self._show_results(None, exc))

        threading.Thread(target=worker, daemon=True).start()

    @staticmethod
    def _configure_progress_styles() -> None:
        style = ttk.Style()
        style.configure(
            "Idle.Horizontal.TProgressbar",
            troughcolor="#e8e8e8",
            background="#e8e8e8",
            lightcolor="#e8e8e8",
            darkcolor="#e8e8e8",
        )
        style.configure(
            "Success.Horizontal.TProgressbar",
            troughcolor="#e8e8e8",
            background="#2e7d32",
            lightcolor="#43a047",
            darkcolor="#1b5e20",
        )

    def _start_loading_progress(self) -> None:
        self.progress.configure(
            style="Idle.Horizontal.TProgressbar",
            mode="indeterminate",
            value=0,
        )
        self.progress.start(10)

    def _finish_loading_progress_success(self) -> None:
        self.progress.stop()
        self.progress.configure(
            style="Success.Horizontal.TProgressbar",
            mode="determinate",
            maximum=100,
            value=100,
        )

    def _show_results(
        self,
        result: Optional[SearchResult],
        error: Optional[Exception],
    ) -> None:
        self.search_btn.config(state=tk.NORMAL)

        if error:
            self.progress.stop()
            messagebox.showerror("Search failed", str(error))
            self.status_var.set(f"Error: {error}")
            return

        if result is None:
            self.progress.stop()
            self.status_var.set("No results.")
            return

        self._finish_loading_progress_success()

        results = result.conferences
        self._results = results
        self._row_links.clear()

        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, conf in enumerate(results, start=1):
            iid = str(i)
            submit_status = submission_status_label(conf)
            attend_status = attendance_status_label(conf)
            submit_click = submit_link_enabled(conf)
            attend_click = attend_link_enabled(conf)

            submit_col = submit_status if not submit_click else f"{submit_status} (link)"
            attend_col = attend_status if not attend_click else f"{attend_status} (link)"

            deadline_display = conf.deadline or (
                conf.deadline_date.isoformat() if conf.deadline_date else "N/A"
            )

            self._row_links[iid] = (
                conf.submit_link if submit_click else "",
                conf.attend_link if attend_click else "",
                submit_click,
                attend_click,
            )
            self.tree.insert(
                "",
                tk.END,
                iid=iid,
                values=(
                    i,
                    conf.name,
                    conf.dates,
                    conf.location,
                    deadline_display,
                    conf.prestige_label,
                    submit_col,
                    attend_col,
                ),
            )

        ts = datetime.now().strftime("%H:%M:%S")
        self.status_var.set(f"{result.status} (updated {ts})")
        if len(results) == 0:
            messagebox.showinfo(
                "No results",
                "No upcoming US conferences matched your filters.\n\n"
                f"{result.status}\n\n"
                "Tips: ensure you are online, try 'All Computer Science', "
                "or clear the semantic search box.",
            )

    def _on_double_click(self, event) -> None:
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        col = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)
        if not row or row not in self._row_links:
            return

        submit_url, attend_url, submit_ok, attend_ok = self._row_links[row]
        col_index = int(col.replace("#", "")) - 1
        col_name = self.COLUMNS[col_index] if col_index < len(self.COLUMNS) else ""

        url = ""
        if col_name == "Submit" and submit_ok and submit_url:
            url = submit_url
        elif col_name == "Attend" and attend_ok and attend_url:
            url = attend_url

        if url:
            webbrowser.open(url)
        else:
            messagebox.showinfo(
                "Not available",
                "No link, or registration/submission is closed based on today's date.",
            )


def run_app() -> None:
    root = tk.Tk()
    style = ttk.Style()
    if "vista" in style.theme_names():
        style.theme_use("vista")
    ConferenceFinderApp(root)
    root.mainloop()
