#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de build Windows pour BulletinPro
Prépare la structure pour l'installateur Inno Setup
Compatible encodage Windows CP1252
"""

import os
import shutil
from pathlib import Path
import sys

# ✅ FIX CRITIQUE : Forcer UTF-8 pour éviter UnicodeEncodeError sur Windows
if sys.platform == "win32":
    # Méthode 1 : Changer l'encodage de stdout/stderr
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    # Méthode 2 : Changer le code page de la console (fallback)
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)  # UTF-8
    except:
        pass

def safe_print(msg):
    """Affiche un message en gérant les erreurs d'encodage"""
    try:
        print(msg)
    except UnicodeEncodeError:
        # Remplacer les caractères problématiques par des versions ASCII
        ascii_msg = msg.encode('ascii', errors='replace').decode('ascii')
        print(ascii_msg)

def create_windows_structure():
    """Prépare les fichiers pour Inno Setup"""
    
    try:
        project_root = Path(__file__).parent.parent
        dist_dir = project_root / "dist"
        installers_dir = dist_dir / "installers"
        
        safe_print("[INFO] Preparation de la structure Windows...")
        
        # Créer le dossier installers
        installers_dir.mkdir(parents=True, exist_ok=True)
        
        # Vérifier que l'exécutable existe
        exe_path = dist_dir / "BulletinPro-Prof.exe"
        if not exe_path.exists():
            safe_print("[ERROR] BulletinPro-Prof.exe introuvable dans dist/")
            safe_print("[INFO] Lancez d'abord PyInstaller pour creer l'executable")
            return False
        
        safe_print(f"[OK] Executable trouve : {exe_path}")
        safe_print(f"[INFO] Taille : {exe_path.stat().st_size / (1024*1024):.2f} MB")
        
        # Copier les fichiers nécessaires dans un dossier temporaire
        temp_dir = dist_dir / "BulletinPro-Prof_Package"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir()
        
        # Copier l'exécutable et le renommer
        shutil.copy2(exe_path, temp_dir / "BulletinPro-Prof.exe")
        safe_print("[OK] Executable copie et renomme en BulletinPro-Prof.exe")
        
        # Chercher et copier les icônes
        icons_dir = project_root / "assets" / "icons"
        icon_copied = False
        
        # Essayer différents noms d'icônes
        icon_names = ["logo.ico", "app_icon.ico"]
        for icon_name in icon_names:
            icon_path = icons_dir / icon_name
            if icon_path.exists():
                shutil.copy2(icon_path, temp_dir / "logo.ico")
                safe_print(f"[OK] Icone copiee depuis {icon_name}")
                icon_copied = True
                break
        
        if not icon_copied:
            safe_print("[WARN] Aucune icone trouvee, installateur sans icone")
            safe_print("[INFO] Executez: python scripts/create_icons.py")
        
        # Copier les fichiers de configuration (si présents)
        files_to_copy = ["config.py", ".env", "README.md", "LICENSE.txt"]
        for file in files_to_copy:
            src = project_root / file
            if src.exists():
                shutil.copy2(src, temp_dir / file)
                safe_print(f"[OK] {file} copie")
        
        # Copier le dossier assets/icons si présent
        if icons_dir.exists():
            assets_dest = temp_dir / "assets" / "icons"
            assets_dest.mkdir(parents=True, exist_ok=True)
            
            for icon_file in icons_dir.glob("*"):
                if icon_file.is_file():
                    shutil.copy2(icon_file, assets_dest / icon_file.name)
            
            safe_print("[OK] Dossier assets/icons copie")
        
        safe_print("\n[SUCCESS] Structure Windows prete pour Inno Setup !")
        safe_print(f"[INFO] Dossier : {temp_dir}")
        safe_print(f"[INFO] Contenu :")
        for item in temp_dir.rglob("*"):
            if item.is_file():
                safe_print(f"  - {item.relative_to(temp_dir)}")
        
        return True
        
    except Exception as e:
        safe_print(f"[ERROR] Erreur : {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale"""
    
    safe_print("=" * 60)
    safe_print("BUILD WINDOWS - BulletinPro-Prof")
    safe_print("=" * 60)
    safe_print("")
    
    # Préparer la structure
    if not create_windows_structure():
        safe_print("\n[ERROR] Build Windows echoue")
        return 1
    
    safe_print("\n" + "=" * 60)
    safe_print("[SUCCESS] PREPARATION WINDOWS TERMINEE")
    safe_print("=" * 60)
    safe_print("\n[INFO] Prochaines etapes :")
    safe_print("   1. L'executable est pret dans : dist/BulletinPro-Prof_Package/")
    safe_print("   2. Inno Setup compilera automatiquement l'installateur")
    safe_print("   3. Resultat : dist/installers/BulletinPro-Prof_Setup_1.0.0.exe")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
