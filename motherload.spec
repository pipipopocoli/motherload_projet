# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

block_cipher = None
try:
    root = Path(__file__).resolve().parent
except NameError:
    # __file__ may be undefined in some PyInstaller executions
    root = Path.cwd()

app_entry = root / "app" / "main.py"


a = Analysis(
    [str(app_entry)],
    pathex=[str(root)],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="Motherload",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

app = BUNDLE(
    exe,
    name="Motherload.app",
    icon=None,
    bundle_identifier="com.motherload.app",
)
