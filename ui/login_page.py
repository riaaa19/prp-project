"""
Authentication Page
───────────────────
Contains separate Sign In and Sign Up sub-pages.
"""
import tkinter as tk
from ui.components import (
    BG, SURFACE, SURFACE2, ACCENT, ACCENT2, ACCENT3,
    TEXT, MUTED, BORDER, FONT_TITLE, FONT_HEAD, FONT_BODY, FONT_BTN, FONT_SMALL,
    make_frame, make_label, make_entry, make_button, show_toast,
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

        sidebar = tk.Frame(self, bg=SURFACE, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="🎓 Welcome", bg=SURFACE, fg=TEXT,
                 font=FONT_HEAD, pady=20).pack(fill="x", padx=16)

        self._signin_btn = make_button(sidebar, "Sign In", lambda: self._switch("signin"), width=20)
        self._signin_btn.pack(pady=(10, 4), padx=16)
        self._signup_btn = make_button(sidebar, "Sign Up", lambda: self._switch("signup"), width=20)
        self._signup_btn.pack(pady=(0, 8), padx=16)

        tk.Label(sidebar, text="Already have an account? Use Sign In",
                 bg=SURFACE, fg=MUTED, font=("Helvetica", 8), wraplength=200, justify="center").pack(pady=20)

        self._content = tk.Frame(self, bg=BG)
        self._content.pack(side="left", fill="both", expand=True)

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
        box = tk.Frame(self, bg=SURFACE, padx=40, pady=40, bd=0, highlightthickness=1, highlightbackground=BORDER)
        box.place(relx=0.5, rely=0.5, anchor="center", width=460, height=460)

        make_label(box, "Sign In", font=FONT_TITLE).pack(pady=(0, 16))

        # Role tabs (Student / Admin) displayed above email
        self._role_var = tk.StringVar(value="student")
        role_tabs = tk.Frame(box, bg=BG)
        role_tabs.pack(fill="x", pady=(0, 18))

        def make_role_tab(label, value):
            btn = tk.Label(role_tabs, text=label,
                           bg=ACCENT if self._role_var.get()==value else SURFACE2,
                           fg="white" if self._role_var.get()==value else TEXT,
                           font=("Helvetica", 10, "bold"), bd=1, relief="ridge", padx=16, pady=8, cursor="hand2")
            btn.pack(side="left", expand=True, fill="x", padx=2)

            def _select_role(evt=None):
                self._role_var.set(value)
                for child in role_tabs.winfo_children():
                    child_value = "student" if child.cget("text")=="Student" else "admin"
                    child.config(bg=ACCENT if child_value == self._role_var.get() else SURFACE2,
                                 fg="white" if child_value == self._role_var.get() else TEXT)

            btn.bind("<Button-1>", _select_role)
            return btn

        self._student_tab = make_role_tab("Student", "student")
        self._admin_tab = make_role_tab("Admin", "admin")

        make_label(box, "Email", fg=MUTED, font=("Helvetica", 9, "bold")).pack(anchor="w")
        self._email = make_entry(box, width=36)
        self._email.pack(pady=(4, 10))

        make_label(box, "Password", fg=MUTED, font=("Helvetica", 9, "bold")).pack(anchor="w")
        self._password = make_entry(box, show="●", width=36)
        self._password.pack(pady=(4, 10))

        self._err = tk.StringVar()
        tk.Label(box, textvariable=self._err, bg=SURFACE, fg=ACCENT2, font=FONT_SMALL).pack(pady=(4, 12))

        make_button(box, "Sign In", self._try_login, width=22).pack(pady=(8, 0))

    def _try_login(self):
        self._err.set("")
        email = self._email.get().strip()
        password = self._password.get()
        requested_role = self._role_var.get()
        try:
            user = login(email, password)
            if user.role != requested_role:
                raise ValueError(f"Role mismatch: logged-in user is '{user.role}', not '{requested_role}'.")
            self._on_login_success(user)
        except ValueError as e:
            self._err.set(str(e))


class SignUpPanel(tk.Frame):
    def __init__(self, parent, on_signup_success):
        super().__init__(parent, bg=BG)
        self._on_signup_success = on_signup_success
        self._build()

    def _build(self):
        box = tk.Frame(self, bg=SURFACE, padx=40, pady=40, bd=0, highlightthickness=1, highlightbackground=BORDER)
        box.place(relx=0.5, rely=0.5, anchor="center", width=500, height=520)

        make_label(box, "Sign Up", font=FONT_TITLE).pack(pady=(0, 16))

        make_label(box, "Full Name", fg=MUTED, font=("Helvetica", 9, "bold")).pack(anchor="w")
        self._username = make_entry(box, width=36)
        self._username.pack(pady=(4, 10))

        make_label(box, "Email", fg=MUTED, font=("Helvetica", 9, "bold")).pack(anchor="w")
        self._email = make_entry(box, width=36)
        self._email.pack(pady=(4, 10))

        make_label(box, "Password", fg=MUTED, font=("Helvetica", 9, "bold")).pack(anchor="w")
        self._password = make_entry(box, show="●", width=36)
        self._password.pack(pady=(4, 10))

        make_label(box, "Confirm Password", fg=MUTED, font=("Helvetica", 9, "bold")).pack(anchor="w")
        self._confirm = make_entry(box, show="●", width=36)
        self._confirm.pack(pady=(4, 10))

        self._err = tk.StringVar()
        tk.Label(box, textvariable=self._err, bg=SURFACE, fg=ACCENT2, font=FONT_SMALL).pack(pady=(4, 12))

        make_button(box, "Create Account", self._try_signup, width=22).pack(pady=(8, 0))

        make_button(box, "← Back to Sign In", self._back_to_signin, color=SURFACE2, width=22).pack(pady=(10, 0))
        tk.Label(box, text="Already registered? Use the button above.", bg=SURFACE, fg=MUTED, font=("Helvetica", 8)).pack(pady=(8, 0))

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
