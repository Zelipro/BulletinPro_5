# -*- mode: python ; coding: utf-8 -*-

"""
Configuration PyInstaller pour BulletinPro-Prof LINUX
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
        
        # ✅ FIX : Backports (CRITIQUE pour Linux)
        'backports',
        'backports.zoneinfo',
        'backports.zoneinfo._common',
        'backports.zoneinfo._zoneinfo',
        
        # ✅ FIX : Importlib (requis par pkg_resources)
        'importlib_metadata',
        'importlib_metadata._adapters',
        'importlib_metadata._collections',
        'importlib_metadata._functools',
        'importlib_metadata._itertools',
        'importlib_metadata._meta',
        'importlib_metadata._text',
        
        # ✅ FIX : Jaraco (requis par pkg_resources)
        'jaraco',
        'jaraco.text',
        'jaraco.context',
        'jaraco.functools',
        
        # ✅ FIX : More_itertools (dépendance de jaraco)
        'more_itertools',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # ✅ NE PAS EXCLURE pkg_resources sur Linux
        # (nécessaire pour certaines dépendances)
        
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
# COLLECTE : Tous les fichiers Flet et Backports
# ============================================================
try:
    a.datas += Tree('flet', prefix='flet', excludes=['*.pyc', '__pycache__'])
    a.datas += Tree('flet_core', prefix='flet_core', excludes=['*.pyc', '__pycache__'])
    a.datas += Tree('flet_runtime', prefix='flet_runtime', excludes=['*.pyc', '__pycache__'])
    
    # ✅ IMPORTANT : Inclure backports manuellement
    try:
        import backports
        backports_path = Path(backports.__file__).parent
        a.datas += Tree(str(backports_path), prefix='backports', excludes=['*.pyc', '__pycache__'])
    except:
        print("⚠️ Module backports introuvable, installation requise")
    
    # ✅ IMPORTANT : Inclure jaraco manuellement
    try:
        import jaraco
        jaraco_path = Path(jaraco.__file__).parent
        a.datas += Tree(str(jaraco_path), prefix='jaraco', excludes=['*.pyc', '__pycache__'])
    except:
        print("⚠️ Module jaraco introuvable")
        
except Exception as e:
    print(f"⚠️ Erreur collecte modules: {e}")

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
    name='bulletinpro-prof',
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
    icon='assets/icons/logo.png',
)
