"""
Authentication Page
───────────────────
Contains separate Sign In and Sign Up sub-pages.
"""
import tkinter as tk
from ui.components import (
    BG, SURFACE, SURFACE2, ACCENT, ACCENT2, ACCENT3,
    TEXT, MUTED, BORDER, FONT_TITLE, FONT_HEAD, FONT_BODY, FONT_BTN, FONT_SMALL,
    make_frame, make_card, make_label, make_entry, make_button, show_toast,
)
from services.auth_service import login, register_user


class AuthPage(tk.Frame):
    """Root authentication UI with tabs for Sign In / Sign Up."""

    def __init__(self, parent, on_login_success):
        super().__init__(parent, bg=BG)
        self._on_login_success = on_login_success
        self._active = "signin"
        self._build()

    def _build(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        hero_panel = tk.Frame(self, bg=SURFACE, width=360)
        hero_panel.pack(side="left", fill="y")
        hero_panel.pack_propagate(False)


        hero_content = tk.Frame(hero_panel, bg=SURFACE)
        hero_content.place(relx=0.5, rely=0.5, anchor="center", width=340)
        tk.Label(hero_content, text="Campus Club Manager", bg=SURFACE, fg=ACCENT,
                 font=("Segoe UI", 28, "bold"), wraplength=320, anchor="w", justify="left").pack(anchor="w", pady=(0, 18), fill="x")
        tk.Label(hero_content, text="Run college events the way students expect",
                 bg=SURFACE, fg=TEXT, font=("Segoe UI", 18, "bold"), wraplength=320, anchor="w", justify="left").pack(anchor="w", fill="x")
        tk.Label(hero_content,
                 text="Coordinate clubs, manage registrations, and track attendance from a single modern dashboard.",
                 bg=SURFACE, fg=MUTED, font=FONT_BODY, wraplength=320, anchor="w", justify="left").pack(anchor="w", pady=(12, 24), fill="x")

        for title, desc in [
            ("Smart Decision Engine", "Group-friendly event suggestions with smarter matching."),
            ("Conflict Resolver", "See and fix schedule clashes in an instant."),
            ("Expense Splitter", "Keep finances clear and fair for every member."),
        ]:
            feature_card = make_card(hero_content, bg=SURFACE2, padx=14, pady=12)
            feature_card.pack(fill="x", pady=6)
            tk.Label(feature_card, text=title, bg=SURFACE2, fg=TEXT,
                     font=("Segoe UI", 11, "bold"), wraplength=300, anchor="w", justify="left").pack(anchor="w", fill="x")
            tk.Label(feature_card, text=desc, bg=SURFACE2, fg=MUTED,
                     font=FONT_SMALL, wraplength=300, anchor="w", justify="left").pack(anchor="w", pady=(4, 0), fill="x")

        content_area = tk.Frame(self, bg=BG)
        content_area.pack(side="left", fill="both", expand=True)

        tab_row = tk.Frame(content_area, bg=BG)
        tab_row.pack(fill="x", pady=(28, 12), padx=24)
        self._signin_btn = make_button(tab_row, "Sign In", lambda: self._switch("signin"), width=16)
        self._signin_btn.pack(side="left", padx=(0, 8))
        self._signup_btn = make_button(tab_row, "Sign Up", lambda: self._switch("signup"), color=SURFACE2, width=16)
        self._signup_btn.pack(side="left")

        self._content = tk.Frame(content_area, bg=BG)
        self._content.pack(fill="both", expand=True)

        self._switch("signin")

    def _switch(self, page):
        self._active = page
        self._signin_btn.config(bg=ACCENT if page == "signin" else SURFACE)
        self._signup_btn.config(bg=ACCENT if page == "signup" else SURFACE)

        for w in self._content.winfo_children():
            w.destroy()

        if page == "signin":
            SignInPanel(self._content, self._on_login_success).pack(fill="both", expand=True)
        else:
            SignUpPanel(self._content, self._on_signup_success).pack(fill="both", expand=True)

    def _on_signup_success(self, user):
        show_toast(self, "✅ Account created successfully! Please sign in.", success=True)
        self._switch("signin")


class SignInPanel(tk.Frame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent, bg=BG)
        self._on_login_success = on_login_success
        self._build()

    def _build(self):
        box = make_card(self, bg=SURFACE2, padx=40, pady=40)
        box.place(relx=0.5, rely=0.5, anchor="center", width=460, height=460)

        make_label(box, "Sign In", font=FONT_TITLE).pack(pady=(0, 20))

        make_label(box, "Email", fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self._email = make_entry(box, width=36)
        self._email.pack(pady=(6, 12))

        make_label(box, "Password", fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self._password = make_entry(box, show="●", width=36)
        self._password.pack(pady=(6, 18))

        self._err = tk.StringVar()
        tk.Label(box, textvariable=self._err, bg=SURFACE2, fg=ACCENT2, font=FONT_SMALL).pack(pady=(0, 16))

        make_button(box, "Sign In", self._try_login, width=24).pack(pady=(4, 0))

    def _try_login(self):
        self._err.set("")
        email = self._email.get().strip()
        password = self._password.get()
        try:
            user = login(email, password)
            self._on_login_success(user)
        except ValueError as e:
            self._err.set(str(e))


class SignUpPanel(tk.Frame):
    def __init__(self, parent, on_signup_success):
        super().__init__(parent, bg=BG)
        self._on_signup_success = on_signup_success
        self._build()

    def _build(self):
        box = make_card(self, bg=SURFACE2, padx=40, pady=40)
        box.place(relx=0.5, rely=0.5, anchor="center", width=500, height=520)

        make_label(box, "Create Account", font=FONT_TITLE).pack(pady=(0, 20))

        make_label(box, "Full Name", fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self._username = make_entry(box, width=36)
        self._username.pack(pady=(6, 12))

        make_label(box, "Email", fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self._email = make_entry(box, width=36)
        self._email.pack(pady=(6, 12))

        make_label(box, "Password", fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self._password = make_entry(box, show="●", width=36)
        self._password.pack(pady=(6, 12))

        make_label(box, "Confirm Password", fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self._confirm = make_entry(box, show="●", width=36)
        self._confirm.pack(pady=(6, 18))

        self._err = tk.StringVar()
        tk.Label(box, textvariable=self._err, bg=SURFACE2, fg=ACCENT2, font=FONT_SMALL).pack(pady=(0, 16))

        make_button(box, "Create Account", self._try_signup, width=24).pack(pady=(4, 0))
        make_button(box, "← Back to Sign In", self._back_to_signin, color=SURFACE, width=24).pack(pady=(12, 0))
        tk.Label(box, text="Already registered? Use the button above.", bg=SURFACE2, fg=MUTED, font=("Segoe UI", 8)).pack(pady=(8, 0))

    def _try_signup(self):
        self._err.set("")
        try:
            user = register_user(
                self._username.get().strip(),
                self._email.get().strip(),
                self._password.get(),
                self._confirm.get(),
            )
            self._on_signup_success(user)
        except ValueError as e:
            self._err.set(str(e))

    def _back_to_signin(self):
        parent = self.master
        while parent and not isinstance(parent, AuthPage):
            parent = parent.master
        if parent:
            parent._switch("signin")
