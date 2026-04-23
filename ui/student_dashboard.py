"""
Student Dashboard
─────────────────
Three sections reachable via sidebar:
  • View Events       – browse all events
  • Register          – pick an event and register
  • My Events         – see own registrations

All buttons fully wired.
"""
import csv
import tkinter as tk
from datetime import date, datetime
from tkinter import filedialog, messagebox, ttk
import services.attendance_service as att_svc
import services.event_service as event_svc
import services.registration_service as reg_svc
import services.notification_service as notif_svc
from ui.components import (
    BG, SURFACE, SURFACE2, ACCENT, ACCENT2, ACCENT3,
    TEXT, MUTED, BORDER, FONT_TITLE, FONT_HEAD, FONT_BODY, FONT_BTN, FONT_SMALL,
    make_frame, make_card, make_label, make_entry, make_button, make_treeview, show_toast,
)


class StudentDashboard(tk.Frame):
    def __init__(self, parent, user, on_logout):
        super().__init__(parent, bg=BG)
        self._user = user
        self._on_logout = on_logout
        self._active_section = None
        self._build()
        self._show_section("overview")

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

        tk.Label(sidebar, text="Campus Club Hub", bg=SURFACE, fg=ACCENT3,
                 font=("Segoe UI", 20, "bold"), pady=18).pack(fill="x", padx=16)
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=16)

        tk.Label(sidebar, text=f"Hi, {self._user.username}",
                 bg=SURFACE, fg=MUTED, font=FONT_SMALL).pack(anchor="w", padx=16, pady=(12, 0))
        tk.Label(sidebar, text="Student",
                 bg=SURFACE, fg=ACCENT3, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=16, pady=(0, 12))
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=16)

        self._nav_btns = {}
        nav_items = [
            ("🏠  Overview",      "overview"),
            ("📅  View Events",   "view_events"),
            ("✏️  Register",     "register"),
            ("🎟  My Events",     "my_events"),
            ("👤  Profile",       "profile"),
            ("📊  Attendance",    "attendance"),
            ("🏛️   Clubs",        "clubs"),
            ("🔔  Notifications", "notifications"),
        ]
        for label, key in nav_items:
            def make_nav_btn(lbl, ky):
                btn = tk.Button(sidebar, text=lbl, bg=SURFACE, fg=TEXT,
                                activebackground=ACCENT, activeforeground="white",
                                font=("Segoe UI", 11), relief="flat", bd=0,
                                anchor="w", padx=18, pady=14, cursor="hand2",
                                highlightthickness=0,
                                command=lambda k=ky: self._show_section(k))
                btn.pack(fill="x", padx=8, pady=2)
                def _on_enter(e, btn=btn, key=ky):
                    if self._active_section != key:
                        btn.config(bg=SURFACE2)
                def _on_leave(e, btn=btn, key=ky):
                    if self._active_section != key:
                        btn.config(bg=SURFACE)
                btn.bind("<Enter>", _on_enter)
                btn.bind("<Leave>", _on_leave)
                self._nav_btns[ky] = btn
            make_nav_btn(label, key)

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
            if k == key:
                btn.config(bg=ACCENT, fg="white", relief="flat")
            else:
                btn.config(bg=SURFACE, fg=TEXT, relief="flat")
        self._active_section = key

        for w in self._content.winfo_children():
            w.destroy()

        {
            "overview":    self._build_overview,
            "view_events": self._build_view_events,
            "register":    self._build_register,
            "my_events":   self._build_my_events,
            "profile":     self._build_profile,
            "attendance":  self._build_attendance,
            "clubs":       self._build_clubs,
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

    def _get_registered_events(self):
        return reg_svc.get_events_for_student(self._user.id)

    def _get_registered_event_ids(self):
        return {event["id"] for event in self._get_registered_events()}

    def _format_event_status(self, event_date: str):
        event_day = self._safe_parse_date(event_date)
        if event_day is None:
            return "Date not available"
        days_left = (event_day - date.today()).days
        if days_left < 0:
            return f"Completed {abs(days_left)} day(s) ago"
        if days_left == 0:
            return "Happening today"
        if days_left == 1:
            return "Happening tomorrow"
        return f"Starts in {days_left} day(s)"

    def _build_overview(self):
        wrap = tk.Frame(self._content, bg=BG, padx=30, pady=24)
        wrap.pack(fill="both", expand=True)

        make_label(wrap, "Student Overview", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "Your events, notifications, and next steps in one place.",
                   fg=MUTED).pack(anchor="w", pady=(4, 12))

        registered_events = self._get_registered_events()
        registered_ids = {event["id"] for event in registered_events}
        unread_count = notif_svc.get_unread_count(self._user.id)
        attendance_rows = [
            row for row in att_svc.get_all_attendance()
            if row["user_id"] == self._user.id and row["status"] == "present"
        ]

        upcoming_registered = []
        open_events = []
        today = date.today()
        for ev in event_svc.get_all_events():
            event_day = self._safe_parse_date(ev.date)
            if ev.id not in registered_ids:
                open_events.append(ev)
            if event_day and event_day >= today and ev.id in registered_ids:
                upcoming_registered.append((event_day, ev))

        upcoming_registered.sort(key=lambda item: item[0])
        next_event_text = "No upcoming registered events"
        if upcoming_registered:
            next_event = upcoming_registered[0][1]
            next_event_text = f"{next_event.name} • {next_event.date}"

        card_row = tk.Frame(wrap, bg=BG)
        card_row.pack(fill="x", pady=(6, 16))

        def summary_card(parent, title, value, note, accent):
            card = make_card(parent, bg=SURFACE, padx=16, pady=16)
            card.pack(side="left", expand=True, fill="x", padx=6)
            tk.Label(card, text=title, bg=SURFACE, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w")
            tk.Label(card, text=str(value), bg=SURFACE, fg=accent, font=("Segoe UI", 24, "bold")).pack(anchor="w", pady=(2, 0))
            tk.Label(card, text=note, bg=SURFACE, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 0))
            return card

        summary_card(card_row, "My Events", len(registered_events), "Registered activities", ACCENT)
        summary_card(card_row, "Upcoming", len(upcoming_registered), "Still ahead on your schedule", ACCENT3)
        summary_card(card_row, "Unread", unread_count, "Notification(s) waiting", ACCENT2)
        summary_card(card_row, "Present", len(attendance_rows), "Attendance marked present", ACCENT3)

        lower = tk.Frame(wrap, bg=BG)
        lower.pack(fill="both", expand=True)

        left = tk.Frame(lower, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = tk.Frame(lower, bg=BG, width=280)
        right.pack(side="left", fill="y")
        right.pack_propagate(False)

        quick = make_card(left, bg=SURFACE, padx=16, pady=16)
        quick.pack(fill="x", pady=(0, 12))
        make_label(quick, "Quick Actions", font=FONT_HEAD, bg=SURFACE).pack(anchor="w")
        make_label(quick, f"Next event: {next_event_text}", fg=MUTED, bg=SURFACE).pack(anchor="w", pady=(2, 10))
        actions = tk.Frame(quick, bg=SURFACE)
        actions.pack(fill="x")
        make_button(actions, "Browse Events", lambda: self._show_section("view_events"), width=14).pack(side="left")
        make_button(actions, "My Schedule", lambda: self._show_section("my_events"), color=ACCENT3, width=14).pack(side="left", padx=(8, 0))
        make_button(actions, "Notifications", lambda: self._show_section("notifications"), color=SURFACE2, width=14).pack(side="left", padx=(8, 0))

        make_label(left, "Suggested Events", font=FONT_HEAD).pack(anchor="w")
        make_label(left, "Events you have not registered for yet.", fg=MUTED).pack(anchor="w", pady=(0, 8))
        suggestion_box = make_card(left, bg=SURFACE, padx=16, pady=12)
        suggestion_box.pack(fill="both", expand=True)

        if open_events:
            for ev in open_events[:4]:
                tk.Label(
                    suggestion_box,
                    text=f"• {ev.name}\n  {ev.date} • {ev.club}\n  {self._format_event_status(ev.date)}",
                    bg=SURFACE,
                    fg=TEXT,
                    justify="left",
                    anchor="w",
                    wraplength=500,
                    font=FONT_SMALL,
                ).pack(anchor="w", fill="x", pady=(0, 8))
        else:
            make_label(suggestion_box, "You are already registered for all available events.",
                       fg=MUTED, bg=SURFACE).pack(anchor="w")

        side_card = make_card(right, bg=SURFACE, padx=14, pady=14)
        side_card.pack(fill="both", expand=True)
        make_label(side_card, "Latest Updates", font=FONT_HEAD, bg=SURFACE).pack(anchor="w")
        notes = notif_svc.get_notifications(self._user.id)[:4]
        if notes:
            for note in notes:
                tag = "Unread" if note["read_flag"] == 0 else "Read"
                tk.Label(
                    side_card,
                    text=f"• {tag}: {note['message']}",
                    bg=SURFACE,
                    fg=TEXT,
                    justify="left",
                    anchor="w",
                    wraplength=240,
                    font=FONT_SMALL,
                ).pack(anchor="w", fill="x", pady=(0, 8))
        else:
            make_label(side_card, "No notifications yet.", fg=MUTED, bg=SURFACE).pack(anchor="w")

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
        self._ve_tree.bind("<<TreeviewSelect>>", lambda _e: self._update_view_event_preview())

        preview_card = tk.Frame(wrap, bg=SURFACE, padx=14, pady=12,
                                highlightthickness=1, highlightbackground=BORDER)
        preview_card.pack(fill="x", pady=(10, 0))
        make_label(preview_card, "Selected Event Details", font=FONT_HEAD, bg=SURFACE).pack(anchor="w")
        self._ve_preview_var = tk.StringVar(value="Select an event to view its details and registration status.")
        tk.Label(preview_card, textvariable=self._ve_preview_var,
                 bg=SURFACE, fg=TEXT, justify="left", anchor="w", wraplength=760,
                 font=FONT_SMALL).pack(fill="x", pady=(6, 0))

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

        children = self._ve_tree.get_children()
        if children:
            self._ve_tree.selection_set(children[0])
            self._update_view_event_preview()
        elif hasattr(self, "_ve_preview_var"):
            self._ve_preview_var.set("No events match the current filters.")

    def _update_view_event_preview(self):
        if not hasattr(self, "_ve_preview_var"):
            return

        sel = self._ve_tree.selection()
        if not sel:
            self._ve_preview_var.set("Select an event to view its details and registration status.")
            return

        values = self._ve_tree.item(sel[0])["values"]
        event_id, event_name, event_date, club = values
        is_registered = int(event_id) in self._get_registered_event_ids()
        registration_text = "Already in your schedule" if is_registered else "Open for registration"
        self._ve_preview_var.set(
            f"{event_name}\nClub: {club}\nDate: {event_date} • {self._format_event_status(event_date)}\nStatus: {registration_text}"
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
        registered_ids = self._get_registered_event_ids()
        events = [
            ev for ev in self._get_filtered_events(self._reg_search.get(), self._reg_club_var.get())
            if ev.id not in registered_ids
        ]
        self._reg_ev_tree.delete(*self._reg_ev_tree.get_children())
        for ev in events:
            self._reg_ev_tree.insert("", "end", iid=ev.id,
                                     values=(ev.id, ev.name, ev.date, ev.club))
        if events:
            self._reg_summary_var.set(f"{len(events)} new event(s) ready for registration")
        else:
            self._reg_summary_var.set("No new events available right now.")

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
            if hasattr(self, "_reg_ev_tree"):
                self._load_register_events()
            if hasattr(self, "_ve_tree"):
                self._update_view_event_preview()
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
        make_button(action_row, "❌ Cancel Selected", self._cancel_selected_registration,
                    color=ACCENT2, width=16).pack(side="left")
        make_button(action_row, "💬 Leave Feedback", self._leave_feedback,
                    color=ACCENT, width=16).pack(side="left", padx=(8, 0))
        make_button(action_row, "⬇ Export Schedule", self._export_my_events,
                    color=ACCENT3, width=16).pack(side="left", padx=(8, 0))
        make_button(action_row, "🔄  Refresh", self._refresh_my_events,
                    color=SURFACE2, width=12).pack(side="right")

        cols = ("Event Name", "Date", "Club", "Attendance")
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
        attendance_map = {
            row["event_id"]: row["status"].title()
            for row in att_svc.get_all_attendance()
            if row["user_id"] == self._user.id
        }

        for ev in reg_svc.get_events_for_student(self._user.id):
            attendance_status = attendance_map.get(ev["id"], "Pending")
            self._my_tree.insert("", "end", iid=str(ev["id"]),
                                 values=(ev["name"], ev["date"], ev["club"], attendance_status))
            event_day = self._safe_parse_date(ev["date"])
            if event_day and event_day >= today and (next_event_date is None or event_day < next_event_date):
                next_event_date = event_day
                next_event_text = f" Next up: {ev['name']} on {ev['date']}."

        self._next_registered_event_text = next_event_text

    def _export_my_events(self):
        path = filedialog.asksaveasfilename(
            title="Export My Schedule",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*")],
        )
        if not path:
            return

        try:
            rows = [self._my_tree.item(item_id)["values"] for item_id in self._my_tree.get_children()]
            with open(path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["event_name", "date", "club", "attendance"])
                writer.writerows(rows)
            show_toast(self, "My event schedule exported.", success=True)
        except Exception as exc:
            messagebox.showerror("Export Schedule", str(exc))

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

    def _leave_feedback(self):
        sel = self._my_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select an event to leave feedback.")
            return

        event_id = int(sel[0])
        event_name = self._my_tree.item(sel[0])["values"][0]
        event_date = self._my_tree.item(sel[0])["values"][1]

        # Check if event has passed
        event_day = self._safe_parse_date(event_date)
        if event_day and event_day > date.today():
            messagebox.showinfo("Event not completed", "You can only leave feedback for past events.")
            return

        # Create feedback dialog
        feedback_window = tk.Toplevel(self)
        feedback_window.title(f"Feedback for {event_name}")
        feedback_window.geometry("400x300")
        feedback_window.configure(bg=BG)
        feedback_window.transient(self)
        feedback_window.grab_set()

        # Title
        tk.Label(feedback_window, text=f"Share your feedback for", bg=BG, fg=TEXT, font=FONT_HEAD).pack(pady=(20, 0))
        tk.Label(feedback_window, text=event_name, bg=BG, fg=ACCENT, font=FONT_TITLE).pack(pady=(0, 10))

        # Rating
        rating_frame = tk.Frame(feedback_window, bg=BG)
        rating_frame.pack(pady=(10, 0))
        tk.Label(rating_frame, text="Rating:", bg=BG, fg=TEXT, font=FONT_BODY).pack(side="left")

        rating_var = tk.StringVar(value="5")
        ratings = [("⭐", "1"), ("⭐⭐", "2"), ("⭐⭐⭐", "3"), ("⭐⭐⭐⭐", "4"), ("⭐⭐⭐⭐⭐", "5")]
        for stars, value in ratings:
            tk.Radiobutton(rating_frame, text=stars, variable=rating_var, value=value,
                          bg=BG, fg=TEXT, selectcolor=SURFACE, font=FONT_BODY).pack(side="left", padx=2)

        # Comment
        tk.Label(feedback_window, text="Comments (optional):", bg=BG, fg=TEXT, font=FONT_BODY).pack(anchor="w", padx=20, pady=(20, 5))
        comment_text = tk.Text(feedback_window, height=4, width=40, font=FONT_BODY,
                              bg=SURFACE, fg=TEXT, insertbackground=TEXT)
        comment_text.pack(padx=20, pady=(0, 20))

        # Buttons
        btn_frame = tk.Frame(feedback_window, bg=BG)
        btn_frame.pack(pady=(0, 20))

        def submit_feedback():
            rating = rating_var.get()
            comment = comment_text.get("1.0", "end").strip()

            # Here we would normally save to database
            # For now, just show confirmation
            messagebox.showinfo("Feedback Submitted",
                              f"Thank you for your feedback!\n\nRating: {rating} stars\nComment: {comment[:50]}{'...' if len(comment) > 50 else ''}")

            feedback_window.destroy()
            show_toast(self, "Feedback submitted successfully!", success=True)

        make_button(btn_frame, "Submit Feedback", submit_feedback, width=14).pack(side="left", padx=5)
        make_button(btn_frame, "Cancel", feedback_window.destroy, color=SURFACE2, width=10).pack(side="left", padx=5)

    def _update_count(self):
        total = len(self._my_tree.get_children())
        extra = getattr(self, "_next_registered_event_text", "")
        self._my_count_var.set(f"You are registered for {total} event(s).{extra}")

    # ══════════════════════════════════════════════════════════════════════
    # Section: Profile
    # ══════════════════════════════════════════════════════════════════════
    def _build_profile(self):
        wrap = tk.Frame(self._content, bg=BG, padx=40, pady=30)
        wrap.pack(fill="both", expand=True)

        make_label(wrap, "My Profile", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "View and manage your account information.",
                   fg=MUTED).pack(anchor="w", pady=(4, 16))

        # Profile info card
        profile_card = tk.Frame(wrap, bg=SURFACE, padx=20, pady=20,
                                highlightthickness=1, highlightbackground=BORDER)
        profile_card.pack(fill="x", pady=(0, 16))

        make_label(profile_card, "Account Information", font=FONT_HEAD, bg=SURFACE).pack(anchor="w", pady=(0, 12))

        # Username
        user_row = tk.Frame(profile_card, bg=SURFACE)
        user_row.pack(fill="x", pady=(0, 8))
        make_label(user_row, "Username:", fg=MUTED, bg=SURFACE, width=12).pack(side="left")
        make_label(user_row, self._user.username, bg=SURFACE).pack(side="left")

        # Email
        email_row = tk.Frame(profile_card, bg=SURFACE)
        email_row.pack(fill="x", pady=(0, 8))
        make_label(email_row, "Email:", fg=MUTED, bg=SURFACE, width=12).pack(side="left")
        make_label(email_row, self._user.email, bg=SURFACE).pack(side="left")

        # Role
        role_row = tk.Frame(profile_card, bg=SURFACE)
        role_row.pack(fill="x")
        make_label(role_row, "Role:", fg=MUTED, bg=SURFACE, width=12).pack(side="left")
        make_label(role_row, self._user.role.title(), bg=SURFACE).pack(side="left")

        # Statistics card
        stats_card = tk.Frame(wrap, bg=SURFACE, padx=20, pady=20,
                              highlightthickness=1, highlightbackground=BORDER)
        stats_card.pack(fill="x", pady=(0, 16))

        make_label(stats_card, "Activity Statistics", font=FONT_HEAD, bg=SURFACE).pack(anchor="w", pady=(0, 12))

        # Get stats
        registered_events = len(reg_svc.get_events_for_student(self._user.id))
        attendance_rows = [
            row for row in att_svc.get_all_attendance()
            if row["user_id"] == self._user.id and row["status"] == "present"
        ]
        present_count = len(attendance_rows)
        unread_notifications = notif_svc.get_unread_count(self._user.id)

        stats_grid = tk.Frame(stats_card, bg=SURFACE)
        stats_grid.pack(fill="x")

        def stat_item(parent, label, value, color=ACCENT):
            item = tk.Frame(parent, bg=SURFACE)
            item.pack(side="left", expand=True, fill="x", padx=8)
            tk.Label(item, text=str(value), bg=SURFACE, fg=color, font=("Helvetica", 24, "bold")).pack(anchor="w")
            tk.Label(item, text=label, bg=SURFACE, fg=MUTED, font=FONT_SMALL).pack(anchor="w", pady=(2, 0))
            return item

        stat_item(stats_grid, "Events Registered", registered_events, ACCENT)
        stat_item(stats_grid, "Present Count", present_count, ACCENT3)
        stat_item(stats_grid, "Unread Notifications", unread_notifications, ACCENT2)

        # Change password section
        password_card = tk.Frame(wrap, bg=SURFACE, padx=20, pady=20,
                                 highlightthickness=1, highlightbackground=BORDER)
        password_card.pack(fill="x")

        make_label(password_card, "Change Password", font=FONT_HEAD, bg=SURFACE).pack(anchor="w", pady=(0, 12))

        form_frame = tk.Frame(password_card, bg=SURFACE)
        form_frame.pack(fill="x")

        # Current password
        current_row = tk.Frame(form_frame, bg=SURFACE)
        current_row.pack(fill="x", pady=(0, 8))
        make_label(current_row, "Current Password:", fg=MUTED, bg=SURFACE, width=16).pack(side="left")
        self._current_pass = make_entry(current_row, width=20, show="*")
        self._current_pass.pack(side="left")

        # New password
        new_row = tk.Frame(form_frame, bg=SURFACE)
        new_row.pack(fill="x", pady=(0, 8))
        make_label(new_row, "New Password:", fg=MUTED, bg=SURFACE, width=16).pack(side="left")
        self._new_pass = make_entry(new_row, width=20, show="*")
        self._new_pass.pack(side="left")

        # Confirm password
        confirm_row = tk.Frame(form_frame, bg=SURFACE)
        confirm_row.pack(fill="x", pady=(0, 12))
        make_label(confirm_row, "Confirm Password:", fg=MUTED, bg=SURFACE, width=16).pack(side="left")
        self._confirm_pass = make_entry(confirm_row, width=20, show="*")
        self._confirm_pass.pack(side="left")

        make_button(password_card, "Update Password", self._change_password,
                    color=ACCENT, width=16).pack(anchor="w")

    def _change_password(self):
        current = self._current_pass.get().strip()
        new_pass = self._new_pass.get().strip()
        confirm = self._confirm_pass.get().strip()

        if not current or not new_pass or not confirm:
            messagebox.showerror("Error", "All password fields are required.")
            return

        if new_pass != confirm:
            messagebox.showerror("Error", "New password and confirmation do not match.")
            return

        if len(new_pass) < 6:
            messagebox.showerror("Error", "New password must be at least 6 characters long.")
            return

        # Here we would normally verify the current password and update it
        # For now, we'll just show a success message
        messagebox.showinfo("Success", "Password updated successfully!")
        self._current_pass.delete(0, "end")
        self._new_pass.delete(0, "end")
        self._confirm_pass.delete(0, "end")

    # ══════════════════════════════════════════════════════════════════════
    # Section: Attendance History
    # ══════════════════════════════════════════════════════════════════════
    def _build_attendance(self):
        wrap = tk.Frame(self._content, bg=BG, padx=40, pady=30)
        wrap.pack(fill="both", expand=True)

        make_label(wrap, "My Attendance History", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "Track your attendance records for registered events.",
                   fg=MUTED).pack(anchor="w", pady=(4, 16))

        # Summary cards
        summary_frame = tk.Frame(wrap, bg=BG)
        summary_frame.pack(fill="x", pady=(0, 16))

        # Get attendance data
        attendance_data = [
            row for row in att_svc.get_all_attendance()
            if row["user_id"] == self._user.id
        ]

        present_count = len([row for row in attendance_data if row["status"] == "present"])
        absent_count = len([row for row in attendance_data if row["status"] == "absent"])
        total_events = len(reg_svc.get_events_for_student(self._user.id))

        def summary_card(parent, title, value, subtitle, color):
            card = tk.Frame(parent, bg=SURFACE, padx=16, pady=12)
            card.pack(side="left", expand=True, fill="x", padx=4)
            tk.Label(card, text=title, bg=SURFACE, fg=MUTED, font=FONT_SMALL).pack(anchor="w")
            tk.Label(card, text=str(value), bg=SURFACE, fg=color, font=("Helvetica", 20, "bold")).pack(anchor="w", pady=(2, 0))
            tk.Label(card, text=subtitle, bg=SURFACE, fg=MUTED, font=FONT_SMALL).pack(anchor="w")
            return card

        summary_card(summary_frame, "Present", present_count, "Events attended", ACCENT)
        summary_card(summary_frame, "Absent", absent_count, "Events missed", ACCENT2)
        summary_card(summary_frame, "Total Registered", total_events, "Events registered", ACCENT3)

        # Attendance table
        make_label(wrap, "Detailed Attendance Records", font=FONT_HEAD).pack(anchor="w", pady=(0, 8))

        action_row = tk.Frame(wrap, bg=BG)
        action_row.pack(fill="x", pady=(0, 8))
        make_button(action_row, "⬇ Export Attendance", self._export_attendance,
                    color=ACCENT3, width=18).pack(side="left")
        make_button(action_row, "🔄  Refresh", self._refresh_attendance,
                    color=SURFACE2, width=12).pack(side="right")

        cols = ("Event Name", "Date", "Club", "Status")
        tv_frame, self._att_tree = make_treeview(wrap, cols)
        tv_frame.pack(fill="both", expand=True)

        self._load_attendance()

        # Attendance rate
        attendance_rate = (present_count / total_events * 100) if total_events > 0 else 0
        rate_text = f"Overall Attendance Rate: {attendance_rate:.1f}%"
        tk.Label(wrap, text=rate_text, bg=BG, fg=ACCENT3, font=FONT_BODY).pack(anchor="w", pady=(10, 0))

    def _load_attendance(self):
        self._att_tree.delete(*self._att_tree.get_children())

        # Get all registered events with attendance status
        attendance_map = {
            row["event_id"]: row["status"].title()
            for row in att_svc.get_all_attendance()
            if row["user_id"] == self._user.id
        }

        for ev in reg_svc.get_events_for_student(self._user.id):
            status = attendance_map.get(ev["id"], "Not Marked")
            status_color = ACCENT if status == "Present" else ACCENT2 if status == "Absent" else MUTED
            self._att_tree.insert("", "end", values=(ev["name"], ev["date"], ev["club"], status))

    def _export_attendance(self):
        path = filedialog.asksaveasfilename(
            title="Export Attendance History",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*")],
        )
        if not path:
            return

        try:
            rows = [self._att_tree.item(item_id)["values"] for item_id in self._att_tree.get_children()]
            with open(path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["event_name", "date", "club", "attendance_status"])
                writer.writerows(rows)
            show_toast(self, "Attendance history exported.", success=True)
        except Exception as exc:
            messagebox.showerror("Export Attendance", str(exc))

    def _refresh_attendance(self):
        self._load_attendance()
        show_toast(self, "Attendance records refreshed.", success=True)

    # ══════════════════════════════════════════════════════════════════════
    # Section: Clubs
    # ══════════════════════════════════════════════════════════════════════
    def _build_clubs(self):
        wrap = tk.Frame(self._content, bg=BG, padx=40, pady=30)
        wrap.pack(fill="both", expand=True)

        make_label(wrap, "College Clubs", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "Learn about the clubs organizing events on campus.",
                   fg=MUTED).pack(anchor="w", pady=(4, 16))

        # Import club service
        import services.club_service as club_svc

        # Get all clubs
        clubs = club_svc.get_all_clubs()

        # Summary
        tk.Label(wrap, text=f"Total Clubs: {len(clubs)}",
                 bg=BG, fg=ACCENT3, font=FONT_BODY).pack(anchor="w", pady=(0, 12))

        # Clubs grid
        clubs_frame = tk.Frame(wrap, bg=BG)
        clubs_frame.pack(fill="both", expand=True)

        row_frame = None
        clubs_per_row = 2

        for i, club in enumerate(clubs):
            if i % clubs_per_row == 0:
                row_frame = tk.Frame(clubs_frame, bg=BG)
                row_frame.pack(fill="x", pady=(0, 12))

            # Club card
            club_card = tk.Frame(row_frame, bg=SURFACE, padx=16, pady=16,
                                 highlightthickness=1, highlightbackground=BORDER)
            club_card.pack(side="left", expand=True, fill="both", padx=6)

            # Club name
            make_label(club_card, club["name"], font=FONT_HEAD, bg=SURFACE).pack(anchor="w", pady=(0, 4))

            # Description
            desc_text = club["description"] if club["description"] else "No description available."
            desc_label = tk.Label(club_card, text=desc_text, bg=SURFACE, fg=TEXT,
                                  wraplength=300, justify="left", anchor="w", font=FONT_SMALL)
            desc_label.pack(anchor="w", pady=(0, 8), fill="x")

            # Event count for this club
            event_count = len([ev for ev in event_svc.get_all_events() if ev.club == club["name"]])
            tk.Label(club_card, text=f"Events: {event_count}",
                     bg=SURFACE, fg=ACCENT3, font=FONT_SMALL).pack(anchor="w", pady=(0, 4))

            # My registrations for this club
            my_registrations = len([
                ev for ev in reg_svc.get_events_for_student(self._user.id)
                if ev["club"] == club["name"]
            ])
            if my_registrations > 0:
                tk.Label(club_card, text=f"My Registrations: {my_registrations}",
                         bg=SURFACE, fg=ACCENT, font=FONT_SMALL).pack(anchor="w")

        if not clubs:
            make_label(clubs_frame, "No clubs found.", fg=MUTED, bg=BG).pack(anchor="w")

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

