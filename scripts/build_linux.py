#!/usr/bin/env python3
"""Crée la structure .deb pour Ubuntu/Debian"""

import os
import shutil
from pathlib import Path

def create_deb_structure():
    project_root = Path(__file__).parent.parent
    dist_dir = project_root / "dist"
    # ✅ NOM CORRIGÉ : tirets au lieu de underscores
    pkg_dir = dist_dir / "bulletinpro-prof-1.0.0"
    
    print("📦 Création de la structure .deb...")
    
    # Créer l'arborescence
    dirs = [
        pkg_dir / "DEBIAN",
        pkg_dir / "usr" / "bin",
        pkg_dir / "usr" / "share" / "applications",
        pkg_dir / "usr" / "share" / "pixmaps",
    ]
    
    for size in [16, 32, 48, 64, 128, 256, 512]:
        dirs.append(pkg_dir / "usr" / "share" / "icons" / "hicolor" / f"{size}x{size}" / "apps")
    
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)
    
    # ✅ Fichier DEBIAN/control avec nom valide
    control = """Package: bulletinpro-prof
Version: 1.0.0
Section: education
Priority: optional
Architecture: amd64
Depends: libc6 (>= 2.31), libgtk-3-0
Maintainer: Zeli <eliseeatikpo10@gmail.com>
Homepage: https://github.com/Zelipro/BulletinPro
Description: Système de gestion de bulletins scolaires
 BulletinPro Prof est une application pour la saisie des notes
 et la consultation des élèves par les enseignants.
"""
    
    with open(pkg_dir / "DEBIAN" / "control", "w") as f:
        f.write(control)
    
    # ✅ Fichier .desktop avec noms cohérents
    desktop = """[Desktop Entry]
Version=1.0
Type=Application
Name=BulletinPro-Prof
GenericName=Gestion de Notes Scolaires
Comment=Saisie des notes pour les enseignants
Exec=/usr/bin/bulletinpro-prof
Icon=bulletinpro-prof
Terminal=false
Categories=Education;Office;
Keywords=école;notes;bulletins;professeur;
StartupNotify=true
"""
    
    with open(pkg_dir / "usr" / "share" / "applications" / "bulletinpro-prof.desktop", "w") as f:
        f.write(desktop)
    
    # Scripts post-installation
    postinst = """#!/bin/bash
set -e
gtk-update-icon-cache /usr/share/icons/hicolor -f > /dev/null 2>&1 || true
update-desktop-database /usr/share/applications > /dev/null 2>&1 || true
echo "✅ BulletinPro Prof installé avec succès !"
exit 0
"""
    
    postinst_path = pkg_dir / "DEBIAN" / "postinst"
    with open(postinst_path, "w") as f:
        f.write(postinst)
    os.chmod(postinst_path, 0o755)
    
    # ✅ Copier l'exécutable (chercher les deux noms possibles)
    exe_found = False
    for exe_name in ["bulletinpro-Prof", "bulletinpro-prof", "bulletinpro-prof"]:
        exe_src = dist_dir / exe_name
        if exe_src.exists():
            exe_dst = pkg_dir / "usr" / "bin" / "bulletinpro-prof"
            shutil.copy2(exe_src, exe_dst)
            os.chmod(exe_dst, 0o755)
            print(f"  ✅ Exécutable copié depuis {exe_name}")
            exe_found = True
            break
    
    if not exe_found:
        print("  ⚠️ Exécutable non trouvé, cherchez dans dist/")
    
    # Copier les icônes
    icons_dir = project_root / "assets" / "icons"
    for size in [16, 32, 48, 64, 128, 256, 512]:
        icon_src = icons_dir / f"logo_{size}x{size}.png"
        icon_dst = pkg_dir / "usr" / "share" / "icons" / "hicolor" / f"{size}x{size}" / "apps" / "bulletinpro-prof.png"
        if icon_src.exists():
            shutil.copy2(icon_src, icon_dst)
    
    # Copier vers pixmaps
    main_icon = icons_dir / "logo.png"
    if main_icon.exists():
        shutil.copy2(main_icon, pkg_dir / "usr" / "share" / "pixmaps" / "bulletinpro-prof.png")
    
    print("✅ Structure .deb créée avec succès !")

if __name__ == "__main__":
    create_deb_structure()
