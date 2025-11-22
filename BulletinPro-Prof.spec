# -*- mode: python ; coding: utf-8 -*-

"""
Configuration PyInstaller pour BulletinPro-Prof
Résout les problèmes de dépendances (backports, pkg_resources)
"""

import sys
from pathlib import Path

block_cipher = None

# Chemin du projet
project_root = Path.cwd()

# ============================================================
# ANALYSE : Collecte des dépendances
# ============================================================
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.py', '.'),
        ('assets/icons', 'assets/icons'),
    ],
    hiddenimports=[
        # Flet et ses dépendances
        'flet',
        'flet.core',
        'flet_core',
        'flet_runtime',
        
        # Supabase et PostgreSQL
        'supabase',
        'postgrest',
        
        # Utilitaires
        'PIL',
        'PIL.Image',
        'sqlite3',
        'dotenv',
        
        # ✅ FIX : Backports
        'backports',
        'backports.zoneinfo',
        'backports.zoneinfo._zoneinfo',
        
        # ✅ FIX : Importlib
        'importlib_metadata',
        'importlib_metadata._adapters',
        'importlib_metadata._collections',
        'importlib_metadata._functools',
        'importlib_metadata._itertools',
        'importlib_metadata._meta',
        'importlib_metadata._text',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # ✅ EXCLURE pkg_resources (cause des problèmes)
        'pkg_resources',
        'pkg_resources.extern',
        
        # Modules inutiles (réduire la taille)
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'tkinter',
        '_tkinter',
        'unittest',
        'test',
        'tests',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ============================================================
# COLLECTE : Tous les fichiers Flet
# ============================================================
a.datas += Tree('flet', prefix='flet', excludes=['*.pyc', '__pycache__'])
a.datas += Tree('flet_core', prefix='flet_core', excludes=['*.pyc', '__pycache__'])
a.datas += Tree('flet_runtime', prefix='flet_runtime', excludes=['*.pyc', '__pycache__'])

# ============================================================
# PYZ : Compression des modules Python
# ============================================================
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# ============================================================
# EXE : Création de l'exécutable
# ============================================================
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BulletinPro-Prof',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compression UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Mode GUI (pas de console)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/logo.ico' if sys.platform == 'win32' else 'assets/icons/logo.png',
)
