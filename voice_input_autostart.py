"""
Voice Input — Windows autostart management.

Creates / removes a shortcut in the Startup folder so the app
launches automatically after login. No third-party dependencies:
the .lnk file is created via PowerShell + WScript.Shell.
"""

import os
import subprocess
import sys

from voice_input_config import BASE_DIR

# Startup folder: %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
STARTUP_DIR = os.path.join(
    os.environ.get("APPDATA", ""),
    "Microsoft", "Windows", "Start Menu", "Programs", "Startup",
)
LINK_NAME = "VoiceInput.lnk"
LINK_PATH = os.path.join(STARTUP_DIR, LINK_NAME)

_WSCRIPT = os.path.join(
    os.environ.get("WINDIR", r"C:\Windows"), "System32", "wscript.exe")


def is_enabled() -> bool:
    """True if the startup shortcut currently exists."""
    return os.path.exists(LINK_PATH)


def set_enabled(enabled: bool) -> None:
    """Enable or disable autostart (idempotent)."""
    if enabled:
        _create_shortcut()
    else:
        _remove_shortcut()


def _launcher_target() -> str:
    """What the shortcut should run: vbs launcher (source) or exe (frozen)."""
    if getattr(sys, "frozen", False):
        return sys.executable
    return os.path.join(BASE_DIR, "voice_input_launcher.vbs")


def _ps_quote(s: str) -> str:
    """Quote a string as a PowerShell single-quoted literal."""
    return "'" + s.replace("'", "''") + "'"


def _create_shortcut() -> None:
    """Create/refresh the startup shortcut (overwrites stale ones)."""
    if not os.path.isdir(STARTUP_DIR):
        raise RuntimeError(f"Startup folder not found: {STARTUP_DIR}")
    target = _launcher_target()
    if target.lower().endswith(".vbs"):
        # Source mode: run hidden via wscript — no console flash on login
        ps = (
            "$ws = New-Object -ComObject WScript.Shell; "
            f"$sc = $ws.CreateShortcut({_ps_quote(LINK_PATH)}); "
            f"$sc.TargetPath = {_ps_quote(_WSCRIPT)}; "
            f"$sc.Arguments = {_ps_quote('"' + target + '"')}; "
            f"$sc.WorkingDirectory = {_ps_quote(BASE_DIR)}; "
            "$sc.Description = 'Voice Input autostart'; "
            "$sc.Save()"
        )
    else:
        # Frozen mode: run the exe directly
        ps = (
            "$ws = New-Object -ComObject WScript.Shell; "
            f"$sc = $ws.CreateShortcut({_ps_quote(LINK_PATH)}); "
            f"$sc.TargetPath = {_ps_quote(target)}; "
            f"$sc.WorkingDirectory = {_ps_quote(BASE_DIR)}; "
            "$sc.Description = 'Voice Input autostart'; "
            "$sc.Save()"
        )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            check=True, capture_output=True, text=True, timeout=30)
    except (subprocess.CalledProcessError, OSError) as e:
        raise RuntimeError(f"Failed to create autostart shortcut: {e}") from e


def _remove_shortcut() -> None:
    """Remove the startup shortcut if present."""
    try:
        os.remove(LINK_PATH)
    except FileNotFoundError:
        pass
