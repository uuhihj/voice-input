# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Voice Input.
Output: single exe (model folder stays external, user copies alongside).
"""

import os
import sys

# Collect only essential CUDA DLLs (CTranslate2 needs cublas + cudnn + cudart)
_nvidia_dir = os.path.join(sys.prefix, "Lib", "site-packages", "nvidia")
_binaries = []
for _pkg in ["cublas", "cudnn", "cuda_runtime"]:
    _bin_dir = os.path.join(_nvidia_dir, _pkg, "bin")
    if os.path.isdir(_bin_dir):
        for _f in os.listdir(_bin_dir):
            if _f.endswith(".dll"):
                _src = os.path.join(_bin_dir, _f)
                _binaries.append((_src, "."))

a = Analysis(
    ['voice_input.py'],
    pathex=[],
    binaries=_binaries,
    datas=[],
    hiddenimports=[
        # faster-whisper + ctranslate2
        'faster_whisper', 'ctranslate2',
        # tokenizers
        'tokenizers', 'tokenizers.decoders',
        # audio
        'sounddevice', '_sounddevice_data',
        # keyboard
        'keyboard', 'keyboard._winkeyboard', 'keyboard._nixkeyboard',
        # pystray + PIL
        'pystray', 'pystray._win32',
        'PIL', 'PIL.Image', 'PIL.ImageDraw',
        # ML
        'numpy', 'scipy',
        # internationalization
        'zhconv',
        # misc
        'av', 'logging', 'json', 'wave', 'tempfile', 'threading',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter.test', 'unittest', 'pydoc',
        'setuptools', 'pip', 'wheel', 'pkg_resources',
        'matplotlib', 'pandas', 'torch', 'tensorflow',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VoiceInput',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # windows subsystem (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
