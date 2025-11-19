import sqlite3
import threading
import time
from datetime import datetime
from supabase import create_client, Client
from typing import Optional, Dict, Any
import json

from config import SUPABASE_URL, SUPABASE_KEY, LOCAL_DB, SYNC_INTERVAL


class SyncManager:
    """Gestionnaire de synchronisation entre SQLite local et Supabase"""
    
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.local_db = LOCAL_DB
        self.sync_thread: Optional[threading.Thread] = None
        self.is_syncing = False
        self.last_sync: Optional[datetime] = None
        
    # ============ CONNEXION & INITIALISATION ============
    
    def get_local_connection(self):
        """Obtenir une connexion à la base locale"""
        return sqlite3.connect(self.local_db)
    
    def init_local_tables(self):
        """Initialise les tables locales avec structure complète"""
        conn = self.get_local_connection()
        cursor = conn.cursor()
        
        try:
            # Table Users
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS User (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    identifiant TEXT NOT NULL UNIQUE,
                    passwords TEXT NOT NULL,
                    nom TEXT NOT NULL,
                    prenom TEXT NOT NULL,
                    email TEXT NOT NULL,
                    telephone TEXT NOT NULL,
                    etablissement TEXT NOT NULL,
                    titre TEXT NOT NULL,
                    theme TEXT DEFAULT 'light',
                    language TEXT DEFAULT 'fr',
                    last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table Students
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    prenom TEXT NOT NULL,
                    matricule TEXT NOT NULL,
                    date_naissance TEXT NOT NULL,
                    sexe TEXT NOT NULL,
                    classe TEXT NOT NULL,
                    etablissement TEXT NOT NULL,
                    last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(matricule, etablissement)
                )
            """)
            
            # Table Matieres
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Matieres (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    genre TEXT NOT NULL,
                    etablissement TEXT NOT NULL,
                    last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(nom, etablissement)
                )
            """)
            
            # Table Teacher
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Teacher (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ident TEXT NOT NULL UNIQUE,
                    pass TEXT NOT NULL,
                    matiere TEXT NOT NULL,
                    last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table Notes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    classe TEXT NOT NULL,
                    matricule TEXT NOT NULL,
                    matiere TEXT NOT NULL,
                    coefficient TEXT NOT NULL,
                    note_interrogation TEXT NOT NULL,
                    note_devoir TEXT NOT NULL,
                    note_composition TEXT NOT NULL,
                    moyenne TEXT,
                    date_saisie TEXT,
                    last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(matricule, matiere, classe)
                )
            """)
            
            # Table Classes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Class (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    etablissement TEXT NOT NULL,
                    last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(nom, etablissement)
                )
            """)
            
            # Table de métadonnées de sync
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_metadata (
                    table_name TEXT PRIMARY KEY,
                    last_sync TIMESTAMP,
                    sync_status TEXT DEFAULT 'pending'
                )
            """)
            
            conn.commit()
            print("✅ Tables locales initialisées")
            
        except Exception as e:
            print(f"❌ Erreur initialisation tables: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    # ============ SYNC AU LOGIN ============
    
    def sync_on_login(self, callback=None):
        """
        Synchronisation lors de la connexion
        1. Charge TOUS les Users
        2. Après login, charge données de l'établissement
        """
        try:
            print("🔄 Sync au login - Chargement Users...")
            
            # Charger tous les users
            self.sync_table_from_supabase("User")
            
            if callback:
                callback("Users chargés")
            
            print("✅ Sync login terminé")
            return True
            
        except Exception as e:
            print(f"❌ Erreur sync login: {e}")
            return False
    
    def sync_etablissement_data(self, etablissement: str, callback=None):
        """
        Charge toutes les données d'un établissement spécifique
        """
        try:
            print(f"🔄 Chargement données: {etablissement}")
            
            tables = ["Students", "Matieres", "Teacher", "Notes", "Class"]
            
            for table in tables:
                if callback:
                    callback(f"Chargement {table}...")
                
                self.sync_table_from_supabase(
                    table, 
                    filter_col="etablissement",
                    filter_val=etablissement
                )
            
            print(f"✅ Données {etablissement} chargées")
            return True
            
        except Exception as e:
            print(f"❌ Erreur sync établissement: {e}")
            return False
    
    # ============ SYNC TABLES ============
    
    def sync_table_from_supabase(self, table_name: str, 
                                  filter_col: str = None, 
                                  filter_val: str = None):
        """
        Synchronise une table depuis Supabase vers local
        """
        try:
            # Récupérer depuis Supabase
            query = self.supabase.table(table_name).select("*")
            
            if filter_col and filter_val:
                query = query.eq(filter_col, filter_val)
            
            response = query.execute()
            remote_data = response.data
            
            if not remote_data:
                print(f"ℹ️ Aucune donnée pour {table_name}")
                return
            
            # Insérer/Mettre à jour en local
            conn = self.get_local_connection()
            cursor = conn.cursor()
            
            for row in remote_data:
                # Supprimer 'id' pour éviter les conflits
                row_data = {k: v for k, v in row.items() if k != 'id'}
                
                # Construire la requête INSERT OR REPLACE
                columns = ', '.join(row_data.keys())
                placeholders = ', '.join(['?' for _ in row_data])
                
                # Déterminer la clé unique selon la table
                if table_name == "User":
                    unique_check = "identifiant = ?"
                    unique_val = row_data.get('identifiant')
                elif table_name in ["Students", "Notes"]:
                    unique_check = "matricule = ? AND etablissement = ?"
                    unique_val = (row_data.get('matricule'), row_data.get('etablissement'))
                elif table_name in ["Matieres", "Class"]:
                    unique_check = "nom = ? AND etablissement = ?"
                    unique_val = (row_data.get('nom'), row_data.get('etablissement'))
                elif table_name == "Teacher":
                    unique_check = "ident = ?"
                    unique_val = row_data.get('ident')
                else:
                    unique_check = None
                
                if unique_check:
                    # Vérifier existence
                    if isinstance(unique_val, tuple):
                        cursor.execute(f"SELECT id FROM {table_name} WHERE {unique_check}", unique_val)
                    else:
                        cursor.execute(f"SELECT id FROM {table_name} WHERE {unique_check}", (unique_val,))
                    
                    exists = cursor.fetchone()
                    
                    if exists:
                        # UPDATE
                        set_clause = ', '.join([f"{k} = ?" for k in row_data.keys()])
                        values = list(row_data.values())
                        
                        if isinstance(unique_val, tuple):
                            values.extend(unique_val)
                            cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE {unique_check}", values)
                        else:
                            values.append(unique_val)
                            cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE {unique_check}", values)
                    else:
                        # INSERT
                        cursor.execute(
                            f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})",
                            list(row_data.values())
                        )
                else:
                    # INSERT simple
                    cursor.execute(
                        f"INSERT OR REPLACE INTO {table_name} ({columns}) VALUES ({placeholders})",
                        list(row_data.values())
                    )
            
            conn.commit()
            conn.close()
            
            print(f"✅ {table_name}: {len(remote_data)} lignes synchronisées")
            
        except Exception as e:
            print(f"❌ Erreur sync {table_name}: {e}")
    
    def sync_table_to_supabase(self, table_name: str, 
                               filter_col: str = None, 
                               filter_val: str = None):
        """
        Synchronise une table depuis local vers Supabase
        """
        try:
            conn = self.get_local_connection()
            cursor = conn.cursor()
            
            # Récupérer données locales modifiées
            query = f"SELECT * FROM {table_name}"
            params = []
            
            if filter_col and filter_val:
                query += f" WHERE {filter_col} = ?"
                params.append(filter_val)
            
            cursor.execute(query, params)
            columns = [description[0] for description in cursor.description]
            local_data = cursor.fetchall()
            
            conn.close()
            
            if not local_data:
                return
            
            # Préparer les données pour Supabase
            for row in local_data:
                row_dict = dict(zip(columns, row))
                
                # Supprimer 'id' et 'last_sync' locaux
                row_dict.pop('id', None)
                row_dict.pop('last_sync', None)
                
                # Upsert vers Supabase
                self.supabase.table(table_name).upsert(row_dict).execute()
            
            print(f"✅ {table_name}: {len(local_data)} lignes envoyées à Supabase")
            
        except Exception as e:
            print(f"❌ Erreur sync vers Supabase {table_name}: {e}")
    
    # ============ SYNC AUTOMATIQUE ============
    
    def start_auto_sync(self, etablissement: str):
        """
        Démarre la synchronisation automatique toutes les 10 minutes
        """
        if self.is_syncing:
            print("⚠️ Sync déjà en cours")
            return
        
        self.is_syncing = True
        
        def sync_loop():
            while self.is_syncing:
                try:
                    print(f"🔄 Sync auto - {datetime.now()}")
                    
                    # Sync bidirectionnel pour l'établissement
                    tables = ["Students", "Matieres", "Teacher", "Notes", "Class", "User"]
                    
                    for table in tables:
                        # Depuis Supabase vers local
                        if table == "User":
                            self.sync_table_from_supabase(table)
                        else:
                            self.sync_table_from_supabase(
                                table,
                                filter_col="etablissement",
                                filter_val=etablissement
                            )
                        
                        # Depuis local vers Supabase
                        if table == "User":
                            self.sync_table_to_supabase(table)
                        else:
                            self.sync_table_to_supabase(
                                table,
                                filter_col="etablissement",
                                filter_val=etablissement
                            )
                    
                    self.last_sync = datetime.now()
                    print(f"✅ Sync auto terminé - {self.last_sync}")
                    
                except Exception as e:
                    print(f"❌ Erreur sync auto: {e}")
                
                # Attendre 10 minutes
                time.sleep(SYNC_INTERVAL)
        
        self.sync_thread = threading.Thread(target=sync_loop, daemon=True)
        self.sync_thread.start()
        print("✅ Sync automatique démarré (10 min)")
    
    def stop_auto_sync(self):
        """Arrête la synchronisation automatique"""
        self.is_syncing = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        print("🛑 Sync automatique arrêté")


# Instance globale
sync_manager = SyncManager()