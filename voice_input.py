#!/usr/bin/env python3
"""
Voice Input — Alt+Numpad+ to record, system tray app.
中英混合 · CUDA · 无窗口 · 托盘运行 · 可配置快捷键
"""

import os
import sys
import wave
import time
import tempfile
import threading
import ctypes
import signal
import logging

import numpy as np
import sounddevice as sd
import keyboard
from PIL import Image, ImageDraw
import pystray
import zhconv
import tkinter as tk

from voice_input_config import load_config, save_config
from voice_input_indicator import FloatingIndicator
from voice_input_settings import SettingsWindow

# ═══════════════════════════════════════════════════════════
# Logging to file (since pythonw has no console)
# ═══════════════════════════════════════════════════════════
LOG_FILE = os.path.join(tempfile.gettempdir(), "voice_input.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("voice_input")

# ═══════════════════════════════════════════════════════════
# Configuration (loaded from JSON at startup)
# ═══════════════════════════════════════════════════════════
_config = load_config()
MODEL_PATH = _config["model"]["path"]
COMPUTE_TYPE = _config["model"]["compute_type"]
DEVICE = _config["model"]["device"]
SAMPLE_RATE = 16000

# ═══════════════════════════════════════════════════════════
# CUDA DLL pre-loading
# ═══════════════════════════════════════════════════════════
def _preload_cuda_dlls():
    site = os.path.join(sys.prefix, "Lib", "site-packages", "nvidia")
    cookies = []
    for pkg in ["cublas\\bin", "cudnn\\bin", "cuda_runtime\\bin",
                "cufft\\bin", "curand\\bin", "cusolver\\bin",
                "cusparse\\bin", "nvjitlink\\bin", "cuda_nvrtc\\bin"]:
        d = os.path.join(site, pkg)
        if os.path.isdir(d):
            try:
                cookies.append(os.add_dll_directory(d))
            except OSError:
                pass
    load_order = [
        "cuda_runtime\\bin\\cudart64_12.dll",
        "cublas\\bin\\cublas64_12.dll",
        "cublas\\bin\\cublasLt64_12.dll",
        "curand\\bin\\curand64_10.dll",
        "cufft\\bin\\cufft64_11.dll",
        "cusparse\\bin\\cusparse64_12.dll",
        "nvjitlink\\bin\\nvJitLink_120.dll",
    ]
    for dll_rel in load_order:
        dll_path = os.path.join(site, dll_rel)
        if os.path.exists(dll_path):
            try:
                ctypes.CDLL(dll_path)
            except Exception:
                pass
    return cookies

_cuda_cookies = _preload_cuda_dlls()
log.info("CUDA DLLs preloaded")

from faster_whisper import WhisperModel

# ═══════════════════════════════════════════════════════════
# Global state
# ═══════════════════════════════════════════════════════════
model: WhisperModel | None = None
recording = False
audio_chunks: list = []
_lock = threading.Lock()
tray_icon: pystray.Icon | None = None
_tk_root: tk.Tk | None = None
_indicator: FloatingIndicator | None = None

def _output_text(text: str):
    """Type text directly at cursor — no clipboard."""
    def _do_type():
        for _ in range(50):
            if not keyboard.is_pressed("alt") and not keyboard.is_pressed("ctrl"):
                break
            time.sleep(0.02)
        time.sleep(0.1)
        keyboard.write(text)
        log.info("Typed: %s", text[:80])
    threading.Thread(target=_do_type, daemon=True).start()

# ═══════════════════════════════════════════════════════════
# Model
# ═══════════════════════════════════════════════════════════
def load_model():
    global model, DEVICE, COMPUTE_TYPE
    model_path = _config["model"]["path"]
    if not os.path.exists(model_path):
        log.error("Model not found: %s", model_path)
        _notify("Model not found", f"Path: {model_path}")
        sys.exit(1)

    device_cfg = _config["model"].get("device", "cuda")
    compute_cfg = _config["model"].get("compute_type", "float16")
    for device, compute in [(device_cfg, compute_cfg), ("cpu", "int8")]:
        try:
            log.info("Loading WhisperModel: device=%s compute=%s", device, compute)
            model = WhisperModel(model_path, device=device, compute_type=compute)
            DEVICE = device
            COMPUTE_TYPE = compute
            log.info("Model loaded successfully on %s/%s", device, compute)
            _set_tray_state("idle")
            if _config["appearance"].get("show_tray_notifications", True) and tray_icon:
                tray_icon.notify(f"Voice Input ready ({DEVICE})", "Voice Input")
            return
        except Exception as e:
            log.error("%s/%s failed: %s", device, compute, e)

    log.critical("Cannot load model on any device")
    _notify("Error", "Cannot load model")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════
# Audio
# ═══════════════════════════════════════════════════════════
def _audio_callback(indata, frames, time_info, status):
    if recording:
        audio_chunks.append(indata.copy())

def record_loop():
    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                            dtype="float32", callback=_audio_callback):
            while recording:
                sd.sleep(50)
    except Exception as e:
        log.error("Audio stream error: %s", e)

def start_recording():
    global recording, audio_chunks
    with _lock:
        if recording:
            return
        audio_chunks = []
        recording = True
    log.info("Recording started")
    threading.Thread(target=record_loop, daemon=True).start()
    _set_tray_state("recording")

def stop_recording_and_transcribe():
    global recording, audio_chunks
    with _lock:
        if not recording:
            return
        recording = False

    log.info("Recording stopped")
    time.sleep(0.2)
    if not audio_chunks:
        log.info("No audio captured")
        _set_tray_state("idle")
        return

    _set_tray_state("processing")
    audio = np.concatenate(audio_chunks, axis=0)
    duration = len(audio) / SAMPLE_RATE
    log.info("Audio: %.1fs, transcribing...", duration)

    tmp_path = os.path.join(tempfile.gettempdir(), "voice_input_tmp.wav")
    try:
        audio_int16 = (audio * 32767).astype(np.int16)
        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_int16.tobytes())

        text = _transcribe_with_fallback(tmp_path)
        log.info("Transcription: %s", text[:100])
        if text.strip():
            threading.Thread(target=_output_text, args=(text,), daemon=True).start()

    except Exception as exc:
        log.error("Transcription error: %s", exc)
    finally:
        _set_tray_state("idle")
        try:
            os.remove(tmp_path)
        except OSError:
            pass

# ═══════════════════════════════════════════════════════════
# Transcription
# ═══════════════════════════════════════════════════════════
def _transcribe_with_fallback(wav_path: str) -> str:
    global model, DEVICE, COMPUTE_TYPE
    try:
        segments, info = model.transcribe(
            wav_path, language=None, beam_size=5, vad_filter=True)
        text = " ".join(seg.text.strip() for seg in segments)
        return _fix_chinese(text, info.language)
    except Exception as e:
        if DEVICE == "cuda":
            log.warning("CUDA transcribe failed: %s, switching to CPU", e)
            model = WhisperModel(_config["model"]["path"],
                                 device="cpu", compute_type="int8")
            DEVICE = "cpu"; COMPUTE_TYPE = "int8"
            segments, info = model.transcribe(
                wav_path, language=None, beam_size=5, vad_filter=True)
            text = " ".join(seg.text.strip() for seg in segments)
            return _fix_chinese(text, info.language)
        return ""


def _fix_chinese(text: str, lang: str) -> str:
    """Convert Traditional → Simplified when language is Chinese."""
    if lang == "zh":
        return zhconv.convert(text, "zh-cn")
    return text

# ═══════════════════════════════════════════════════════════
# Hotkeys
# ═══════════════════════════════════════════════════════════
def _register_hotkeys():
    """Register hotkeys from current config. Unhooks existing first."""
    keyboard.unhook_all()

    hk = _config.get("hotkeys", {})

    for action, default_key in [("record", "alt+num add"),
                                 ("exit", "alt+num -")]:
        key = hk.get(action, default_key)
        if key:
            _try_register_hotkey(key, action)

    settings_key = hk.get("settings")
    if settings_key:
        try:
            keyboard.add_hotkey(settings_key, open_settings, suppress=False)
            log.info("Settings hotkey: %s", settings_key)
        except Exception as e:
            log.warning("Settings hotkey '%s' failed: %s", settings_key, e)


def _try_register_hotkey(hotkey_str: str, action: str):
    """Register a hotkey, trying alternative key name formats for numpad."""
    target = toggle_recording if action == "record" else exit_app

    # Parse modifier + key
    if "+" in hotkey_str:
        parts = hotkey_str.rsplit("+", 1)
        modifier = parts[0].strip().lower()
        key_name = parts[1].strip()
    else:
        modifier = ""
        key_name = hotkey_str.strip()

    # Try key name as-is, then common alternatives
    key_aliases = [key_name]
    KNOWN_ALIASES = {
        "num +":          ["num add", "add"],
        "num add":        ["num add", "num +", "add"],
        "add":            ["add", "num add", "num +"],
        "num subtract":   ["num -", "subtract"],
        "subtract":       ["subtract", "num -", "num subtract"],
        "num multiply":   ["num *", "num multiply", "multiply"],
        "num divide":     ["num /", "num divide", "divide"],
    }
    if key_name.lower() in KNOWN_ALIASES:
        key_aliases = KNOWN_ALIASES[key_name.lower()]

    for alias in key_aliases:
        combo = f"{modifier}+{alias}" if modifier else alias
        try:
            keyboard.add_hotkey(combo, target, suppress=False)
            log.info("%s hotkey: %s", action.capitalize(), combo)
            return
        except Exception:
            continue

    log.warning("%s hotkey failed for all aliases of '%s'", action, hotkey_str)

def toggle_recording():
    try:
        if recording:
            stop_recording_and_transcribe()
        else:
            start_recording()
    except Exception as e:
        log.error("toggle_recording error: %s", e)

def exit_app():
    log.info("Exit requested")
    if tray_icon:
        tray_icon.stop()
    if _tk_root:
        _tk_root.quit()
    os._exit(0)

def open_settings():
    """Open settings window (from hotkey or tray menu)."""
    _tk_root.after(0, _do_open_settings)

def _do_open_settings():
    """Actually open settings — must run on tk main thread."""
    global _config
    SettingsWindow.show(_tk_root, _config, on_settings_saved)

def on_settings_saved(new_config: dict):
    """Called after user saves settings."""
    global _config, DEVICE, COMPUTE_TYPE
    _config = new_config
    save_config(_config)

    # Re-register hotkeys
    _register_hotkeys()

    # Update indicator style
    if _indicator:
        a = _config.get("appearance", {})
        _indicator.update_style(
            color=a.get("indicator_color"),
            position=a.get("indicator_position"),
            opacity=a.get("indicator_opacity"),
        )

    # Update model config (won't reload until next restart, but save for reference)
    DEVICE = _config["model"]["device"]
    COMPUTE_TYPE = _config["model"]["compute_type"]

    log.info("Settings applied: hotkeys=%s", _config["hotkeys"])

# ═══════════════════════════════════════════════════════════
# System Tray
# ═══════════════════════════════════════════════════════════
def _create_tray_image(color="#4CAF50"):
    """Draw a simple circle icon."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([10, 10, 54, 54], fill=color)
    return img

_ICON_IDLE = _create_tray_image("#4CAF50")
_ICON_RECORDING = _create_tray_image("#F44336")
_ICON_PROCESSING = _create_tray_image("#FF9800")

def _set_tray_state(state: str):
    """Update tray icon + title + floating indicator."""
    if tray_icon:
        if state == "idle":
            tray_icon.icon = _ICON_IDLE
            tray_icon.title = "Voice Input — 就绪"
        elif state == "recording":
            tray_icon.icon = _ICON_RECORDING
            tray_icon.title = "● 录音中... (快捷键停止)"
        elif state == "processing":
            tray_icon.icon = _ICON_PROCESSING
            tray_icon.title = "⟳ 识别中..."
    # Floating indicator
    if _indicator:
        if state == "recording":
            _indicator.show()
        else:
            _indicator.hide()


def _notify(title: str, msg: str):
    try:
        ctypes.windll.user32.MessageBoxW(0, msg, title, 0x40)
    except Exception:
        pass

def _setup_tray():
    global tray_icon
    img = _create_tray_image()
    menu = pystray.Menu(
        pystray.MenuItem("🎤 Voice Input", lambda: None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("⚙️ 设置", open_settings),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出", lambda: exit_app()),
    )
    tray_icon = pystray.Icon("voice_input", img, "Voice Input", menu)
    return tray_icon

# ═══════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════
def main():
    global _tk_root, _indicator

    signal.signal(signal.SIGINT, signal.SIG_IGN)
    log.info("=== Voice Input starting ===")

    # 1. Load model on main thread (avoids tkinter thread conflicts)
    load_model()

    # 2. Create tk root on main thread (Python 3.12 requirement)
    _tk_root = tk.Tk()
    _tk_root.withdraw()

    # 3. Create floating indicator
    _indicator = FloatingIndicator(_tk_root, _config.get("appearance", {}))

    # 4. Setup system tray (with async open_settings)
    tray = _setup_tray()

    # 5. Register hotkeys from config
    _register_hotkeys()

    # 6. Run pystray in background thread
    tray.run_detached()
    log.info("Tray running (detached)")

    # 7. Tk main loop on MAIN thread
    log.info("Entering tk main loop")
    _tk_root.mainloop()

    log.info("=== Voice Input exiting ===")


if __name__ == "__main__":
    main()
