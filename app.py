import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import pandas as pd
import os
import time
import random
import string
import io
import json
from fpdf import FPDF

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="ASR Pro - Excellence Pédagogique",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SÉCURITÉ (JS UNIQUEMENT) ---
st.components.v1.html("""
    <script>
    document.addEventListener('contextmenu', event => event.preventDefault());
    document.addEventListener('copy', e => e.preventDefault());
    document.addEventListener('paste', e => e.preventDefault());
    </script>
""", height=0)

# --- 3. DESIGN SYSTEM (CSS AVANCÉ & FALLBACK) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
    
    :root {
        --bg-dark: #0a192f;
        --bg-panel: #112240;
        --primary: #c2410c;
        --accent: #f57c00;
        --text-white: #ffffff;
    }

    /* GLOBAL */
    html, body, [data-testid="stAppViewContainer"], .main {
        background-color: var(--bg-dark) !important;
        color: var(--text-white) !important;
        font-family: 'Inter', sans-serif;
    }

    /* HEADER */
    .custom-header {
        text-align: center;
        padding: 30px 20px;
        background: radial-gradient(circle at center, #1e3a8a 0%, #0a192f 80%);
        border-bottom: 2px solid var(--accent);
        margin-bottom: 40px;
        border-radius: 0 0 15px 15px;
    }
    .header-title { 
        font-size: 2.2rem; font-weight: 900; color: var(--accent); margin: 0; 
        text-transform: uppercase; letter-spacing: 2px;
    }
    .header-subtitle { 
        font-size: 0.9rem; color: rgba(255,255,255,0.7); 
        text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;
    }
    .header-inst {
        margin-top: 10px; font-weight: 700; color: white; font-size: 1.1rem;
    }

    /* BOUTONS (Si navbar custom utilisée) */
    .stButton > button {
        background-color: var(--primary) !important;
        color: white !important;
        border: none;
        border-radius: 6px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* CONTACT */
    .contact-line {
        font-size: 1.2rem; margin-bottom: 15px; color: #e2e8f0;
        display: flex; align-items: center; justify-content: center;
    }
    .contact-emoji { font-size: 1.5rem; margin-right: 15px; }

    /* FOOTER */
    .footer-official {
        margin-top: 80px; padding: 60px 20px; background-color: var(--bg-panel);
        border-top: 4px solid var(--accent); text-align: center;
    }
    .f-name { font-size: 1.5rem; font-weight: 800; color: white; margin-bottom: 10px; }
    .f-line { font-size: 1.1rem; color: #cbd5e1; margin-bottom: 5px; }
    .f-bottom { margin-top: 30px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1); font-size: 0.9rem; color: #64748b; letter-spacing: 1px; font-weight: bold; }
    
    /* Navbar Custom Fallback Styles */
    .navbar-container {
        display: flex; align-items: center; background-color: var(--bg-panel);
        padding: 10px 20px; border-bottom: 3px solid var(--accent);
        border-radius: 0 0 16px 16px; margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .nav-logo {
        width: 50px; height: 50px; background: white; border: 3px solid var(--accent); 
        border-radius: 50%; color: #0047AB; font-weight: 900; 
        display: flex; align-items: center; justify-content: center; margin-right: 15px;
    }
    .nav-title { font-weight: 900; font-size: 1.2rem; color: white; text-transform: uppercase; letter-spacing: 2px; }
    </style>
""", unsafe_allow_html=True)

# --- 4. INITIALISATION FIREBASE ---
if not firebase_admin._apps:
    try:
        if os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
        else:
            try:
                firebase_secrets = json.loads(st.secrets["FIREBASE_JSON"])
                cred = credentials.Certificate(firebase_secrets)
                firebase_admin.initialize_app(cred)
            except:
                pass 
    except Exception as e:
        pass

db = firestore.client()
PROJET_ID = "examen-asr-prod"

# --- 5. ETAT DE SESSION ---
if 'user' not in st.session_state: st.session_state.user = None
if 'page' not in st.session_state: st.session_state.page = 'Accueil' # Default capitalized for navbar
if 'step' not in st.session_state: st.session_state.step = 0
if 'answers' not in st.session_state: st.session_state.answers = {}
if 'codes' not in st.session_state: st.session_state.codes = {}
if 'cheats' not in st.session_state: st.session_state.cheats = 0
if 'exam_open' not in st.session_state: st.session_state.exam_open = True
if 'ex_start_time' not in st.session_state: st.session_state.ex_start_time = time.time()

# --- 6. DONNÉES EXAMEN ---
EXERCICES = [
    {"id": 1, "titre": "Algorithmique - Contrôle d'Accès", "points": 5, "enonce": "Écrivez un programme qui demande l'année de naissance de l'utilisateur.\n1. Calculez son âge (référence 2026).\n2. Si l'utilisateur a 18 ans ou plus, affichez: 'Accès autorisé. Bienvenue !'.\n3. Sinon, affichez: 'Accès refusé. Vous devez être majeur.'.", "questions": [{"id":"q1_1","text":"Âge calculé pour naissance en 2010 ?", "type":"number", "correct":16}, {"id":"q1_2","text":"Message retourné pour 16 ans ?", "type":"choice", "options":["Accès autorisé. Bienvenue !", "Accès refusé. Vous devez être majeur."], "correct":"Accès refusé. Vous devez être majeur."}]},
    {"id": 2, "titre": "Physique - État de l'eau", "points": 5, "enonce": "Demandez la température T de l'eau (°C) et affichez son état :\n- T <= 0 : Glace\n- 0 < T < 100 : Liquide\n- T >= 100 : Vapeur\nBonus : Si T > 300, affichez 'Attention : Température critique !'.", "questions": [{"id":"q2_1","text":"État physique à 100°C pile ?", "type":"choice", "options":["Glace", "Liquide", "Vapeur"], "correct":"Vapeur"}]},
    {"id": 3, "titre": "Gestion - Assurance Auto", "points": 5, "enonce": "Calculez le tarif d'assurance :\n- Tarif de base : 500 €.\n- Si le conducteur a moins de 25 ans ET moins de 2 ans de permis : + 200 €.\n- Si le conducteur a plus de 25 ans OU plus de 5 ans de permis : - 50 €.", "questions": [{"id":"q3_1","text":"Prix final pour 22 ans et 1 an de permis ?", "type":"number", "correct":700}]},
    {"id": 4, "titre": "Ingénierie Financière - Crédit", "points": 5, "enonce": "Vérifiez l'éligibilité au crédit :\n- Épargne (Revenu - Dépenses) <= 0 : Refus (Fonds insuffisants).\n- Taux d'endettement (Mensualité / Revenu) > 33% : Refus (Taux > 33%).\n- Sinon : Pré-approuvé.", "questions": [{"id":"q4_1","text":"Revenu 2000, Dépenses 2000. Décision ?", "type":"choice", "options":["Fonds insuffisants", "Taux > 33%"], "correct":"Fonds insuffisants"}]}
]

# --- 7. COMPOSANTS D'INTERFACE ---

def show_header():
    st.markdown("""
        <div class="custom-header">
            <div class="header-subtitle">République Algérienne Démocratique et Populaire</div>
            <h1 class="header-title">ASR PRO EXCELLENCE</h1>
            <div class="header-inst">Institut National Spécialisé Belazzoug Athmane BBA 01</div>
        </div>
    """, unsafe_allow_html=True)

def show_footer():
    st.markdown("""
        <div class="footer-official">
            <div class="f-name">M. Ahmed Haithem BERKANE PSFEP CIP</div>
            <div class="f-line">Institut National Spécialisé dans la formation professionnelle BBA01</div>
            <div class="f-line">Direction de la formation professionnelle BBA</div>
            <div class="f-line">Ministère de la formation et de l'enseignement professionnels</div>
            <div class="f-bottom">
                RÉPUBLIQUE ALGÉRIENNE DÉMOCRATIQUE ET POPULAIRE 🇩🇿 | TOUS DROITS RÉSERVÉS © 2026
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 8. VUES ---

def accueil_view():
    show_header()
    st.markdown("""
        <div style="background:white; color:#0f172a; padding:40px; border-radius:12px; border-left:8px solid #f57c00; text-align:center;">
            <h1>Bienvenue sur le Portail ASR Pro</h1>
            <p style="font-size:1.2rem;">Plateforme d'évaluation certifiée pour le module Prog DevNet & Scripts.</p>
        </div>
    """, unsafe_allow_html=True)
    show_footer()

def enonce_view():
    show_header()
    st.markdown("<h2 style='text-align:center; color:#f57c00; margin-bottom:30px;'>📜 ÉNONCÉS DE L'EXAMEN</h2>", unsafe_allow_html=True)
    for ex in EXERCICES:
        st.markdown(f"""
            <div style="background:white; color:#0f172a; padding:30px; border-radius:12px; border-left:8px solid #f57c00; margin-bottom:20px;">
                <h3 style="color:#c2410c; margin-top:0;">EXERCICE {ex['id']} : {ex['titre']}</h3>
                <p style="white-space: pre-wrap; background:#f1f5f9; padding:15px; border-radius:8px; font-family:monospace;">{ex['enonce']}</p>
                <p style="text-align:right; font-weight:bold; color:#c2410c;">Note : {ex['points']} Points</p>
            </div>
        """, unsafe_allow_html=True)
    show_footer()

def contact_view():
    show_header()
    st.markdown("""
        <div style="background:#112240; border:1px solid rgba(255,255,255,0.1); border-radius:16px; padding:50px; max-width:600px; margin:0 auto; text-align:center;">
            <h2 style="color:#f57c00; font-weight:900; font-size:2.5rem; margin-bottom:5px;">Ahmed Haithem BERKANE</h2>
            <p style="color:#94a3b8; font-weight:700; text-transform:uppercase; letter-spacing:2px; margin-bottom:40px;">PSFEP CIP - Expert ASR Pro</p>
            
            <div class="contact-line"><span class="contact-emoji">📞</span> +213 699 102 523</div>
            <div class="contact-line"><span class="contact-emoji">📧</span> haithemcomputing@gmail.com</div>
            <div class="contact-line"><span class="contact-emoji">🔵</span> Facebook : Haithem BERKANE</div>
            <div class="contact-line"><span class="contact-emoji">💼</span> LinkedIn : Haithem BERKANE</div>
            <div class="contact-line"><span class="contact-emoji">📍</span> INSFP Belazzoug Athmane BBA 01</div>
        </div>
    """, unsafe_allow_html=True)
    show_footer()

def faq_view():
    show_header()
    st.markdown("<h2 style='text-align:center; color:#f57c00;'>❓ FAQ</h2>", unsafe_allow_html=True)
    with st.expander("Comment se déroule l'examen ?"):
        st.write("L'examen dure 2h. Vous devez compléter les 4 exercices séquentiellement.")
    with st.expander("Le système anti-triche"):
        st.write("Le système détecte si vous changez d'onglet ou quittez la page. Ces actions sont enregistrées.")
    show_footer()

def login_view():
    show_header()
    st.markdown("""<div style="background:white; color:#0f172a; padding:30px; border-radius:12px; border-left:8px solid #f57c00; max-width:500px; margin:0 auto;"><h2 style="text-align:center;">Connexion</h2></div>""", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u = st.text_input("Identifiant")
        p = st.text_input("Mot de passe", type="password")
        if st.button("SE CONNECTER", use_container_width=True):
            if u == "admin" and p == "admin":
                st.session_state.user = {"name": "ADMINISTRATEUR", "role": "teacher", "username": "admin"}
                st.session_state.page = 'Teacher'
                st.rerun()
            elif u and p:
                 st.session_state.user = {"name": f"Stagiaire {u}", "role": "student", "username": u}
                 st.session_state.page = 'Student Dash'
                 st.rerun()
            else:
                st.error("Veuillez remplir les champs.")
    show_footer()

def student_dash():
    show_header()
    st.markdown(f"<h1 style='text-align:center;'>Espace Candidat : {st.session_state.user['name']}</h1>", unsafe_allow_html=True)
    if st.session_state.exam_open:
        c1, c2 = st.columns(2)
        with c1: st.info("Statut de l'examen : EN COURS")
        with c2:
            if st.button("🚀 DÉMARRER L'EXAMEN", use_container_width=True):
                st.session_state.page = 'Exam'
                st.session_state.ex_start_time = time.time()
                st.rerun()
    else: st.warning("L'examen est actuellement verrouillé.")
    show_footer()

def exam_view():
    step = st.session_state.step
    if step >= len(EXERCICES):
        st.success("Examen terminé ! Vos réponses ont été enregistrées.")
        if st.button("Retour au tableau de bord"):
            st.session_state.page = 'Student Dash'
            st.rerun()
        return

    ex = EXERCICES[step]
    show_header()
    st.markdown(f"## Exercice {ex['id']}: {ex['titre']}")
    st.info(ex['enonce'])
    st.text_area("Votre code Python", height=200, key=f"code_{ex['id']}")
    st.write("---")
    st.write("**Questions théoriques**")
    for q in ex['questions']:
        if q['type'] == 'choice': st.radio(q['text'], q['options'], key=f"ans_{q['id']}")
        else: st.number_input(q['text'], key=f"ans_{q['id']}")
    c1, c2 = st.columns([1, 5])
    with c2:
        if st.button("VALIDER ET CONTINUER ➡️"):
            st.session_state.step += 1
            st.rerun()

def teacher_dash():
    show_header()
    st.title("Tableau de Bord Enseignant")
    st.info("Gestion des sessions et des notes.")
    show_footer()

# --- NAVIGATION SYSTEM (INTELLIGENT) ---

# Mapping des noms de pages vers les fonctions
FUNCTIONS = {
    "Accueil": accueil_view,
    "Énoncés": enonce_view,
    "FAQ": faq_view,
    "Contact": contact_view,
    "Connexion": login_view,
    "Student Dash": student_dash,
    "Exam": exam_view,
    "Teacher": teacher_dash
}

# 1. Tentative d'import de la librairie demandée
try:
    from streamlit_navigation_bar import st_navbar
    
    # Styles adaptés au thème ASR Pro (Navy/Orange)
    styles = {
        "nav": {"background-color": "#112240", "justify-content": "center"},
        "img": {"padding-right": "14px"},
        "span": {"color": "white", "padding": "14px"},
        "active": {"background-color": "#f57c00", "color": "white", "font-weight": "bold", "padding": "14px"}
    }
    options = {"show_menu": False, "show_sidebar": False}
    
    # Définition des pages disponibles dans le menu
    pages = ["Accueil", "Énoncés", "FAQ", "Contact"]
    if st.session_state.user:
        pages.append("Déconnexion")
    else:
        pages.append("Connexion")
        
    # Affichage de la navbar
    selected_page = st_navbar(pages, styles=styles, options=options)
    
    # Gestion de la sélection
    if selected_page == "Déconnexion":
        st.session_state.user = None
        st.session_state.page = "Accueil"
        st.rerun()
    elif selected_page == "Connexion":
        st.session_state.page = "Connexion"
    elif selected_page in pages:
        st.session_state.page = selected_page

except ImportError:
    # 2. Fallback: Navbar CSS Custom (Si la librairie n'est pas installée)
    st.markdown("""
        <div class="navbar-container">
            <div class="nav-logo">HB</div>
            <div class="nav-title">ASR PRO</div>
            <div style="flex-grow:1;"></div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1.5])
    with col1: 
        if st.button("🏠 ACCUEIL", use_container_width=True): st.session_state.page = 'Accueil'
    with col2: 
        if st.button("📜 ÉNONCÉS", use_container_width=True): st.session_state.page = 'Énoncés'
    with col3: 
        if st.button("❓ FAQ", use_container_width=True): st.session_state.page = 'FAQ'
    with col4: 
        if st.button("📞 CONTACT", use_container_width=True): st.session_state.page = 'Contact'
    with col5:
        if st.session_state.user:
            if st.button("👤 DÉCONNEXION", use_container_width=True): 
                st.session_state.user = None
                st.session_state.page = 'Accueil'
                st.rerun()
        else:
            if st.button("🔐 CONNEXION", use_container_width=True): 
                st.session_state.page = 'Connexion'

# Exécution de la page courante
if st.session_state.page in FUNCTIONS:
    FUNCTIONS[st.session_state.page]()
elif st.session_state.page == 'Connexion': # Alias pour le fallback
    login_view()
else:
    accueil_view()
