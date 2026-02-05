# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [
    ('motherload_projet/agents_manuals', 'motherload_projet/agents_manuals'),
    ('motherload_projet/catalogs', 'motherload_projet/catalogs'),
]
binaries = []
hiddenimports = [
    'tkinterdnd2',
    'pandas',
    'openpyxl',
    'motherload_projet.ui.dashboard',
    'motherload_projet.ui.log_console',
    'motherload_projet.desktop_app.agent_status',
]
tmp_ret = collect_all('tkinterdnd2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

a = Analysis(
    ['motherload_projet/desktop_app/app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Motherload',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Motherload',
)
app = BUNDLE(
    coll,
    name='Motherload.app',
    icon=None,
    bundle_identifier='com.oliviercloutier.motherload',
)
