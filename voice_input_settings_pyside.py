"""
PySide6 glass settings window for Voice Input.
Integrates with voice_input.py: receives config dict + on_save callback.
"""
import sys
import ctypes
import ctypes.wintypes

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QComboBox, QSlider, QCheckBox,
    QRadioButton, QLineEdit, QGraphicsDropShadowEffect,
    QFileDialog,
)
from PySide6.QtCore import Qt, QPoint, QEvent, QTimer
from PySide6.QtGui import QColor, QBitmap, QPainter

from voice_input_autostart import is_enabled as autostart_is_enabled


# ═══════════════════════════════════════════════════════════
# Windows acrylic
# ═══════════════════════════════════════════════════════════

class ACCENTPOLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState",   ctypes.c_int),
        ("AccentFlags",   ctypes.c_int),
        ("GradientColor", ctypes.c_int),
        ("AnimationId",   ctypes.c_int),
    ]

class WINCOMPATTRDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute",  ctypes.c_int),
        ("Data",       ctypes.POINTER(ACCENTPOLICY)),
        ("SizeOfData", ctypes.c_size_t),
    ]

def enable_acrylic(widget, tint_rgb=(255, 255, 255), alpha=0x03):
    hwnd = int(widget.winId())
    r, g, b = tint_rgb
    gradient = (alpha << 24) | (b << 16) | (g << 8) | r
    accent = ACCENTPOLICY()
    accent.AccentState = 3
    accent.GradientColor = gradient
    data = WINCOMPATTRDATA()
    data.Attribute = 19
    data.Data = ctypes.pointer(accent)
    data.SizeOfData = ctypes.sizeof(accent)
    ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))


# ═══════════════════════════════════════════════════════════
# KeyCaptureButton
# ═══════════════════════════════════════════════════════════

KEY_NAMES = {
    Qt.Key_Plus: "Num +", Qt.Key_Minus: "Num -",
    Qt.Key_Asterisk: "Num *", Qt.Key_Slash: "Num /",
    Qt.Key_Period: "Num .",
    Qt.Key_0: "0", Qt.Key_1: "1", Qt.Key_2: "2", Qt.Key_3: "3",
    Qt.Key_4: "4", Qt.Key_5: "5", Qt.Key_6: "6", Qt.Key_7: "7",
    Qt.Key_8: "8", Qt.Key_9: "9",
    Qt.Key_A: "A", Qt.Key_B: "B", Qt.Key_C: "C", Qt.Key_D: "D",
    Qt.Key_E: "E", Qt.Key_F: "F", Qt.Key_G: "G", Qt.Key_H: "H",
    Qt.Key_I: "I", Qt.Key_J: "J", Qt.Key_K: "K", Qt.Key_L: "L",
    Qt.Key_M: "M", Qt.Key_N: "N", Qt.Key_O: "O", Qt.Key_P: "P",
    Qt.Key_Q: "Q", Qt.Key_R: "R", Qt.Key_S: "S", Qt.Key_T: "T",
    Qt.Key_U: "U", Qt.Key_V: "V", Qt.Key_W: "W", Qt.Key_X: "X",
    Qt.Key_Y: "Y", Qt.Key_Z: "Z",
    Qt.Key_F1: "F1", Qt.Key_F2: "F2", Qt.Key_F3: "F3",
    Qt.Key_F4: "F4", Qt.Key_F5: "F5", Qt.Key_F6: "F6",
    Qt.Key_F7: "F7", Qt.Key_F8: "F8", Qt.Key_F9: "F9",
    Qt.Key_F10: "F10", Qt.Key_F11: "F11", Qt.Key_F12: "F12",
    Qt.Key_Space: "Space", Qt.Key_Return: "Enter",
    Qt.Key_Tab: "Tab", Qt.Key_Backspace: "Backspace",
    Qt.Key_Delete: "Delete", Qt.Key_Escape: "Esc",
    Qt.Key_Up: "↑", Qt.Key_Down: "↓",
    Qt.Key_Left: "←", Qt.Key_Right: "→",
}

class KeyCaptureButton(QPushButton):
    def __init__(self, text="点击录制", parent=None, on_captured=None):
        super().__init__(text, parent)
        self._on_captured = on_captured
        self._capturing = False
        self._original_text = text
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("keycap_btn")
        self.setStyleSheet(
            "#keycap_btn {"
            "  background: rgba(255,255,255,12);"
            "  border: 1px solid rgba(255,255,255,60);"
            "  border-radius: 8px;"
            "  padding: 6px 16px;"
            "  font-weight: bold;"
            "  color: #FFFFFF;"
            "  min-width: 80px;"
            "}"
            "#keycap_btn:hover { background: rgba(255,255,255,25); }"
            "#keycap_btn:checked { background: rgba(255,255,100,40); }")

    def mousePressEvent(self, e):
        if self._capturing:
            self._capturing = False
            self.setChecked(False)
            self.setText(self._original_text)
            self.releaseKeyboard()
        else:
            self._capturing = True
            self.setChecked(True)
            self.setText("...")
            self.grabKeyboard()
        super().mousePressEvent(e)

    def keyPressEvent(self, e):
        if self._capturing:
            name = KEY_NAMES.get(e.key())
            if name is None:
                name = e.text().upper() if e.text() else None
            if name is None:
                return
            self._original_text = name
            self.setText(name)
            self._capturing = False
            self.setChecked(False)
            self.releaseKeyboard()
            if self._on_captured:
                self._on_captured(name)

    def set_key(self, key_name):
        self._original_text = key_name
        self.setText(key_name)
        self._capturing = False
        self.setChecked(False)


# ═══════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════

def add_shadow(widget, color=QColor(0, 0, 0, 160), radius=6, dx=0, dy=1):
    effect = QGraphicsDropShadowEffect()
    effect.setBlurRadius(radius)
    effect.setColor(color)
    effect.setOffset(dx, dy)
    widget.setGraphicsEffect(effect)

def L(text, bold=False, size=13, color="#FFFFFF", shadow=True):
    lbl = QLabel(text)
    wgt = "bold" if bold else "normal"
    lbl.setStyleSheet(
        f"color: {color}; font-weight: {wgt}; font-size: {size}px; background: transparent;")
    if shadow:
        add_shadow(lbl)
    return lbl


# ═══════════════════════════════════════════════════════════
# Theme
# ═══════════════════════════════════════════════════════════

T = {
    "glow":       "rgba(255,255,255,140)",
    "glow_soft":  "rgba(255,255,255,70)",
    "text":       "#FFFFFF",
    "text_dim":   "#D8D0CC",
    "input_bg":   "rgba(255,255,255,15)",
    "tab_bg":     "rgba(255,255,255,20)",
    "tab_active": "rgba(255,255,255,160)",
    "green":      "rgba(120,200,135,210)",
    "red":        "rgba(220,120,120,210)",
}

STYLE = f"""
* {{
    font-family: "Microsoft YaHei";
    font-size: 13px;
    font-weight: bold;
    color: {T["text"]};
    background: rgba(255,255,255,2);
}}

#card {{
    background: transparent;
    border: 1px solid {T["glow_soft"]};
    border-radius: 14px;
    padding: 16px;
}}

#tab_btn, #tab_btn_active {{
    border: 1px solid {T["glow_soft"]};
    border-radius: 10px;
    padding: 8px 20px;
    font-weight: bold;
}}
#tab_btn         {{ background: {T["tab_bg"]}; }}
#tab_btn:hover   {{ background: rgba(255,255,255,60); border-color: rgba(255,255,255,140); }}
#tab_btn_active  {{ background: {T["tab_active"]}; color: #1A1A1A; border-color: {T["glow"]}; }}

#save_btn {{
    background: {T["green"]};
    color: #FFFFFF;
    font-size: 14px;
    padding: 12px 36px;
    border: 1px solid rgba(255,255,255,100);
    border-radius: 12px;
    font-weight: bold;
}}
#save_btn:hover {{ background: rgba(140,220,155,230); }}

#reset_btn {{
    background: {T["red"]};
    color: #FFFFFF;
    padding: 8px 20px;
    border: 1px solid rgba(255,255,255,80);
    border-radius: 10px;
    font-weight: bold;
}}
#reset_btn:hover {{ background: rgba(240,140,140,230); }}

#browse_btn {{
    background: rgba(255,255,255,100);
    color: #1A1A1A;
    padding: 6px 16px;
    border: 1px solid {T["glow"]};
    border-radius: 6px;
    font-weight: bold;
}}
#browse_btn:hover {{ background: rgba(255,255,255,160); }}

#close_btn, #min_btn {{
    background: transparent;
    color: {T["text"]};
    font-size: 18px;
    font-weight: bold;
    padding: 4px 10px;
    border: none;
    border-radius: 6px;
}}
#close_btn:hover {{ background: rgba(220,100,100,180); color: white; }}
#min_btn:hover   {{ background: rgba(255,255,255,30); }}

#swatch_btn {{
    border: 1px solid rgba(255,255,255,60);
    border-radius: 8px;
}}
#swatch_btn:hover {{ border: 2px solid rgba(255,255,255,180); }}
#swatch_btn:checked {{ border: 3px solid #FFFFFF; }}

QLineEdit {{
    background: {T["input_bg"]};
    border: 1px solid {T["glow_soft"]};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 12px;
}}

QComboBox {{
    background: {T["input_bg"]};
    border: 1px solid {T["glow_soft"]};
    border-radius: 8px;
    padding: 6px 12px;
    min-width: 80px;
}}
QComboBox:hover {{ background: rgba(255,255,255,25); }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background: rgba(20,20,20,200);
    border: 1px solid {T["glow"]};
    selection-background-color: rgba(255,255,255,80);
}}

QSlider::groove:horizontal {{
    border: none; height: 4px;
    background: rgba(255,255,255,12);
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {T["glow"]};
    width: 16px; height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}}
QSlider::handle:horizontal:hover {{ background: rgba(255,255,255,200); }}
QSlider::sub-page:horizontal {{
    background: rgba(255,255,255,80);
    border-radius: 2px;
}}

QCheckBox::indicator {{
    width: 18px; height: 18px;
    border-radius: 4px;
    border: 1px solid {T["glow_soft"]};
    background: {T["input_bg"]};
}}
QCheckBox::indicator:hover {{ border-color: {T["glow"]}; }}
QCheckBox::indicator:checked {{
    background: rgba(255,255,255,120);
    border-color: {T["glow"]};
}}

QRadioButton::indicator {{
    width: 16px; height: 16px;
    border-radius: 8px;
    border: 2px solid {T["glow_soft"]};
    background: {T["input_bg"]};
}}
QRadioButton::indicator:hover {{ border-color: {T["glow"]}; }}
QRadioButton::indicator:checked {{
    background: rgba(255,255,255,140);
    border-color: {T["glow"]};
}}
"""


# ═══════════════════════════════════════════════════════════
# Main settings window
# ═══════════════════════════════════════════════════════════

class GlassSettingsWindow(QWidget):
    """PySide6 glass settings window. Use GlassSettingsWindow.show(config, on_save)."""

    _KNOWN_MODS = {"None", "Ctrl", "Alt", "Shift"}
    _MOD_LOWER_TO_CASE = {"none": "None", "ctrl": "Ctrl", "alt": "Alt", "shift": "Shift"}
    _INTERACTIVE = (QPushButton, QComboBox, QSlider, QCheckBox, QRadioButton, QLineEdit)
    COLORS = ["#F44336", "#FF9800", "#FFEB3B", "#4CAF50",
              "#2196F3", "#9C27B0", "#FAFAFA", "#607D8B"]

    def __init__(self, config, on_save):
        super().__init__()
        self._config = config
        self._on_save = on_save
        self._current_tab = None
        self._drag_pos = None
        self._build()

    # ── paintEvent: alpha fill for DWM hit-test ──
    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(255, 255, 255, 2))

    # ── showEvent: DWM round corners + Qt mask ──
    def showEvent(self, event):
        super().showEvent(event)
        hwnd = int(self.winId())
        w, h = self.width(), self.height()
        r = 14
        # Win11 DWM native rounded corners
        try:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 33, ctypes.byref(ctypes.c_int(2)),
                ctypes.sizeof(ctypes.c_int))
        except Exception:
            pass
        # Qt bitmap mask (fallback)
        bmp = QBitmap(self.size())
        bmp.fill(Qt.color0)
        p = QPainter(bmp)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(Qt.color1)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(self.rect(), r, r)
        p.end()
        self.setMask(bmp)

    # ── nativeEvent: HTCLIENT → deliver mouse events ──
    def nativeEvent(self, eventType, message):
        if eventType == "windows_generic_MSG":
            msg = ctypes.wintypes.MSG.from_address(int(message))
            if msg.message == 0x0084:  # WM_NCHITTEST
                return True, 1  # HTCLIENT
        return False, 0

    # ── eventFilter: drag on non-interactive areas ──
    def eventFilter(self, obj, event):
        if isinstance(obj, self._INTERACTIVE):
            return False
        if isinstance(obj, QWidget):
            w = obj
            while w is not None:
                if w is self:
                    break
                w = w.parentWidget()
            else:
                return False
        else:
            return False
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
        elif event.type() == QEvent.MouseMove and self._drag_pos is not None:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
        elif event.type() == QEvent.MouseButtonRelease:
            self._drag_pos = None
        return False

    # ═════════════════════════════════════════════════════════
    # Build UI
    # ═════════════════════════════════════════════════════════

    def _build(self):
        self.setWindowTitle("衔音令 设置")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(540, 740)
        self.setStyleSheet("background: transparent;")
        enable_acrylic(self, tint_rgb=(255, 255, 255), alpha=0x03)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        container = QWidget()
        container.setObjectName("container")
        container.setStyleSheet(
            "#container {"
            f"  background: transparent;"
            f"  border: 1px solid {T['glow']};"
            "  border-radius: 14px;"
            "}")
        outer.addWidget(container)

        root = QVBoxLayout(container)
        root.setContentsMargins(24, 0, 24, 18)
        root.setSpacing(0)

        self._build_titlebar(root)

        root.addSpacing(12)
        tab_row = QHBoxLayout()
        tab_row.setSpacing(8)
        self._tab_btns = {}
        for key, text in [("shortcuts", "快捷键"), ("model", "模型"),
                          ("appearance", "外观"), ("general", "常规")]:
            btn = QPushButton(text)
            btn.setObjectName("tab_btn_active" if key == "shortcuts" else "tab_btn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._switch_tab(k))
            self._tab_btns[key] = btn
            tab_row.addWidget(btn)
        tab_row.addStretch()
        root.addLayout(tab_row)
        root.addSpacing(12)

        self._pages = {}
        self._stack = QVBoxLayout()
        self._stack.setSpacing(8)
        root.addLayout(self._stack)

        self._build_shortcuts()
        self._build_model()
        self._build_appearance()
        self._build_general()
        self._switch_tab("shortcuts")

        root.addSpacing(16)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        reset = QPushButton("恢复默认")
        reset.setObjectName("reset_btn")
        reset.setCursor(Qt.PointingHandCursor)
        reset.clicked.connect(self._reset_defaults)
        btn_row.addWidget(reset)
        btn_row.addStretch()
        save = QPushButton("保存设置")
        save.setObjectName("save_btn")
        save.setCursor(Qt.PointingHandCursor)
        save.clicked.connect(self._save_settings)
        self._save_btn = save
        btn_row.addWidget(save)
        root.addLayout(btn_row)

        QApplication.instance().installEventFilter(self)

    def _build_titlebar(self, root):
        bar = QWidget()
        bar.setFixedHeight(64)
        bar.setStyleSheet("background: transparent;")
        vbox = QVBoxLayout(bar)
        vbox.setContentsMargins(16, 4, 8, 0)
        vbox.setSpacing(2)
        row = QHBoxLayout()
        row.setSpacing(4)
        row.addWidget(L("✦  衔音令  设置", bold=True, size=13))
        row.addStretch()
        min_btn = QPushButton("—")
        min_btn.setObjectName("min_btn")
        min_btn.setFixedSize(32, 28)
        min_btn.setCursor(Qt.PointingHandCursor)
        min_btn.clicked.connect(lambda: self.showMinimized())
        row.addWidget(min_btn)
        close_btn = QPushButton("✕")
        close_btn.setObjectName("close_btn")
        close_btn.setFixedSize(32, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self._on_close)
        row.addWidget(close_btn)
        vbox.addLayout(row)
        sub = QLabel("自定义快捷键、语音模型与外观样式")
        sub.setStyleSheet(
            f"color: {T['text_dim']}; font-size: 10px; background: transparent; padding: 0 4px;")
        vbox.addWidget(sub)
        root.addWidget(bar)

    def _on_close(self):
        self.hide()
        QApplication.instance().quit()

    # ═════════════════════════════════════════════════════════
    # Tab switching
    # ═════════════════════════════════════════════════════════

    def _switch_tab(self, key):
        if self._current_tab == key:
            return
        if self._current_tab in self._pages:
            self._pages[self._current_tab].hide()
        for k, b in self._tab_btns.items():
            b.setObjectName("tab_btn_active" if k == key else "tab_btn")
            b.style().unpolish(b)
            b.style().polish(b)
        self._pages[key].show()
        self._current_tab = key

    def _card(self, title=""):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        if title:
            layout.addWidget(L(title, bold=True, size=13, color="#FFFFFF"))
        return card, layout

    # ═════════════════════════════════════════════════════════
    # Shortcuts page
    # ═════════════════════════════════════════════════════════

    def _build_shortcuts(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._sc_fields = {}
        for section_key, title, desc in [
            ("record",   "录制 / 停止", "按下快捷键开始录音，再次按下停止并识别"),
            ("exit",     "退出程序",     "按下快捷键退出语音输入"),
            ("settings", "打开设置",     "按下快捷键打开此设置窗口"),
        ]:
            card, cl = self._card(title)
            cl.addWidget(L(desc, size=10, color="#C8C0BC"))
            row = QHBoxLayout()
            row.setSpacing(8)
            row.addWidget(L("修饰键", size=13))
            mod = QComboBox()
            mod.addItems(["None", "Ctrl", "Alt", "Shift"])
            row.addWidget(mod)
            row.addSpacing(12)
            row.addWidget(L("按键", size=13))
            cap = KeyCaptureButton(parent=page)
            row.addWidget(cap)
            row.addStretch()
            cl.addLayout(row)
            layout.addWidget(card)
            self._sc_fields[section_key] = {"mod": mod, "key": cap}

        layout.addStretch()
        page.hide()
        self._stack.addWidget(page)
        self._pages["shortcuts"] = page
        self._load_shortcuts_from_config()

    def _parse_hotkey(self, val):
        if val is None:
            return "None", ""
        val = val.strip()
        if "+" not in val:
            return "None", val
        parts = val.rsplit("+", 1)
        mod, key = parts[0].strip(), parts[1].strip()
        # Case-insensitive match config's lowercase to UI title-case
        mod_case = self._MOD_LOWER_TO_CASE.get(mod.lower())
        if mod_case:
            return mod_case, key
        # If not a known modifier, the whole string might just be a key name
        return "None", val

    def _load_shortcuts_from_config(self):
        hotkeys = self._config.get("hotkeys", {})
        for sk, fallback_mod, fallback_key in [
            ("record", "Alt", "Num +"),
            ("exit", "Alt", "Num -"),
            ("settings", "None", "点击录制"),
        ]:
            val = hotkeys.get(sk, None)
            if val is None:
                # Config explicitly stores None for unset (e.g. settings hotkey)
                mod_name, key_name = fallback_mod, fallback_key
            else:
                mod_name, key_name = self._parse_hotkey(val)
            fields = self._sc_fields.get(sk)
            if fields:
                idx = fields["mod"].findText(mod_name)
                if idx >= 0:
                    fields["mod"].setCurrentIndex(idx)
                fields["key"].set_key(key_name)

    def _collect_shortcuts(self):
        result = {}
        for sk, fields in self._sc_fields.items():
            mod = fields["mod"].currentText()
            key = fields["key"].text()
            # If key is still the placeholder, treat as unconfigured (None)
            if key == "点击录制":
                result[sk] = None
            elif mod == "None":
                result[sk] = key
            else:
                result[sk] = f"{mod}+{key}"
        return result

    # ═════════════════════════════════════════════════════════
    # Model page
    # ═════════════════════════════════════════════════════════

    def _build_model(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        card1, c1 = self._card("模型路径")
        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        self._model_path_le = QLineEdit()
        path_row.addWidget(self._model_path_le)
        browse = QPushButton("浏览...")
        browse.setObjectName("browse_btn")
        browse.setCursor(Qt.PointingHandCursor)
        browse.clicked.connect(self._browse_model_path)
        path_row.addWidget(browse)
        c1.addLayout(path_row)
        layout.addWidget(card1)

        card2, c2 = self._card("运行设备")
        dev_row = QHBoxLayout()
        dev_row.setSpacing(8)
        dev_row.addWidget(L("设备", size=13))
        self._model_device_cb = QComboBox()
        self._model_device_cb.addItems(["cuda", "cpu"])
        dev_row.addWidget(self._model_device_cb)
        dev_row.addSpacing(16)
        dev_row.addWidget(L("精度", size=13))
        self._model_prec_cb = QComboBox()
        self._model_prec_cb.addItems(["float16", "int8", "bfloat16"])
        dev_row.addWidget(self._model_prec_cb)
        dev_row.addStretch()
        c2.addLayout(dev_row)
        layout.addWidget(card2)

        layout.addStretch()
        page.hide()
        self._stack.addWidget(page)
        self._pages["model"] = page

        mc = self._config.get("model", {})
        self._model_path_le.setText(mc.get("path", ""))
        di = self._model_device_cb.findText(mc.get("device", "cuda"))
        if di >= 0:
            self._model_device_cb.setCurrentIndex(di)
        pi = self._model_prec_cb.findText(mc.get("compute_type", "float16"))
        if pi >= 0:
            self._model_prec_cb.setCurrentIndex(pi)

    def _browse_model_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择模型目录",
                                                 self._model_path_le.text())
        if path:
            self._model_path_le.setText(path)

    def _collect_model(self):
        return {
            "path": self._model_path_le.text(),
            "device": self._model_device_cb.currentText(),
            "compute_type": self._model_prec_cb.currentText(),
        }

    # ═════════════════════════════════════════════════════════
    # Appearance page
    # ═════════════════════════════════════════════════════════

    def _build_appearance(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        card1, c1 = self._card("指示器颜色")
        swatch_row = QHBoxLayout()
        swatch_row.setSpacing(6)
        self._swatch_btns = {}
        for c in self.COLORS:
            dot = QPushButton("")
            dot.setFixedSize(32, 26)
            dot.setObjectName("swatch_btn")
            dot.setCheckable(True)
            dot.setStyleSheet(
                f"#swatch_btn {{ background: {c}; border-radius: 6px; "
                f"border: 1px solid rgba(255,255,255,60); }}"
                f"#swatch_btn:hover {{ border: 2px solid rgba(255,255,255,180); }}"
                f"#swatch_btn:checked {{ border: 3px solid #FFFFFF; }}")
            dot.setCursor(Qt.PointingHandCursor)
            dot.clicked.connect(lambda checked, col=c: self._on_color_pick(col))
            self._swatch_btns[c] = dot
            swatch_row.addWidget(dot)
        swatch_row.addStretch()
        c1.addLayout(swatch_row)
        layout.addWidget(card1)

        card2, c2 = self._card("指示器位置")
        pos_row = QHBoxLayout()
        pos_row.setSpacing(24)
        self._pos_top = QRadioButton("屏幕顶部")
        self._pos_bot = QRadioButton("屏幕底部")
        self._pos_top.setStyleSheet("background: transparent; font-weight: bold;")
        self._pos_bot.setStyleSheet("background: transparent; font-weight: bold;")
        pos_row.addWidget(self._pos_top)
        pos_row.addWidget(self._pos_bot)
        pos_row.addStretch()
        c2.addLayout(pos_row)
        layout.addWidget(card2)

        card3, c3 = self._card("不透明度")
        op_row = QHBoxLayout()
        op_row.setSpacing(12)
        self._op_slider = QSlider(Qt.Horizontal)
        self._op_slider.setRange(30, 100)
        op_row.addWidget(self._op_slider)
        self._op_label = L("88%", size=13)
        op_row.addWidget(self._op_label)
        self._op_slider.valueChanged.connect(self._on_opacity_change)
        c3.addLayout(op_row)
        layout.addWidget(card3)

        card4, c4 = self._card("托盘通知")
        self._tray_cb = QCheckBox("显示托盘通知（模型就绪、录音状态等）")
        self._tray_cb.setStyleSheet("font-weight: bold;")
        c4.addWidget(self._tray_cb)
        layout.addWidget(card4)

        layout.addStretch()
        page.hide()
        self._stack.addWidget(page)
        self._pages["appearance"] = page

        ac = self._config.get("appearance", {})
        self._on_color_pick(ac.get("indicator_color", "#F44336"))
        if ac.get("indicator_position") == "top":
            self._pos_top.setChecked(True)
        else:
            self._pos_bot.setChecked(True)
        self._op_slider.setValue(int(ac.get("indicator_opacity", 0.88) * 100))
        self._tray_cb.setChecked(ac.get("show_tray_notifications", True))

    def _on_color_pick(self, color):
        self._selected_color = color
        for c, btn in self._swatch_btns.items():
            btn.setChecked(c == color)

    def _on_opacity_change(self, val):
        self._op_label.setText(f"{val}%")

    def _collect_appearance(self):
        return {
            "indicator_color": getattr(self, '_selected_color', '#F44336'),
            "indicator_position": "top" if self._pos_top.isChecked() else "bottom",
            "indicator_opacity": self._op_slider.value() / 100.0,
            "show_tray_notifications": self._tray_cb.isChecked(),
        }

    # ═════════════════════════════════════════════════════════
    # General page
    # ═════════════════════════════════════════════════════════

    def _build_general(self):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        card, c = self._card("开机自启")
        self._autostart_cb = QCheckBox("登录 Windows 后自动启动衔音令")
        self._autostart_cb.setStyleSheet("font-weight: bold;")
        c.addWidget(self._autostart_cb)
        c.addWidget(L("勾选后，开机登录即自动在后台运行，无需手动启动。", size=10, color="#C8C0BC"))
        layout.addWidget(card)

        layout.addStretch()
        page.hide()
        self._stack.addWidget(page)
        self._pages["general"] = page

        gc = self._config.get("general", {})
        # Reflect reality: config is source of truth, but also check the actual
        # shortcut so a pre-existing manual setup shows as enabled.
        self._autostart_cb.setChecked(
            gc.get("autostart", False) or autostart_is_enabled())

    def _collect_general(self):
        return {"autostart": self._autostart_cb.isChecked()}

    # ═════════════════════════════════════════════════════════
    # Save / Reset
    # ═════════════════════════════════════════════════════════

    def _save_settings(self):
        new_config = {}
        new_config["hotkeys"] = self._collect_shortcuts()
        new_config["model"] = self._collect_model()
        new_config["appearance"] = self._collect_appearance()
        new_config["general"] = self._collect_general()
        # Merge into original config to keep any extra keys
        self._config.clear()
        self._config.update(new_config)
        self._on_save(new_config)
        self._flash_button("保存成功 ✓", "#4CAF50")
        QTimer.singleShot(800, self._on_close)

    def _reset_defaults(self):
        from voice_input_config import DEFAULT_CONFIG
        self._config.clear()
        self._config.update(DEFAULT_CONFIG)
        self._load_shortcuts_from_config()
        mc = self._config.get("model", {})
        self._model_path_le.setText(mc.get("path", ""))
        di = self._model_device_cb.findText(mc.get("device", "cuda"))
        if di >= 0:
            self._model_device_cb.setCurrentIndex(di)
        pi = self._model_prec_cb.findText(mc.get("compute_type", "float16"))
        if pi >= 0:
            self._model_prec_cb.setCurrentIndex(pi)
        ac = self._config.get("appearance", {})
        self._on_color_pick(ac.get("indicator_color", "#F44336"))
        self._pos_bot.setChecked(ac.get("indicator_position") != "top")
        self._pos_top.setChecked(ac.get("indicator_position") == "top")
        self._op_slider.setValue(int(ac.get("indicator_opacity", 0.88) * 100))
        self._tray_cb.setChecked(ac.get("show_tray_notifications", True))
        gc = self._config.get("general", {})
        self._autostart_cb.setChecked(gc.get("autostart", False))
        self._flash_button("已恢复默认", "#FF9800")

    def _flash_button(self, msg, color):
        btn = self._save_btn
        old_text = btn.text()
        old_style = btn.styleSheet()
        btn.setText(msg)
        btn.setStyleSheet(
            f"background: {color}; color: #FFF; font-size: 14px;"
            "padding: 12px 36px; border-radius: 12px; font-weight: bold;"
            f"border: 1px solid rgba(255,255,255,100);")
        QTimer.singleShot(1500, lambda: (
            btn.setText(old_text),
            btn.setStyleSheet(old_style),
        ))

    # ═════════════════════════════════════════════════════════
    # Static show method — called from voice_input.py
    # ═════════════════════════════════════════════════════════

    @staticmethod
    def show_settings(config, on_save):
        """Open the PySide6 glass settings window.
        Blocks until the window is closed via save or close button.
        """
        import shiboken6

        old = QApplication.instance()
        if old is not None:
            old.quit()
            QApplication.processEvents()
            shiboken6.delete(old)

        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        app.setStyleSheet(STYLE)

        win = GlassSettingsWindow(config, on_save)
        win.show()
        app.exec()
        del win
