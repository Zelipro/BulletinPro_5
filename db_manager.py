#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de base de données SQLite avec chemin sécurisé
Compatible Windows/Linux/macOS
"""

import sqlite3
import os
from pathlib import Path
import sys


class DatabaseManager:
    """Gère la connexion et le chemin de la base de données"""
    
    _instance = None
    _db_path = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize_db_path()
        return cls._instance
    
    def _initialize_db_path(self):
        """Initialise le chemin de la base de données selon l'OS"""
        
        # Déterminer le dossier de données selon l'OS
        if sys.platform == "win32":
            # Windows: %APPDATA%\BulletinPro
            app_data = os.getenv('APPDATA')
            base_dir = Path(app_data) / "BulletinPro"
        else:
            # Linux/macOS: ~/.local/share/BulletinPro
            home = Path.home()
            base_dir = home / ".local" / "share" / "BulletinPro"
        
        # Créer le dossier s'il n'existe pas
        try:
            base_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 Dossier données: {base_dir}")
        except Exception as e:
            print(f"⚠️ Erreur création dossier: {e}")
            # Fallback: utiliser le dossier courant
            base_dir = Path.cwd()
        
        # Définir le chemin complet de la base
        self._db_path = str(base_dir / "base.db")
        print(f"💾 Base de données: {self._db_path}")
        
        # Vérifier les permissions
        self._check_permissions(base_dir)
    
    def _check_permissions(self, directory):
        """Vérifie les permissions d'écriture"""
        try:
            test_file = directory / ".write_test"
            test_file.touch()
            test_file.unlink()
            print("✅ Permissions d'écriture OK")
        except Exception as e:
            print(f"❌ Erreur permissions: {e}")
            print("⚠️ L'application pourrait ne pas fonctionner correctement")
    
    def get_connection(self):
        """Retourne une connexion à la base de données"""
        try:
            conn = sqlite3.connect(self._db_path)
            return conn
        except sqlite3.Error as e:
            print(f"❌ Erreur connexion DB: {e}")
            raise
    
    @property
    def db_path(self):
        """Retourne le chemin de la base de données"""
        return self._db_path


# Instance globale
db_manager = DatabaseManager()


def get_db_connection():
    """
    Fonction utilitaire pour obtenir une connexion
    À utiliser partout dans le code à la place de sqlite3.connect("base.db")
    """
    return db_manager.get_connection()
