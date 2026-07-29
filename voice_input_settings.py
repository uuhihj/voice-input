"""
Voice Input — Settings window.
Sakura-pink themed with glass effect + rounded buttons.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageDraw, ImageTk
import logging

log = logging.getLogger("voice_input")

# ═══════════════════════════════════════════════════════════
# Sakura color theme
# ═══════════════════════════════════════════════════════════
C = {
    "bg":       "#FFE4E1",
    "card":     "#FFF0F0",
    "border":   "#F0C8C8",
    "accent":   "#E88A8A",
    "text":     "#5D4037",
    "subtext":  "#A08080",
    "save":     "#81C784",
    "reset":    "#E57373",
    "tab_sel":  "#FFD0D0",
    "tab":      "#F5E0E0",
    "white":    "#FFFFFF",
}

MODIFIER_CHOICES = ["None", "Ctrl", "Alt", "Shift"]
KEY_CHOICES = [
    "num add", "num -", "num *", "num /",
    "num 0", "num 1", "num 2", "num 3", "num 4",
    "num 5", "num 6", "num 7", "num 8", "num 9",
    "num multiply", "num divide", "num decimal", "num enter",
    "F1", "F2", "F3", "F4", "F5", "F6",
    "F7", "F8", "F9", "F10", "F11", "F12",
    "space", "enter", "tab", "esc", "backspace", "delete",
    "insert", "home", "end", "page up", "page down",
    "up", "down", "left", "right",
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j",
    "k", "l", "m", "n", "o", "p", "q", "r", "s", "t",
    "u", "v", "w", "x", "y", "z",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    ".", ",", "/", "-", "=",
]
DEVICE_CHOICES = ["cuda", "cpu"]
COMPUTE_CHOICES = ["float16", "int8", "bfloat16"]
PRESET_COLORS = [
    "#F44336", "#FF9800", "#FFEB3B", "#4CAF50",
    "#2196F3", "#9C27B0", "#FAFAFA", "#607D8B",
]

# ═══════════════════════════════════════════════════════════
# Image helpers
# ═══════════════════════════════════════════════════════════

def _hex_rgb(hx: str) -> tuple:
    return tuple(int(hx.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))


def _round_btn_img(w: int, h: int, r: int, fill: str, text: str,
                   text_color: str = "#FFFFFF") -> Image.Image:
    """PIL rounded-rect button with centered text."""
    img = Image.new("RGB", (w, h), _hex_rgb(C["bg"]))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, w - 1, h - 1], r, fill=_hex_rgb(fill))
    # Text
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("C:\\Windows\\Fonts\\msyh.ttc", 12)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((w - tw) / 2, (h - th) / 2 - 2), text, fill=_hex_rgb(text_color), font=font)
    return img


# ═══════════════════════════════════════════════════════════
# Rounded Button (Canvas-based, for bottom action buttons)
# ═══════════════════════════════════════════════════════════

class RoundedButton(tk.Canvas):
    """PIL-rounded button with hover effect."""

    def __init__(self, parent, text: str, color: str, command,
                 width=120, height=38, radius=14, text_color="#FFFFFF"):
        super().__init__(parent, width=width, height=height,
                         highlightthickness=0, borderwidth=0, bg=C["bg"])
        self._cmd = command
        self._hover_color = _darken(color)
        self._img_normal = ImageTk.PhotoImage(
            _round_btn_img(width, height, radius, color, text, text_color))
        self._img_hover = ImageTk.PhotoImage(
            _round_btn_img(width, height, radius, self._hover_color, text, text_color))
        self._bg_id = self.create_image(width // 2, height // 2,
                                        image=self._img_normal, anchor="center")
        self.bind("<Enter>", lambda e: self.itemconfig(self._bg_id, image=self._img_hover))
        self.bind("<Leave>", lambda e: self.itemconfig(self._bg_id, image=self._img_normal))
        self.bind("<Button-1>", lambda e: self._cmd() if self._cmd else None)


def _darken(hex_color: str, factor: float = 0.85) -> str:
    rgb = _hex_rgb(hex_color)
    return "#{:02X}{:02X}{:02X}".format(*[max(0, int(c * factor)) for c in rgb])


# ═══════════════════════════════════════════════════════════
# Helper: make a card-style Frame
# ═══════════════════════════════════════════════════════════

def _card_frame(parent, title: str = "", pad: tuple = (16, 12)) -> tk.Frame:
    """Return a Frame with card styling (bg, border line)."""
    outer = tk.Frame(parent, bg=C["border"], padx=1, pady=1)
    inner = tk.Frame(outer, bg=C["card"], padx=pad[0], pady=pad[1])
    inner.pack(fill="both", expand=True)
    if title:
        tk.Label(inner, text=title, font=("Microsoft YaHei", 10, "bold"),
                 fg=C["accent"], bg=C["card"]).pack(anchor="w", pady=(0, 6))
    inner._content = tk.Frame(inner, bg=C["card"])
    inner._content.pack(fill="x")
    return outer, inner._content


# ═══════════════════════════════════════════════════════════
# Settings Window
# ═══════════════════════════════════════════════════════════

class SettingsWindow:

    def __init__(self, parent_root: tk.Tk, config: dict, on_save):
        self._root = parent_root
        self._config = config
        self._on_save = on_save
        self._build()
        self._load_to_ui()

    def _build(self):
        self._win = tk.Toplevel(self._root)
        self._win.title("Voice Input 设置")
        self._win.configure(bg=C["bg"])
        self._win.resizable(False, False)
        self._win.attributes("-alpha", 0.96)

        # Increased window size for better DPI feel
        w, h = 520, 680
        sw = self._win.winfo_screenwidth()
        sh = self._win.winfo_screenheight()
        self._win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

        # ── Drag support (title bar drags the window) ──
        self._drag_x = 0
        self._drag_y = 0
        def _start_drag(e):
            self._drag_x = e.x
            self._drag_y = e.y
        def _do_drag(e):
            x = self._win.winfo_x() + (e.x - self._drag_x)
            y = self._win.winfo_y() + (e.y - self._drag_y)
            self._win.geometry(f"+{x}+{y}")

        # ── Title bar ──
        hdr = tk.Frame(self._win, bg=C["bg"])
        hdr.pack(fill="x", padx=28, pady=(18, 0))
        hdr.bind("<Button-1>", _start_drag)
        hdr.bind("<B1-Motion>", _do_drag)
        lbl1 = tk.Label(hdr, text="🎤  Voice Input  设置",
                 font=("Microsoft YaHei", 18, "bold"),
                 fg=C["accent"], bg=C["bg"])
        lbl1.pack(anchor="w")
        lbl1.bind("<Button-1>", _start_drag)
        lbl1.bind("<B1-Motion>", _do_drag)
        lbl2 = tk.Label(hdr, text="自定义快捷键、语音模型与外观样式",
                 font=("Microsoft YaHei", 9),
                 fg=C["subtext"], bg=C["bg"])
        lbl2.pack(anchor="w", pady=(2, 0))
        lbl2.bind("<Button-1>", _start_drag)
        lbl2.bind("<B1-Motion>", _do_drag)

        # ── Custom tab bar ──
        self._tab_frame = tk.Frame(self._win, bg=C["bg"])
        self._tab_frame.pack(fill="x", padx=24, pady=(14, 0))
        self._tab_btns = {}
        self._tab_pages = {}
        self._current_tab = None

        self._page_area = tk.Frame(self._win, bg=C["bg"])
        self._page_area.pack(fill="both", expand=True, padx=24, pady=(6, 0))

        self._add_tab("shortcuts", "快捷键")
        self._add_tab("model", "模型")
        self._add_tab("appearance", "外观")

        self._build_shortcuts_page()
        self._build_model_page()
        self._build_appearance_page()
        self._build_action_buttons()
        self._show_tab("shortcuts")

    def _add_tab(self, key: str, label: str):
        btn = tk.Button(self._tab_frame, text=label,
                        font=("Microsoft YaHei", 10),
                        fg=C["text"], bg=C["tab"],
                        activebackground=C["tab_sel"],
                        activeforeground=C["accent"],
                        relief="flat", borderwidth=0,
                        padx=18, pady=6,
                        command=lambda k=key: self._show_tab(k))
        btn.pack(side="left", padx=(0, 6))
        self._tab_btns[key] = btn
        page = tk.Frame(self._page_area, bg=C["bg"])
        self._tab_pages[key] = page

    def _show_tab(self, key: str):
        if self._current_tab == key:
            return
        for p in self._tab_pages.values():
            p.pack_forget()
        for k, b in self._tab_btns.items():
            b.configure(bg=C["tab"], fg=C["text"])
        self._tab_pages[key].pack(fill="both", expand=True)
        self._tab_btns[key].configure(bg=C["tab_sel"], fg=C["accent"])
        self._current_tab = key

    # ── Shortcuts page ──────────────────────────────────

    def _build_shortcuts_page(self):
        page = self._tab_pages["shortcuts"]
        self._hk_widgets = {}

        items = [
            ("record", "录制 / 停止", "按下快捷键开始录音，再次按下停止并识别"),
            ("exit", "退出程序", "按下快捷键退出语音输入"),
            ("settings", "打开设置（可选）", "按下快捷键打开此设置窗口"),
        ]

        for idx, (key, title, desc) in enumerate(items):
            outer, content = _card_frame(page, title)
            outer.pack(fill="x", pady=(0 if idx == 0 else 8, 8))

            tk.Label(content, text=desc,
                     font=("Microsoft YaHei", 8),
                     fg=C["subtext"], bg=C["card"]).pack(anchor="w", pady=(0, 8))

            row = tk.Frame(content, bg=C["card"])
            row.pack(fill="x")

            tk.Label(row, text="修饰键", font=("Microsoft YaHei", 10),
                     fg=C["text"], bg=C["card"]).pack(side="left")
            mod_var = tk.StringVar()
            ttk.Combobox(row, textvariable=mod_var,
                         values=MODIFIER_CHOICES, state="readonly",
                         width=8, font=("Microsoft YaHei", 10)).pack(
                side="left", padx=(6, 20))

            tk.Label(row, text="按键", font=("Microsoft YaHei", 10),
                     fg=C["text"], bg=C["card"]).pack(side="left")
            key_var = tk.StringVar()
            ttk.Combobox(row, textvariable=key_var,
                         values=KEY_CHOICES, state="readonly",
                         width=14, font=("Microsoft YaHei", 10)).pack(
                side="left", padx=6)

            self._hk_widgets[key] = (mod_var, key_var)

    # ── Model page ──────────────────────────────────────

    def _build_model_page(self):
        page = self._tab_pages["model"]

        outer1, c1 = _card_frame(page, "模型路径")
        outer1.pack(fill="x", pady=(0, 10))
        row = tk.Frame(c1, bg=C["card"])
        row.pack(fill="x")
        self._model_path_var = tk.StringVar()
        tk.Entry(row, textvariable=self._model_path_var,
                 font=("Consolas", 9), width=36,
                 bg=C["white"], relief="solid",
                 highlightbackground=C["border"],
                 highlightthickness=1, borderwidth=1).pack(
            side="left", ipady=4, padx=(0, 6))
        tk.Button(row, text="浏览...", font=("Microsoft YaHei", 9),
                  bg=C["accent"], fg="white", relief="flat",
                  activebackground=C["accent"],
                  borderwidth=0, padx=12, pady=4,
                  command=self._browse_model).pack(side="left")

        outer2, c2 = _card_frame(page, "运行设备")
        outer2.pack(fill="x", pady=10)
        row2 = tk.Frame(c2, bg=C["card"])
        row2.pack(fill="x")
        tk.Label(row2, text="设备", font=("Microsoft YaHei", 10),
                 fg=C["text"], bg=C["card"]).pack(side="left")
        self._device_var = tk.StringVar()
        ttk.Combobox(row2, textvariable=self._device_var,
                     values=DEVICE_CHOICES, state="readonly",
                     width=10, font=("Microsoft YaHei", 10)).pack(
            side="left", padx=(6, 24))
        tk.Label(row2, text="精度", font=("Microsoft YaHei", 10),
                 fg=C["text"], bg=C["card"]).pack(side="left")
        self._compute_var = tk.StringVar()
        ttk.Combobox(row2, textvariable=self._compute_var,
                     values=COMPUTE_CHOICES, state="readonly",
                     width=10, font=("Microsoft YaHei", 10)).pack(
            side="left", padx=6)

    # ── Appearance page ─────────────────────────────────

    def _build_appearance_page(self):
        page = self._tab_pages["appearance"]

        # Color
        outer1, c1 = _card_frame(page, "指示器颜色")
        outer1.pack(fill="x", pady=(0, 10))
        self._color_var = tk.StringVar()
        self._color_btns = []
        swatches = tk.Frame(c1, bg=C["card"])
        swatches.pack(fill="x")
        for i, hx in enumerate(PRESET_COLORS):
            f = tk.Frame(swatches, width=36, height=28, bg=hx)
            f.pack_propagate(False)
            f.pack(side="left", padx=(0 if i == 0 else 6, 0), pady=4)
            f.bind("<Button-1>", lambda e, col=hx: self._pick_color(col))
            f.configure(highlightbackground=hx, highlightthickness=2,
                        relief="flat")
            self._color_btns.append((f, hx))

        # Position
        outer2, c2 = _card_frame(page, "指示器位置")
        outer2.pack(fill="x", pady=10)
        self._pos_var = tk.StringVar()
        rf = tk.Frame(c2, bg=C["card"])
        rf.pack(fill="x")
        for text, val in [("屏幕顶部", "top"), ("屏幕底部", "bottom")]:
            tk.Radiobutton(rf, text=text, variable=self._pos_var, value=val,
                           font=("Microsoft YaHei", 10),
                           bg=C["card"], fg=C["text"],
                           activebackground=C["card"],
                           selectcolor=C["card"],
                           indicatoron=True).pack(side="left", padx=(0, 28))

        # Opacity
        outer3, c3 = _card_frame(page, "不透明度")
        outer3.pack(fill="x", pady=10)
        sf = tk.Frame(c3, bg=C["card"])
        sf.pack(fill="x")
        self._opacity_var = tk.DoubleVar(value=0.88)
        self._opacity_label = tk.Label(sf, text="88%", width=4,
                                       font=("Microsoft YaHei", 10),
                                       fg=C["text"], bg=C["card"])
        tk.Scale(sf, from_=0.3, to=1.0, resolution=0.05,
                 orient="horizontal", variable=self._opacity_var,
                 command=lambda v: self._opacity_label.config(
                     text=f"{float(v):.0%}"),
                 showvalue=False, length=280,
                 bg=C["card"], fg=C["text"],
                 highlightbackground=C["card"],
                 troughcolor=C["border"],
                 activebackground=C["accent"]).pack(side="left")
        self._opacity_label.pack(side="left", padx=10)

        # Notifications
        outer4, c4 = _card_frame(page, "托盘通知")
        outer4.pack(fill="x", pady=10)
        self._notify_var = tk.BooleanVar()
        tk.Checkbutton(c4, text="显示托盘通知（模型就绪、录音状态等）",
                       variable=self._notify_var,
                       font=("Microsoft YaHei", 10),
                       bg=C["card"], fg=C["text"],
                       activebackground=C["card"],
                       selectcolor=C["card"]).pack(anchor="w")

    # ── Action buttons ──────────────────────────────────

    def _build_action_buttons(self):
        bf = tk.Frame(self._win, bg=C["bg"])
        bf.pack(fill="x", padx=28, pady=(16, 18))

        RoundedButton(bf, "恢复默认", C["reset"],
                      self._reset_defaults,
                      width=100, height=36, radius=10).pack(side="left")

        RoundedButton(bf, "保存设置", C["save"],
                      self._do_save,
                      width=130, height=42, radius=12).pack(side="right")

    # ── Helpers ──────────────────────────────────────────

    def _browse_model(self):
        path = filedialog.askdirectory(title="选择模型目录")
        if path:
            self._model_path_var.set(path)

    def _pick_color(self, color: str):
        self._color_var.set(color)
        for f, hx in self._color_btns:
            bw = 3 if hx == color else 2
            f.configure(highlightbackground=("#333" if hx == color else hx),
                        highlightthickness=bw)

    # ── Data I/O ────────────────────────────────────────

    def _load_to_ui(self):
        hk = self._config.get("hotkeys", {})
        for key, (mod_var, key_var) in self._hk_widgets.items():
            val = hk.get(key)
            if val and "+" in val:
                parts = val.rsplit("+", 1)
                mod_map = {"ctrl": "Ctrl", "alt": "Alt", "shift": "Shift"}
                mod_var.set(mod_map.get(parts[0].strip().lower(), parts[0].strip()))
                key_var.set(parts[1].strip())
            elif val:
                mod_var.set("None")
                key_var.set(val.strip())
            else:
                mod_var.set("None")
                key_var.set("")

        m = self._config.get("model", {})
        self._model_path_var.set(m.get("path", ""))
        self._device_var.set(m.get("device", "cuda"))
        self._compute_var.set(m.get("compute_type", "float16"))

        a = self._config.get("appearance", {})
        color = a.get("indicator_color", "#F44336")
        self._color_var.set(color)
        self._pick_color(color)
        self._pos_var.set(a.get("indicator_position", "top"))
        self._opacity_var.set(a.get("indicator_opacity", 0.88))
        self._opacity_label.config(
            text=f"{a.get('indicator_opacity', 0.88):.0%}")
        self._notify_var.set(a.get("show_tray_notifications", True))

    def _save_from_ui(self) -> dict:
        hk = {}
        for key, (mod_var, key_var) in self._hk_widgets.items():
            mod = mod_var.get().strip()
            k = key_var.get().strip()
            if k:
                hk[key] = f"{mod}+{k}" if mod and mod != "None" else k
            else:
                hk[key] = None

        return {
            "hotkeys": hk,
            "model": {
                "path": self._model_path_var.get().strip(),
                "device": self._device_var.get(),
                "compute_type": self._compute_var.get(),
            },
            "appearance": {
                "indicator_color": self._color_var.get(),
                "indicator_position": self._pos_var.get(),
                "indicator_opacity": round(self._opacity_var.get(), 2),
                "show_tray_notifications": self._notify_var.get(),
            },
        }

    def _do_save(self):
        new_config = self._save_from_ui()
        self._config.clear()
        self._config.update(new_config)
        self._on_save(new_config)
        self._win.destroy()

    def _reset_defaults(self):
        if not messagebox.askyesno("恢复默认",
                                   "确定要恢复所有设置为默认值吗？",
                                   parent=self._win):
            return
        from voice_input_config import DEFAULT_CONFIG
        self._config.clear()
        self._config.update(DEFAULT_CONFIG)
        self._load_to_ui()

    @staticmethod
    def show(parent_root: tk.Tk, config: dict, on_save):
        try:
            sw = SettingsWindow(parent_root, config, on_save)
            sw._win.wait_window()
        except Exception as e:
            log.error("Settings window failed: %s", e, exc_info=True)
