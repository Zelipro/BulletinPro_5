#!/usr/bin/env python3
"""
Crée la structure .deb pour Ubuntu/Debian - VERSION CORRIGÉE
✅ Fix : Numéro de version sans préfixe 'v'
✅ Compatible avec le workflow GitHub Actions
"""

import os
import shutil
import sys
from pathlib import Path

def create_deb_structure():
    """Crée la structure du paquet .deb"""
    
    project_root = Path(__file__).parent.parent
    dist_dir = project_root / "dist"
    
    # ✅ CORRECTION : Nettoyer le préfixe 'v' et 'main'
    if len(sys.argv) > 1:
        version = sys.argv[1].replace('v', '').replace('main', '1.0.0').strip()
    else:
        version = os.environ.get('VERSION', '1.0.0').replace('v', '').replace('main', '1.0.0').strip()
    
    # ✅ VALIDATION : S'assurer que la version commence par un chiffre
    if not version or not version[0].isdigit():
        version = "1.0.0"
        print(f"⚠️ Version invalide, utilisation de la version par défaut : {version}")
    
    print(f"📦 Version détectée : {version}")
    
    # ✅ Nom cohérent avec le workflow : bulletinpro-prof-VERSION
    pkg_dir = dist_dir / f"bulletinpro-prof-{version}"
    
    print(f"📦 Création de la structure .deb dans : {pkg_dir}")
    
    # Nettoyer si existe
    if pkg_dir.exists():
        print(f"🧹 Nettoyage de l'ancien paquet...")
        shutil.rmtree(pkg_dir)
    
    # Créer l'arborescence
    dirs = [
        pkg_dir / "DEBIAN",
        pkg_dir / "usr" / "bin",
        pkg_dir / "usr" / "share" / "applications",
        pkg_dir / "usr" / "share" / "pixmaps",
    ]
    
    # Icônes multiples tailles
    for size in [16, 32, 48, 64, 128, 256, 512]:
        dirs.append(pkg_dir / "usr" / "share" / "icons" / "hicolor" / f"{size}x{size}" / "apps")
    
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ Créé : {directory.relative_to(dist_dir)}")
    
    # ============================================================
    # ✅ FICHIER DEBIAN/control - FORMAT STRICT
    # ============================================================
    control_content = f"""Package: bulletinpro-prof
Version: {version}
Section: education
Priority: optional
Architecture: amd64
Depends: libc6 (>= 2.31), libgtk-3-0
Maintainer: Zeli <eliseeatikpo10@gmail.com>
Homepage: https://github.com/Zelipro/BulletinPro
Description: Système de gestion de bulletins scolaires
 BulletinPro Prof est une application pour la saisie des notes
 et la consultation des élèves par les enseignants.
 Compatible Ubuntu 20.04+, Debian 11+.
"""
    
    control_path = pkg_dir / "DEBIAN" / "control"
    with open(control_path, "w", encoding="utf-8") as f:
        f.write(control_content)
    
    # ✅ IMPORTANT : Pas de ligne vide à la fin
    print(f"  ✅ Créé : DEBIAN/control (version: {version})")
    
    # ============================================================
    # FICHIER .desktop
    # ============================================================
    desktop_content = """[Desktop Entry]
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
    
    desktop_path = pkg_dir / "usr" / "share" / "applications" / "bulletinpro-prof.desktop"
    with open(desktop_path, "w", encoding="utf-8") as f:
        f.write(desktop_content)
    print(f"  ✅ Créé : bulletinpro-prof.desktop")
    
    # ============================================================
    # SCRIPTS POST-INSTALLATION
    # ============================================================
    postinst_content = """#!/bin/bash
set -e
gtk-update-icon-cache /usr/share/icons/hicolor -f > /dev/null 2>&1 || true
update-desktop-database /usr/share/applications > /dev/null 2>&1 || true
echo "✅ BulletinPro Prof installé avec succès !"
exit 0
"""
    
    postinst_path = pkg_dir / "DEBIAN" / "postinst"
    with open(postinst_path, "w", encoding="utf-8") as f:
        f.write(postinst_content)
    os.chmod(postinst_path, 0o755)
    print(f"  ✅ Créé : DEBIAN/postinst (exécutable)")
    
    # ============================================================
    # COPIER L'EXÉCUTABLE
    # ============================================================
    exe_found = False
    possible_names = ["bulletinpro-prof", "bulletinpro-Prof", "BulletinPro-Prof"]
    
    for exe_name in possible_names:
        exe_src = dist_dir / exe_name
        if exe_src.exists():
            exe_dst = pkg_dir / "usr" / "bin" / "bulletinpro-prof"
            shutil.copy2(exe_src, exe_dst)
            os.chmod(exe_dst, 0o755)
            print(f"  ✅ Exécutable copié : {exe_name} → /usr/bin/bulletinpro-prof")
            exe_found = True
            break
    
    if not exe_found:
        print("\n❌ ERREUR : Exécutable introuvable !")
        print(f"📂 Cherché dans : {dist_dir}")
        print(f"📂 Fichiers disponibles :")
        for item in dist_dir.glob("*"):
            if item.is_file() and not item.suffix in ['.deb', '.exe', '.zip']:
                print(f"    - {item.name}")
        print("\n⚠️ Le build PyInstaller a peut-être échoué.")
        return False
    
    # ============================================================
    # COPIER LES ICÔNES
    # ============================================================
    icons_dir = project_root / "assets" / "icons"
    if icons_dir.exists():
        # Icônes multiples tailles
        icon_count = 0
        for size in [16, 32, 48, 64, 128, 256, 512]:
            icon_src = icons_dir / f"app_icon_{size}x{size}.png"
            if icon_src.exists():
                icon_dst = pkg_dir / "usr" / "share" / "icons" / "hicolor" / f"{size}x{size}" / "apps" / "bulletinpro-prof.png"
                shutil.copy2(icon_src, icon_dst)
                icon_count += 1
        
        # Icône principale pour pixmaps
        main_icon = icons_dir / "logo.png"
        if main_icon.exists():
            shutil.copy2(main_icon, pkg_dir / "usr" / "share" / "pixmaps" / "bulletinpro-prof.png")
            icon_count += 1
        
        print(f"  ✅ {icon_count} icônes copiées")
    else:
        print(f"  ⚠️ Dossier assets/icons introuvable")
    
    # ============================================================
    # RÉSUMÉ FINAL
    # ============================================================
    print("\n" + "="*60)
    print("✅ STRUCTURE .DEB CRÉÉE AVEC SUCCÈS")
    print("="*60)
    print(f"📁 Dossier : {pkg_dir}")
    print(f"📦 Package : bulletinpro-prof-{version}")
    print(f"📋 Version : {version} (valide pour dpkg)")
    print(f"\n🎯 Prochaine étape : dpkg-deb --build")
    return True


if __name__ == "__main__":
    success = create_deb_structure()
    sys.exit(0 if success else 1)
