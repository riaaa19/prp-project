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
    make_frame, make_label, make_entry, make_button, make_treeview, show_toast,
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
            ("🏠  Overview",      "overview"),
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
            "overview":    self._build_overview,
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
            card = tk.Frame(parent, bg=SURFACE, padx=14, pady=12)
            card.pack(side="left", expand=True, fill="x", padx=6)
            tk.Label(card, text=title, bg=SURFACE, fg=MUTED, font=("Helvetica", 9)).pack(anchor="w")
            tk.Label(card, text=str(value), bg=SURFACE, fg=accent, font=("Helvetica", 24, "bold")).pack(anchor="w", pady=(2, 0))
            tk.Label(card, text=note, bg=SURFACE, fg=MUTED, font=("Helvetica", 8)).pack(anchor="w", pady=(2, 0))
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

        quick = tk.Frame(left, bg=SURFACE, padx=16, pady=16,
                         highlightthickness=1, highlightbackground=BORDER)
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
        suggestion_box = tk.Frame(left, bg=SURFACE, padx=16, pady=12,
                                  highlightthickness=1, highlightbackground=BORDER)
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

        side_card = tk.Frame(right, bg=SURFACE, padx=14, pady=14,
                             highlightthickness=1, highlightbackground=BORDER)
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

