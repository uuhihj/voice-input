"""
Voice Input — Floating recording indicator overlay.
Creates a topmost tkinter bar at screen top/bottom during recording.
"""

import tkinter as tk
import logging

log = logging.getLogger("voice_input")


class FloatingIndicator:
    """A topmost colored bar that appears while recording."""

    def __init__(self, tk_root: tk.Tk, config: dict):
        self._root = tk_root
        self._win: tk.Toplevel | None = None
        self._config = config  # appearance config dict

    # ── Public API ──────────────────────────────────────

    def show(self):
        """Show the indicator. Safe to call from any thread."""
        if self._root is None:
            return
        self._root.after(0, self._create)

    def hide(self):
        """Hide the indicator. Safe to call from any thread."""
        if self._root is None:
            return
        self._root.after(0, self._destroy)

    def update_style(self, color: str | None = None,
                     position: str | None = None,
                     opacity: float | None = None):
        """Update appearance without recreating. Call after config change."""
        if color is not None:
            self._config["indicator_color"] = color
        if position is not None:
            self._config["indicator_position"] = position
        if opacity is not None:
            self._config["indicator_opacity"] = opacity
        # Apply to existing window if visible
        self._root.after(0, self._restyle)

    # ── Internal ────────────────────────────────────────

    def _create(self):
        if self._win is not None:
            return
        color = self._config.get("indicator_color", "#F44336")
        opacity = self._config.get("indicator_opacity", 0.88)
        position = self._config.get("indicator_position", "top")

        win = tk.Toplevel(self._root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-alpha", opacity)
        win.configure(bg=color)

        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        h = 36
        y = 0 if position == "top" else sh - h
        geo = f"280x{h}+{(sw - 280) // 2}+{y}"
        log.info("Indicator pos=%s screen=%sx%s geometry=%s", position, sw, sh, geo)
        win.geometry(geo)
        win.update_idletasks()
        win.update()
        log.info("Indicator actual position: x=%s y=%s size=%s", win.winfo_x(), win.winfo_y(), win.winfo_geometry())

        tk.Label(win, text="● 正在录音中...  按快捷键停止",
                 fg="white", bg=color,
                 font=("Microsoft YaHei", 11, "bold")).pack(expand=True)
        self._win = win
        log.debug("Indicator shown")

    def _destroy(self):
        if self._win is not None:
            try:
                self._win.destroy()
            except Exception:
                pass
            self._win = None
            log.debug("Indicator hidden")

    def _restyle(self):
        """Apply current style to existing window."""
        if self._win is None:
            return
        color = self._config.get("indicator_color", "#F44336")
        opacity = self._config.get("indicator_opacity", 0.88)
        position = self._config.get("indicator_position", "top")
        self._win.configure(bg=color)
        self._win.attributes("-alpha", opacity)
        sw = self._win.winfo_screenwidth()
        h = 36
        y = 0 if position == "top" else self._win.winfo_screenheight() - h
        self._win.geometry(f"280x{h}+{(sw - 280) // 2}+{y}")
        # Update label background
        for child in self._win.winfo_children():
            if isinstance(child, tk.Label):
                child.configure(bg=color)
