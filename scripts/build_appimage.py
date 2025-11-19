#!/usr/bin/env python3
"""
Crée un AppImage pour BulletinPro (plus portable que .deb)
Compatible avec toutes les distributions Linux
"""

import os
import shutil
import subprocess
from pathlib import Path


def create_appimage():
    """Crée un AppImage auto-contenu"""
    
    project_root = Path(__file__).parent.parent
    dist_dir = project_root / "dist"
    appdir = dist_dir / "BulletinPro-Prof.AppDir"
    
    print("📦 Création de l'AppImage...")
    
    # Nettoyer
    if appdir.exists():
        shutil.rmtree(appdir)
    
    # Structure AppDir
    dirs = [
        appdir / "usr" / "bin",
        appdir / "usr" / "share" / "applications",
        appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps",
    ]
    
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Copier l'exécutable
    exe_src = dist_dir / "bulletinpro-prof"
    if not exe_src.exists():
        # Essayer avec majuscule
        exe_src = dist_dir / "bulletinpro-Prof"
    
    if exe_src.exists():
        shutil.copy2(exe_src, appdir / "usr" / "bin" / "bulletinpro-prof")
        os.chmod(appdir / "usr" / "bin" / "bulletinpro-prof", 0o755)
    else:
        print("❌ Exécutable introuvable")
        return False
    
    # Fichier .desktop
    desktop_content = """[Desktop Entry]
Type=Application
Name=BulletinPro Prof
Exec=bulletinpro-prof
Icon=bulletinpro-prof
Categories=Education;Office;
Terminal=false
"""
    
    with open(appdir / "bulletinpro-prof.desktop", "w") as f:
        f.write(desktop_content)
    
    shutil.copy2(
        appdir / "bulletinpro-prof.desktop",
        appdir / "usr" / "share" / "applications" / "bulletinpro-prof.desktop"
    )
    
    # Copier l'icône
    icon_src = project_root / "assets" / "icons" / "logo.png"
    if icon_src.exists():
        shutil.copy2(
            icon_src,
            appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps" / "bulletinpro-prof.png"
        )
        shutil.copy2(icon_src, appdir / "bulletinpro-prof.png")
    
    # Script AppRun
    apprun = """#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/bulletinpro-prof" "$@"
"""
    
    apprun_path = appdir / "AppRun"
    with open(apprun_path, "w") as f:
        f.write(apprun)
    os.chmod(apprun_path, 0o755)
    
    # Télécharger appimagetool si nécessaire
    appimagetool = dist_dir / "appimagetool-x86_64.AppImage"
    
    if not appimagetool.exists():
        print("📥 Téléchargement appimagetool...")
        subprocess.run([
            "wget",
            "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage",
            "-O", str(appimagetool)
        ], check=True)
        os.chmod(appimagetool, 0o755)
    
    # Créer l'AppImage
    print("🔨 Construction de l'AppImage...")
    output_appimage = dist_dir / "BulletinPro-Prof-x86_64.AppImage"
    
    subprocess.run([
        str(appimagetool),
        str(appdir),
        str(output_appimage)
    ], env={**os.environ, "ARCH": "x86_64"}, check=True)
    
    if output_appimage.exists():
        size = output_appimage.stat().st_size / (1024 * 1024)
        print(f"✅ AppImage créé: {size:.2f} MB")
        print(f"📁 {output_appimage}")
        return True
    else:
        print("❌ Échec de création de l'AppImage")
        return False


if __name__ == "__main__":
    import sys
    success = create_appimage()
    sys.exit(0 if success else 1)
