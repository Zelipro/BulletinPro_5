# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec pour BulletinPro-Prof LINUX
✅ Pas de backports.zoneinfo (Python 3.11 l'inclut)
✅ Pas de Tree('flet') - utilise hidden imports
"""

import sys
from pathlib import Path

block_cipher = None
project_root = Path.cwd()

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.py', '.'),
        ('assets/icons', 'assets/icons'),
    ],
    hiddenimports=[
        'flet',
        'flet.core',
        'flet_core',
        'flet_runtime',
        'supabase',
        'postgrest',
        'PIL',
        'PIL.Image',
        'sqlite3',
        'dotenv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'tkinter',
        '_tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='bulletinpro-prof',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/logo.png',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='bulletinpro-prof'
)
