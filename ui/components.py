"""
Shared UI components and theme constants.
All colour / font decisions live here so every screen looks consistent.
"""
import tkinter as tk
from tkinter import ttk

# ── Palette ────────────────────────────────────────────────────────────────
BG          = "#0A0E27"   # ultra dark background (premium feel)
SURFACE     = "#141D3A"   # deep panel surface
SURFACE2    = "#1F2A4D"   # secondary surface for cards and inputs
ACCENT      = "#7C3AED"   # purple (primary gradient)
ACCENT_LIGHT= "#A78BFA"   # light purple (hover state)
ACCENT2     = "#F97316"   # bright orange accent for alerts and actions
ACCENT3     = "#34D399"   # fresh green accent for success states
TEXT        = "#F0F4F8"   # high contrast text
MUTED       = "#A1A8B8"   # muted text and placeholder prompts
BORDER      = "#2D3A52"   # subtle surface border
GLOW_COLOR  = "#7C3AED"   # glow effects

# ── Typography ─────────────────────────────────────────────────────────────
FONT_TITLE  = ("Segoe UI", 28, "bold")
FONT_HEAD   = ("Segoe UI", 15, "bold")
FONT_BODY   = ("Segoe UI", 11)
FONT_SMALL  = ("Segoe UI", 9)
FONT_BTN    = ("Segoe UI", 12, "bold")


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────

def apply_global_style(root: tk.Tk):
    """Apply modern ttk styles and root background."""
    root.configure(bg=BG)
    style = ttk.Style(root)
    style.theme_use("clam")

    # Treeview - Premium styling
    style.configure("Custom.Treeview",
                    background=SURFACE2,
                    foreground=TEXT,
                    fieldbackground=SURFACE2,
                    rowheight=32,
                    font=FONT_BODY,
                    borderwidth=0,
                    relief="flat")
    
    style.configure("Custom.Treeview.Heading",
                    background=ACCENT,
                    foreground="white",
                    font=("Segoe UI", 11, "bold"),
                    relief="flat",
                    borderwidth=0)
    
    style.map("Custom.Treeview",
              background=[("selected", ACCENT), ("alternate", SURFACE)],
              foreground=[("selected", "white")],
              fieldbackground=[("selected", ACCENT)])
    
    # Alternate row colors for better readability
    style.configure("Custom.Treeview",
                    rowheight=32,
                    relief="flat",
                    borderwidth=0)

    # Entry and combobox
    style.configure("TEntry",
                    fieldbackground=SURFACE2,
                    background=SURFACE2,
                    foreground=TEXT,
                    bordercolor=BORDER,
                    lightcolor=ACCENT,
                    relief="flat",
                    borderwidth=0)
    
    style.configure("TCombobox",
                    fieldbackground=SURFACE2,
                    background=SURFACE2,
                    foreground=TEXT,
                    arrowcolor=ACCENT,
                    relief="flat",
                    borderwidth=0)

    style.map("TCombobox",
              fieldbackground=[("readonly", SURFACE2)],
              background=[("readonly", SURFACE2)])

    # Scrollbar - Modern thin style
    style.configure("Vertical.TScrollbar",
                    background=SURFACE2,
                    troughcolor=SURFACE,
                    arrowcolor=TEXT,
                    bordercolor=SURFACE,
                    relief="flat",
                    darkcolor=SURFACE2,
                    lightcolor=SURFACE2,
                    borderwidth=0)
    
    style.map("Vertical.TScrollbar",
              background=[("active", ACCENT)])


def make_frame(parent, **kw):
    """Create a styled tk.Frame."""
    defaults = dict(bg=BG, bd=0, highlightthickness=0)
    defaults.update(kw)
    return tk.Frame(parent, **defaults)


def make_card(parent, **kw):
    """Create a premium card-style surface with rounded borders effect."""
    # Filter card-specific kwargs
    padx = kw.pop('padx', 18)
    pady = kw.pop('pady', 18)
    bg = kw.pop('bg', SURFACE)
    
    # Create the card frame with highlight border effect
    card = tk.Frame(parent,
                    bg=bg,
                    bd=0,
                    highlightthickness=2,
                    highlightbackground=BORDER,
                    highlightcolor=ACCENT,
                    padx=padx,
                    pady=pady)
    
    # Hover effect for visual feedback
    def on_enter(e):
        card.config(highlightbackground=ACCENT_LIGHT)
    
    def on_leave(e):
        card.config(highlightbackground=BORDER)
    
    card.bind("<Enter>", on_enter)
    card.bind("<Leave>", on_leave)
    
    return card



def make_label(parent, text, font=FONT_BODY, fg=TEXT, **kw):
    """Create a styled label."""
    defaults = dict(bg=BG, fg=fg, font=font, text=text)
    defaults.update(kw)
    return tk.Label(parent, **defaults)


def make_entry(parent, show=None, width=30):
    """Create a premium styled entry widget."""
    e = tk.Entry(parent,
                 font=FONT_BODY,
                 bg=SURFACE2,
                 fg=TEXT,
                 insertbackground=ACCENT,
                 relief="flat",
                 width=width,
                 bd=0,
                 highlightthickness=3,
                 highlightcolor=ACCENT,
                 highlightbackground=BORDER,
                 insertborderwidth=0)
    if show:
        e.config(show=show)
    
    # Hover effect on border
    def on_focus_in(event):
        e.config(highlightbackground=ACCENT_LIGHT)
    
    def on_focus_out(event):
        e.config(highlightbackground=BORDER)
    
    e.bind("<FocusIn>", on_focus_in)
    e.bind("<FocusOut>", on_focus_out)
    
    return e


def make_button(parent, text, command, color=ACCENT, width=18, **kw):
    """Create a premium button with smooth hover effects."""
    defaults = dict(
        text=text,
        command=command,
        bg=color,
        fg="white",
        activebackground=_lighten(color, 1.15),
        activeforeground="white",
        font=FONT_BTN,
        relief="flat",
        bd=0,
        cursor="hand2",
        width=width,
        pady=12,
        padx=14,
        highlightthickness=0,
        overrelief="flat",
    )
    defaults.update(kw)
    btn = tk.Button(parent, **defaults)
    
    # Smooth hover effect with slight transition
    original_bg = color
    hover_bg = _lighten(color, 1.1)
    
    def on_enter(e):
        btn.config(bg=hover_bg)
    
    def on_leave(e):
        btn.config(bg=original_bg)
    
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    
    return btn


def make_treeview(parent, columns: list, show="headings"):
    """Create a premium styled Treeview with scrollbar."""
    # Main frame with padding effect
    frame = make_frame(parent, bg=SURFACE)
    
    tv = ttk.Treeview(frame, columns=columns, show=show,
                      style="Custom.Treeview", 
                      selectmode='browse')
    
    sb = ttk.Scrollbar(frame, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=sb.set)
    
    tv.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y", padx=(2, 0))
    
    # Improved column styling
    for col in columns:
        tv.heading(col, text=col.replace("_", " ").title())
        tv.column(col, anchor="w", width=120)
    
    # Add alternating row colors via Treeview tags
    tv.tag_configure('oddrow', background=SURFACE2)
    tv.tag_configure('evenrow', background=_lighten(SURFACE2, 1.05))
    
    return frame, tv


def show_toast(parent, message: str, success: bool = True):
    """Show a premium disappearing toast popup."""
    color = ACCENT3 if success else ACCENT2
    toast = tk.Toplevel(parent)
    toast.overrideredirect(True)
    toast.attributes("-topmost", True)
    toast.attributes("-alpha", 0.95)

    # position near top-centre of parent
    px = parent.winfo_rootx() + parent.winfo_width() // 2 - 160
    py = parent.winfo_rooty() + 30
    toast.geometry(f"320x50+{px}+{py}")
    toast.configure(bg=color, highlightthickness=1, highlightbackground=_lighten(color, 1.2))

    # Content
    content_frame = tk.Frame(toast, bg=color, bd=0)
    content_frame.pack(fill="both", expand=True)
    
    tk.Label(content_frame, text=message, bg=color, fg="white",
             font=("Segoe UI", 11, "bold"), wraplength=300).pack(fill="both", expand=True, padx=12, pady=12)

    # Smooth fade out
    def fade_out():
        try:
            for alpha in [0.95, 0.85, 0.7, 0.5, 0.3, 0.0]:
                toast.attributes("-alpha", alpha)
                toast.update()
                toast.after(50)
        except:
            pass
        try:
            toast.destroy()
        except:
            pass

    toast.after(2200, fade_out)


def _darken(hex_color: str, factor: float = 0.82) -> str:
    """Return a slightly darker version of a hex colour."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return "#{:02x}{:02x}{:02x}".format(
        int(r * factor), int(g * factor), int(b * factor))


def _lighten(hex_color: str, factor: float = 1.15) -> str:
    """Return a slightly lighter version of a hex colour."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    r = min(int(r * factor), 255)
    g = min(int(g * factor), 255)
    b = min(int(b * factor), 255)
    return "#{:02x}{:02x}{:02x}".format(r, g, b)

