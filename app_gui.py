# ============================================================
# COMP9001 Final Project  —  Smart Review Scoring System
# Student: Qiyuan Dong
#
# HOW TO RUN:
#   python app_gui.py
#
# LIBRARIES USED:
#   tkinter  —  Python built-in GUI library (creates a desktop window)
#
# NOTE FOR TUTOR:
#   This is a GUI application. It will NOT run inside Ed's browser
#   terminal because a display is required.
#   Please run it locally with:  python app_gui.py
#   A pre-built Windows executable is also available at:
#   https://github.com/haichuan121/9001
# ============================================================
"""
Smart Review Scoring System - GUI Application
USYD COMP9001 Final Project
"""

import tkinter as tk
from tkinter import ttk, messagebox

# ============================================================
# Data storage
# ============================================================

items = {}   # { name: { "reviews": [...], "score": float } }
users = {}   # { username: { "weight": float, "history": [float], "note": str } }


# ============================================================
# Core logic  (no external libraries)
# ============================================================

def compute_user_weight(history):
    """Return (weight, note) based on the user's scoring history."""
    if len(history) < 2:
        return 1.0, "Not enough history"

    total = 0.0
    for s in history:
        total = total + s
    average = total / len(history)

    variance_sum = 0.0
    for s in history:
        variance_sum = variance_sum + (s - average) ** 2
    variance = variance_sum / len(history)

    if average >= 8.5:
        return 0.4, "Always high scores"
    elif average <= 1.5:
        return 0.4, "Always low scores"
    elif variance < 1.0:
        return 0.7, "Low score variety"
    else:
        return 1.0, "Normal"


# ── helpers ──────────────────────────────────────────────────────────

def _mean(values):
    if len(values) == 0:
        return 0.0
    total = 0.0
    for v in values:
        total = total + v
    return total / len(values)


def _stddev(values):
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    variance = 0.0
    for v in values:
        variance = variance + (v - m) ** 2
    return (variance / len(values)) ** 0.5


# ── malicious review filter ───────────────────────────────────────────

def filter_malicious(review_list):
    """Remove malicious reviews using three standards.

    Standard 1 — Formula gaming:
        raw >= 9.5 or raw <= 0.5, AND satisfaction == 0.0
        (extreme score + zero satisfaction = maximum formula impact)

    Standard 2 — Statistical outlier:
        |raw - group_mean| > 3 * std_dev  (requires >= 5 reviews)

    Standard 3 — Coordinated identical:
        >= 3 different users submit the exact same (raw, satisfaction) pair

    Returns (clean_list, flagged_list).
    """
    flagged = []
    keep    = []

    # --- Standard 1: formula gaming ---
    for review in review_list:
        raw = review["raw"]
        sat = review["satisfaction"]
        if (raw >= 9.5 or raw <= 0.5) and sat == 0.0:
            flagged.append(review)
        else:
            keep.append(review)

    # --- Standard 3: coordinated identical (no mean needed) ---
    combo_users = {}
    for review in review_list:
        key = (review["raw"], review["satisfaction"])
        if key not in combo_users:
            combo_users[key] = set()
        combo_users[key].add(review["user"])

    still_keep = []
    for review in keep:
        key = (review["raw"], review["satisfaction"])
        if len(combo_users[key]) >= 3:
            flagged.append(review)
        else:
            still_keep.append(review)
    keep = still_keep

    # --- Standard 2: statistical outlier (uses mean of pre-filtered set) ---
    if len(keep) >= 5:
        raws   = [r["raw"] for r in keep]
        mean   = _mean(raws)
        stddev = _stddev(raws)
        if stddev > 0:
            final_keep = []
            for review in keep:
                if abs(review["raw"] - mean) > 3 * stddev:
                    flagged.append(review)
                else:
                    final_keep.append(review)
            keep = final_keep

    return keep, flagged


# ── scoring ───────────────────────────────────────────────────────────

def compute_item_score(review_list):
    """Compute the final score for one item.

    Steps:
      1. Filter malicious reviews.
      2. Compute group_mean from clean reviews (= current overall score).
      3. Adjust each review:
           adjusted = raw * (1 - satisfaction) + group_mean * satisfaction
         satisfaction = 1.0 → you agree with the current score, vote = group_mean
         satisfaction = 0.0 → you strongly disagree, vote = your raw score
      4. Final = weighted mean of adjusted scores, weighted by user_weight.
    """
    if len(review_list) == 0:
        return 0.0

    # Step 1: remove malicious reviews
    clean, _ = filter_malicious(review_list)
    if len(clean) == 0:
        return 0.0

    # Step 2: group mean of raw scores
    raws       = [r["raw"] for r in clean]
    group_mean = _mean(raws)

    # Steps 3 & 4: adjusted score weighted by user trust
    weighted_sum = 0.0
    weight_total = 0.0

    for review in clean:
        username    = review["user"]
        user_weight = users[username]["weight"] if username in users else 1.0
        adjusted    = review["raw"] * (1 - review["satisfaction"]) \
                    + group_mean    *      review["satisfaction"]
        weighted_sum = weighted_sum + adjusted    * user_weight
        weight_total = weight_total + user_weight

    if weight_total == 0.0:
        return 0.0
    return weighted_sum / weight_total


def refresh_scores():
    for name in items:
        items[name]["score"] = compute_item_score(items[name]["reviews"])


# ============================================================
# GUI
# ============================================================

FONT_TITLE  = ("Segoe UI", 14, "bold")
FONT_LABEL  = ("Segoe UI", 10)
FONT_BUTTON = ("Segoe UI", 10, "bold")
BG_HEADER   = "#1a1a2e"
FG_HEADER   = "#e0e0e0"
ACCENT      = "#4f8ef7"
BG_MAIN     = "#f5f5f5"


class SmartReviewApp:
    def __init__(self, root):
        self.root = root
        root.title("Smart Review Scoring System")
        root.geometry("780x560")
        root.resizable(False, False)
        root.configure(bg=BG_MAIN)

        self._build_header()
        self._build_notebook()
        self._build_add_tab()
        self._build_rate_tab()
        self._build_leaderboard_tab()
        self._build_weights_tab()

        # Auto-refresh table tabs when selected
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

    # ── Header ──────────────────────────────────────────────────────

    def _build_header(self):
        header = tk.Frame(self.root, bg=BG_HEADER, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="Smart Review Scoring System",
            font=FONT_TITLE, bg=BG_HEADER, fg=FG_HEADER
        ).pack(side="left", padx=20, pady=12)

        tk.Label(
            header, text="USYD COMP9001",
            font=("Segoe UI", 9), bg=BG_HEADER, fg="#888"
        ).pack(side="right", padx=20)

    # ── Notebook ─────────────────────────────────────────────────────

    def _build_notebook(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook",        background=BG_MAIN)
        style.configure("TNotebook.Tab",    font=FONT_LABEL, padding=[14, 6])
        style.configure("Treeview",         font=FONT_LABEL, rowheight=26)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("TButton",          font=FONT_BUTTON)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(8, 12))

    def _frame(self, title):
        """Create and return a padded frame registered as a tab."""
        f = tk.Frame(self.notebook, bg=BG_MAIN)
        self.notebook.add(f, text=title)
        return f

    # ── Tab 1 — Add Item ─────────────────────────────────────────────

    def _build_add_tab(self):
        tab = self._frame("  Add Item  ")

        form = tk.Frame(tab, bg=BG_MAIN)
        form.pack(fill="x", padx=20, pady=16)

        tk.Label(form, text="Item name:", font=FONT_LABEL, bg=BG_MAIN).grid(
            row=0, column=0, sticky="w", pady=4)

        self.add_entry = tk.Entry(form, font=FONT_LABEL, width=30)
        self.add_entry.grid(row=0, column=1, padx=10, pady=4)
        self.add_entry.bind("<Return>", lambda e: self._do_add_item())

        btn = tk.Button(form, text="Add", font=FONT_BUTTON,
                        bg=ACCENT, fg="white", relief="flat",
                        padx=12, command=self._do_add_item)
        btn.grid(row=0, column=2, padx=4)

        # Item list
        tk.Label(tab, text="Existing items:", font=FONT_LABEL, bg=BG_MAIN,
                 anchor="w").pack(fill="x", padx=20)

        cols = ("Item", "Score", "Reviews")
        self.add_tree = ttk.Treeview(tab, columns=cols, show="headings", height=12)
        for col in cols:
            self.add_tree.heading(col, text=col)
        self.add_tree.column("Item",    width=320)
        self.add_tree.column("Score",   width=100, anchor="center")
        self.add_tree.column("Reviews", width=100, anchor="center")
        self.add_tree.pack(fill="both", padx=20, pady=8)

    def _do_add_item(self):
        name = self.add_entry.get().strip()
        if not name:
            messagebox.showwarning("Empty name", "Please enter an item name.")
            return
        if name in items:
            messagebox.showwarning("Duplicate", f"'{name}' already exists.")
            return
        items[name] = {"reviews": [], "score": 0.0}
        self.add_entry.delete(0, "end")
        self._refresh_add_tree()
        self._refresh_rate_combo()

    def _refresh_add_tree(self):
        self.add_tree.delete(*self.add_tree.get_children())
        for name, data in items.items():
            self.add_tree.insert("", "end", values=(
                name,
                f"{data['score']:.2f}",
                len(data["reviews"])
            ))

    # ── Tab 2 — Rate Item ────────────────────────────────────────────

    def _build_rate_tab(self):
        tab = self._frame("  Rate Item  ")
        pad = {"bg": BG_MAIN}

        form = tk.Frame(tab, bg=BG_MAIN)
        form.pack(fill="x", padx=24, pady=14)

        def row_label(r, text):
            tk.Label(form, text=text, font=FONT_LABEL, **pad).grid(
                row=r, column=0, sticky="w", pady=6)

        row_label(0, "Select item:")
        self.rate_combo = ttk.Combobox(form, state="readonly", width=28, font=FONT_LABEL)
        self.rate_combo.grid(row=0, column=1, padx=10, sticky="w")
        self.rate_combo.bind("<<ComboboxSelected>>", self._on_item_selected)

        row_label(1, "Username:")
        self.rate_user = tk.Entry(form, font=FONT_LABEL, width=30)
        self.rate_user.grid(row=1, column=1, padx=10, sticky="w")

        # Round 1 — raw score slider
        row_label(2, "Round 1 — Your Score (0-10):")
        score_frame = tk.Frame(form, bg=BG_MAIN)
        score_frame.grid(row=2, column=1, padx=10, sticky="w")
        self.raw_var = tk.DoubleVar(value=5.0)
        self.raw_label = tk.Label(score_frame, text="5.0", font=("Segoe UI", 11, "bold"),
                                  fg=ACCENT, bg=BG_MAIN, width=4)
        self.raw_label.pack(side="right")
        tk.Scale(score_frame, from_=0, to=10, resolution=0.5, orient="horizontal",
                 length=260, variable=self.raw_var, bg=BG_MAIN,
                 command=lambda v: self.raw_label.config(text=f"{float(v):.1f}")
                 ).pack(side="left")

        # Current score display (shown before Round 2)
        row_label(3, "Current overall score:")
        self.current_score_info = tk.Label(
            form, text="— (select an item first)",
            font=("Segoe UI", 11, "bold"), fg=ACCENT, bg=BG_MAIN, anchor="w")
        self.current_score_info.grid(row=3, column=1, padx=10, sticky="w")

        # Round 2 — satisfaction with current score
        row_label(4, "Round 2 — Satisfaction (0-1):")
        sat_frame = tk.Frame(form, bg=BG_MAIN)
        sat_frame.grid(row=4, column=1, padx=10, sticky="w")
        self.sat_var = tk.DoubleVar(value=0.5)
        self.sat_label = tk.Label(sat_frame, text="0.5", font=("Segoe UI", 11, "bold"),
                                  fg=ACCENT, bg=BG_MAIN, width=4)
        self.sat_label.pack(side="right")
        tk.Scale(sat_frame, from_=0, to=1, resolution=0.1, orient="horizontal",
                 length=260, variable=self.sat_var, bg=BG_MAIN,
                 command=lambda v: self.sat_label.config(text=f"{float(v):.1f}")
                 ).pack(side="left")

        tk.Label(form, text="How satisfied are you with the current overall score?  "
                            "(1.0 = fully agree  ·  0.0 = strongly disagree)",
                 font=("Segoe UI", 9), fg="#888", bg=BG_MAIN
                 ).grid(row=5, column=1, padx=10, sticky="w")

        # Submit
        tk.Button(form, text="Submit Review", font=FONT_BUTTON,
                  bg=ACCENT, fg="white", relief="flat",
                  padx=16, pady=4, command=self._do_rate_item
                  ).grid(row=6, column=1, sticky="w", padx=10, pady=12)

        # Result label
        self.rate_result = tk.Label(tab, text="", font=FONT_LABEL, bg=BG_MAIN, fg="#333")
        self.rate_result.pack(pady=4)

    def _refresh_rate_combo(self):
        self.rate_combo["values"] = list(items.keys())

    def _on_item_selected(self, event=None):
        """Update the current score label when the user picks an item."""
        name = self.rate_combo.get()
        if name in items:
            score = items[name]["score"]
            count = len(items[name]["reviews"])
            if count == 0:
                self.current_score_info.config(text="No reviews yet — be the first!")
            else:
                self.current_score_info.config(
                    text=f"{score:.2f} / 10   ({count} review{'s' if count != 1 else ''})")

    def _do_rate_item(self):
        name = self.rate_combo.get()
        username = self.rate_user.get().strip()
        raw = self.raw_var.get()
        satisfaction = self.sat_var.get()

        if not name:
            messagebox.showwarning("No item", "Please select an item.")
            return
        if not username:
            messagebox.showwarning("No username", "Please enter your username.")
            return

        # Store review
        items[name]["reviews"].append(
            {"user": username, "raw": raw, "satisfaction": satisfaction}
        )

        # Update user record
        if username not in users:
            users[username] = {"weight": 1.0, "history": [], "note": "New user"}
        users[username]["history"].append(raw)
        w, note = compute_user_weight(users[username]["history"])
        users[username]["weight"] = w
        users[username]["note"] = note

        refresh_scores()
        self._refresh_add_tree()

        msg = f"Saved!  '{name}' new score: {items[name]['score']:.2f}"
        if w < 1.0:
            msg += f"   |   Your weight: {w:.1f}  ({note})"
        self.rate_result.config(text=msg)

    # ── Tab 3 — Leaderboard ──────────────────────────────────────────

    def _build_leaderboard_tab(self):
        tab = self._frame("  Leaderboard  ")

        tk.Button(tab, text="Refresh", font=FONT_BUTTON,
                  bg=ACCENT, fg="white", relief="flat", padx=10,
                  command=self._refresh_leaderboard
                  ).pack(anchor="ne", padx=20, pady=10)

        cols = ("Rank", "Item", "Score", "Reviews")
        self.lb_tree = ttk.Treeview(tab, columns=cols, show="headings", height=14)
        self.lb_tree.heading("Rank",    text="Rank")
        self.lb_tree.heading("Item",    text="Item")
        self.lb_tree.heading("Score",   text="Score")
        self.lb_tree.heading("Reviews", text="Reviews")
        self.lb_tree.column("Rank",    width=60,  anchor="center")
        self.lb_tree.column("Item",    width=340)
        self.lb_tree.column("Score",   width=120, anchor="center")
        self.lb_tree.column("Reviews", width=100, anchor="center")
        self.lb_tree.pack(fill="both", padx=20, pady=(0, 12))

    def _refresh_leaderboard(self):
        self.lb_tree.delete(*self.lb_tree.get_children())

        # Sort by score descending
        ranked = []
        for name in items:
            ranked.append((name, items[name]))

        for i in range(len(ranked)):
            for j in range(len(ranked) - 1 - i):
                if ranked[j][1]["score"] < ranked[j + 1][1]["score"]:
                    ranked[j], ranked[j + 1] = ranked[j + 1], ranked[j]

        for rank, (name, data) in enumerate(ranked, 1):
            self.lb_tree.insert("", "end", values=(
                rank,
                name,
                f"{data['score']:.2f}",
                len(data["reviews"])
            ))

    # ── Tab 4 — User Weights ─────────────────────────────────────────

    def _build_weights_tab(self):
        tab = self._frame("  User Weights  ")

        tk.Button(tab, text="Refresh", font=FONT_BUTTON,
                  bg=ACCENT, fg="white", relief="flat", padx=10,
                  command=self._refresh_weights
                  ).pack(anchor="ne", padx=20, pady=10)

        cols = ("User", "Weight", "Reviews", "Avg Score", "Note")
        self.wt_tree = ttk.Treeview(tab, columns=cols, show="headings", height=14)
        widths = [160, 80, 80, 90, 260]
        for col, w in zip(cols, widths):
            self.wt_tree.heading(col, text=col)
            self.wt_tree.column(col, width=w,
                                anchor="center" if w <= 90 else "w")
        self.wt_tree.pack(fill="both", padx=20, pady=(0, 12))

    def _refresh_weights(self):
        self.wt_tree.delete(*self.wt_tree.get_children())
        for username, data in users.items():
            history = data["history"]
            avg = sum(history) / len(history) if history else 0.0
            # Colour rows with reduced weight in light red
            tag = "reduced" if data["weight"] < 1.0 else ""
            self.wt_tree.insert("", "end", tags=(tag,), values=(
                username,
                f"{data['weight']:.1f}",
                len(history),
                f"{avg:.2f}",
                data["note"]
            ))
        self.wt_tree.tag_configure("reduced", background="#ffe0e0")

    # ── Tab change event ─────────────────────────────────────────────

    def _on_tab_change(self, event):
        tab_name = self.notebook.tab(self.notebook.select(), "text").strip()
        if "Leaderboard" in tab_name:
            self._refresh_leaderboard()
        elif "User Weights" in tab_name:
            self._refresh_weights()
        elif "Add Item" in tab_name:
            self._refresh_add_tree()


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    SmartReviewApp(root)
    root.mainloop()
