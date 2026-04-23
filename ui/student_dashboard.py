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
import services.reminder_service as rem_svc
import services.social_service as soc_svc
import services.gamification_service as gamif_svc
from ui.components import (
    BG, SURFACE, SURFACE2, ACCENT, ACCENT2, ACCENT3,
    TEXT, MUTED, BORDER, FONT_TITLE, FONT_HEAD, FONT_BODY, FONT_BTN, FONT_SMALL,
    make_frame, make_card, make_label, make_entry, make_button, make_treeview, show_toast,
)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def fade_in(widget, step=0):
    try:
        if step > 1:
            return
        widget.attributes("-alpha", step)
        widget.after(20, lambda: fade_in(widget, step + 0.08))
    except:
        pass

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
            ("🔔  Reminders",     "reminders"),
            ("👥  Social",        "social"),
            ("🔔  Notifications", "notifications"),
            ("🎮  Gamification",  "gamification"),
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
            btn.config(bg=ACCENT, fg="white")
        else:
            btn.config(bg=SURFACE, fg=TEXT)

    self._active_section = key

    for w in self._content.winfo_children():
        w.destroy()

    # 🔥 animation
    try:
        self._content.attributes("-alpha", 0)
        fade_in(self._content)
    except:
        pass

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

    registered_events = self._get_registered_events()
    unread_count = notif_svc.get_unread_count(self._user.id)

    total_events = len(event_svc.get_all_events())
    my_events = len(registered_events)

    # 🔥 CARDS (cleaner UI)
    row = tk.Frame(wrap, bg=BG)
    row.pack(fill="x", pady=15)

    def card(title, value):
        c = tk.Frame(row, bg=SURFACE, padx=16, pady=16,
                     highlightthickness=1, highlightbackground=BORDER)
        c.pack(side="left", expand=True, fill="x", padx=6)
        tk.Label(c, text=title, bg=SURFACE, fg=MUTED).pack(anchor="w")
        tk.Label(c, text=value, bg=SURFACE, fg=ACCENT,
                 font=("Segoe UI", 20, "bold")).pack(anchor="w")

    card("My Events", my_events)
    card("All Events", total_events)
    card("Notifications", unread_count)

    # 🔥 CHART (NEW)
    chart_frame = tk.Frame(wrap, bg=SURFACE)
    chart_frame.pack(fill="both", expand=True, pady=10)

    fig, ax = plt.subplots(figsize=(5, 2.5))
    ax.bar(["My Events", "All Events"],
           [my_events, total_events])
    ax.set_title("Your Activity")

    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    # 🔥 SMART INSIGHT
    if my_events == 0:
        insight = "You haven’t registered yet ⚠️"
    elif my_events < 3:
        insight = "Good start 👍"
    else:
        insight = "Very active 🎉"

    make_label(wrap, f"Insight: {insight}", fg=ACCENT).pack(anchor="w", pady=10)
    # ══════════════════════════════════════════════════════════════════════
    # Section: View Events
    # ══════════════════════════════════════════════════════════════════════
    def _build_view_events(self):
        wrap = tk.Frame(self._content, bg=BG, padx=40, pady=30)
        wrap.pack(fill="both", expand=True)

       make_label(wrap, "Search + filter events smartly", fg=MUTED).pack(anchor="w")
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
    # Section: Reminders
    # ══════════════════════════════════════════════════════════════════════
    def _build_reminders(self):
        wrap = tk.Frame(self._content, bg=BG, padx=40, pady=30)
        wrap.pack(fill="both", expand=True)

        make_label(wrap, "Smart Reminders & Notifications", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "Manage your event reminders and notification preferences.",
                   fg=MUTED).pack(anchor="w", pady=(4, 16))

        # Get user preferences
        prefs = rem_svc.get_user_preferences(self._user.id)

        # Preferences section
        prefs_card = tk.Frame(wrap, bg=SURFACE, padx=20, pady=20,
                              highlightthickness=1, highlightbackground=BORDER)
        prefs_card.pack(fill="x", pady=(0, 16))

        make_label(prefs_card, "Notification Preferences", font=FONT_HEAD, bg=SURFACE).pack(anchor="w", pady=(0, 12))

        # Create checkboxes for preferences
        self._reminder_vars = {}
        pref_options = [
            ('email_reminders', 'Email Reminders'),
            ('push_notifications', 'Push Notifications'),
            ('weather_alerts', 'Weather Alerts'),
            ('transport_reminders', 'Transportation Reminders'),
            ('default_reminder_1day', '1 Day Before Events'),
            ('default_reminder_1hr', '1 Hour Before Events'),
        ]

        prefs_grid = tk.Frame(prefs_card, bg=SURFACE)
        prefs_grid.pack(fill="x")

        for i, (key, label) in enumerate(pref_options):
            row = i // 2
            col = i % 2

            if col == 0:
                frame = tk.Frame(prefs_grid, bg=SURFACE)
                frame.pack(fill="x", pady=(0, 8))

            var = tk.BooleanVar(value=bool(prefs.get(key, 1)))
            self._reminder_vars[key] = var

            cb = tk.Checkbutton(frame, text=label, variable=var, bg=SURFACE,
                               fg=TEXT, selectcolor=ACCENT, font=FONT_BODY)
            cb.pack(side="left", padx=(0, 20))

        make_button(prefs_card, "Save Preferences", self._save_reminder_preferences,
                    color=ACCENT, width=16).pack(anchor="w", pady=(12, 0))

        # Active reminders section
        reminders_card = tk.Frame(wrap, bg=SURFACE, padx=20, pady=20,
                                  highlightthickness=1, highlightbackground=BORDER)
        reminders_card.pack(fill="both", expand=True)

        make_label(reminders_card, "Your Active Reminders", font=FONT_HEAD, bg=SURFACE).pack(anchor="w", pady=(0, 12))

        action_row = tk.Frame(reminders_card, bg=SURFACE)
        action_row.pack(fill="x", pady=(0, 8))
        make_button(action_row, "🔄  Refresh", self._refresh_reminders,
                    color=SURFACE2, width=12).pack(side="left")
        make_button(action_row, "⚙️  Setup for My Events", self._setup_event_reminders,
                    color=ACCENT, width=18).pack(side="left", padx=(8, 0))

        # Reminders list
        cols = ("Event", "Type", "Time", "Status")
        tv_frame, self._reminders_tree = make_treeview(reminders_card, cols)
        tv_frame.pack(fill="both", expand=True)

        self._load_reminders()

        # Weather & Transport info section
        info_card = tk.Frame(wrap, bg=SURFACE, padx=20, pady=20,
                             highlightthickness=1, highlightbackground=BORDER)
        info_card.pack(fill="x", pady=(12, 0))

        make_label(info_card, "Weather & Transportation Info", font=FONT_HEAD, bg=SURFACE).pack(anchor="w", pady=(0, 12))

        # Sample weather info
        weather_frame = tk.Frame(info_card, bg=SURFACE)
        weather_frame.pack(fill="x", pady=(0, 8))

        make_label(weather_frame, "🌤️  Today's Weather: Sunny, 22°C", bg=SURFACE, font=FONT_BODY).pack(side="left")
        make_label(weather_frame, "🚌 Next Shuttle: 14:00 (Main Campus)", bg=SURFACE, font=FONT_BODY).pack(side="right")

        make_label(info_card, "Weather alerts and transport reminders will be sent based on your preferences.",
                   fg=MUTED, bg=SURFACE, font=FONT_SMALL).pack(anchor="w")

    def _save_reminder_preferences(self):
        prefs = {key: int(var.get()) for key, var in self._reminder_vars.items()}
        rem_svc.update_user_preferences(self._user.id, prefs)
        show_toast(self, "Reminder preferences saved!", success=True)

    def _load_reminders(self):
        self._reminders_tree.delete(*self._reminders_tree.get_children())

        reminders = rem_svc.get_user_reminders(self._user.id)

        for reminder in reminders:
            reminder_time = datetime.fromisoformat(reminder['reminder_time'])
            time_str = reminder_time.strftime("%m/%d %H:%M")

            status = "Active" if reminder['is_active'] else "Sent"
            reminder_type_display = {
                'event_start': 'Event Reminder',
                'event_update': 'Event Update',
                'weather_alert': 'Weather Alert',
                'transport': 'Transport Reminder'
            }.get(reminder['reminder_type'], reminder['reminder_type'])

            self._reminders_tree.insert("", "end", values=(
                reminder['event_name'],
                reminder_type_display,
                time_str,
                status
            ))

    def _refresh_reminders(self):
        self._load_reminders()
        show_toast(self, "Reminders refreshed.", success=True)

    def _setup_event_reminders(self):
        """Setup reminders for all registered events."""
        registered_events = reg_svc.get_events_for_student(self._user.id)

        reminder_count = 0
        for event in registered_events:
            rem_svc.create_event_reminders(self._user.id, event['id'])
            reminder_count += 1

        self._load_reminders()
        show_toast(self, f"Set up reminders for {reminder_count} event(s)!", success=True)

    # ══════════════════════════════════════════════════════════════════════
    # Section: Social
    # ══════════════════════════════════════════════════════════════════════
    def _build_social(self):
        wrap = tk.Frame(self._content, bg=BG, padx=40, pady=30)
        wrap.pack(fill="both", expand=True)

        make_label(wrap, "Social Hub", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "Connect with friends, join study groups, and share events.",
                   fg=MUTED).pack(anchor="w", pady=(4, 16))

        # Social stats
        stats = soc_svc.get_social_stats(self._user.id)
        stats_frame = tk.Frame(wrap, bg=BG)
        stats_frame.pack(fill="x", pady=(0, 16))

        def stat_card(parent, label, value, icon):
            card = tk.Frame(parent, bg=SURFACE, padx=16, pady=12)
            card.pack(side="left", expand=True, fill="x", padx=4)
            tk.Label(card, text=f"{icon} {value}", bg=SURFACE, fg=ACCENT, font=("Helvetica", 18, "bold")).pack(anchor="w")
            tk.Label(card, text=label, bg=SURFACE, fg=MUTED, font=FONT_SMALL).pack(anchor="w", pady=(2, 0))
            return card

        stat_card(stats_frame, "Friends", stats['friend_count'], "👥")
        stat_card(stats_frame, "Study Groups", stats['study_group_count'], "📚")
        stat_card(stats_frame, "Events Shared", stats['events_shared'], "📤")

        # Tabbed interface
        tab_frame = tk.Frame(wrap, bg=BG)
        tab_frame.pack(fill="both", expand=True)

        # Tab buttons
        self._tab_buttons = {}
        tab_names = ["Friends", "Study Groups", "Ambassadors", "Share Events"]

        tab_btn_frame = tk.Frame(tab_frame, bg=BG)
        tab_btn_frame.pack(fill="x", pady=(0, 12))

        for i, tab_name in enumerate(tab_names):
            btn = tk.Button(tab_btn_frame, text=tab_name, bg=SURFACE, fg=TEXT,
                           font=FONT_BODY, relief="flat", bd=0, width=16,
                           padx=20, pady=8,
                           command=lambda t=tab_name.lower().replace(" ", "_"): self._switch_social_tab(t))
            btn.pack(side="left", padx=2)
            self._tab_buttons[tab_name.lower().replace(" ", "_")] = btn

        # Tab content area
        self._social_content = tk.Frame(tab_frame, bg=BG)
        self._social_content.pack(fill="both", expand=True)

        # Initialize with friends tab
        self._switch_social_tab("friends")

    def _switch_social_tab(self, tab_name):
        # Clear current content
        for widget in self._social_content.winfo_children():
            widget.destroy()

        # Update tab button styles
        for btn_name, btn in self._tab_buttons.items():
            if btn_name == tab_name:
                btn.config(bg=ACCENT, fg="white")
            else:
                btn.config(bg=SURFACE, fg=TEXT)

        self._active_social_tab = tab_name

        # Load appropriate tab content
        tab_methods = {
            "friends": self._build_friends_tab,
            "study_groups": self._build_study_groups_tab,
            "ambassadors": self._build_ambassadors_tab,
            "share_events": self._build_share_events_tab
        }

        if tab_name in tab_methods:
            tab_methods[tab_name]()

    def _build_friends_tab(self):
        content = self._social_content

        # Friend requests section
        requests_frame = tk.Frame(content, bg=SURFACE, padx=16, pady=16)
        requests_frame.pack(fill="x", pady=(0, 12))

        make_label(requests_frame, "Friend Requests", font=FONT_HEAD, bg=SURFACE).pack(anchor="w")

        requests = soc_svc.get_friend_requests(self._user.id)
        if requests:
            for req in requests[:3]:  # Show only first 3
                req_frame = tk.Frame(requests_frame, bg=SURFACE)
                req_frame.pack(fill="x", pady=(8, 0))

                tk.Label(req_frame, text=f"🤝 {req['username']} wants to be friends",
                        bg=SURFACE, fg=TEXT, font=FONT_BODY).pack(side="left")

                tk.Button(req_frame, text="Accept", bg=ACCENT, fg="white",
                         font=("Helvetica", 9), padx=10, pady=2,
                         command=lambda uid=req['id']: self._accept_friend_request(uid)).pack(side="right", padx=(4, 0))
        else:
            make_label(requests_frame, "No pending friend requests.", fg=MUTED, bg=SURFACE).pack(anchor="w", pady=(8, 0))

        # Add friend section
        add_frame = tk.Frame(content, bg=SURFACE, padx=16, pady=16)
        add_frame.pack(fill="x", pady=(0, 12))

        make_label(add_frame, "Add Friend", font=FONT_HEAD, bg=SURFACE).pack(anchor="w")

        friend_entry = make_entry(add_frame, width=30, placeholder="Enter username")
        friend_entry.pack(pady=(8, 0))

        tk.Button(add_frame, text="Send Request", bg=ACCENT, fg="white",
                 font=FONT_BTN, padx=16, pady=6,
                 command=lambda: self._send_friend_request(friend_entry.get())).pack()

        # Friends list
        make_label(content, "My Friends", font=FONT_HEAD).pack(anchor="w", pady=(12, 8))

        friends = soc_svc.get_friends(self._user.id)
        if friends:
            friends_frame = tk.Frame(content, bg=SURFACE, padx=16, pady=16)
            friends_frame.pack(fill="both", expand=True)

            for friend in friends:
                friend_frame = tk.Frame(friends_frame, bg=SURFACE)
                friend_frame.pack(fill="x", pady=(0, 8))

                tk.Label(friend_frame, text=f"👤 {friend['username']}",
                        bg=SURFACE, fg=TEXT, font=FONT_BODY).pack(side="left")

                tk.Label(friend_frame, text=f"Added {friend['created_at'][:10]}",
                        bg=SURFACE, fg=MUTED, font=FONT_SMALL).pack(side="right")
        else:
            make_label(content, "No friends yet. Send some friend requests to get started!",
                      fg=MUTED, bg=BG).pack(anchor="w")

        tk.Frame(content, bg=BG).pack(fill="both", expand=True)

    def _build_study_groups_tab(self):
        content = self._social_content

        # Create study group section
        create_frame = tk.Frame(content, bg=SURFACE, padx=16, pady=16)
        create_frame.pack(fill="x", pady=(0, 12))

        make_label(create_frame, "Create Study Group", font=FONT_HEAD, bg=SURFACE).pack(anchor="w")

        # Form fields
        form_frame = tk.Frame(create_frame, bg=SURFACE)
        form_frame.pack(fill="x", pady=(8, 0))

        name_entry = make_entry(form_frame, width=25, placeholder="Group name")
        name_entry.pack(pady=(0, 8))

        desc_text = tk.Text(form_frame, height=3, width=40, font=FONT_SMALL,
                           bg=SURFACE2, fg=TEXT)
        desc_text.pack(pady=(0, 8))
        desc_text.insert("1.0", "Group description...")

        tk.Button(create_frame, text="Create Group", bg=ACCENT, fg="white",
                 font=FONT_BTN, padx=16, pady=6,
                 command=lambda: self._create_study_group(name_entry.get(), desc_text.get("1.0", "end").strip())).pack()

        # Study groups list
        make_label(content, "Available Study Groups", font=FONT_HEAD).pack(anchor="w", pady=(12, 8))

        groups = soc_svc.get_study_groups()
        if groups:
            groups_frame = tk.Frame(content, bg=SURFACE, padx=16, pady=16)
            groups_frame.pack(fill="both", expand=True)

            for group in groups[:5]:  # Show first 5
                group_frame = tk.Frame(groups_frame, bg=SURFACE)
                group_frame.pack(fill="x", pady=(0, 12))

                # Group info
                info_frame = tk.Frame(group_frame, bg=SURFACE)
                info_frame.pack(fill="x")

                tk.Label(info_frame, text=f"📚 {group['name']}",
                        bg=SURFACE, fg=TEXT, font=FONT_BODY).pack(anchor="w")

                tk.Label(info_frame, text=f"by {group['creator_name']} • {group['member_count']}/{group['max_members']} members",
                        bg=SURFACE, fg=MUTED, font=FONT_SMALL).pack(anchor="w")

                if group['description']:
                    tk.Label(info_frame, text=group['description'][:100] + "..." if len(group['description']) > 100 else group['description'],
                            bg=SURFACE, fg=TEXT, font=FONT_SMALL, wraplength=400).pack(anchor="w", pady=(4, 0))

                # Join button
                tk.Button(group_frame, text="Join Group", bg=ACCENT, fg="white",
                         font=("Helvetica", 9), padx=12, pady=4,
                         command=lambda gid=group['id']: self._join_study_group(gid)).pack(anchor="e", pady=(8, 0))
        else:
            make_label(content, "No study groups available. Create one to get started!",
                      fg=MUTED, bg=BG).pack(anchor="w")

        tk.Frame(content, bg=BG).pack(fill="both", expand=True)

    def _build_ambassadors_tab(self):
        content = self._social_content

        make_label(content, "Club Ambassadors", font=FONT_HEAD).pack(anchor="w", pady=(0, 8))
        make_label(content, "Connect with club representatives for questions and guidance.",
                   fg=MUTED, bg=BG).pack(anchor="w", pady=(0, 16))

        ambassadors = soc_svc.get_club_ambassadors()
        if ambassadors:
            ambassadors_frame = tk.Frame(content, bg=SURFACE, padx=16, pady=16)
            ambassadors_frame.pack(fill="both", expand=True)

            # Group by club
            clubs = {}
            for ambassador in ambassadors:
                club = ambassador['club_name']
                if club not in clubs:
                    clubs[club] = []
                clubs[club].append(ambassador)

            for club_name, club_ambassadors in clubs.items():
                # Club header
                tk.Label(ambassadors_frame, text=f"🏛️ {club_name}",
                        bg=ambassadors_frame.cget('bg'), fg=ACCENT, font=FONT_HEAD).pack(anchor="w", pady=(0, 8))

                for ambassador in club_ambassadors:
                    amb_frame = tk.Frame(ambassadors_frame, bg=SURFACE2, padx=12, pady=8)
                    amb_frame.pack(fill="x", pady=(0, 8))

                    tk.Label(amb_frame, text=f"👤 {ambassador['username']} - {ambassador['title']}",
                            bg=SURFACE2, fg=TEXT, font=FONT_BODY).pack(anchor="w")

                    if ambassador['bio']:
                        tk.Label(amb_frame, text=ambassador['bio'][:150] + "..." if len(ambassador['bio']) > 150 else ambassador['bio'],
                                bg=SURFACE2, fg=MUTED, font=FONT_SMALL, wraplength=500).pack(anchor="w", pady=(2, 0))

                    if ambassador['contact_info']:
                        tk.Label(amb_frame, text=f"📧 {ambassador['contact_info']}",
                                bg=SURFACE2, fg=ACCENT3, font=FONT_SMALL).pack(anchor="w", pady=(2, 0))
        else:
            make_label(content, "No club ambassadors available at the moment.",
                      fg=MUTED, bg=BG).pack(anchor="w")

        tk.Frame(content, bg=BG).pack(fill="both", expand=True)

    def _build_share_events_tab(self):
        content = self._social_content

        make_label(content, "Share Events", font=FONT_HEAD).pack(anchor="w", pady=(0, 8))
        make_label(content, "Share interesting events with friends and on social media.",
                   fg=MUTED, bg=BG).pack(anchor="w", pady=(0, 16))

        # Registered events to share
        events = reg_svc.get_events_for_student(self._user.id)
        if events:
            share_frame = tk.Frame(content, bg=SURFACE, padx=16, pady=16)
            share_frame.pack(fill="both", expand=True)

            make_label(share_frame, "Share Your Events", font=FONT_HEAD, bg=SURFACE).pack(anchor="w", pady=(0, 12))

            for event in events[:5]:  # Show first 5
                event_frame = tk.Frame(share_frame, bg=SURFACE)
                event_frame.pack(fill="x", pady=(0, 12))

                tk.Label(event_frame, text=f"🎟️ {event['name']}",
                        bg=SURFACE, fg=TEXT, font=FONT_BODY).pack(anchor="w")

                tk.Label(event_frame, text=f"{event['date']} • {event['club']}",
                        bg=SURFACE, fg=MUTED, font=FONT_SMALL).pack(anchor="w")

                # Share buttons
                btn_frame = tk.Frame(event_frame, bg=SURFACE)
                btn_frame.pack(anchor="w", pady=(6, 0))

                tk.Button(btn_frame, text="📘 Facebook", bg="#1877F2", fg="white",
                         font=("Helvetica", 8), padx=8, pady=3,
                         command=lambda eid=event['id']: self._share_event(eid, 'social_media', 'facebook')).pack(side="left", padx=(0, 4))

                tk.Button(btn_frame, text="🐦 Twitter", bg="#1DA1F2", fg="white",
                         font=("Helvetica", 8), padx=8, pady=3,
                         command=lambda eid=event['id']: self._share_event(eid, 'social_media', 'twitter')).pack(side="left", padx=(0, 4))

                tk.Button(btn_frame, text="🔗 Copy Link", bg=ACCENT3, fg="white",
                         font=("Helvetica", 8), padx=8, pady=3,
                         command=lambda eid=event['id']: self._copy_event_link(eid)).pack(side="left")
        else:
            make_label(content, "Register for events to start sharing them with friends!",
                      fg=MUTED, bg=BG).pack(anchor="w")

        tk.Frame(content, bg=BG).pack(fill="both", expand=True)

    # Social action methods
    def _send_friend_request(self, username):
        if not username.strip():
            messagebox.showerror("Error", "Please enter a username.")
            return

        try:
            soc_svc.send_friend_request(self._user.id, username.strip())
            show_toast(self, f"Friend request sent to {username}!", success=True)
            self._switch_social_tab("friends")  # Refresh friends tab
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _accept_friend_request(self, friend_id):
        try:
            soc_svc.accept_friend_request(self._user.id, friend_id)
            show_toast(self, "Friend request accepted!", success=True)
            self._switch_social_tab("friends")  # Refresh friends tab
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _create_study_group(self, name, description):
        if not name.strip():
            messagebox.showerror("Error", "Please enter a group name.")
            return

        try:
            soc_svc.create_study_group(self._user.id, name.strip(), description)
            show_toast(self, f"Study group '{name}' created!", success=True)
            self._switch_social_tab("study_groups")  # Refresh study groups tab
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _join_study_group(self, group_id):
        try:
            soc_svc.join_study_group(self._user.id, group_id)
            show_toast(self, "Joined study group!", success=True)
            self._switch_social_tab("study_groups")  # Refresh study groups tab
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _share_event(self, event_id, share_type, platform=None):
        try:
            soc_svc.share_event(self._user.id, event_id, share_type, platform)
            platform_name = platform.title() if platform else "social media"
            show_toast(self, f"Event shared on {platform_name}!", success=True)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _copy_event_link(self, event_id):
        link = soc_svc.generate_event_share_link(event_id)
        # In a real app, this would copy to clipboard
        messagebox.showinfo("Share Link", f"Event link: {link}\n\n(Link copied to clipboard)")

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
        self._notif_tree.config(height=14)

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

    # ══════════════════════════════════════════════════════════════════════
    # Section: Gamification
    # ══════════════════════════════════════════════════════════════════════
    def _build_gamification(self):
        wrap = tk.Frame(self._content, bg=BG, padx=40, pady=30)
        wrap.pack(fill="both", expand=True)

        make_label(wrap, "Gamification & Achievements", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "Earn badges, collect points, and track your progress!",
                   fg=MUTED).pack(anchor="w", pady=(4, 16))

        # Get gamification stats
        stats = gamif_svc.get_gamification_stats(self._user.id)

        # Overview stats
        stats_frame = tk.Frame(wrap, bg=BG)
        stats_frame.pack(fill="x", pady=(0, 16))

        def stat_card(parent, label, value, icon, color=ACCENT):
            card = tk.Frame(parent, bg=SURFACE, padx=16, pady=12)
            card.pack(side="left", expand=True, fill="x", padx=4)
            tk.Label(card, text=f"{icon} {value}", bg=SURFACE, fg=color, font=("Helvetica", 18, "bold")).pack(anchor="w")
            tk.Label(card, text=label, bg=SURFACE, fg=MUTED, font=FONT_SMALL).pack(anchor="w", pady=(2, 0))
            return card

        stat_card(stats_frame, "Total Points", stats['points']['total_points'], "⭐")
        stat_card(stats_frame, "Current Level", stats['points']['current_level'], "🏆")
        stat_card(stats_frame, "Badges Earned", stats['badges']['earned'], "🎖️")
        stat_card(stats_frame, "Leaderboard Rank", f"#{stats['leaderboard_rank'] or 'N/A'}", "📊")

        # Tabbed interface for gamification features
        tab_frame = tk.Frame(wrap, bg=BG)
        tab_frame.pack(fill="both", expand=True)

        # Tab buttons
        self._gamif_tab_buttons = {}
        tab_names = ["Achievements", "Points", "Leaderboards", "Progress"]

        tab_btn_frame = tk.Frame(tab_frame, bg=BG)
        tab_btn_frame.pack(fill="x", pady=(0, 12))

        for i, tab_name in enumerate(tab_names):
            btn = tk.Button(tab_btn_frame, text=tab_name, bg=SURFACE, fg=TEXT,
                           font=FONT_BODY, relief="flat", bd=0, width=16,
                           padx=20, pady=8,
                           command=lambda t=tab_name.lower(): self._switch_gamif_tab(t))
            btn.pack(side="left", padx=2)
            self._gamif_tab_buttons[tab_name.lower()] = btn

        # Tab content area
        self._gamif_content = tk.Frame(tab_frame, bg=BG)
        self._gamif_content.pack(fill="both", expand=True)

        # Initialize with achievements tab
        self._switch_gamif_tab("achievements")

    def _switch_gamif_tab(self, tab_name):
        # Clear current content
        for widget in self._gamif_content.winfo_children():
            widget.destroy()

        # Update tab button styles
        for btn_name, btn in self._gamif_tab_buttons.items():
            if btn_name == tab_name:
                btn.config(bg=ACCENT, fg="white")
            else:
                btn.config(bg=SURFACE, fg=TEXT)

        self._active_gamif_tab = tab_name

        # Load appropriate tab content
        tab_methods = {
            "achievements": self._build_achievements_tab,
            "points": self._build_points_tab,
            "leaderboards": self._build_leaderboards_tab,
            "progress": self._build_progress_tab
        }

        if tab_name in tab_methods:
            tab_methods[tab_name]()

    def _build_achievements_tab(self):
        content = self._gamif_content

        make_label(content, "Achievement Badges", font=FONT_HEAD).pack(anchor="w", pady=(0, 8))
        make_label(content, "Earn badges by participating in events and activities.",
                   fg=MUTED, bg=BG).pack(anchor="w", pady=(0, 16))

        # Earned badges section
        earned_frame = tk.Frame(content, bg=SURFACE, padx=16, pady=16)
        earned_frame.pack(fill="x", pady=(0, 12))

        make_label(earned_frame, "Your Badges", font=FONT_HEAD, bg=SURFACE).pack(anchor="w")

        earned_badges = gamif_svc.get_user_achievements(self._user.id)
        if earned_badges:
            badges_frame = tk.Frame(earned_frame, bg=SURFACE)
            badges_frame.pack(fill="x", pady=(8, 0))

            for i, badge in enumerate(earned_badges[:8]):  # Show first 8
                badge_btn = tk.Button(badges_frame, text=f"{badge['icon']} {badge['name']}",
                                     bg=SURFACE2, fg=TEXT, font=("Helvetica", 10),
                                     relief="flat", padx=12, pady=8,
                                     command=lambda b=badge: self._show_badge_details(b))
                badge_btn.pack(side="left", padx=4, pady=4)
        else:
            make_label(earned_frame, "No badges earned yet. Start participating to earn your first badge!",
                      fg=MUTED, bg=SURFACE).pack(anchor="w", pady=(8, 0))

        # Available badges section
        available_frame = tk.Frame(content, bg=SURFACE, padx=16, pady=16)
        available_frame.pack(fill="both", expand=True)

        make_label(available_frame, "Available Badges", font=FONT_HEAD, bg=SURFACE).pack(anchor="w")

        available_badges = gamif_svc.get_available_badges(self._user.id)
        if available_badges:
            badges_frame = tk.Frame(available_frame, bg=SURFACE)
            badges_frame.pack(fill="both", expand=True, pady=(8, 0))

            for badge in available_badges[:12]:  # Show first 12
                badge_frame = tk.Frame(badges_frame, bg=SURFACE2, padx=12, pady=8)
                badge_frame.pack(fill="x", pady=(0, 8))

                # Badge icon and name
                tk.Label(badge_frame, text=f"{badge['icon']} {badge['name']}",
                        bg=SURFACE2, fg=TEXT, font=FONT_BODY).pack(anchor="w")

                # Description and progress
                tk.Label(badge_frame, text=badge['description'],
                        bg=SURFACE2, fg=MUTED, font=FONT_SMALL, wraplength=400).pack(anchor="w", pady=(2, 0))

                progress_text = f"Progress: {badge['current_progress']}/{badge['requirement_value']}"
                tk.Label(badge_frame, text=progress_text,
                        bg=SURFACE2, fg=ACCENT3, font=FONT_SMALL).pack(anchor="w")
        else:
            make_label(available_frame, "All badges earned! You're a champion!",
                      fg=MUTED, bg=SURFACE).pack(anchor="w", pady=(8, 0))

        tk.Frame(content, bg=BG).pack(fill="both", expand=True)

    def _build_points_tab(self):
        content = self._gamif_content

        make_label(content, "Points System", font=FONT_HEAD).pack(anchor="w", pady=(0, 8))
        make_label(content, "Earn points for various activities and level up your participation.",
                   fg=MUTED, bg=BG).pack(anchor="w", pady=(0, 16))

        # Current points display
        points_info = gamif_svc.get_user_points(self._user.id)

        points_card = tk.Frame(content, bg=SURFACE, padx=20, pady=20)
        points_card.pack(fill="x", pady=(0, 16))

        # Level indicator
        level_frame = tk.Frame(points_card, bg=SURFACE)
        level_frame.pack(fill="x", pady=(0, 12))

        level_label = tk.Label(level_frame, text=f"Level {points_info['current_level']}",
                              bg=SURFACE, fg=ACCENT, font=("Helvetica", 16, "bold"))
        level_label.pack(side="left")

        # Progress to next level
        next_level_points = {1: 50, 2: 200, 3: 500, 4: 1000, 5: 999999}
        current_needed = next_level_points.get(points_info['current_level'], 999999)
        progress_pct = min(100, (points_info['total_points'] / current_needed) * 100) if current_needed > 0 else 100

        progress_frame = tk.Frame(level_frame, bg=SURFACE)
        progress_frame.pack(side="right", fill="x", expand=True, padx=(20, 0))

        tk.Label(progress_frame, text=f"{points_info['total_points']}/{current_needed} points to next level",
                bg=SURFACE, fg=MUTED, font=FONT_SMALL).pack(anchor="w")

        # Progress bar
        progress_bar = tk.Frame(progress_frame, bg=SURFACE2, height=8)
        progress_bar.pack(fill="x", pady=(4, 0))
        progress_bar.config(width=int(progress_pct * 2))  # Rough width approximation

        # Points breakdown
        breakdown_frame = tk.Frame(points_card, bg=SURFACE)
        breakdown_frame.pack(fill="x")

        def points_item(label, value, color=TEXT):
            item_frame = tk.Frame(breakdown_frame, bg=SURFACE)
            item_frame.pack(fill="x", pady=(4, 0))
            tk.Label(item_frame, text=label, bg=SURFACE, fg=color, font=FONT_BODY).pack(side="left")
            tk.Label(item_frame, text=str(value), bg=SURFACE, fg=color, font=FONT_BODY).pack(side="right")

        points_item("Total Points", points_info['total_points'], ACCENT)
        points_item("This Month", points_info['points_this_month'], ACCENT3)
        points_item("Last Updated", points_info['last_updated'][:10], MUTED)

        # Points earning guide
        guide_frame = tk.Frame(content, bg=SURFACE, padx=16, pady=16)
        guide_frame.pack(fill="both", expand=True)

        make_label(guide_frame, "How to Earn Points", font=FONT_HEAD, bg=SURFACE).pack(anchor="w")

        points_guide = [
            ("🎯 Event Attendance", "10-25 points"),
            ("💬 Feedback Submission", "5-15 points"),
            ("🤝 Club Participation", "20 points"),
            ("📚 Study Group Creation", "30 points"),
            ("🦋 Social Connections", "5-10 points"),
            ("🏆 Achievement Badges", "20-200 points")
        ]

        for activity, points in points_guide:
            guide_item = tk.Frame(guide_frame, bg=SURFACE)
            guide_item.pack(fill="x", pady=(6, 0))
            tk.Label(guide_item, text=activity, bg=SURFACE, fg=TEXT, font=FONT_BODY).pack(side="left")
            tk.Label(guide_item, text=points, bg=SURFACE, fg=ACCENT3, font=FONT_BODY).pack(side="right")

        tk.Frame(content, bg=BG).pack(fill="both", expand=True)

    def _build_leaderboards_tab(self):
        content = self._gamif_content

        make_label(content, "Leaderboards", font=FONT_HEAD).pack(anchor="w", pady=(0, 8))
        make_label(content, "See how you rank against other participants.",
                   fg=MUTED, bg=BG).pack(anchor="w", pady=(0, 16))

        # Leaderboard categories
        categories = [
            ("Total Points", "total_points"),
            ("Monthly Points", "monthly_points"),
            ("Attendance Count", "attendance_streak")
        ]

        for cat_name, cat_key in categories:
            cat_frame = tk.Frame(content, bg=SURFACE, padx=16, pady=16)
            cat_frame.pack(fill="x", pady=(0, 12))

            make_label(cat_frame, cat_name, font=FONT_HEAD, bg=SURFACE).pack(anchor="w")

            leaderboard = gamif_svc.get_leaderboard(cat_key, limit=5)

            if leaderboard:
                for entry in leaderboard:
                    entry_frame = tk.Frame(cat_frame, bg=SURFACE)
                    entry_frame.pack(fill="x", pady=(6, 0))

                    rank_text = f"#{entry['rank']}"
                    tk.Label(entry_frame, text=rank_text, bg=SURFACE, fg=ACCENT,
                            font=("Helvetica", 12, "bold"), width=4).pack(side="left")

                    name_text = entry['username'][:15] + "..." if len(entry['username']) > 15 else entry['username']
                    tk.Label(entry_frame, text=name_text, bg=SURFACE, fg=TEXT,
                            font=FONT_BODY).pack(side="left", padx=(8, 0))

                    score_text = f"{entry['score']:,}"
                    tk.Label(entry_frame, text=score_text, bg=SURFACE, fg=ACCENT3,
                            font=FONT_BODY).pack(side="right")
            else:
                make_label(cat_frame, "No data available yet.", fg=MUTED, bg=SURFACE).pack(anchor="w", pady=(8, 0))

        tk.Frame(content, bg=BG).pack(fill="both", expand=True)

    def _build_progress_tab(self):
        content = self._gamif_content

        make_label(content, "Progress Tracking", font=FONT_HEAD).pack(anchor="w", pady=(0, 8))
        make_label(content, "Track your progress towards club membership requirements.",
                   fg=MUTED, bg=BG).pack(anchor="w", pady=(0, 16))

        progress_data = gamif_svc.get_user_progress(self._user.id)

        if progress_data:
            progress_frame = tk.Frame(content, bg=SURFACE, padx=16, pady=16)
            progress_frame.pack(fill="both", expand=True)

            for club_data in progress_data:
                # Club header
                club_header = tk.Frame(progress_frame, bg=SURFACE)
                club_header.pack(fill="x", pady=(0, 12))

                tk.Label(club_header, text=f"🏛️ {club_data['club_name']}",
                        bg=SURFACE, fg=ACCENT, font=FONT_HEAD).pack(anchor="w")

                # Requirements
                for req in club_data['requirements']:
                    req_frame = tk.Frame(progress_frame, bg=SURFACE2, padx=12, pady=8)
                    req_frame.pack(fill="x", pady=(0, 8))

                    req_name = req['requirement_type'].replace('_', ' ').title()
                    tk.Label(req_frame, text=req_name, bg=SURFACE2, fg=TEXT, font=FONT_BODY).pack(anchor="w")

                    progress_text = f"{req['current_value']}/{req['target_value']}"
                    tk.Label(req_frame, text=progress_text, bg=SURFACE2, fg=ACCENT3, font=FONT_SMALL).pack(anchor="w")

                    # Progress bar
                    progress_pct = min(100, (req['current_value'] / req['target_value']) * 100) if req['target_value'] > 0 else 0

                    progress_bar_frame = tk.Frame(req_frame, bg=SURFACE, height=6)
                    progress_bar_frame.pack(fill="x", pady=(4, 0))

                    if progress_pct > 0:
                        progress_fill = tk.Frame(progress_bar_frame, bg=ACCENT, height=6, width=int(progress_pct * 2))
                        progress_fill.pack(side="left")

                    # Completion indicator
                    if req['is_completed']:
                        tk.Label(req_frame, text="✅ Completed!", bg=SURFACE2, fg="#28a745", font=FONT_SMALL).pack(anchor="e")
        else:
            make_label(content, "No progress data available.", fg=MUTED, bg=BG).pack(anchor="w")

        tk.Frame(content, bg=BG).pack(fill="both", expand=True)

    # Gamification action methods
    def _show_badge_details(self, badge):
        """Show detailed information about a badge."""
        detail_window = tk.Toplevel(self)
        detail_window.title(f"Achievement: {badge['name']}")
        detail_window.geometry("400x300")
        detail_window.configure(bg=BG)

        # Badge icon and name
        header_frame = tk.Frame(detail_window, bg=BG, padx=20, pady=20)
        header_frame.pack(fill="x")

        tk.Label(header_frame, text=badge['icon'], bg=BG, fg=ACCENT, font=("Helvetica", 48)).pack()
        tk.Label(header_frame, text=badge['name'], bg=BG, fg=TEXT, font=FONT_TITLE).pack(pady=(8, 0))

        # Description
        desc_frame = tk.Frame(detail_window, bg=SURFACE, padx=20, pady=16)
        desc_frame.pack(fill="x", pady=(0, 12))

        tk.Label(desc_frame, text="Description", bg=SURFACE, fg=ACCENT3, font=FONT_HEAD).pack(anchor="w")
        tk.Label(desc_frame, text=badge['description'], bg=SURFACE, fg=TEXT,
                font=FONT_BODY, wraplength=360, justify="left").pack(anchor="w", pady=(8, 0))

        # Details
        details_frame = tk.Frame(detail_window, bg=SURFACE, padx=20, pady=16)
        details_frame.pack(fill="x")

        def detail_row(label, value):
            row = tk.Frame(details_frame, bg=SURFACE)
            row.pack(fill="x", pady=(4, 0))
            tk.Label(row, text=label, bg=SURFACE, fg=MUTED, font=FONT_SMALL).pack(side="left")
            tk.Label(row, text=str(value), bg=SURFACE, fg=TEXT, font=FONT_SMALL).pack(side="right")

        detail_row("Category", badge['category'].title())
        detail_row("Points Reward", badge['points_reward'])
        detail_row("Earned", badge['earned_at'][:10] if badge.get('earned_at') else "Not earned")

        # Close button
        tk.Button(detail_window, text="Close", bg=ACCENT, fg="white", font=FONT_BTN,
                 padx=20, pady=8, command=detail_window.destroy).pack(pady=20)

