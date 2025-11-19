#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de build Windows pour BulletinPro
Prépare la structure pour l'installateur Inno Setup
Compatible encodage Windows
"""

import os
import shutil
from pathlib import Path
import sys

# Forcer l'encodage UTF-8 pour Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

def create_windows_structure():
    """Prépare les fichiers pour Inno Setup"""
    
    try:
        project_root = Path(__file__).parent.parent
        dist_dir = project_root / "dist"
        installers_dir = dist_dir / "installers"
        
        print("[INFO] Preparation de la structure Windows...")
        
        # Créer le dossier installers
        installers_dir.mkdir(parents=True, exist_ok=True)
        
        # Vérifier que l'exécutable existe
        exe_path = dist_dir / "BulletinPro.exe"
        if not exe_path.exists():
            print("[ERROR] BulletinPro.exe introuvable dans dist/")
            print("[INFO] Lancez d'abord PyInstaller pour creer l'executable")
            return False
        
        print(f"[OK] Executable trouve : {exe_path}")
        print(f"[INFO] Taille : {exe_path.stat().st_size / (1024*1024):.2f} MB")
        
        # Copier les fichiers nécessaires dans un dossier temporaire
        temp_dir = dist_dir / "BulletinPro_Package"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir()
        
        # Copier l'exécutable et le renommer
        shutil.copy2(exe_path, temp_dir / "BulletinPro_Prof.exe")
        print("[OK] Executable copie et renomme en BulletinPro_Prof.exe")
        
        # Chercher et copier les icônes
        icons_dir = project_root / "assets" / "icons"
        icon_copied = False
        
        # Essayer différents noms d'icônes
        icon_names = ["logo.ico", "app_icon.ico"]
        for icon_name in icon_names:
            icon_path = icons_dir / icon_name
            if icon_path.exists():
                shutil.copy2(icon_path, temp_dir / "logo.ico")
                print(f"[OK] Icone copiee depuis {icon_name}")
                icon_copied = True
                break
        
        if not icon_copied:
            print("[WARN] Aucune icone trouvee, installateur sans icone")
            print("[INFO] Executez: python scripts/create_icons.py")
        
        # Copier les fichiers de configuration (si présents)
        files_to_copy = ["config.py", ".env", "README.md", "LICENSE.txt"]
        for file in files_to_copy:
            src = project_root / file
            if src.exists():
                shutil.copy2(src, temp_dir / file)
                print(f"[OK] {file} copie")
        
        # Copier le dossier assets/icons si présent
        if icons_dir.exists():
            assets_dest = temp_dir / "assets" / "icons"
            assets_dest.mkdir(parents=True, exist_ok=True)
            
            for icon_file in icons_dir.glob("*"):
                if icon_file.is_file():
                    shutil.copy2(icon_file, assets_dest / icon_file.name)
            
            print("[OK] Dossier assets/icons copie")
        
        print("\n[SUCCESS] Structure Windows prete pour Inno Setup !")
        print(f"[INFO] Dossier : {temp_dir}")
        print(f"[INFO] Contenu :")
        for item in temp_dir.rglob("*"):
            if item.is_file():
                print(f"  - {item.relative_to(temp_dir)}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Erreur : {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale"""
    
    print("=" * 60)
    print("BUILD WINDOWS - BulletinPro")
    print("=" * 60)
    print("")
    
    # Préparer la structure
    if not create_windows_structure():
        print("\n[ERROR] Build Windows echoue")
        return 1
    
    print("\n" + "=" * 60)
    print("[SUCCESS] PREPARATION WINDOWS TERMINEE")
    print("=" * 60)
    print("\n[INFO] Prochaines etapes :")
    print("   1. L'executable est pret dans : dist/BulletinPro_Package/")
    print("   2. Inno Setup compilera automatiquement l'installateur")
    print("   3. Resultat : dist/installers/BulletinPro_Setup_1.0.0.exe")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
