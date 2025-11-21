import flet as ft
from Zeli_Dialog import ZeliDialog2
import sqlite3
import os
import shutil
from pathlib import Path
from time import sleep
from db_manager import get_db_connection

def Saisie_Notes(page, Donner):
    """Saisie des notes par le professeur pour sa matière uniquement"""
    Dialog = ZeliDialog2(page)
    
    # ✅ IMPORTANT: Déclarer student_list_dialog GLOBALEMENT en haut
    student_list_dialog = None
    
    # Vérifier que c'est bien un prof
    if Donner.get("role") != "prof":
        Dialog.alert_dialog(
            title="Accès refusé",
            message="Seuls les enseignants peuvent saisir des notes."
        )
        return
    
    def Return(Ident):
        """Récupère une information depuis la table User"""
        con = None
        try:
            con = get_db_connection()
            cur = con.cursor()
            cur.execute(
                f"SELECT {Ident} FROM User WHERE identifiant = ? AND titre = ? AND passwords = ?",
                (Donner.get("ident"), Donner.get("role"), Donner.get("pass"))
            )
            donne = cur.fetchall()
            cur.close()
            return donne
        except Exception as e:
            Dialog.error_toast(f"Erreur de récupération: {str(e)}")
            return []
        finally:
            if con:
                con.close()
    
    def get_teacher_subject():
        """Récupère la matière du professeur"""
        con = None
        try:
            con = get_db_connection()
            cur = con.cursor()
            cur.execute("SELECT matiere FROM Teacher WHERE ident = ?", (Donner.get("ident"),))
            result = cur.fetchone()
            return result[0] if result else None
        except:
            return None
        finally:
            if con:
                con.close()
    
    def load_classes_with_students():
        """Charge les classes qui ont des élèves"""
        Etat = Return("etablissement")
        if not Etat:
            return []
        
        con = None
        try:
            con = get_db_connection()
            cur = con.cursor()
            cur.execute("""
                SELECT DISTINCT classe, COUNT(*) as effectif
                FROM Students 
                WHERE etablissement = ?
                GROUP BY classe
                ORDER BY classe
            """, (Etat[0][0],))
            return cur.fetchall()
        except:
            return []
        finally:
            if con:
                con.close()
    
    def load_students_by_class(classe_nom):
        """Charge tous les élèves d'une classe"""
        Etat = Return("etablissement")
        if not Etat:
            return []
        
        con = None
        try:
            con = get_db_connection()
            cur = con.cursor()
            cur.execute("""
                SELECT * FROM Students 
                WHERE classe = ? AND etablissement = ?
                ORDER BY nom, prenom
            """, (classe_nom, Etat[0][0]))
            return cur.fetchall()
        except:
            return []
        finally:
            if con:
                con.close()
    
    def get_matiere_coefficient(matiere_nom):
        """Récupère le coefficient d'une matière"""
        Etat = Return("etablissement")
        if not Etat:
            return "2"
        
        con = None
        try:
            con = get_db_connection()
            cur = con.cursor()
            return "2"
        except:
            return "2"
        finally:
            if con:
                con.close()
    
    def check_note_exists(matricule, matiere, classe):
        """Vérifie si une note existe déjà"""
        con = None
        try:
            con = get_db_connection()
            cur = con.cursor()
            
            cur.execute("""
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
                    UNIQUE(matricule, matiere, classe)
                )
            """)
            con.commit()
            
            cur.execute("""
                SELECT * FROM Notes 
                WHERE matricule = ? AND matiere = ? AND classe = ?
            """, (matricule, matiere, classe))
            
            result = cur.fetchone()
            return result
            
        except:
            return None
        finally:
            if con:
                con.close()
    
    def calculate_moyenne(note_interro, note_devoir, note_compo):
        """Calcule la moyenne"""
        try:
            interro = float(note_interro) if note_interro else 0
            devoir = float(note_devoir) if note_devoir else 0
            compo = float(note_compo) if note_compo else 0
            
            moyenne = (interro + devoir + (2 * compo)) / 4
            return f"{moyenne:.2f}"
        except:
            return "0.00"
    
    # ✅ DÉPLACER show_students_list ICI (avant create_student_card)
    def show_students_list(classe_nom):
        """Affiche la liste des élèves d'une classe"""
        nonlocal student_list_dialog  # ✅ Utiliser nonlocal pour modifier la variable
        
        students = load_students_by_class(classe_nom)
        matiere = get_teacher_subject()
        
        if not matiere:
            Dialog.error_toast("Impossible de récupérer votre matière")
            return
        
        # Créer les cartes élèves
        student_cards = []
        for student in students:
            student_cards.append(create_student_card(student, classe_nom, matiere))
        
        if not student_cards:
            student_cards = [
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.PEOPLE, size=60, color=ft.Colors.GREY_400),
                        ft.Text("Aucun élève dans cette classe", size=16, color=ft.Colors.GREY_600),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10
                    ),
                    padding=30
                )
            ]
        
        # Statistiques
        total_students = len(students)
        notes_saisies = sum(1 for s in students if check_note_exists(s[2], matiere, classe_nom))
        reste = total_students - notes_saisies
        
        student_list_dialog = Dialog.custom_dialog(
            title=f"📚 {matiere} - Classe {classe_nom}",
            content=ft.Column([
                # Statistiques
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"{total_students}", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE),
                                ft.Text("Élèves", size=12),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            padding=10,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"{notes_saisies}", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                                ft.Text("Saisies", size=12),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            padding=10,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"{reste}", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE),
                                ft.Text("Restantes", size=12),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            padding=10,
                            expand=True,
                        ),
                    ]),
                    bgcolor=ft.Colors.BLUE_50,
                    padding=10,
                    border_radius=10,
                ),
                
                ft.Divider(),
                
                ft.Text("Cliquez sur un élève pour saisir/modifier ses notes", 
                       size=12, italic=True, color=ft.Colors.GREY_600),
                
                # Liste des élèves
                ft.Container(
                    content=ft.Column(
                        controls=student_cards,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    height=350,
                ),
            ],
            width=500,
            height=500,
            spacing=10,
            ),
            actions=[
                ft.TextButton(
                    "Retour",
                    icon=ft.Icons.ARROW_BACK,
                    on_click=lambda e: back_to_class_selection()
                )
            ]
        )
    
    def back_to_class_selection():
        """Retourne à la sélection de classe"""
        if student_list_dialog:
            Dialog.close_dialog(student_list_dialog)
        # Recharger la page principale
        Saisie_Notes(page, Donner)
    
    def create_student_card(student, classe_nom, matiere):
        """Crée une carte pour un élève"""
        
        note_exists = check_note_exists(student[2], matiere, classe_nom)
        
        status_icon = ft.Icons.CHECK_CIRCLE if note_exists else ft.Icons.ADD_CIRCLE
        status_color = ft.Colors.GREEN if note_exists else ft.Colors.ORANGE
        status_text = "Notes saisies" if note_exists else "À saisir"
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    # Avatar
                    ft.Container(
                        content=ft.Text(
                            student[0][0].upper(),
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                        width=40,
                        height=40,
                        border_radius=20,
                        bgcolor=ft.Colors.BLUE_400 if 'M' in str(student[4]) else ft.Colors.PINK_400,
                        alignment=ft.alignment.center,
                    ),
                    
                    # Infos
                    ft.Column([
                        ft.Text(
                            f"{student[0]} {student[1]}",
                            size=15,
                            weight=ft.FontWeight.W_500,
                        ),
                        ft.Text(
                            f"Matricule: {student[2]}",
                            size=12,
                            color=ft.Colors.GREY_700,
                        ),
                    ], spacing=2, expand=True),
                    
                    # Statut
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(status_icon, color=status_color, size=18),
                            ft.Text(status_text, size=11, color=status_color),
                        ], spacing=5),
                        padding=5,
                        border_radius=5,
                        bgcolor=f"{status_color}20",
                    ),
                ], spacing=10),
            ]),
            padding=12,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=10,
            ink=True,
            height=70,
            on_click=lambda e, s=student: show_student_notes(s, classe_nom, matiere),
        )
    
    # Reste du code (show_student_notes, etc.)
    # ... [GARDER TOUT LE RESTE DU CODE INCHANGÉ]
    
    def show_student_notes(student, classe_nom, matiere):
        """Affiche le formulaire de saisie/modification des notes"""
        existing_note = check_note_exists(student[2], matiere, classe_nom)
        
        if existing_note:
            show_existing_notes(student, classe_nom, matiere, existing_note)
        else:
            show_add_notes_form(student, classe_nom, matiere)
    
    # ✅ Ajouter toutes les autres fonctions ici...
    # (show_existing_notes, modify_notes, show_add_notes_form, etc.)
    # Je les ai omises pour la clarté, mais gardez-les toutes !
    
    def create_class_card(classe):
        """Crée une carte pour une classe"""
        classe_nom = classe[0]
        effectif = classe[1]
        
        matiere = get_teacher_subject()
        
        notes_count = 0
        if matiere:
            con = None
            try:
                con = get_db_connection()
                cur = con.cursor()
                cur.execute("""
                    SELECT COUNT(*) FROM Notes 
                    WHERE classe = ? AND matiere = ?
                """, (classe_nom, matiere))
                result = cur.fetchone()
                notes_count = result[0] if result else 0
            except:
                pass
            finally:
                if con:
                    con.close()
        
        pourcentage = int((notes_count / effectif * 100)) if effectif > 0 else 0
        
        if pourcentage == 100:
            progress_color = ft.Colors.GREEN
        elif pourcentage >= 50:
            progress_color = ft.Colors.ORANGE
        else:
            progress_color = ft.Colors.RED
        
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.CLASS_, color=ft.Colors.BLUE, size=40),
                ft.Text(
                    classe_nom,
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=5),
                ft.Row([
                    ft.Icon(ft.Icons.PEOPLE, color=ft.Colors.BLUE, size=20),
                    ft.Text(f"{effectif} élève(s)", size=14),
                ],
                alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Container(height=5),
                ft.Column([
                    ft.Text(f"{notes_count}/{effectif} notes saisies", 
                           size=12, color=ft.Colors.GREY_700),
                    ft.ProgressBar(
                        value=pourcentage / 100,
                        color=progress_color,
                        bgcolor=ft.Colors.GREY_300,
                        height=8,
                    ),
                    ft.Text(f"{pourcentage}%", size=12, 
                           weight=ft.FontWeight.BOLD, color=progress_color),
                ],
                spacing=3,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5,
            alignment=ft.MainAxisAlignment.CENTER,
            ),
            border=ft.border.all(2, ft.Colors.BLUE_200),
            border_radius=15,
            padding=20,
            margin=10,
            width=220,
            height=220,
            ink=True,
            on_click=lambda e, c=classe_nom: show_students_list(c),  # ✅ Maintenant ça marche !
        )
    
    # ==================== DIALOGUE PRINCIPAL ====================
    
    teacher_subject = get_teacher_subject()
    
    if not teacher_subject:
        Dialog.alert_dialog(
            title="Erreur",
            message="Impossible de récupérer votre matière d'enseignement."
        )
        return
    
    classes = load_classes_with_students()
    
    class_cards = [create_class_card(classe) for classe in classes]
    
    if not class_cards:
        class_cards = [
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.CLASS_, size=60, color=ft.Colors.GREY_400),
                    ft.Text(
                        "Aucune classe disponible",
                        size=16,
                        color=ft.Colors.GREY_600
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
                ),
                padding=30
            )
        ]
    
    main_dialog = Dialog.custom_dialog(
        title=f"📝 Saisie des notes - {teacher_subject}",
        content=ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.PERSON, color=ft.Colors.PURPLE, size=30),
                        ft.Column([
                            ft.Text(
                                f"Prof : {Donner.get('name', 'Enseignant')}",
                                size=16,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Text(
                                f"Matière : {teacher_subject}",
                                size=14,
                                color=ft.Colors.PURPLE,
                                weight=ft.FontWeight.W_500
                            ),
                        ], spacing=2),
                    ], spacing=10),
                ]),
                bgcolor=ft.Colors.PURPLE_50,
                padding=15,
                border_radius=10,
            ),
            
            ft.Divider(),
            
            ft.Text(
                "Sélectionnez une classe pour saisir les notes",
                size=14,
                italic=True,
                color=ft.Colors.GREY_600,
                text_align=ft.TextAlign.CENTER
            ),
            
            ft.Container(height=5),
            
            ft.Container(
                content=ft.GridView(
                    controls=class_cards,
                    runs_count=2,
                    max_extent=240,
                    child_aspect_ratio=1.0,
                    spacing=10,
                    run_spacing=10,
                ),
                height=350,
            ),
        ],
        width=550,
        height=500,
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        actions=[
            ft.TextButton(
                "Fermer",
                icon=ft.Icons.CLOSE,
                on_click=lambda e: Dialog.close_dialog(main_dialog)
            )
        ]
    )
