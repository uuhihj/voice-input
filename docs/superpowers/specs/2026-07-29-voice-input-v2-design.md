# Voice Input v2 — Settings GUI + Packaging Design

## Overview

Add a樱花粉 GUI settings page to configure hotkeys/model/appearance, refactor monolith into modules, and package as portable zip for non-technical users.

## File Structure

```
VoiceInput/                      ← distribution folder
├── VoiceInput.exe               ← PyInstaller single-file entry
├── models/
│   └── faster-whisper-large-v3/ ← bundled model
├── voice_input_config.json      ← auto-generated on first run
└── 使用说明.txt

dev/
├── voice_input.py               ← entry point, tray, hotkeys, recording, transcription (~250 lines)
├── voice_input_config.py        ← JSON config read/write, defaults, validation (~60 lines)
├── voice_input_settings.py      ← tkinter settings window UI (~150 lines)
├── voice_input_indicator.py     ← floating recording overlay (~40 lines)
├── voice_input.spec             ← PyInstaller config
├── voice_input_launcher.vbs     ← auto-start (unchanged)
└── voice_input_launcher.bat     ← dev launcher (unchanged)
```

## Module Responsibilities

### voice_input.py (main)
- CUDA DLL preloading
- Whisper model loading (main thread, before tk)
- System tray (pystray) with right-click menu: "设置" / "退出"
- Global hotkey registration (re-bindable via config)
- Audio recording (sounddevice)
- Transcription (faster-whisper + CPU fallback)
- Text output (keyboard.write)
- Floating indicator management
- Logging to `%TEMP%/voice_input.log`

### voice_input_config.py
- `CONFIG_PATH` = `voice_input_config.json` next to exe/py
- `DEFAULT_CONFIG` dict with all defaults
- `load_config()` → dict, creates default if missing
- `save_config(dict)` → write JSON with indentation
- `validate_config(dict)` → check key existence, types, ranges

### voice_input_settings.py
- `SettingsWindow(tk.Toplevel)` class
- Three tabs via `ttk.Notebook`: Shortcuts / Model / Appearance
- Sakura pink theme (#FFE4E1 base, #FFF5F5 cards, #E88A8A accents)
- Card-style layout with border shadows for depth
- Dropdowns for modifier keys and key selection
- Save / Reset Defaults buttons
- On save: writes config → re-registers hotkeys → applies appearance

### voice_input_indicator.py
- `FloatingIndicator` class
- `show()` / `hide()` / `update_style(color, position, opacity)`
- Creates tkinter Toplevel on main thread via `after()`

## Config Schema (voice_input_config.json)

```json
{
  "hotkeys": {
    "record": "alt+num add",
    "exit": "alt+num subtract",
    "settings": null
  },
  "model": {
    "path": "models/faster-whisper-large-v3",
    "device": "cuda",
    "compute_type": "float16"
  },
  "appearance": {
    "indicator_color": "#F44336",
    "indicator_position": "top",
    "indicator_opacity": 0.88,
    "show_tray_notifications": true
  }
}
```

## Settings Window UI Design

```
┌──────────────────────────────────────┐
│  🎤 Voice Input 设置                │
├──────────────────────────────────────┤
│  [⌨️ 快捷键] [🧠 模型] [🎨 外观]   │
├──────────────────────────────────────┤
│  ┌──────────────────────────────┐   │
│  │  录制/停止                   │   │
│  │  修饰键: [Alt ▾]  按键: [+] │   │
│  ├──────────────────────────────┤   │
│  │  退出程序                    │   │
│  │  修饰键: [Alt ▾]  按键: [-] │   │
│  ├──────────────────────────────┤   │
│  │  打开设置（可选）            │   │
│  │  修饰键: [无 ▾]  按键: [无] │   │
│  └──────────────────────────────┘   │
│                                      │
│  [恢复默认]              [保存]     │
└──────────────────────────────────────┘
```

### Color Palette
- Window background: #FFE4E1 (sakura/MistyRose)
- Card background: #FFF5F5
- Card border: #F0C0C0
- Title/accent: #E88A8A
- Text: #5D4037 (warm brown)
- Tab selected: #FFB6C1 (LightPink)

### Depth Simulation
- Cards use `Frame(borderwidth=1, relief="solid")` with light border
- Outer wrapper Frame offset 1-2px with slightly darker color for pseudo-shadow
- Input fields elevated with `relief="groove"`

## Packing Strategy

### Tool: PyInstaller
- Entry script: `voice_input.py`
- Output: single exe (--onefile) + external model folder
- Hidden imports: faster_whisper, ctranslate2, tokenizers, sounddevice, keyboard, pystray, PIL, zhconv
- Data: models/ folder copied alongside exe
- Binaries: CUDA DLLs from nvidia packages

### Distribution Zip
```
VoiceInput_v2.0.zip
└── VoiceInput/
    ├── VoiceInput.exe
    ├── models/
    │   └── faster-whisper-large-v3/
    ├── voice_input_config.json (optional, auto-created)
    └── 使用说明.txt
```

### User Flow
1. Unzip anywhere
2. Double-click VoiceInput.exe
3. Tray icon appears (green)
4. Alt+Numpad+ to record
5. Right-click tray → 设置 to customize

## Implementation Order
1. `voice_input_config.py` — config module (no dependencies)
2. `voice_input_indicator.py` — extract indicator from main
3. `voice_input_settings.py` — settings window
4. `voice_input.py` — refactor to use all modules, add tray "设置" menu
5. `voice_input.spec` — PyInstaller config
6. Build and test exe
7. Package zip
