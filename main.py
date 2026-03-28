"""
main.py – application entry point.

Run with:
    python main.py
"""
import sys
import os

# ── Make all sub-packages importable regardless of working directory ──────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from database.db import initialize_db
from ui.components import apply_global_style, BG
from ui.login_page import AuthPage
from ui.admin_dashboard import AdminDashboard
from ui.student_dashboard import StudentDashboard


class App(tk.Tk):
    """Root Tk window – manages navigation between screens."""

    def __init__(self):
        super().__init__()
        self.title("College Club & Event Management System")
        self.geometry("1000x640")
        self.minsize(800, 560)
        self.configure(bg=BG)

        apply_global_style(self)

        # initialise database (creates tables + seed data on first run)
        initialize_db()

        self._current_frame = None
        self._show_login()

    # ── Screen transitions ─────────────────────────────────────────────────
    def _switch_frame(self, frame: tk.Frame):
        if self._current_frame:
            self._current_frame.destroy()
        self._current_frame = frame
        frame.pack(fill="both", expand=True)

    def _show_login(self):
        self._switch_frame(AuthPage(self, self._on_login_success))

    def _on_login_success(self, user):
        if user.role == "admin":
            self._switch_frame(
                AdminDashboard(self, user, on_logout=self._show_login)
            )
        else:
            self._switch_frame(
                StudentDashboard(self, user, on_logout=self._show_login)
            )


if __name__ == "__main__":
    app = App()
    app.mainloop()
