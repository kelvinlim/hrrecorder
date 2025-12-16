# -*- mode: python ; coding: utf-8 -*-
import sys
import os

# Platform detection
IS_MAC = sys.platform == 'darwin'
IS_WIN = sys.platform == 'win32'

# Icon paths
ICON_MAC = 'hrrecorder.icns' if os.path.exists('hrrecorder.icns') else None
ICON_WIN = 'hrrecorder.ico' if os.path.exists('hrrecorder.ico') else None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['bleak', 'polar_python'],
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
    a.binaries,
    a.datas,
    [],
    name='hrrecorder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_WIN if IS_WIN else None,
)

# macOS app bundle
if IS_MAC:
    app = BUNDLE(
        exe,
        name='hrrecorder.app',
        icon=ICON_MAC,
        bundle_identifier='com.kelvinlim.hrrecorder',
        info_plist={
            'CFBundleName': 'HR Recorder',
            'CFBundleDisplayName': 'HR Recorder',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHumanReadableCopyright': 'Copyright © 2025 Kelvin Lim',
            'NSBluetoothAlwaysUsageDescription': 'This app requires Bluetooth to connect to Polar heart rate monitors.',
            'NSBluetoothPeripheralUsageDescription': 'This app requires Bluetooth to connect to Polar heart rate monitors.',
        }
    )
