import flet as ft
from Zeli_Dialog import ZeliDialog2
import sqlite3
import os
import shutil
from pathlib import Path
from time import sleep
import sys
import traceback

#-------
from stats import Stats
from Students import Gestion_Eleve_Liste
from Note import Saisie_Notes
#from Bulletin import Generation_Bulletin
from sync_manager import sync_manager
from db_manager import get_db_connection, db_manager, init_all_tables
#-----


def ensure_database_ready(page):
    """
    S'assure que la DB est prête avant de démarrer l'app
    Affiche une fenêtre de progression avec Flet
    """
    try:
        print("\n" + "="*60)
        print("🔍 VÉRIFICATION BASE DE DONNÉES")
        print("="*60)
        
        db_path = Path(db_manager.db_path)
        print(f"📁 Chemin DB: {db_path}")
        print(f"📁 Existe: {db_path.exists()}")
        
        # Si la DB n'existe pas, la créer
        if not db_path.exists():
            print("📦 Création de la base de données...")
            init_all_tables()
            print("✅ Base de données créée avec succès")
        else:
            print("✅ Base de données existante trouvée")
            # Vérifier que les tables sont bien là
            try:
                init_all_tables()  # Créer les tables manquantes si besoin
                print("✅ Structure des tables vérifiée")
            except Exception as e:
                print(f"⚠️ Erreur vérification structure: {e}")
        
        # Test de connexion
        print("🔌 Test de connexion...")
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        
        print(f"✅ Connexion OK - {len(tables)} tables trouvées:")
        for table in tables:
            print(f"   • {table[0]}")
        
        print("="*60)
        print("✅ BASE DE DONNÉES PRÊTE\n")
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE BASE DE DONNÉES:")
        print(f"   {e}")
        traceback.print_exc()
        
        # Afficher une alerte Flet à l'utilisateur
        try:
            error_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Row([
                    ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED, size=40),
                    ft.Text("Erreur de démarrage", size=20, weight=ft.FontWeight.BOLD),
                ]),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "Impossible d'initialiser la base de données.",
                            size=16,
                            weight=ft.FontWeight.W_500
                        ),
                        ft.Container(height=10),
                        ft.Text("Détails de l'erreur:", size=14, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Text(
                                str(e),
                                size=12,
                                color=ft.Colors.RED_700,
                                selectable=True
                            ),
                            padding=10,
                            bgcolor=ft.Colors.RED_50,
                            border_radius=5,
                        ),
                        ft.Container(height=10),
                        ft.Text(
                            f"📁 Chemin tentative: {db_manager.db_path}",
                            size=11,
                            color=ft.Colors.GREY_700,
                            selectable=True
                        ),
                    ], 
                    spacing=5,
                    tight=True
                    ),
                    width=450,
                ),
                actions=[
                    ft.TextButton(
                        "Quitter",
                        on_click=lambda e: page.window_destroy()
                    ),
                ],
            )
            
            page.overlay.append(error_dialog)
            error_dialog.open = True
            page.update()
            
        except:
            print("⚠️ Impossible d'afficher le dialog d'erreur")
        
        return False


#======================= Pour Page 0 =======
#======================             ==============

def Get_on_db_local(mention):
    def User():
        donne = []
        con = None
        try:
            con = get_db_connection()
            cur = con.cursor()
            cur.execute("SELECT * FROM User")
            donne = cur.fetchall()
            cur.close()
            
        except sqlite3.Error as e:
            pass
        finally:
            if con:
                con.close()
        return donne
    
    dic = {
        "User":User
    }
    
    func = dic.get(mention)
    if not func:
        return []   # return empty list when unknown mention
    return func()

def Submit(page , Ident , Pass): 
    Dialog = ZeliDialog2(page)
    #================================================================
    # NOUVEAU : Sync des Users au chargement de la page de login
    if not hasattr(Submit, 'users_synced'):
        loading = Dialog.loading_dialog(
            title="Chargement...",
            message="Synchronisation des utilisateurs"
        )
        
        # Initialiser tables locales
        sync_manager.init_local_tables()
        
        # Charger tous les users
        sync_manager.sync_on_login(
            callback=lambda msg: print(msg)
        )
        
        Dialog.close_dialog(loading)
        Submit.users_synced = True
    
    def login_success(donner_info,Dial):
        Dialog.close_dialog(Dial)
        
        # NOUVEAU : Charger les données de l'établissement
        
        if donner_info["role"] == "admin":
            Dialog.alert_dialog(
                title="Impossible",
                message="Veuillez utiliser BulletinPro version administrateur"
            )
            
            return # Ne pas continuer la connexion
        elif donner_info.get("role") != "creator":
            loading = Dialog.loading_dialog(
                title="Chargement...",
                message="Synchronisation des données de votre établissement"
            )
            
            # Récupérer l'établissement
            conn = sync_manager.get_local_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT etablissement FROM User WHERE identifiant = ? AND titre = ?",
                (donner_info["ident"], donner_info["role"])
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                etablissement = result[0]
                
                # Charger données établissement
                sync_manager.sync_etablissement_data(
                    etablissement,
                    callback=lambda msg: print(msg)
                )
                
                # Démarrer sync auto
                sync_manager.start_auto_sync(etablissement)
            
            Dialog.close_dialog(loading)
        
        # Afficher la page principale
        page.clean()
        sidebar, main_content = Page1(page, donner_info)
        page.add(ft.Row([sidebar, main_content], spacing=0, expand=True))
        page.update()
    
    # Reste du code inchangé...
    Donne = Get_on_db_local("User")
    if all([Ident.value == "Deg" , Pass.value == "Deg"]):
        Donner = {
                "ident": "Deg",
                "pass" : "Deg",
                "name": "Zeli",
                "role": "creator"
        }
        Dial = Dialog.custom_dialog(
            title = "Notification",
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE_OUTLINE,
                        size = 60,
                        color=ft.Colors.GREEN_200,
                    ),
                    ft.Text(
                        value="Bienvenue Mon createur"
                    )
                ],
                height=100,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            actions=[
                ft.ElevatedButton(
                    content=ft.Text(
                        value ="Ok",
                        color=ft.Colors.WHITE,
                        ),
                    bgcolor=ft.Colors.GREEN_300,
                    on_click=lambda e : login_success(Donner ,Dial )
                )
            ]
        )
        #pass #Nxte page
    elif Donne:
        found = False
        for elmt in Donne:
            ident , passs = elmt[1],elmt[2]
            if ident == Ident.value and passs == Pass.value:
                found = True
                
                Donner = {
                    "ident": ident,
                    "pass" : passs,
                    "name": elmt[3],
                    "role": elmt[8]
                    }
                
                Dial = Dialog.custom_dialog(
                    title = "Notification",
                    content=ft.Column(
                        [
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE_OUTLINE,
                                size = 60,
                                color=ft.Colors.GREEN_200,
                            ),
                            ft.Text(
                                value=f"Bienvenue {Ident.value}"
                            )
                        ],
                        height=100,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    actions=[
                        ft.ElevatedButton(
                            content=ft.Text(
                                value ="Ok",
                                color=ft.Colors.WHITE,
                                ),
                            bgcolor=ft.Colors.GREEN_200,
                            on_click=lambda e : login_success(Donner ,Dial )
                        )
                    ]
                )
                #break  # stop after first match
        if not found:
            # show error dialog when no matching credentials found
            Dial = Dialog.custom_dialog(
                title = "Notification",
                content=ft.Column(
                    [
                        ft.Icon(
                            ft.Icons.ERROR_ROUNDED,
                            size = 60,
                            color=ft.Colors.RED_200,
                        ),
                        ft.Text(
                            value="Erreur de connexion"
                        )
                    ],
                    height=100,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                actions=[
                    ft.ElevatedButton(
                        content=ft.Text(
                            value ="Ok",
                            color=ft.Colors.WHITE,
                            ),
                        bgcolor=ft.Colors.RED_200,
                        on_click=lambda e : Dialog.close_dialog(Dial)
                    )
                ]
            )
    else:
        Dial = Dialog.custom_dialog(
            title = "Notification",
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.ERROR_ROUNDED,
                        size = 60,
                        color=ft.Colors.RED_200,
                    ),
                    ft.Text(
                        value="Erreur de connexion"
                    )
                ],
                height=100,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            actions=[
                ft.ElevatedButton(
                    content=ft.Text(
                        value ="Ok",
                        color=ft.Colors.WHITE,
                        ),
                    bgcolor=ft.Colors.RED_200,
                    on_click=lambda e : Dialog.close_dialog(Dial)
                )
            ]
        )

def Page0(page):#page: ft.Page):
    page.title = "Login page"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK
    #page.bgcolor = "#1a0d2e"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    
    # Fonction de connexion
    def learn_more_click(e):
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Learn More clicked!", color=ft.Colors.WHITE),
            bgcolor=ft.Colors.BLUE_700,
        )
        page.snack_bar.open = True
        page.update()
    
    # Champs de formulaire
    
    # Panneau gauche - Welcome
    left_panel = ft.Container(
        content=ft.Column([
            # Logo
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text("", size=0),
                        width=8,
                        height=30,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=2,
                    ),
                    ft.Container(width=5),
                    ft.Container(
                        content=ft.Text("", size=0),
                        width=8,
                        height=30,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=2,
                    ),
                ], spacing=0),
                margin=ft.margin.only(bottom=40),
            ),
            
            # Welcome text
            ft.Text(
                "Welcome",
                size=60,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
            ),
            
            ft.Text(
                "On BulletinPro !",
                size=25,
                #weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
            ),
            
            # Ligne décorative
            ft.Container(
                width=80,
                height=4,
                bgcolor="#ff6b6b",
                border_radius=2,
                margin=ft.margin.only(top=10, bottom=30),
            ),
            
            # Description
            ft.Container(
                content=ft.Text(
                    value = "Simplifiez la gestion académique de votre établissement.Générez des bulletins scolaires professionnels en quelques clics, suivez les performances de vos élèves et concentrez-vous sur l'essentiel : leur réussite éducative.Commencez dès maintenant et transformez votre gestion scolaire !",

                    size=14,
                    color="#b8a7d1",
                    text_align=ft.TextAlign.LEFT,
                ),
                width=350,
                margin=ft.margin.only(bottom=40),
            ),
            
            # Bouton Learn More
        ], 
        horizontal_alignment=ft.CrossAxisAlignment.START,
        spacing=0),
        padding=60,
        alignment=ft.alignment.center_left,
    )
    
    # Ajout d'une fonction pour gérer la visibilité du mot de passe
    def toggle_password_visibility(e):
        Pass.password = not Pass.password
        e.control.icon = ft.Icons.VISIBILITY_OFF if Pass.password else ft.Icons.VISIBILITY
        page.update()
    
    Pass = ft.TextField(
        label="Password",
        hint_text="Password",
        password=True,
        color=ft.Colors.WHITE,
        suffix_icon=ft.IconButton(
            icon=ft.Icons.VISIBILITY_OFF,
            icon_color=ft.Colors.WHITE60,
            on_click=toggle_password_visibility,
            tooltip="Afficher/Masquer le mot de passe"
        ),
    )
    Ident = ft.TextField(
        label =  "User Name",
        hint_text =  "User Name",
        color=ft.Colors.WHITE,
    )
    
    def forgot_password(e):
        Dialog = ZeliDialog2(page)
        
        def validate_and_search(e):
            if not all([name_field.value, surname_field.value, email_field.value]):
                error_text.value = "Tous les champs sont obligatoires"
                page.update()
                return
                
            Donne = Get_on_db_local("User")
            found = False
            
            for user in Donne:
                # Structure: id(0), ident(1), pass(2), nom(3), prenom(4), annee(5), email(6)
                if all([user[3].lower() == name_field.value.lower(),
                       user[4].lower() == surname_field.value.lower(),
                       user[6].lower() == email_field.value.lower()]):
                    found = True
                    if user[8]: # Si c'est un mot de passe par défaut
                        Dialog.custom_dialog(
                            title="Récupération réussie",
                            content=ft.Column(
                                [
                                    ft.Icon(
                                        ft.Icons.CHECK_CIRCLE_OUTLINE,
                                        size=50,
                                        color=ft.Colors.GREEN
                                    ),
                                    ft.Text("Vos identifiants:"),
                                    ft.Container(height=10),
                                    ft.Text(f"Identifiant: {user[1]}", size=16),
                                    ft.Text(f"Mot de passe: {user[2]}", size=16, weight=ft.FontWeight.BOLD),
                                ],
                                height=200,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            actions=[
                                ft.ElevatedButton(
                                    text="Ok",
                                    bgcolor=ft.Colors.GREEN,
                                    color=ft.Colors.WHITE,
                                    on_click=lambda e: Dialog.close_dialog(search_dialog)
                                )
                            ]
                        )
                    else:
                        Dialog.alert_dialog(
                            title="Mot de passe personnalisé",
                            message="Vous avez personnalisé votre mot de passe. Veuillez répondre à votre question de sécurité."
                        )
                        security_dialog = Dialog.custom_dialog(
                            title="Question de sécurité",
                            content=ft.Column(
                                [
                                    ft.Text("Question:"),
                                    ft.Text(user[9], size=16, weight=ft.FontWeight.BOLD),  # question
                                    ft.Container(height=20),
                                    ft.TextField(
                                        label="Votre réponse",
                                        password=True
                                    ),
                                    ft.Text("", color="red")  # error text
                                ],
                                height=200,
                                width=400,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            actions=[
                                ft.TextButton("Annuler", 
                                            on_click=lambda e: Dialog.close_dialog(security_dialog)),
                                ft.ElevatedButton(
                                    "Vérifier",
                                    on_click=lambda e: verify_security_answer(
                                        security_dialog.content.controls[3].value,  # réponse
                                        user[10],  # réponse correcte
                                        security_dialog,
                                        user,
                                        security_dialog.content.controls[4]  # error text
                                    )
                                )
                            ]
                        )
                    break
                    
            if not found:
                error_text.value = "Aucun compte trouvé avec ces informations"
                page.update()

        def verify_security_answer(answer, correct_answer, dialog, user, error_text):
            if answer == correct_answer:
                Dialog.custom_dialog(
                    title="Identifiants récupérés",
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.LOCK_OPEN, color=ft.Colors.GREEN, size=50),
                            ft.Text("Vos identifiants:"),
                            ft.Text(f"Identifiant: {user[1]}", size=16),
                            ft.Text(f"Mot de passe: {user[2]}", size=16, weight=ft.FontWeight.BOLD)
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    actions=[
                        ft.ElevatedButton("Ok", 
                                        on_click=lambda e: [Dialog.close_dialog(dialog), 
                                                          Dialog.close_dialog(search_dialog)])
                    ]
                )
            else:
                error_text.value = "Réponse incorrecte"
                page.update()

        name_field = ft.TextField(
            label="Nom",
            hint_text="Votre nom",
            width=300,
            text_align=ft.TextAlign.CENTER,
        )
        
        surname_field = ft.TextField(
            label="Prénom",
            hint_text="Votre prénom",
            width=300,
            text_align=ft.TextAlign.CENTER,
        )
        
        email_field = ft.TextField(
            label="Email",
            hint_text="Votre email",
            width=300,
            text_align=ft.TextAlign.CENTER,
        )
        
        error_text = ft.Text(
            value="",
            color=ft.Colors.RED,
            size=12,
        )

        search_dialog = Dialog.custom_dialog(
            title="Récupération de mot de passe",
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.PASSWORD_ROUNDED,
                        size=50,
                        color=ft.Colors.BLUE,
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        "Veuillez entrer vos informations",
                        text_align=ft.TextAlign.CENTER,
                        size=14,
                    ),
                    ft.Container(height=20),
                    name_field,
                    surname_field,
                    email_field,
                    error_text,
                ],
                height=400,
                width=400,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
            ),
            actions=[
                ft.TextButton(
                    text="Annuler",
                    on_click=lambda e: Dialog.close_dialog(search_dialog)
                ),
                ft.ElevatedButton(
                    text="Rechercher",
                    bgcolor=ft.Colors.BLUE,
                    color=ft.Colors.WHITE,
                    on_click=validate_and_search
                ),
            ]
        )

    # Panneau droit - Sign in
    right_panel = ft.Container(
        content=ft.Column([
            # Titre Sign in
            ft.Text(
                "Sign in",
                size=36,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
                text_align=ft.TextAlign.CENTER,
            ),
            
            ft.Container(height=30),
            
            # User Name
            ft.Column([
                Ident,
                ft.Container(height=8),
            ], spacing=0),
            
            ft.Container(height=20),
            
            # Password
            ft.Column([
                Pass,
                ft.Container(height=8),
            ], spacing=0),
            
            ft.Container(height=5),
            
            # Lien "Mot de passe oublié"
            ft.TextButton(
                text = "Mot de passe oublié",
                on_click=forgot_password,
                ),
            ft.Container(height=30),
            ft.Container(
                content=ft.Text(
                    "Submit",
                    size=16,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.WHITE,
                    text_align=ft.TextAlign.CENTER,
                ),
                width=280,
                height=50,
                bgcolor=None,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.center_left,
                    end=ft.alignment.center_right,
                    colors=["#ff7b54", "#ff5252"],
                ),
                border_radius=25,
                alignment=ft.alignment.center,
                ink=True,
                on_click = lambda e : Submit(page , Ident , Pass),
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=20,
                    color="#ff5252",
                    offset=ft.Offset(0, 5),
                ),
            ),
            
            ft.Container(height=25),
            
            # Social media Icons
            ft.Row([
                ft.IconButton(
                    icon=ft.Icons.FACEBOOK,
                    icon_color=ft.Colors.WHITE,
                    icon_size=22,
                    tooltip="Facebook",
                ),
                ft.IconButton(
                    icon=ft.Icons.CAMERA_ALT,
                    icon_color=ft.Colors.WHITE,
                    icon_size=22,
                    tooltip="Instagram",
                ),
                ft.IconButton(
                    icon=ft.Icons.PUSH_PIN,
                    icon_color=ft.Colors.WHITE,
                    icon_size=22,
                    tooltip="Pinterest",
                ),
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=15),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=0),
        bgcolor="#3d2f52",
        padding=50,
        border_radius=ft.border_radius.only(top_right=15, bottom_right=15),
        width=400,
        #alignment=ft.alignment.center,
    )
    
    # Conteneur principal avec fond décoratif
    main_container = ft.Container(
        content=ft.Stack([
            # Formes décoratives en arrière-plan
            ft.Container(
                width=400,
                height=400,
                border_radius=200,
                bgcolor="#2d1b47",
                opacity=0.3,
                left=-100,
                top=-100,
            ),
            ft.Container(
                width=300,
                height=300,
                border_radius=150,
                bgcolor="#4a2d6b",
                opacity=0.2,
                right=-50,
                top=100,
            ),
            ft.Container(
                width=200,
                height=200,
                border_radius=100,
                bgcolor="#5c3d7a",
                opacity=0.25,
                left=100,
                bottom=-50,
            ),
            
            # Panneau de login avec effet glassmorphism
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=left_panel,
                        bgcolor="#2d1947",
                        expand=True,
                        border_radius=ft.border_radius.only(top_left=15, bottom_left=15),
                    ),
                    right_panel,
                ], spacing=0),
                width=900,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=50,
                    color="#000000",
                    offset=ft.Offset(0, 10),
                ),
                border_radius=15,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
            ),
        ]),
        alignment=ft.alignment.center,
        expand=True,
    )
    
    # Boutons en haut
    
    # Layout complet
    return ft.Stack([
            main_container,
        ], expand=True)



#==============================================================================
def get_user_preference(setting_name,Donner):
    """Récupère les préférences utilisateur"""
    con = None
    try:
        con = get_db_connection()
        cur = con.cursor()
        
        if Donner and Donner.get("ident") == "Deg":
            cur.execute(f"SELECT {setting_name} FROM Dev_Preferences WHERE id = 1")
        else:
            cur.execute(f"SELECT {setting_name} FROM User_Preferences WHERE user_id = ?",
                       (Donner.get("ident") if Donner else None,))
        
        result = cur.fetchone()
        return result[0] if result else "light" if setting_name == "theme" else "fr"
    except sqlite3.Error:
        return "light" if setting_name == "theme" else "fr"
    finally:
        if con:
            con.close()

def User_Config(page, Donner):  # Ajout du paramètre Donner
    """Gestion des préférences utilisateur (mode/langue)
    Maintenant: applique automatiquement les préférences stockées au chargement.
    """
    Dialog = ZeliDialog2(page)

    # --- apply stored preferences immediately on load ---
    try:
        pref_theme = get_user_preference("theme", Donner)
        pref_lang = get_user_preference("language", Donner)
        page.theme_mode = ft.ThemeMode.DARK if pref_theme == "dark" else ft.ThemeMode.LIGHT
        # you can store language on page or Info if needed
        page.update()
    except Exception:
        pass
    
    def save_preferences(theme, language, dialog):
        con = None
        try:
            con = get_db_connection()
            cur = con.cursor()
            
            # Table pour développeur
            cur.execute("""
                CREATE TABLE IF NOT EXISTS Dev_Preferences (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    theme TEXT DEFAULT 'light',
                    language TEXT DEFAULT 'fr'
                )
            """)
            
            # Table pour utilisateurs normaux
            cur.execute("""
                CREATE TABLE IF NOT EXISTS User_Preferences (
                    user_id TEXT PRIMARY KEY,
                    theme TEXT DEFAULT 'light',
                    language TEXT DEFAULT 'fr'
                )
            """)
            
            if Donner and Donner.get("ident") == "Deg":  # Utilisation de Donner
                cur.execute("""
                    INSERT OR REPLACE INTO Dev_Preferences (id, theme, language)
                    VALUES (1, ?, ?)
                """, (theme, language))
            elif Donner:  # Vérification que Donner existe
                cur.execute("""
                    INSERT OR REPLACE INTO User_Preferences (user_id, theme, language)
                    VALUES (?, ?, ?)
                """, (Donner.get("ident"), theme, language))
            
            con.commit()
            
            # Appliquer le thème immédiatement
            page.theme_mode = ft.ThemeMode.DARK if theme == "dark" else ft.ThemeMode.LIGHT
            page.update()
            
            Dialog.alert_dialog(title="Succès", message="Préférences enregistrées!")
            Dialog.close_dialog(dialog)
            
        except sqlite3.Error as e:
            Dialog.alert_dialog(title="Erreur", message=str(e))
        finally:
            if con:
                con.close()
