"""
Student Dashboard
─────────────────
Three sections reachable via sidebar:
  • View Events       – browse all events
  • Register          – pick an event and register
  • My Events         – see own registrations

All buttons fully wired.
"""
import tkinter as tk
from tkinter import messagebox
import services.event_service as event_svc
import services.registration_service as reg_svc
import services.notification_service as notif_svc
from ui.components import (
    BG, SURFACE, SURFACE2, ACCENT, ACCENT2, ACCENT3,
    TEXT, MUTED, BORDER, FONT_TITLE, FONT_HEAD, FONT_BODY, FONT_BTN, FONT_SMALL,
    make_frame, make_label, make_entry, make_button, make_treeview, show_toast,
)


class StudentDashboard(tk.Frame):
    def __init__(self, parent, user, on_logout):
        super().__init__(parent, bg=BG)
        self._user = user
        self._on_logout = on_logout
        self._active_section = None
        self._build()
        self._show_section("view_events")

    # ══════════════════════════════════════════════════════════════════════
    # Layout skeleton
    # ══════════════════════════════════════════════════════════════════════
    def _build(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # ── Sidebar ───────────────────────────────────────────────────────
        sidebar = tk.Frame(self, bg=SURFACE, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="🎓  Student Hub", bg=SURFACE, fg=TEXT,
                 font=FONT_HEAD, pady=20).pack(fill="x", padx=16)
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=16)

        tk.Label(sidebar, text=f"Hi, {self._user.username}",
                 bg=SURFACE, fg=MUTED, font=FONT_SMALL).pack(anchor="w", padx=16, pady=(8, 0))
        tk.Label(sidebar, text="Student",
                 bg=SURFACE, fg=ACCENT3, font=("Helvetica", 8, "bold")).pack(anchor="w", padx=16, pady=(0, 12))
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=16)

        self._nav_btns = {}
        nav_items = [
            ("📅  View Events",   "view_events"),
            ("✏️   Register",      "register"),
            ("🎟  My Events",     "my_events"),
            ("🔔  Notifications", "notifications"),
        ]
        for label, key in nav_items:
            btn = tk.Button(sidebar, text=label, bg=SURFACE, fg=TEXT,
                            activebackground=ACCENT, activeforeground="white",
                            font=FONT_BODY, relief="flat", bd=0,
                            anchor="w", padx=20, pady=12, cursor="hand2",
                            command=lambda k=key: self._show_section(k))
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=SURFACE2))
            btn.bind("<Leave>", lambda e, b=btn, k=key: b.config(
                bg=ACCENT if self._active_section == k else SURFACE2))
            self._nav_btns[key] = btn

        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=16, side="bottom", pady=10)
        make_button(sidebar, "🚪  Logout", self._on_logout,
                    color="#333655", width=20).pack(side="bottom", fill="x", padx=16, pady=10)

        # ── Content area ──────────────────────────────────────────────────
        self._content = tk.Frame(self, bg=BG)
        self._content.pack(side="left", fill="both", expand=True)

    # ══════════════════════════════════════════════════════════════════════
    # Navigation
    # ══════════════════════════════════════════════════════════════════════
    def _show_section(self, key: str):
        for k, btn in self._nav_btns.items():
            btn.config(bg=ACCENT if k == key else SURFACE)
        self._active_section = key

        for w in self._content.winfo_children():
            w.destroy()

        {
            "view_events": self._build_view_events,
            "register":    self._build_register,
            "my_events":   self._build_my_events,
            "notifications": self._build_notifications,
        }[key]()

    # ══════════════════════════════════════════════════════════════════════
    # Section: View Events
    # ══════════════════════════════════════════════════════════════════════
    def _build_view_events(self):
        wrap = tk.Frame(self._content, bg=BG, padx=40, pady=30)
        wrap.pack(fill="both", expand=True)

        make_label(wrap, "All Events", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "Browse upcoming college club events.",
                   fg=MUTED).pack(anchor="w", pady=(4, 16))

        make_button(wrap, "🔄  Refresh", self._refresh_events_view,
                    color=SURFACE2, width=12).pack(anchor="e", pady=(0, 8))

        cols = ("ID", "Event Name", "Date", "Club")
        tv_frame, self._ve_tree = make_treeview(wrap, cols)
        tv_frame.pack(fill="both", expand=True)
        self._ve_tree.column("ID", width=50)

        self._load_all_events_view()

        # quick-register shortcut
        btn_row = tk.Frame(wrap, bg=BG)
        btn_row.pack(fill="x", pady=(12, 0))
        make_button(btn_row, "✏️  Register for Selected",
                    self._quick_register, width=22).pack(side="left")

    def _load_all_events_view(self):
        self._ve_tree.delete(*self._ve_tree.get_children())
        for ev in event_svc.get_all_events():
            self._ve_tree.insert("", "end", iid=ev.id,
                                 values=(ev.id, ev.name, ev.date, ev.club))

    def _refresh_events_view(self):
        self._load_all_events_view()
        show_toast(self, "Events refreshed.", success=True)

    def _quick_register(self):
        """Register for the selected row in the View Events table."""
        sel = self._ve_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select an event first.")
            return
        event_id = int(sel[0])
        event_name = self._ve_tree.item(sel[0])["values"][1]
        self._do_register(event_id, event_name)

    # ══════════════════════════════════════════════════════════════════════
    # Section: Register
    # ══════════════════════════════════════════════════════════════════════
    def _build_register(self):
        wrap = tk.Frame(self._content, bg=BG, padx=40, pady=30)
        wrap.pack(fill="both", expand=True)

        make_label(wrap, "Register for an Event", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "Select an event from the list, then click Register.",
                   fg=MUTED).pack(anchor="w", pady=(4, 16))

        make_button(wrap, "🔄  Refresh", self._refresh_register_list,
                    color=SURFACE2, width=12).pack(anchor="e", pady=(0, 8))

        cols = ("ID", "Event Name", "Date", "Club")
        tv_frame, self._reg_ev_tree = make_treeview(wrap, cols)
        tv_frame.pack(fill="both", expand=True)
        self._reg_ev_tree.column("ID", width=50)

        self._load_register_events()

        make_button(wrap, "✅  Register for Selected Event",
                    self._register_selected, width=26).pack(anchor="w", pady=(14, 0))

    def _load_register_events(self):
        self._reg_ev_tree.delete(*self._reg_ev_tree.get_children())
        for ev in event_svc.get_all_events():
            self._reg_ev_tree.insert("", "end", iid=ev.id,
                                     values=(ev.id, ev.name, ev.date, ev.club))

    def _refresh_register_list(self):
        self._load_register_events()

    def _register_selected(self):
        sel = self._reg_ev_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select an event to register.")
            return
        event_id   = int(sel[0])
        event_name = self._reg_ev_tree.item(sel[0])["values"][1]
        self._do_register(event_id, event_name)

    def _do_register(self, event_id: int, event_name: str):
        """Shared registration logic used by both sections."""
        if not messagebox.askyesno("Confirm",
                                   f"Register for '{event_name}'?"):
            return
        try:
            reg_svc.register_student(self._user.id, event_id)
            notif_svc.create_notification(self._user.id, f"You registered for '{event_name}'.")
            show_toast(self, f"Registered for '{event_name}'! 🎉", success=True)
        except ValueError as exc:
            show_toast(self, str(exc), success=False)

    # ══════════════════════════════════════════════════════════════════════
    # Section: My Events
    # ══════════════════════════════════════════════════════════════════════
    def _build_my_events(self):
        wrap = tk.Frame(self._content, bg=BG, padx=40, pady=30)
        wrap.pack(fill="both", expand=True)

        make_label(wrap, "My Registered Events", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "All events you have signed up for.",
                   fg=MUTED).pack(anchor="w", pady=(4, 16))

        make_button(wrap, "🔄  Refresh", self._refresh_my_events,
                    color=SURFACE2, width=12).pack(anchor="e", pady=(0, 8))

        cols = ("Event Name", "Date", "Club")
        tv_frame, self._my_tree = make_treeview(wrap, cols)
        tv_frame.pack(fill="both", expand=True)

        self._load_my_events()

        # summary badge
        self._my_count_var = tk.StringVar()
        tk.Label(wrap, textvariable=self._my_count_var,
                 bg=BG, fg=ACCENT3, font=FONT_BODY).pack(anchor="w", pady=(10, 0))
        self._update_count()

    def _load_my_events(self):
        self._my_tree.delete(*self._my_tree.get_children())
        for ev in reg_svc.get_events_for_student(self._user.id):
            self._my_tree.insert("", "end",
                                 values=(ev["name"], ev["date"], ev["club"]))

    def _refresh_my_events(self):
        self._load_my_events()
        self._update_count()
        show_toast(self, "My Events refreshed.", success=True)

    def _update_count(self):
        total = len(self._my_tree.get_children())
        self._my_count_var.set(f"You are registered for {total} event(s).")

    # ══════════════════════════════════════════════════════════════════════
    # Section: Notifications
    # ══════════════════════════════════════════════════════════════════════
    def _build_notifications(self):
        wrap = tk.Frame(self._content, bg=BG, padx=40, pady=30)
        wrap.pack(fill="both", expand=True)

        make_label(wrap, "Notifications", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "In-app updates for your activities.", fg=MUTED).pack(anchor="w", pady=(4, 16))

        btn_row = tk.Frame(wrap, bg=BG)
        btn_row.pack(fill="x", pady=(0, 8))
        make_button(btn_row, "🔄  Refresh", self._refresh_notifications,
                    color=SURFACE2, width=12).pack(side="left")
        make_button(btn_row, "✅ Mark All Read", self._mark_all_read,
                    color=ACCENT, width=16).pack(side="left", padx=(8, 0))

        cols = ("Time","Message","Status")
        tv_frame, self._notif_tree = make_treeview(wrap, cols)
        tv_frame.pack(fill="both", expand=True)
        self._notif_tree.column("Time", width=160)
        self._notif_tree.column("Status", width=110, anchor="center")

        self._load_notifications()

    def _load_notifications(self):
        self._notif_tree.delete(*self._notif_tree.get_children())
        notes = notif_svc.get_notifications(self._user.id)
        for n in notes:
            status = "🔔 Unread" if n["read_flag"] == 0 else "✓ Read"
            self._notif_tree.insert("", "end", values=(n["created_at"], n["message"], status))

    def _refresh_notifications(self):
        self._load_notifications()
        show_toast(self, "Notifications refreshed.", success=True)

    def _mark_all_read(self):
        notif_svc.mark_all_read(self._user.id)
        self._load_notifications()
        show_toast(self, "All notifications marked as read.", success=True)

