# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all mediapipe submodules and data
mediapipe_hidden_imports = collect_submodules('mediapipe')
mediapipe_datas = collect_data_files('mediapipe')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('Frontend', 'Frontend'),
        ('logs', 'logs'),  # Ensure logs directory exists
        ('config.py', '.')
    ] + mediapipe_datas,
    hiddenimports=[
        'engineio.async_drivers.threading',
        'flask',
        'cv2',
        'numpy',
        'sounddevice',
        'fpdf',
        'psutil'
    ] + mediapipe_hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GuardAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keep console for debug logs (User requested debug prints)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GuardAI',
)
app = BUNDLE(
    coll,
    name='GuardAI.app',
    icon=None,
    bundle_identifier='com.guardai.proctoring',
)
