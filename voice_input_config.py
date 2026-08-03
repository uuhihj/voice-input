"""
Voice Input — Configuration management.
JSON persist, defaults, validation.
"""

import json
import os
import sys

# Resolve base directory (works for both script and frozen exe)
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(BASE_DIR, "voice_input_config.json")

DEFAULT_CONFIG = {
    "hotkeys": {
        "record": "alt+num add",
        "exit": "alt+num -",
        "settings": None,
    },
    "model": {
        "path": os.path.join(BASE_DIR, "models"),
        "device": "cuda",
        "compute_type": "float16",
    },
    "appearance": {
        "indicator_color": "#F44336",
        "indicator_position": "top",
        "indicator_opacity": 0.88,
        "show_tray_notifications": True,
    },
    "general": {
        "autostart": False,
    },
}


def load_config() -> dict:
    """Load config from JSON file. Create with defaults if missing or broken."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            # Merge with defaults to handle new keys added in updates
            merged = _deep_merge(DEFAULT_CONFIG, cfg)
            return merged
        except (json.JSONDecodeError, OSError):
            pass  # fall through to create default
    # Create default config file
    save_config(DEFAULT_CONFIG)
    return dict(DEFAULT_CONFIG)  # return a copy


def save_config(config: dict) -> None:
    """Write config to JSON file."""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def _deep_merge(default: dict, override: dict) -> dict:
    """Recursively merge override into default, preserving default keys."""
    result = dict(default)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
