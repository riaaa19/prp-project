"""
Shared UI components and theme constants.
All colour / font decisions live here so every screen looks consistent.
"""
import tkinter as tk
from tkinter import ttk

# ── Palette ────────────────────────────────────────────────────────────────
BG          = "#0F1117"   # main background  (near-black navy)
SURFACE     = "#1A1D2E"   # card / panel surface
SURFACE2    = "#252840"   # slightly lighter surface (table rows, inputs)
ACCENT      = "#6C63FF"   # primary purple accent
ACCENT2     = "#FF6584"   # secondary pink accent  (danger / delete)
ACCENT3     = "#43E97B"   # green  (success)
TEXT        = "#E8E8F0"   # primary text
MUTED       = "#7B7F9E"   # secondary / placeholder text
BORDER      = "#2E3250"   # subtle border

# ── Typography ─────────────────────────────────────────────────────────────
FONT_TITLE  = ("Helvetica", 22, "bold")
FONT_HEAD   = ("Helvetica", 14, "bold")
FONT_BODY   = ("Helvetica", 11)
FONT_SMALL  = ("Helvetica", 9)
FONT_BTN    = ("Helvetica", 11, "bold")


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────

def apply_global_style(root: tk.Tk):
    """Apply ttk styles and root background."""
    root.configure(bg=BG)
    style = ttk.Style(root)
    style.theme_use("clam")

    # Treeview
    style.configure("Custom.Treeview",
                    background=SURFACE2,
                    foreground=TEXT,
                    fieldbackground=SURFACE2,
                    rowheight=28,
                    font=FONT_BODY,
                    borderwidth=0)
    style.configure("Custom.Treeview.Heading",
                    background=ACCENT,
                    foreground="white",
                    font=("Helvetica", 10, "bold"),
                    relief="flat")
    style.map("Custom.Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", "white")])

    # Scrollbar
    style.configure("Vertical.TScrollbar",
                    background=SURFACE2,
                    troughcolor=SURFACE,
                    arrowcolor=MUTED)


def make_frame(parent, **kw):
    """Create a styled tk.Frame."""
    defaults = dict(bg=BG, bd=0, highlightthickness=0)
    defaults.update(kw)
    return tk.Frame(parent, **defaults)


def make_label(parent, text, font=FONT_BODY, fg=TEXT, **kw):
    """Create a styled label."""
    defaults = dict(bg=BG, fg=fg, font=font, text=text)
    defaults.update(kw)
    return tk.Label(parent, **defaults)


def make_entry(parent, show=None, width=30):
    """Create a styled entry widget."""
    e = tk.Entry(parent,
                 font=FONT_BODY,
                 bg=SURFACE2,
                 fg=TEXT,
                 insertbackground=TEXT,
                 relief="flat",
                 width=width,
                 bd=8,
                 highlightthickness=1,
                 highlightcolor=ACCENT,
                 highlightbackground=BORDER)
    if show:
        e.config(show=show)
    return e


def make_button(parent, text, command, color=ACCENT, width=18, **kw):
    """Create a styled flat button."""
    defaults = dict(
        text=text,
        command=command,
        bg=color,
        fg="white",
        activebackground=_darken(color),
        activeforeground="white",
        font=FONT_BTN,
        relief="flat",
        bd=0,
        cursor="hand2",
        width=width,
        pady=8,
    )
    defaults.update(kw)
    btn = tk.Button(parent, **defaults)
    # subtle hover effect
    btn.bind("<Enter>", lambda e: btn.config(bg=_darken(color)))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


def make_treeview(parent, columns: list, show="headings"):
    """Create a styled Treeview with scrollbar, packed into a frame."""
    frame = make_frame(parent, bg=SURFACE)
    tv = ttk.Treeview(frame, columns=columns, show=show,
                      style="Custom.Treeview")
    sb = ttk.Scrollbar(frame, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=sb.set)
    tv.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    # set equal column widths
    for col in columns:
        tv.heading(col, text=col.replace("_", " ").title())
        tv.column(col, anchor="center", width=120)
    return frame, tv


def show_toast(parent, message: str, success: bool = True):
    """Show a small disappearing toast popup."""
    color = ACCENT3 if success else ACCENT2
    toast = tk.Toplevel(parent)
    toast.overrideredirect(True)
    toast.attributes("-topmost", True)

    # position near top-centre of parent
    px = parent.winfo_rootx() + parent.winfo_width() // 2 - 150
    py = parent.winfo_rooty() + 20
    toast.geometry(f"300x44+{px}+{py}")
    toast.configure(bg=color)

    tk.Label(toast, text=message, bg=color, fg="white",
             font=FONT_BODY, wraplength=290).pack(fill="both", expand=True, padx=8)

    toast.after(2400, toast.destroy)


def _darken(hex_color: str, factor: float = 0.82) -> str:
    """Return a slightly darker version of a hex colour."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return "#{:02x}{:02x}{:02x}".format(
        int(r * factor), int(g * factor), int(b * factor))
