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
from datetime import date, datetime
from tkinter import messagebox, ttk
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

    def _safe_parse_date(self, value: str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return None

    def _get_filtered_events(self, search_text="", club_filter="All Clubs"):
        search = (search_text or "").strip().lower()
        club_choice = (club_filter or "All Clubs").strip()
        filtered = []
        for ev in event_svc.get_all_events():
            haystack = f"{ev.name} {ev.date} {ev.club}".lower()
            if search and search not in haystack:
                continue
            if club_choice != "All Clubs" and ev.club != club_choice:
                continue
            filtered.append(ev)
        return filtered

    def _set_event_filter_values(self, combo, variable):
        clubs = ["All Clubs", *sorted({ev.club for ev in event_svc.get_all_events() if ev.club})]
        combo["values"] = clubs
        if variable.get() not in clubs:
            variable.set("All Clubs")

    # ══════════════════════════════════════════════════════════════════════
    # Section: View Events
    # ══════════════════════════════════════════════════════════════════════
    def _build_view_events(self):
        wrap = tk.Frame(self._content, bg=BG, padx=40, pady=30)
        wrap.pack(fill="both", expand=True)

        make_label(wrap, "All Events", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "Browse upcoming college club events.",
                   fg=MUTED).pack(anchor="w", pady=(4, 12))

        filter_row = tk.Frame(wrap, bg=BG)
        filter_row.pack(fill="x", pady=(0, 10))
        make_label(filter_row, "Search", fg=MUTED).pack(side="left")
        self._ve_search = make_entry(filter_row, width=24)
        self._ve_search.pack(side="left", padx=(6, 12))
        self._ve_search.bind("<KeyRelease>", lambda _e: self._load_all_events_view())

        make_label(filter_row, "Club", fg=MUTED).pack(side="left")
        self._ve_club_var = tk.StringVar(value="All Clubs")
        self._ve_club = ttk.Combobox(
            filter_row,
            textvariable=self._ve_club_var,
            state="readonly",
            width=18,
            font=FONT_BODY,
        )
        self._ve_club.pack(side="left", padx=(6, 12))
        self._ve_club.bind("<<ComboboxSelected>>", lambda _e: self._load_all_events_view())

        make_button(filter_row, "Clear Filters", self._clear_event_filters,
                    color=SURFACE2, width=12).pack(side="left")
        make_button(filter_row, "🔄  Refresh", self._refresh_events_view,
                    color=SURFACE2, width=12).pack(side="right")

        self._ve_summary_var = tk.StringVar()
        tk.Label(wrap, textvariable=self._ve_summary_var,
                 bg=BG, fg=ACCENT3, font=FONT_SMALL).pack(anchor="w", pady=(0, 8))

        cols = ("ID", "Event Name", "Date", "Club")
        tv_frame, self._ve_tree = make_treeview(wrap, cols)
        tv_frame.pack(fill="both", expand=True)
        self._ve_tree.column("ID", width=50)

        self._load_all_events_view()

        btn_row = tk.Frame(wrap, bg=BG)
        btn_row.pack(fill="x", pady=(12, 0))
        make_button(btn_row, "✏️  Register for Selected",
                    self._quick_register, width=22).pack(side="left")

    def _load_all_events_view(self):
        self._set_event_filter_values(self._ve_club, self._ve_club_var)
        events = self._get_filtered_events(self._ve_search.get(), self._ve_club_var.get())
        today = date.today()
        upcoming_count = 0

        self._ve_tree.delete(*self._ve_tree.get_children())
        for ev in events:
            event_day = self._safe_parse_date(ev.date)
            if event_day and event_day >= today:
                upcoming_count += 1
            self._ve_tree.insert("", "end", iid=ev.id,
                                 values=(ev.id, ev.name, ev.date, ev.club))

        self._ve_summary_var.set(
            f"Showing {len(events)} event(s) • {upcoming_count} upcoming"
        )

    def _refresh_events_view(self):
        self._load_all_events_view()
        show_toast(self, "Events refreshed.", success=True)

    def _clear_event_filters(self):
        self._ve_search.delete(0, "end")
        self._ve_club_var.set("All Clubs")
        self._load_all_events_view()

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
                   fg=MUTED).pack(anchor="w", pady=(4, 12))

        filter_row = tk.Frame(wrap, bg=BG)
        filter_row.pack(fill="x", pady=(0, 10))
        make_label(filter_row, "Search", fg=MUTED).pack(side="left")
        self._reg_search = make_entry(filter_row, width=24)
        self._reg_search.pack(side="left", padx=(6, 12))
        self._reg_search.bind("<KeyRelease>", lambda _e: self._load_register_events())

        make_label(filter_row, "Club", fg=MUTED).pack(side="left")
        self._reg_club_var = tk.StringVar(value="All Clubs")
        self._reg_club = ttk.Combobox(
            filter_row,
            textvariable=self._reg_club_var,
            state="readonly",
            width=18,
            font=FONT_BODY,
        )
        self._reg_club.pack(side="left", padx=(6, 12))
        self._reg_club.bind("<<ComboboxSelected>>", lambda _e: self._load_register_events())

        make_button(filter_row, "Clear Filters", self._clear_register_filters,
                    color=SURFACE2, width=12).pack(side="left")
        make_button(filter_row, "🔄  Refresh", self._refresh_register_list,
                    color=SURFACE2, width=12).pack(side="right")

        self._reg_summary_var = tk.StringVar()
        tk.Label(wrap, textvariable=self._reg_summary_var,
                 bg=BG, fg=ACCENT3, font=FONT_SMALL).pack(anchor="w", pady=(0, 8))

        cols = ("ID", "Event Name", "Date", "Club")
        tv_frame, self._reg_ev_tree = make_treeview(wrap, cols)
        tv_frame.pack(fill="both", expand=True)
        self._reg_ev_tree.column("ID", width=50)

        self._load_register_events()

        make_button(wrap, "✅  Register for Selected Event",
                    self._register_selected, width=26).pack(anchor="w", pady=(14, 0))

    def _load_register_events(self):
        self._set_event_filter_values(self._reg_club, self._reg_club_var)
        events = self._get_filtered_events(self._reg_search.get(), self._reg_club_var.get())
        self._reg_ev_tree.delete(*self._reg_ev_tree.get_children())
        for ev in events:
            self._reg_ev_tree.insert("", "end", iid=ev.id,
                                     values=(ev.id, ev.name, ev.date, ev.club))
        self._reg_summary_var.set(f"{len(events)} event(s) ready for registration")

    def _refresh_register_list(self):
        self._load_register_events()
        show_toast(self, "Registration list refreshed.", success=True)

    def _clear_register_filters(self):
        self._reg_search.delete(0, "end")
        self._reg_club_var.set("All Clubs")
        self._load_register_events()

    def _register_selected(self):
        sel = self._reg_ev_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select an event to register.")
            return
        event_id = int(sel[0])
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

        action_row = tk.Frame(wrap, bg=BG)
        action_row.pack(fill="x", pady=(0, 8))
        make_button(action_row, "🔄  Refresh", self._refresh_my_events,
                    color=SURFACE2, width=12).pack(side="right")
        make_button(action_row, "❌ Cancel Selected", self._cancel_selected_registration,
                    color=ACCENT2, width=16).pack(side="left")

        cols = ("Event Name", "Date", "Club")
        tv_frame, self._my_tree = make_treeview(wrap, cols)
        tv_frame.pack(fill="both", expand=True)

        self._load_my_events()

        self._my_count_var = tk.StringVar()
        tk.Label(wrap, textvariable=self._my_count_var,
                 bg=BG, fg=ACCENT3, font=FONT_BODY).pack(anchor="w", pady=(10, 0))
        self._update_count()

    def _load_my_events(self):
        self._my_tree.delete(*self._my_tree.get_children())
        today = date.today()
        next_event_text = " No upcoming events yet."
        next_event_date = None

        for ev in reg_svc.get_events_for_student(self._user.id):
            self._my_tree.insert("", "end", iid=str(ev["id"]),
                                 values=(ev["name"], ev["date"], ev["club"]))
            event_day = self._safe_parse_date(ev["date"])
            if event_day and event_day >= today and (next_event_date is None or event_day < next_event_date):
                next_event_date = event_day
                next_event_text = f" Next up: {ev['name']} on {ev['date']}."

        self._next_registered_event_text = next_event_text

    def _refresh_my_events(self):
        self._load_my_events()
        self._update_count()
        show_toast(self, "My Events refreshed.", success=True)

    def _cancel_selected_registration(self):
        sel = self._my_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a registered event first.")
            return

        event_id = int(sel[0])
        event_name = self._my_tree.item(sel[0])["values"][0]
        if not messagebox.askyesno("Cancel Registration",
                                   f"Cancel your registration for '{event_name}'?"):
            return

        try:
            reg_svc.cancel_registration(self._user.id, event_id)
            notif_svc.create_notification(self._user.id, f"You cancelled registration for '{event_name}'.")
            self._load_my_events()
            self._update_count()
            show_toast(self, f"Registration cancelled for '{event_name}'.", success=True)
        except ValueError as exc:
            show_toast(self, str(exc), success=False)

    def _update_count(self):
        total = len(self._my_tree.get_children())
        extra = getattr(self, "_next_registered_event_text", "")
        self._my_count_var.set(f"You are registered for {total} event(s).{extra}")

    # ══════════════════════════════════════════════════════════════════════
    # Section: Notifications
    # ══════════════════════════════════════════════════════════════════════
    def _build_notifications(self):
        wrap = tk.Frame(self._content, bg=BG, padx=40, pady=30)
        wrap.pack(fill="both", expand=True)

        make_label(wrap, "Notifications", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "In-app updates for your activities.", fg=MUTED).pack(anchor="w", pady=(4, 8))

        self._notif_count_var = tk.StringVar(value="Unread notifications: 0")
        tk.Label(wrap, textvariable=self._notif_count_var,
                 bg=BG, fg=ACCENT3, font=FONT_SMALL).pack(anchor="w", pady=(0, 10))

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
        unread_total = notif_svc.get_unread_count(self._user.id)
        for n in notes:
            status = "🔔 Unread" if n["read_flag"] == 0 else "✓ Read"
            self._notif_tree.insert("", "end", values=(n["created_at"], n["message"], status))
        self._notif_count_var.set(f"Unread notifications: {unread_total}")

    def _refresh_notifications(self):
        self._load_notifications()
        show_toast(self, "Notifications refreshed.", success=True)

    def _mark_all_read(self):
        notif_svc.mark_all_read(self._user.id)
        self._load_notifications()
        show_toast(self, "All notifications marked as read.", success=True)

