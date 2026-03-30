"""
Admin Dashboard
───────────────
Three sections reachable via the sidebar:
  • Add Event
  • Manage Events  (edit + delete)
  • View Registrations

Everything is wired up — no dead buttons.
"""
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import csv
import calendar
from datetime import date, datetime
import services.event_service as event_svc
import services.club_service as club_svc
import services.registration_service as reg_svc
import services.attendance_service as att_svc
import services.user_service as user_svc
import services.notification_service as notif_svc
from ui.components import (
    BG, SURFACE, SURFACE2, ACCENT, ACCENT2, ACCENT3,
    TEXT, MUTED, BORDER, FONT_TITLE, FONT_HEAD, FONT_BODY, FONT_BTN, FONT_SMALL,
    make_frame, make_label, make_entry, make_button, make_treeview, show_toast,
    apply_global_style,
)


class AdminDashboard(tk.Frame):
    def __init__(self, parent, user, on_logout):
        super().__init__(parent, bg=BG)
        self._user = user
        self._on_logout = on_logout
        self._active_section = None
        self._build()
        self._show_section("dashboard")

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

        # branding
        tk.Label(sidebar, text="⚙  Admin Panel", bg=SURFACE, fg=TEXT,
                 font=FONT_HEAD, pady=20).pack(fill="x", padx=16)
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=16)

        tk.Label(sidebar, text=f"Hi, {self._user.username}",
                 bg=SURFACE, fg=MUTED, font=FONT_SMALL).pack(anchor="w", padx=16, pady=(8, 0))
        tk.Label(sidebar, text="Administrator",
                 bg=SURFACE, fg=ACCENT, font=("Helvetica", 8, "bold")).pack(anchor="w", padx=16, pady=(0, 12))
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=16)

        # nav buttons
        self._nav_btns = {}
        nav_items = [
            ("📊  Dashboard",        "dashboard"),
            ("📅  Events",           "manage_events"),
            ("📣  Announcements",    "announcements"),
            ("📈  Reports",          "reports"),
            ("�  Registrations",    "registrations"),
            ("�👥  Members",          "members"),
            ("🏛  Clubs",            "clubs"),
            ("📝  Attendance",      "attendance"),
            ("📆  Calendar",        "event_calendar"),
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

        # logout at bottom
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
        # update sidebar highlight
        for k, btn in self._nav_btns.items():
            btn.config(bg=ACCENT if k == key else SURFACE)
        self._active_section = key

        # clear content
        for widget in self._content.winfo_children():
            widget.destroy()

        # render section
        builders = {
            "dashboard":          self._build_dashboard,
            "manage_events":      self._build_manage_events,
            "add_event":          self._build_add_event,
            "registrations":      self._build_view_registrations,
            "announcements":      self._build_announcements,
            "reports":            self._build_reports,
            "members":            self._build_members,
            "clubs":              self._build_clubs,
            "attendance":         self._build_attendance,
            "event_calendar":     self._build_event_calendar,
        }
        builders[key]()

    # ══════════════════════════════════════════════════════════════════════
    # Section: Dashboard
    # ══════════════════════════════════════════════════════════════════════
    def _build_dashboard(self):
        wrap = tk.Frame(self._content, bg=BG, padx=24, pady=20)
        wrap.pack(fill="both", expand=True)

        make_label(wrap, "Dashboard", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "Welcome to College CMS Admin", fg=MUTED).pack(anchor="w", pady=(2, 10))

        card_row = tk.Frame(wrap, bg=BG)
        card_row.pack(fill="x", pady=(10, 18))

        def card(parent, title, value, subtitle, accent):
            frame = tk.Frame(parent, bg=SURFACE, bd=0, highlightthickness=0)
            frame.pack(side="left", expand=True, fill="x", padx=6)
            tk.Label(frame, text=title, bg=SURFACE, fg=MUTED, font=("Helvetica", 9)).pack(anchor="w", padx=10, pady=(10, 0))
            tk.Label(frame, text=value, bg=SURFACE, fg=accent, font=("Helvetica", 24, "bold")).pack(anchor="w", padx=10, pady=(2, 0))
            tk.Label(frame, text=subtitle, bg=SURFACE, fg=MUTED, font=("Helvetica", 8)).pack(anchor="w", padx=10, pady=(2, 12))
            return frame

        events = event_svc.get_all_events()
        registrations = reg_svc.get_all_registrations()
        attendance_rows = att_svc.get_all_attendance()
        total_events = len(events)
        total_members = user_svc.get_total_members()
        total_clubs = event_svc.get_club_count()
        unmarked_count = len([row for row in attendance_rows if row["status"] == "unmarked"])

        card(card_row, "Total Events", str(total_events), "All scheduled activities", ACCENT)
        card(card_row, "Members", str(total_members), "Registered student accounts", ACCENT3)
        card(card_row, "Clubs", str(total_clubs), "Active student clubs", ACCENT2)
        card(card_row, "Registrations", str(len(registrations)), f"{unmarked_count} attendance marks pending", ACCENT)

        lower = tk.Frame(wrap, bg=BG)
        lower.pack(fill="both", expand=True)

        left = tk.Frame(lower, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = tk.Frame(lower, bg=BG, width=300)
        right.pack(side="left", fill="y")
        right.pack_propagate(False)

        make_label(left, "Recent Events", font=FONT_HEAD).pack(anchor="w")
        make_label(left, "Overview of your latest events", fg=MUTED).pack(anchor="w", pady=(0, 10))
        cols = ("Event Name", "Date", "Club", "Status")
        tv_frame, tv = make_treeview(left, cols)
        tv_frame.pack(fill="both", expand=True)

        today_iso = date.today().isoformat()
        for ev in events[:5]:
            status = "upcoming" if ev.date >= today_iso else "completed"
            tv.insert("", "end", values=(ev.name, ev.date, ev.club, status))

        make_button(left, "+ Add Event", lambda: self._show_section("add_event"), color=ACCENT, width=12).pack(anchor="e", pady=(8, 0))

        action_card = tk.Frame(right, bg=SURFACE, padx=14, pady=14,
                               highlightthickness=1, highlightbackground=BORDER)
        action_card.pack(fill="x", pady=(0, 12))
        make_label(action_card, "Quick Actions", font=FONT_HEAD, bg=SURFACE).pack(anchor="w")
        make_label(action_card, "Open the most-used admin tools", fg=MUTED, bg=SURFACE).pack(anchor="w", pady=(0, 10))

        action_grid = tk.Frame(action_card, bg=SURFACE)
        action_grid.pack(fill="x")
        action_grid.columnconfigure(0, weight=1)
        action_grid.columnconfigure(1, weight=1)
        make_button(action_grid, "Add Event", lambda: self._show_section("add_event"), color=ACCENT, width=12).grid(row=0, column=0, padx=(0, 8), pady=(0, 8), sticky="ew")
        make_button(action_grid, "Registrations", lambda: self._show_section("registrations"), color=ACCENT3, width=12).grid(row=0, column=1, pady=(0, 8), sticky="ew")
        make_button(action_grid, "Announcements", lambda: self._show_section("announcements"), color=ACCENT, width=12).grid(row=1, column=0, padx=(0, 8), pady=(0, 8), sticky="ew")
        make_button(action_grid, "Reports", lambda: self._show_section("reports"), color=ACCENT3, width=12).grid(row=1, column=1, pady=(0, 8), sticky="ew")
        make_button(action_grid, "Attendance", lambda: self._show_section("attendance"), color=SURFACE2, width=12).grid(row=2, column=0, padx=(0, 8), sticky="ew")
        make_button(action_grid, "Calendar", lambda: self._show_section("event_calendar"), color=SURFACE2, width=12).grid(row=2, column=1, sticky="ew")

        insight_card = tk.Frame(right, bg=SURFACE, padx=14, pady=14,
                                highlightthickness=1, highlightbackground=BORDER)
        insight_card.pack(fill="both", expand=True)
        make_label(insight_card, "Event Highlights", font=FONT_HEAD, bg=SURFACE).pack(anchor="w")
        make_label(insight_card, "Upcoming activity and club momentum", fg=MUTED, bg=SURFACE).pack(anchor="w", pady=(0, 10))

        summary_map = {
            row["event_name"]: row["total_registered"]
            for row in reg_svc.get_registration_summary()
        }
        upcoming_events = []
        today = date.today()
        for ev in events:
            try:
                event_day = datetime.strptime(ev.date, "%Y-%m-%d").date()
            except ValueError:
                continue
            if event_day >= today:
                upcoming_events.append((event_day, ev))
        upcoming_events.sort(key=lambda item: item[0])

        if upcoming_events:
            for event_day, ev in upcoming_events[:3]:
                days_left = (event_day - today).days
                when_text = "Today" if days_left == 0 else "Tomorrow" if days_left == 1 else f"In {days_left} days"
                tk.Label(
                    insight_card,
                    text=f"• {ev.name}\n  {ev.date} • {ev.club}\n  {summary_map.get(ev.name, 0)} registration(s) • {when_text}",
                    bg=SURFACE,
                    fg=TEXT,
                    font=FONT_SMALL,
                    justify="left",
                    anchor="w",
                    wraplength=250,
                ).pack(anchor="w", fill="x", pady=(0, 8))
        else:
            make_label(insight_card, "No upcoming events yet. Add one to get started.",
                       fg=MUTED, bg=SURFACE).pack(anchor="w")

        tk.Frame(insight_card, bg=BORDER, height=1).pack(fill="x", pady=8)
        make_label(insight_card, "Top Clubs", font=FONT_SMALL, fg=ACCENT, bg=SURFACE).pack(anchor="w", pady=(0, 6))
        club_summary = event_svc.get_club_summary()[:3]
        if club_summary:
            for club in club_summary:
                make_label(
                    insight_card,
                    f"{club['club']} • {club['event_count']} event(s)",
                    fg=TEXT,
                    bg=SURFACE,
                    font=FONT_SMALL,
                ).pack(anchor="w", pady=(0, 4))
        else:
            make_label(insight_card, "Club activity will appear here once events are added.",
                       fg=MUTED, bg=SURFACE, font=FONT_SMALL).pack(anchor="w")

    # ══════════════════════════════════════════════════════════════════════
    # Section: Members
    # ══════════════════════════════════════════════════════════════════════
    def _build_members(self):
        wrap = tk.Frame(self._content, bg=BG, padx=40, pady=30)
        wrap.pack(fill="both", expand=True)
        make_label(wrap, "Members", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "List of registered students", fg=MUTED).pack(anchor="w", pady=(4, 16))
        cols = ("Name", "Email", "Role")
        tv_frame, members_tree = make_treeview(wrap, cols)
        tv_frame.pack(fill="both", expand=True)
        for m in user_svc.get_all_members():
            members_tree.insert("", "end", values=(m["username"], m["email"], m["role"]))

    # ══════════════════════════════════════════════════════════════════════
    # Section: Clubs
    # ══════════════════════════════════════════════════════════════════════
    def _build_clubs(self):
        wrap = tk.Frame(self._content, bg=BG, padx=40, pady=30)
        wrap.pack(fill="both", expand=True)
        make_label(wrap, "Clubs", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "Create and manage clubs", fg=MUTED).pack(anchor="w", pady=(4, 16))

        form = tk.Frame(wrap, bg=SURFACE, padx=16, pady=16,
                        highlightthickness=1, highlightbackground=BORDER)
        form.pack(fill="x", pady=(0, 12))

        tk.Label(form, text="Club Name", bg=SURFACE, fg=MUTED,
                 font=("Helvetica", 9, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(form, text="Description", bg=SURFACE, fg=MUTED,
                 font=("Helvetica", 9, "bold")).grid(row=0, column=1, sticky="w", padx=(10, 0))

        self._club_name_entry = make_entry(form, width=26)
        self._club_name_entry.grid(row=1, column=0, sticky="we", pady=(4, 0))
        self._club_desc_entry = make_entry(form, width=44)
        self._club_desc_entry.grid(row=1, column=1, sticky="we", padx=(10, 0), pady=(4, 0))

        btn_row = tk.Frame(form, bg=SURFACE)
        btn_row.grid(row=1, column=2, padx=(12, 0), sticky="e")
        make_button(btn_row, "➕ Add Club", self._submit_add_club, width=12).pack(side="left")
        make_button(btn_row, "🔄 Refresh", self._load_clubs, color=SURFACE2, width=10).pack(side="left", padx=(8, 0))

        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        cols = ("Name", "Description", "Created")
        tv_frame, self._clubs_tree = make_treeview(wrap, cols)
        tv_frame.pack(fill="both", expand=True)
        self._clubs_tree.column("Description", width=360, anchor="w")
        self._clubs_tree.column("Name", width=180, anchor="w")

        self._load_clubs()

        # action buttons
        btn_row = tk.Frame(wrap, bg=BG)
        btn_row.pack(fill="x", pady=(12, 0))
        make_button(btn_row, "✏️  Edit Selected", self._edit_club,
                    color=ACCENT, width=16).pack(side="left", padx=(0, 8))
        make_button(btn_row, "🗑  Delete Selected", self._delete_club,
                    color=ACCENT2, width=16).pack(side="left")

    def _load_clubs(self):
        self._clubs_tree.delete(*self._clubs_tree.get_children())
        for club in club_svc.get_all_clubs():
            self._clubs_tree.insert(
                "",
                "end",
                values=(club["name"], club.get("description", ""), club["created_at"]),
            )

    def _submit_add_club(self):
        name = self._club_name_entry.get().strip()
        description = self._club_desc_entry.get().strip()
        try:
            club_svc.add_club(name, description)
            self._club_name_entry.delete(0, "end")
            self._club_desc_entry.delete(0, "end")
            self._load_clubs()
            show_toast(self, "Club added successfully!", success=True)
        except ValueError as exc:
            messagebox.showwarning("Add Club", str(exc))

    def _get_selected_club(self):
        sel = self._clubs_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a club first.")
            return None
        return self._clubs_tree.item(sel[0])["values"]   # [name, description, created_at]

    def _edit_club(self):
        row = self._get_selected_club()
        if row is None:
            return
        name, description, created_at = row
        self._open_club_edit_dialog(name, description)

    def _delete_club(self):
        row = self._get_selected_club()
        if row is None:
            return
        name = row[0]
        if messagebox.askyesno("Confirm Delete", f"Delete club '{name}'? This will remove the club from the system."):
            try:
                club_svc.delete_club(name)
                show_toast(self, f"'{name}' deleted.", success=False)
                self._load_clubs()
            except Exception as e:
                messagebox.showerror("Delete Error", str(e))

    def _open_club_edit_dialog(self, name, description):
        dlg = tk.Toplevel(self)
        dlg.title("Edit Club")
        dlg.configure(bg=SURFACE)
        dlg.geometry("400x260")
        dlg.resizable(False, False)
        dlg.grab_set()

        tk.Label(dlg, text="Edit Club", bg=SURFACE, fg=TEXT,
                 font=FONT_HEAD).pack(pady=(20, 10))

        labels_vals = [("Club Name", name), ("Description", description)]
        entries = []
        for lbl, val in labels_vals:
            tk.Label(dlg, text=lbl, bg=SURFACE, fg=MUTED,
                     font=("Helvetica", 9, "bold"), anchor="w").pack(fill="x", padx=30)
            en = make_entry(dlg, width=38)
            en.insert(0, val)
            en.pack(fill="x", padx=30, pady=(2, 8))
            entries.append(en)

        # Name field should be read-only
        entries[0].config(state="readonly")

        err_var = tk.StringVar()
        tk.Label(dlg, textvariable=err_var, bg=SURFACE, fg=ACCENT2,
                 font=FONT_SMALL).pack()

        def _save():
            try:
                new_desc = entries[1].get()
                club_svc.update_club(name, new_desc)
                show_toast(self, "Club updated!", success=True)
                self._load_clubs()
                dlg.destroy()
            except ValueError as exc:
                err_var.set(str(exc))

        make_button(dlg, "💾  Save Changes", _save, width=20).pack(pady=12)

    # ══════════════════════════════════════════════════════════════════════
    # Section: Add Event
    # ══════════════════════════════════════════════════════════════════════
    def _build_add_event(self):
        wrap = tk.Frame(self._content, bg=BG, padx=40, pady=30)
        wrap.pack(fill="both", expand=True)

        make_label(wrap, "Add New Event", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "Fill in the details below to create an event.",
                   fg=MUTED).pack(anchor="w", pady=(4, 24))

        card = tk.Frame(wrap, bg=SURFACE, padx=30, pady=30,
                        highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="x", ipadx=10, ipady=10)

        fields = [
            ("Event Name",  "e.g. Tech Fest 2026"),
            ("Date",        "YYYY-MM-DD"),
        ]
        entries = []
        for label, placeholder in fields:
            tk.Label(card, text=label, bg=SURFACE, fg=MUTED,
                     font=("Helvetica", 9, "bold"), anchor="w").pack(fill="x", pady=(6, 2))
            entry = make_entry(card, width=40)
            entry.pack(fill="x", pady=(0, 4))
            # placeholder hint
            entry.insert(0, placeholder)
            entry.config(fg=MUTED)
            entry.bind("<FocusIn>",  lambda e, en=entry, ph=placeholder: self._clear_ph(en, ph))
            entry.bind("<FocusOut>", lambda e, en=entry, ph=placeholder: self._restore_ph(en, ph))
            entries.append(entry)

        self._ae_name, self._ae_date = entries

        tk.Label(card, text="Club", bg=SURFACE, fg=MUTED,
                 font=("Helvetica", 9, "bold"), anchor="w").pack(fill="x", pady=(8, 2))
        clubs = [club["name"] for club in club_svc.get_all_clubs()]
        self._ae_clubs = clubs
        self._ae_club_var = tk.StringVar(value=(clubs[0] if clubs else ""))
        self._ae_club = ttk.Combobox(
            card,
            textvariable=self._ae_club_var,
            values=clubs,
            state="readonly" if clubs else "disabled",
            font=FONT_BODY,
        )
        self._ae_club.pack(fill="x", pady=(0, 4))

        self._ae_err = tk.StringVar()
        tk.Label(card, textvariable=self._ae_err, bg=SURFACE, fg=ACCENT2,
                 font=FONT_SMALL).pack(anchor="w", pady=(6, 0))

        if not clubs:
            self._ae_err.set("No clubs available. Add a club first in the Clubs section.")

        make_button(card, "➕  Add Event", self._submit_add_event, width=20).pack(anchor="w", pady=(10, 0))

    def _clear_ph(self, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, "end")
            entry.config(fg=TEXT)

    def _restore_ph(self, entry, placeholder):
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(fg=MUTED)

    def _get_entry_val(self, entry, placeholder):
        val = entry.get().strip()
        return "" if val == placeholder else val

    def _submit_add_event(self):
        name = self._get_entry_val(self._ae_name, "e.g. Tech Fest 2026")
        date = self._get_entry_val(self._ae_date, "YYYY-MM-DD")
        club = self._ae_club_var.get().strip()
        if club and club not in self._ae_clubs:
            self._ae_err.set("Please select a valid club from the list.")
            return
        try:
            event_svc.add_event(name, date, club)
            show_toast(self, "✅  Event added successfully!", success=True)
            self._show_section("add_event")   # reset form
        except ValueError as exc:
            self._ae_err.set(str(exc))

    # ══════════════════════════════════════════════════════════════════════
    # Section: Manage Events
    # ══════════════════════════════════════════════════════════════════════
    def _build_manage_events(self):
        wrap = tk.Frame(self._content, bg=BG, padx=40, pady=30)
        wrap.pack(fill="both", expand=True)

        make_label(wrap, "Manage Events", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "Select a row to edit or delete an event.",
                   fg=MUTED).pack(anchor="w", pady=(4, 16))

        action_row = tk.Frame(wrap, bg=BG)
        action_row.pack(fill="x", pady=(0, 8))
        make_button(action_row, "➕  Add Event", lambda: self._show_section("add_event"),
                    color=ACCENT, width=12).pack(side="left")
        make_button(action_row, "🔄  Refresh", self._refresh_events,
                    color=SURFACE2, width=12).pack(side="right")

        # Treeview
        cols = ("ID", "Name", "Date", "Club")
        tv_frame, self._ev_tree = make_treeview(wrap, cols)
        tv_frame.pack(fill="both", expand=True)
        self._ev_tree.column("ID", width=50, anchor="center")

        self._load_events()

        # action buttons
        btn_row = tk.Frame(wrap, bg=BG)
        btn_row.pack(fill="x", pady=(12, 0))

        make_button(btn_row, "✏️  Edit Selected",   self._edit_event,
                    color=ACCENT,  width=16).pack(side="left", padx=(0, 8))
        make_button(btn_row, "🗑  Delete Selected", self._delete_event,
                    color=ACCENT2, width=16).pack(side="left")

    def _load_events(self):
        self._ev_tree.delete(*self._ev_tree.get_children())
        for ev in event_svc.get_all_events():
            self._ev_tree.insert("", "end", iid=ev.id,
                                 values=(ev.id, ev.name, ev.date, ev.club))

    def _refresh_events(self):
        self._load_events()
        show_toast(self, "Events refreshed.", success=True)

    def _get_selected_event(self):
        sel = self._ev_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select an event first.")
            return None
        return self._ev_tree.item(sel[0])["values"]   # [id, name, date, club]

    def _delete_event(self):
        row = self._get_selected_event()
        if row is None:
            return
        event_id, name = row[0], row[1]
        if messagebox.askyesno("Confirm Delete", f"Delete '{name}'? This will also remove all registrations."):
            event_svc.delete_event(event_id)
            show_toast(self, f"'{name}' deleted.", success=False)
            self._load_events()

    def _edit_event(self):
        row = self._get_selected_event()
        if row is None:
            return
        event_id, name, date, club = row
        self._open_edit_dialog(event_id, name, date, club)

    def _open_edit_dialog(self, event_id, name, date, club):
        dlg = tk.Toplevel(self)
        dlg.title("Edit Event")
        dlg.configure(bg=SURFACE)
        dlg.geometry("400x320")
        dlg.resizable(False, False)
        dlg.grab_set()

        tk.Label(dlg, text="Edit Event", bg=SURFACE, fg=TEXT,
                 font=FONT_HEAD).pack(pady=(20, 10))

        labels_vals = [("Event Name", name), ("Date", date), ("Club", club)]
        entries = []
        for lbl, val in labels_vals:
            tk.Label(dlg, text=lbl, bg=SURFACE, fg=MUTED,
                     font=("Helvetica", 9, "bold"), anchor="w").pack(fill="x", padx=30)
            en = make_entry(dlg, width=38)
            en.insert(0, val)
            en.pack(fill="x", padx=30, pady=(2, 8))
            entries.append(en)

        err_var = tk.StringVar()
        tk.Label(dlg, textvariable=err_var, bg=SURFACE, fg=ACCENT2,
                 font=FONT_SMALL).pack()

        def _save():
            try:
                event_svc.update_event(event_id, entries[0].get(),
                                       entries[1].get(), entries[2].get())
                show_toast(self, "Event updated!", success=True)
                self._load_events()
                dlg.destroy()
            except ValueError as exc:
                err_var.set(str(exc))

        make_button(dlg, "💾  Save Changes", _save, width=20).pack(pady=12)

    # ══════════════════════════════════════════════════════════════════════
    # Section: View Registrations
    # ══════════════════════════════════════════════════════════════════════
    def _build_view_registrations(self):
        wrap = tk.Frame(self._content, bg=BG, padx=40, pady=30)
        wrap.pack(fill="both", expand=True)

        make_label(wrap, "All Registrations", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "Every student–event pair in the system.",
                   fg=MUTED).pack(anchor="w", pady=(4, 16))

        action_row = tk.Frame(wrap, bg=BG)
        action_row.pack(fill="x", pady=(0, 8))
        self._reg_count_var = tk.StringVar(value="Total registrations: 0")
        tk.Label(action_row, textvariable=self._reg_count_var,
                 bg=BG, fg=ACCENT3, font=FONT_BODY).pack(side="left")
        make_button(action_row, "⬇ Export CSV", self._export_registrations,
                    color=ACCENT, width=14).pack(side="right", padx=(8, 0))
        make_button(action_row, "🔄  Refresh", self._refresh_regs,
                    color=SURFACE2, width=12).pack(side="right")

        cols = ("Student", "Email", "Event", "Date", "Club")
        tv_frame, self._reg_tree = make_treeview(wrap, cols)
        tv_frame.pack(fill="both", expand=True)
        for col in cols:
            self._reg_tree.column(col, width=110)

        self._load_registrations()

    def _load_registrations(self):
        self._reg_tree.delete(*self._reg_tree.get_children())
        rows = reg_svc.get_all_registrations()
        for r in rows:
            self._reg_tree.insert("", "end",
                                  values=(r["username"], r["email"],
                                          r["event_name"], r["date"], r["club"]))
        self._reg_count_var.set(f"Total registrations: {len(rows)}")

    def _export_registrations(self):
        path = filedialog.asksaveasfilename(
            title="Export Registrations",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*")],
        )
        if not path:
            return

        try:
            rows = reg_svc.get_all_registrations()
            with open(path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["student", "email", "event", "date", "club"])
                for row in rows:
                    writer.writerow([
                        row["username"],
                        row["email"],
                        row["event_name"],
                        row["date"],
                        row["club"],
                    ])
            show_toast(self, "Registrations exported to CSV.", success=True)
        except Exception as exc:
            messagebox.showerror("Export Error", str(exc))

    def _refresh_regs(self):
        self._load_registrations()
        show_toast(self, "Registrations refreshed.", success=True)

    # ══════════════════════════════════════════════════════════════════════
    # Section: Announcements
    # ══════════════════════════════════════════════════════════════════════
    def _build_announcements(self):
        wrap = tk.Frame(self._content, bg=BG, padx=40, pady=30)
        wrap.pack(fill="both", expand=True)

        make_label(wrap, "Announcements", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "Send updates and reminders to students without changing the design.",
                   fg=MUTED).pack(anchor="w", pady=(4, 16))

        announce_card = tk.Frame(wrap, bg=SURFACE, padx=18, pady=18,
                                 highlightthickness=1, highlightbackground=BORDER)
        announce_card.pack(fill="x", pady=(0, 12))
        make_label(announce_card, "Send announcement to all students", font=FONT_HEAD, bg=SURFACE).pack(anchor="w")
        make_label(announce_card, "This message appears in the student Notifications tab.",
                   fg=MUTED, bg=SURFACE).pack(anchor="w", pady=(2, 8))

        self._announcement_text = tk.Text(
            announce_card,
            height=5,
            bg=SURFACE2,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=FONT_BODY,
            wrap="word",
        )
        self._announcement_text.pack(fill="x")
        make_button(announce_card, "📣 Send Announcement", self._send_announcement,
                    color=ACCENT, width=18).pack(anchor="w", pady=(10, 0))

        reminder_card = tk.Frame(wrap, bg=SURFACE, padx=18, pady=18,
                                 highlightthickness=1, highlightbackground=BORDER)
        reminder_card.pack(fill="x")
        make_label(reminder_card, "Send event reminder", font=FONT_HEAD, bg=SURFACE).pack(anchor="w")
        make_label(reminder_card, "Choose an event and notify all registered students.",
                   fg=MUTED, bg=SURFACE).pack(anchor="w", pady=(2, 8))

        self._reminder_event_var = tk.StringVar(value="")
        self._reminder_combo = ttk.Combobox(
            reminder_card,
            textvariable=self._reminder_event_var,
            state="readonly",
            font=FONT_BODY,
        )
        self._reminder_combo.pack(fill="x", pady=(0, 8))

        self._reminder_note = tk.Text(
            reminder_card,
            height=4,
            bg=SURFACE2,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=FONT_BODY,
            wrap="word",
        )
        self._reminder_note.pack(fill="x")

        btn_row = tk.Frame(reminder_card, bg=SURFACE)
        btn_row.pack(fill="x", pady=(10, 0))
        make_button(btn_row, "🔄 Refresh Events", self._load_reminder_events,
                    color=SURFACE2, width=16).pack(side="left")
        make_button(btn_row, "⏰ Send Reminder", self._send_event_reminder,
                    color=ACCENT3, width=16).pack(side="left", padx=(8, 0))

        self._load_reminder_events()

    def _load_reminder_events(self):
        events = event_svc.get_all_events()
        options = [f"{ev.id} | {ev.name} ({ev.date})" for ev in events]
        self._reminder_combo["values"] = options
        if options:
            if self._reminder_event_var.get() not in options:
                self._reminder_event_var.set(options[0])
        else:
            self._reminder_event_var.set("")

    def _send_announcement(self):
        message = self._announcement_text.get("1.0", "end").strip()
        try:
            sent_count = notif_svc.broadcast_notification_to_students(message)
            self._announcement_text.delete("1.0", "end")
            show_toast(self, f"Announcement sent to {sent_count} student(s).", success=True)
        except ValueError as exc:
            messagebox.showwarning("Announcements", str(exc))

    def _send_event_reminder(self):
        selected = self._reminder_event_var.get().strip()
        if not selected:
            messagebox.showwarning("Reminder", "Please choose an event first.")
            return

        try:
            event_id = int(selected.split("|", 1)[0].strip())
            extra_note = self._reminder_note.get("1.0", "end").strip()
            sent_count = notif_svc.send_event_reminder(event_id, extra_note)
            self._reminder_note.delete("1.0", "end")
            show_toast(self, f"Reminder sent to {sent_count} student(s).", success=True)
        except ValueError as exc:
            messagebox.showwarning("Reminder", str(exc))

    # ══════════════════════════════════════════════════════════════════════
    # Section: Reports
    # ══════════════════════════════════════════════════════════════════════
    def _build_reports(self):
        wrap = tk.Frame(self._content, bg=BG, padx=40, pady=30)
        wrap.pack(fill="both", expand=True)

        make_label(wrap, "Reports", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "Review event participation and attendance performance.",
                   fg=MUTED).pack(anchor="w", pady=(4, 16))

        action_row = tk.Frame(wrap, bg=BG)
        action_row.pack(fill="x", pady=(0, 8))
        self._report_summary_var = tk.StringVar(value="Loading report summary...")
        tk.Label(action_row, textvariable=self._report_summary_var,
                 bg=BG, fg=ACCENT3, font=FONT_SMALL).pack(side="left")
        make_button(action_row, "⬇ Export Report", self._export_report_csv,
                    color=ACCENT, width=15).pack(side="right")
        make_button(action_row, "🔄 Refresh", self._load_reports,
                    color=SURFACE2, width=12).pack(side="right", padx=(0, 8))

        cols = ("Event", "Date", "Club", "Registered", "Present", "Absent", "Attendance %")
        tv_frame, self._report_tree = make_treeview(wrap, cols)
        tv_frame.pack(fill="both", expand=True)
        self._report_tree.column("Event", width=200, anchor="w")
        self._report_tree.column("Club", width=130, anchor="w")
        for col in ("Registered", "Present", "Absent", "Attendance %"):
            self._report_tree.column(col, width=95, anchor="center")

        self._load_reports()

    def _load_reports(self):
        summary_rows = reg_svc.get_registration_summary()
        attendance_map = {
            row["event_name"]: row for row in att_svc.get_attendance_summary()
        }

        self._report_tree.delete(*self._report_tree.get_children())
        total_registered = 0
        best_event_name = "None"
        best_total = -1
        total_rate = 0.0

        for row in summary_rows:
            registered = row.get("total_registered", 0) or 0
            total_registered += registered
            if registered > best_total:
                best_total = registered
                best_event_name = row["event_name"]

            attendance_row = attendance_map.get(row["event_name"], {})
            present = attendance_row.get("present", 0) or 0
            absent = attendance_row.get("absent", 0) or 0
            rate = attendance_row.get("attendance_rate", 0.0) or 0.0
            total_rate += rate

            self._report_tree.insert("", "end", values=(
                row["event_name"],
                row["date"],
                row["club"],
                registered,
                present,
                absent,
                f"{rate}%",
            ))

        avg_rate = round(total_rate / len(summary_rows), 1) if summary_rows else 0.0
        self._report_summary_var.set(
            f"Events: {len(summary_rows)} • Registrations: {total_registered} • Avg attendance: {avg_rate}% • Top event: {best_event_name}"
        )

    def _export_report_csv(self):
        path = filedialog.asksaveasfilename(
            title="Export Report",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*")],
        )
        if not path:
            return

        try:
            summary_rows = reg_svc.get_registration_summary()
            attendance_map = {
                row["event_name"]: row for row in att_svc.get_attendance_summary()
            }
            with open(path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["event", "date", "club", "registered", "present", "absent", "attendance_rate"])
                for row in summary_rows:
                    attendance_row = attendance_map.get(row["event_name"], {})
                    writer.writerow([
                        row["event_name"],
                        row["date"],
                        row["club"],
                        row.get("total_registered", 0) or 0,
                        attendance_row.get("present", 0) or 0,
                        attendance_row.get("absent", 0) or 0,
                        attendance_row.get("attendance_rate", 0.0) or 0.0,
                    ])
            show_toast(self, "Report exported to CSV.", success=True)
        except Exception as exc:
            messagebox.showerror("Report Export", str(exc))

    # ══════════════════════════════════════════════════════════════════════
    # Section: Attendance
    # ══════════════════════════════════════════════════════════════════════
    def _build_attendance(self):
        wrap = tk.Frame(self._content, bg=BG, padx=24, pady=24)
        wrap.pack(fill="both", expand=True)

        make_label(wrap, "Attendance", font=FONT_TITLE).pack(anchor="w")
        make_label(wrap, "Track event attendance and participation", fg=MUTED).pack(anchor="w", pady=(4, 16))

        # top KPI cards
        card_frame = tk.Frame(wrap, bg=BG)
        card_frame.pack(fill="x", pady=(0, 16))

        today_events = att_svc.get_today_event_count()
        total_present = att_svc.get_total_present()
        total_absent = att_svc.get_total_absent()
        total_records = total_present + total_absent
        rate = round((total_present / total_records) * 100, 1) if total_records else 0.0

        def stat_card(parent, title, value, note):
            c = tk.Frame(parent, bg=SURFACE, bd=0, relief="flat", padx=16, pady=12)
            c.pack(side="left", expand=True, fill="x", padx=6)
            tk.Label(c, text=title, bg=SURFACE, fg=MUTED, font=("Helvetica", 9)).pack(anchor="w")
            tk.Label(c, text=str(value), bg=SURFACE, fg=ACCENT3, font=("Helvetica", 28, "bold")).pack(anchor="w")
            tk.Label(c, text=note, bg=SURFACE, fg=MUTED, font=("Helvetica", 8)).pack(anchor="w", pady=(4, 0))
            return c

        stat_card(card_frame, "Today's Events", today_events, "in pipeline")
        stat_card(card_frame, "Total Attendance", total_present, "present records")
        stat_card(card_frame, "Attendance Rate", f"{rate}%", "overall presence")

        # action bar
        action_row = tk.Frame(wrap, bg=BG)
        action_row.pack(fill="x", pady=(8, 12))
        make_button(action_row, "Scan QR", self._scan_qr, color="#16a34a", width=12).pack(side="left")
        make_button(action_row, "Export", self._export_attendance, color=ACCENT, width=10).pack(side="left", padx=(8, 0))

        # manual attendance area (no QR required)
        manual_frame = tk.Frame(wrap, bg=BG, pady=8)
        manual_frame.pack(fill="x", pady=(0, 12))
        make_label(manual_frame, "Manual Attendance (no QR required)", font=FONT_SMALL, fg=ACCENT).pack(anchor="w")

        mname_frame = tk.Frame(manual_frame, bg=BG)
        mname_frame.pack(fill="x", pady=(4, 4))
        tk.Label(mname_frame, text="Username", bg=BG, fg=TEXT).pack(side="left", padx=(0, 6))
        self._ma_user = make_entry(mname_frame, width=18)
        self._ma_user.pack(side="left", padx=(0, 20))

        tk.Label(mname_frame, text="Event Name", bg=BG, fg=TEXT).pack(side="left", padx=(0, 6))
        self._ma_event = make_entry(mname_frame, width=18)
        self._ma_event.pack(side="left", padx=(0, 20))

        tk.Label(mname_frame, text="Status", bg=BG, fg=TEXT).pack(side="left", padx=(0, 6))
        self._ma_status = make_entry(mname_frame, width=10)
        self._ma_status.insert(0, "present")
        self._ma_status.pack(side="left", padx=(0, 16))

        make_button(manual_frame, "Apply Manual Mark", self._apply_manual_attendance, color=ACCENT3, width=16).pack(anchor="w")

        # event attendance summary table
        make_label(wrap, "Event Attendance Records", font=FONT_HEAD).pack(anchor="w")
        make_label(wrap, "Detailed attendance information for all events", fg=MUTED).pack(anchor="w", pady=(0, 10))

        cols = ("Event", "Date", "Club", "Registered", "Present", "Absent", "Attendance %")
        tv_frame, self._summary_tree = make_treeview(wrap, cols)
        tv_frame.pack(fill="both", expand=True)
        for c in ("Registered", "Present", "Absent", "Attendance %"):
            self._summary_tree.column(c, width=90, anchor="center")
        self._summary_tree.column("Club", width=140, anchor="w")

        self._load_attendance_summary()

        # detail attendance table for marking
        detail_wrap = tk.Frame(wrap, bg=BG, pady=12)
        detail_wrap.pack(fill="both", expand=True)

        make_label(detail_wrap, "Student Attendance", font=FONT_HEAD).pack(anchor="w")
        make_label(detail_wrap, "Select a participant below and mark attendance.", fg=MUTED).pack(anchor="w", pady=(0, 10))

        detail_cols = ("Student", "Email", "Event", "Date", "Club", "Status", "user_id", "event_id")
        detail_frame, self._att_tree = make_treeview(detail_wrap, detail_cols)
        detail_frame.pack(fill="both", expand=True)
        self._att_tree.column("user_id", width=0, stretch=False)
        self._att_tree.column("event_id", width=0, stretch=False)

        self._load_detail_attendance()

        btn_row = tk.Frame(detail_wrap, bg=BG)
        btn_row.pack(fill="x", pady=(8, 0))

        make_button(btn_row, "✅ Mark Present", self._mark_selected_present, color=ACCENT, width=16).pack(side="left", padx=(0, 8))
        make_button(btn_row, "❌ Mark Absent", self._mark_selected_absent, color=ACCENT2, width=16).pack(side="left")

    def _load_attendance_summary(self):
        self._summary_tree.delete(*self._summary_tree.get_children())
        for row in att_svc.get_attendance_summary():
            self._summary_tree.insert("", "end", values=(
                row.get("event_name"),
                row.get("date"),
                row.get("club"),
                row.get("registered", 0),
                row.get("present", 0),
                row.get("absent", 0),
                f"{row.get('attendance_rate', 0.0)}%",
            ))

    def _load_detail_attendance(self):
        self._att_tree.delete(*self._att_tree.get_children())
        for r in att_svc.get_all_attendance():
            self._att_tree.insert("", "end", values=(
                r["username"],
                r["email"],
                r["event_name"],
                r["date"],
                r["club"],
                r["status"],
                r["user_id"],
                r["event_id"],
            ))

    def _refresh_attendance(self):
        self._load_attendance_summary()
        self._load_detail_attendance()
        show_toast(self, "Attendance refreshed.", success=True)

    def _get_selected_attendance(self):
        sel = self._att_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a student attendance entry first.")
            return None
        return self._att_tree.item(sel[0])["values"]

    def _resolve_user_event_for_attendance(self, row):
        # row currently: [username, email, event_name, date, club, status, user_id, event_id]
        try:
            user_id = int(row[6]) if row[6] is not None and str(row[6]).strip() else None
            event_id = int(row[7]) if row[7] is not None and str(row[7]).strip() else None
        except (ValueError, TypeError):
            user_id = None
            event_id = None

        if user_id and event_id:
            return user_id, event_id

        # fall back to query by username/event_name
        return self._get_user_event_from_attendance_row(row)

    def _mark_selected_present(self):
        row = self._get_selected_attendance()
        if row is None:
            return
        try:
            user_id, event_id = self._resolve_user_event_for_attendance(row)
            att_svc.mark_attendance(user_id, event_id, "present")
            notif_svc.create_notification(user_id, f"Your attendance for '{row[2]}' was marked PRESENT.")
            show_toast(self, f"Marked present for {row[0]} on {row[2]}", success=True)
        except Exception as e:
            messagebox.showerror("Mark Present Failed", str(e))
        finally:
            self._refresh_attendance()

    def _mark_selected_absent(self):
        row = self._get_selected_attendance()
        if row is None:
            return
        try:
            user_id, event_id = self._resolve_user_event_for_attendance(row)
            att_svc.mark_attendance(user_id, event_id, "absent")
            notif_svc.create_notification(user_id, f"Your attendance for '{row[2]}' was marked ABSENT.")
            show_toast(self, f"Marked absent for {row[0]} on {row[2]}", success=False)
        except Exception as e:
            messagebox.showerror("Mark Absent Failed", str(e))
        finally:
            self._refresh_attendance()

    def _apply_manual_attendance(self):
        username = self._ma_user.get().strip()
        event_name = self._ma_event.get().strip()
        status = self._ma_status.get().strip().lower()

        if not username or not event_name or status not in ("present", "absent"):
            messagebox.showwarning("Invalid manual attendance", "Provide username, event name, and status (present/absent).")
            return

        from database.db import get_connection
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = cur.fetchone()
            if not user:
                raise ValueError(f"User '{username}' not found.")

            cur.execute("SELECT id FROM events WHERE name = ?", (event_name,))
            ev = cur.fetchone()
            if not ev:
                raise ValueError(f"Event '{event_name}' not found.")

            user_id = user["id"]
            event_id = ev["id"]

            att_svc.mark_attendance(user_id, event_id, status)
            show_toast(self, f"Manually marked {status} for {username} on {event_name}.", success=(status=="present"))
        except Exception as e:
            messagebox.showerror("Manual Mark Failed", str(e))
        finally:
            conn.close()
            self._refresh_attendance()

    def _scan_qr(self):
        path = filedialog.askopenfilename(
            title="Select QR Image",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp"), ("All files", "*")],
        )
        if not path:
            return

        try:
            from PIL import Image
            from pyzbar.pyzbar import decode
        except ImportError:
            messagebox.showerror(
                "QR Scan",
                "QR scanning requires Pillow and pyzbar. Install with: pip install pillow pyzbar",
            )
            return

        try:
            image = Image.open(path)
            decoded = decode(image)
            if not decoded:
                raise ValueError("No QR code found in selected image.")

            decoded_text = decoded[0].data.decode("utf-8")
            # expected formats:
            # - "user_id,event_id"
            # - "username,event_name" (fallback)
            parts = [p.strip() for p in decoded_text.split(",")]

            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                user_id = int(parts[0])
                event_id = int(parts[1])
            else:
                # try resolve from username/event_name and mark present
                from database.db import get_connection
                conn = get_connection()
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT u.id AS user_id, e.id AS event_id FROM users u JOIN events e ON e.name = ? WHERE u.username = ? LIMIT 1",
                        (parts[1], parts[0]),
                    )
                    out = cur.fetchone()
                    if not out:
                        raise ValueError("Could not resolve user/event from QR text.")
                    user_id = out["user_id"]
                    event_id = out["event_id"]
                finally:
                    conn.close()

            att_svc.mark_attendance(user_id, event_id, "present")
            show_toast(self, f"Attendance marked present for user {user_id} at event {event_id}.", success=True)
            self._refresh_attendance()

        except Exception as e:
            messagebox.showerror("QR Scan Error", str(e))

    def _export_attendance(self):
        path = filedialog.asksaveasfilename(
            title="Export Attendance",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*")],
        )
        if not path:
            return

        try:
            rows = att_svc.get_all_attendance()
            with open(path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["user_id", "username", "email", "event_id", "event_name", "date", "club", "status"])
                for r in rows:
                    writer.writerow([
                        r.get("user_id"),
                        r.get("username"),
                        r.get("email"),
                        r.get("event_id"),
                        r.get("event_name"),
                        r.get("date"),
                        r.get("club"),
                        r.get("status"),
                    ])
            show_toast(self, "Attendance exported to CSV.", success=True)
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _get_user_event_from_attendance_row(self, row):
        # row values: [id, username, email, event name, date, club, status]
        event_name = row[3]
        username = row[1]

        conn = None
        from database.db import get_connection
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT u.id AS user_id, e.id AS event_id FROM users u JOIN events e ON e.name = ? WHERE u.username = ? LIMIT 1", (event_name, username))
            found = cur.fetchone()
            if not found:
                raise ValueError("Unable to resolve user/event for attendance action.")
            return found["user_id"], found["event_id"]
        finally:
            conn.close()

    # ══════════════════════════════════════════════════════════════════════
    # Section: Event Calendar
    # ══════════════════════════════════════════════════════════════════════
    def _build_event_calendar(self):
        self._active_calendar_date = date.today().replace(day=1)
        self._selected_calendar_day = date.today()
        self._event_dates_in_month = set()
        self._calendar_events_by_date = {}

        wrap = tk.Frame(self._content, bg=BG, padx=40, pady=30)
        wrap.pack(fill="both", expand=True)

        make_label(wrap, "Event Calendar", font=FONT_TITLE).pack(anchor="center")
        make_label(wrap, "Overview of events and day-by-day schedule", fg=MUTED).pack(anchor="center", pady=(4, 16))

        controls = tk.Frame(wrap, bg=BG)
        controls.pack(pady=(0, 12))

        make_button(controls, "◀", lambda: self._change_month(-1), width=4).pack(side="left")
        self._calendar_label = tk.Label(controls, text="", bg=BG, fg=ACCENT, font=FONT_BODY)
        self._calendar_label.pack(side="left", padx=16)
        make_button(controls, "▶", lambda: self._change_month(1), width=4).pack(side="left", padx=(0, 12))

        make_button(controls, "🔄 Refresh", self._refresh_event_calendar, color=SURFACE2, width=10).pack(side="left")

        cal_frame = tk.Frame(wrap, bg=SURFACE, padx=14, pady=14, highlightthickness=1, highlightbackground=BORDER)
        cal_frame.pack(anchor="center", pady=(0, 18))

        self._day_buttons = []
        headers = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for idx, day_name in enumerate(headers):
            tk.Label(
                cal_frame,
                text=day_name,
                bg=SURFACE,
                fg=MUTED,
                font=FONT_SMALL,
                width=5,
            ).grid(row=0, column=idx, padx=3, pady=(0, 6))

        for week_idx in range(6):
            row_buttons = []
            for day_idx in range(7):
                btn = tk.Button(
                    cal_frame,
                    text="",
                    width=5,
                    height=2,
                    bg=SURFACE2,
                    fg=TEXT,
                    relief="flat",
                    bd=0,
                    cursor="hand2",
                    font=("Helvetica", 11, "bold"),
                )
                btn.grid(row=week_idx + 1, column=day_idx, padx=3, pady=3)
                row_buttons.append(btn)
            self._day_buttons.append(row_buttons)

        details = tk.Frame(wrap, bg=BG)
        details.pack(fill="both", expand=True)

        self._selected_date_title = make_label(details, "", font=FONT_HEAD)
        self._selected_date_title.pack(anchor="w")
        self._selected_date_meta = make_label(details, "", fg=MUTED)
        self._selected_date_meta.pack(anchor="w", pady=(0, 8))

        selected_cols = ("Event", "Club", "Present", "Absent", "Total")
        tv_frame, self._cal_tree = make_treeview(details, selected_cols)
        tv_frame.pack(fill="both", expand=True)
        for c in ("Present", "Absent", "Total"):
            self._cal_tree.column(c, width=80, anchor="center")

        make_label(details, "All Events In This Month", font=FONT_HEAD).pack(anchor="w", pady=(14, 0))
        month_cols = ("Date", "Event", "Club", "Present", "Absent", "Total")
        month_frame, self._month_events_tree = make_treeview(details, month_cols)
        month_frame.pack(fill="both", expand=True, pady=(8, 0))
        for c in ("Present", "Absent", "Total"):
            self._month_events_tree.column(c, width=80, anchor="center")

        self._render_month_calendar()

    def _render_month_calendar(self):
        month = self._active_calendar_date.month
        year = self._active_calendar_date.year
        self._calendar_label.config(text=f"{calendar.month_name[month]} {year}")

        if self._selected_calendar_day.month != month or self._selected_calendar_day.year != year:
            self._selected_calendar_day = date(year, month, 1)

        self._load_event_calendar()

        weeks = calendar.monthcalendar(year, month)
        while len(weeks) < 6:
            weeks.append([0, 0, 0, 0, 0, 0, 0])

        today = date.today()
        default_bg = SURFACE2
        event_bg = "#3B7FD9"
        event_fg = TEXT
        today_bg = "#D97706"
        selected_bg = ACCENT

        for week_idx, week in enumerate(weeks):
            for day_idx, day in enumerate(week):
                btn = self._day_buttons[week_idx][day_idx]
                if day == 0:
                    btn.config(text="", state="disabled", bg=BG, fg=MUTED, command=lambda: None)
                    continue

                cell_date = date(year, month, day)
                has_event = cell_date.isoformat() in self._event_dates_in_month

                bg_color = default_bg
                fg_color = TEXT
                relief_style = "flat"
                border_width = 0
                if has_event:
                    bg_color = event_bg
                    fg_color = event_fg
                    relief_style = "raised"
                    border_width = 1
                if cell_date == today:
                    bg_color = today_bg
                    fg_color = "white"
                    relief_style = "raised"
                    border_width = 1
                if cell_date == self._selected_calendar_day:
                    bg_color = selected_bg
                    fg_color = "white"
                    relief_style = "solid"
                    border_width = 1

                btn.config(
                    text=str(day),
                    state="normal",
                    bg=bg_color,
                    fg=fg_color,
                    relief=relief_style,
                    bd=border_width,
                    activebackground=selected_bg,
                    activeforeground="white",
                    command=lambda d=day: self._select_calendar_day(d),
                )

    def _select_calendar_day(self, day):
        month = self._active_calendar_date.month
        year = self._active_calendar_date.year
        self._selected_calendar_day = date(year, month, day)
        self._render_month_calendar()

    def _change_month(self, delta):
        month = self._active_calendar_date.month + delta
        year = self._active_calendar_date.year
        if month < 1:
            month = 12
            year -= 1
        elif month > 12:
            month = 1
            year += 1
        self._active_calendar_date = self._active_calendar_date.replace(year=year, month=month, day=1)
        self._selected_calendar_day = self._active_calendar_date
        self._render_month_calendar()

    def _load_event_calendar(self):
        self._cal_tree.delete(*self._cal_tree.get_children())
        self._month_events_tree.delete(*self._month_events_tree.get_children())

        month = self._active_calendar_date.month
        year = self._active_calendar_date.year
        selected_date = self._selected_calendar_day.isoformat()

        self._selected_date_title.config(text=f"Details for {self._selected_calendar_day.strftime('%A, %d %B %Y')}")

        summary = att_svc.get_attendance_summary()
        self._calendar_events_by_date = {}
        month_events = []

        for row in summary:
            row_date = row.get("date")
            if not row_date:
                continue
            self._calendar_events_by_date.setdefault(row_date, []).append(row)
            try:
                row_dt = datetime.strptime(row_date, "%Y-%m-%d").date()
            except ValueError:
                continue
            if row_dt.year == year and row_dt.month == month:
                month_events.append(row)

        self._event_dates_in_month = set()
        for row in month_events:
            row_date = row.get("date")
            if not row_date:
                continue
            try:
                row_dt = datetime.strptime(row_date, "%Y-%m-%d").date()
            except ValueError:
                continue
            self._event_dates_in_month.add(row_dt.isoformat())

        selected_events = self._calendar_events_by_date.get(selected_date, [])
        self._selected_date_meta.config(text=f"Events on selected date: {len(selected_events)}")
        if selected_events:
            for row in selected_events:
                self._cal_tree.insert(
                    "",
                    "end",
                    values=(row["event_name"], row["club"], row["present"], row["absent"], row["total"]),
                )
        else:
            self._cal_tree.insert("", "end", values=("No events", "-", "-", "-", "-"))

        month_events.sort(key=lambda r: (r.get("date", ""), r.get("event_name", "")))
        for row in month_events:
            self._month_events_tree.insert(
                "",
                "end",
                values=(row["date"], row["event_name"], row["club"], row["present"], row["absent"], row["total"]),
            )

        if not month_events:
            self._month_events_tree.insert("", "end", values=("-", "No events this month", "-", "-", "-", "-"))

    def _refresh_event_calendar(self):
        self._render_month_calendar()
        show_toast(self, "Event calendar updated.", success=True)
