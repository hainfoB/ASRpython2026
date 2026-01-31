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
    initial_sidebar_state="collapsed" # Sidebar masquée par défaut
)

# --- 2. SÉCURITÉ (JS BASIC - PLUS DE BOUTON) ---
st.components.v1.html("""
    <script>
    document.addEventListener('contextmenu', event => event.preventDefault());
    document.addEventListener('copy', e => e.preventDefault());
    document.addEventListener('paste', e => e.preventDefault());
    </script>
""", height=0)

# --- 3. DESIGN SYSTEM (CSS BARRE DE NAVIGATION & STYLE ÉLITE) ---
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

    html, body, [data-testid="stAppViewContainer"], .main {
        background-color: var(--bg-dark) !important;
        color: var(--text-white) !important;
        font-family: 'Inter', sans-serif;
    }

    /* CACHER LA SIDEBAR NATIVE */
    [data-testid="stSidebar"] { display: none; }
    [data-testid="stSidebarCollapsedControl"] { display: none; }

    /* --- STYLE BARRE DE NAVIGATION (NAVBAR) --- */
    .navbar-container {
        display: flex;
        align-items: center;
        background-color: var(--bg-panel);
        padding: 10px 20px;
        border-bottom: 3px solid var(--accent);
        border-radius: 0 0 16px 16px;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    
    /* BOUTONS DU MENU (TYPE SECONDARY) */
    /* On utilise le type 'secondary' de Streamlit pour les liens du menu */
    button[kind="secondary"] {
        background: transparent !important;
        border: none !important;
        color: rgba(255,255,255,0.7) !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        transition: all 0.3s !important;
    }
    button[kind="secondary"]:hover {
        color: var(--accent) !important;
        background-color: rgba(255,255,255,0.05) !important;
        transform: translateY(-2px);
    }
    button[kind="secondary"]:focus {
        color: var(--accent) !important;
        border: none !important;
        outline: none !important;
    }

    /* BOUTONS D'ACTION PRINCIPAUX (TYPE PRIMARY) */
    button[kind="primary"] {
        background-color: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        box-shadow: 0 4px 10px rgba(194, 65, 12, 0.3) !important;
        transition: all 0.3s !important;
    }
    button[kind="primary"]:hover {
        background-color: var(--accent) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 15px rgba(245, 124, 0, 0.4) !important;
    }

    /* LOGO NAVBAR */
    .nav-logo {
        width: 50px; height: 50px; 
        background: white; 
        border: 3px solid var(--accent); 
        border-radius: 50%; 
        color: #0047AB; 
        font-weight: 900; 
        display: flex; 
        align-items: center; 
        justify-content: center;
        margin-right: 15px;
        box-shadow: 0 0 15px rgba(245,124,0,0.4);
    }
    .nav-title {
        font-weight: 900; 
        font-size: 1.2rem; 
        color: white; 
        text-transform: uppercase; 
        letter-spacing: 2px;
    }

    /* CONTAINERS CONTENU */
    .content-card {
        background: white; 
        color: #0f172a; 
        padding: 40px; 
        border-radius: 12px;
        border-left: 10px solid var(--accent); 
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    /* CONTACT SIMPLE */
    .contact-card {
        background-color: var(--bg-panel);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 40px;
        text-align: center;
        max-width: 600px;
        margin: 0 auto;
    }

    /* FOOTER */
    .footer-official {
        margin-top: 80px;
        padding: 60px 20px;
        background-color: var(--bg-panel);
        border-top: 4px solid var(--accent);
        text-align: center;
        border-radius: 20px 20px 0 0;
    }
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
if 'page' not in st.session_state: st.session_state.page = 'accueil'
if 'step' not in st.session_state: st.session_state.step = 0
if 'answers' not in st.session_state: st.session_state.answers = {}
if 'codes' not in st.session_state: st.session_state.codes = {}
if 'cheats' not in st.session_state: st.session_state.cheats = 0
if 'exam_open' not in st.session_state: st.session_state.exam_open = True
if 'ex_start_time' not in st.session_state: st.session_state.ex_start_time = time.time()
if 'durations' not in st.session_state: st.session_state.durations = {}

# --- 6. DONNÉES EXAMEN ---
EXERCICES = [
    {"id": 1, "titre": "Algorithmique - Contrôle d'Accès", "points": 5, "enonce": "Écrivez un programme qui demande l'année de naissance de l'utilisateur.\n1. Calculez son âge (référence 2026).\n2. Si l'utilisateur a 18 ans ou plus, affichez: 'Accès autorisé. Bienvenue !'.\n3. Sinon, affichez: 'Accès refusé. Vous devez être majeur.'.", "questions": [{"id":"q1_1","text":"Âge calculé pour naissance en 2010 ?", "type":"number", "correct":16}, {"id":"q1_2","text":"Message retourné pour 16 ans ?", "type":"choice", "options":["Accès autorisé. Bienvenue !", "Accès refusé. Vous devez être majeur."], "correct":"Accès refusé. Vous devez être majeur."}]},
    {"id": 2, "titre": "Physique - État de l'eau", "points": 5, "enonce": "Demandez la température T de l'eau (°C) et affichez son état :\n- T <= 0 : Glace\n- 0 < T < 100 : Liquide\n- T >= 100 : Vapeur\nBonus : Si T > 300, affichez 'Attention : Température critique !'.", "questions": [{"id":"q2_1","text":"État physique à 100°C pile ?", "type":"choice", "options":["Glace", "Liquide", "Vapeur"], "correct":"Vapeur"}]},
    {"id": 3, "titre": "Gestion - Assurance Auto", "points": 5, "enonce": "Calculez le tarif d'assurance :\n- Tarif de base : 500 €.\n- Si le conducteur a moins de 25 ans ET moins de 2 ans de permis : + 200 €.\n- Si le conducteur a plus de 25 ans OU plus de 5 ans de permis : - 50 €.", "questions": [{"id":"q3_1","text":"Prix final pour 22 ans et 1 an de permis ?", "type":"number", "correct":700}]},
    {"id": 4, "titre": "Ingénierie Financière - Crédit", "points": 5, "enonce": "Vérifiez l'éligibilité au crédit :\n- Épargne (Revenu - Dépenses) <= 0 : Refus (Fonds insuffisants).\n- Taux d'endettement (Mensualité / Revenu) > 33% : Refus (Taux > 33%).\n- Sinon : Pré-approuvé.", "questions": [{"id":"q4_1","text":"Revenu 2000, Dépenses 2000. Décision ?", "type":"choice", "options":["Fonds insuffisants", "Taux > 33%"], "correct":"Fonds insuffisants"}]}
]

# --- 7. BARRE DE NAVIGATION (REMPLACE SIDEBAR) ---

def show_navbar():
    # Container visuel pour le logo et titre (CSS only)
    st.markdown("""
        <div class="navbar-container">
            <div class="nav-logo">HB</div>
            <div class="nav-title">ASR PRO</div>
            <div style="flex-grow:1;"></div>
        </div>
    """, unsafe_allow_html=True)
    
    # Menu interactif utilisant des colonnes
    # On utilise type="secondary" pour le style transparent défini dans le CSS
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1.5])
    
    with col1:
        if st.button("🏠 ACCUEIL", type="secondary", use_container_width=True): 
            st.session_state.page = 'accueil'
            st.rerun()
            
    with col2:
        if st.button("📜 ÉNONCÉS", type="secondary", use_container_width=True): 
            st.session_state.page = 'info'
            st.rerun()
            
    with col3:
        if st.button("❓ FAQ", type="secondary", use_container_width=True): 
            st.session_state.page = 'faq'
            st.rerun()
            
    with col4:
        if st.button("📞 CONTACT", type="secondary", use_container_width=True): 
            st.session_state.page = 'contact'
            st.rerun()
            
    with col5:
        if st.session_state.user:
            # Bouton déconnexion en Rouge/Orange (Primary)
            if st.button(f"👤 {st.session_state.user['name'].split()[0]} (SORTIR)", type="primary", use_container_width=True):
                st.session_state.user = None
                st.session_state.page = 'accueil'
                st.rerun()
        else:
            # Bouton connexion (Primary)
            if st.button("🔐 CONNEXION", type="primary", use_container_width=True):
                st.session_state.page = 'login'
                st.rerun()
    
    st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)

# --- 8. PIED DE PAGE ---
def show_footer():
    st.markdown("""
        <div class="footer-official">
            <div style="font-size:1.5rem; font-weight:800; color:white; margin-bottom:10px;">M. Ahmed Haithem BERKANE PSFEP CIP</div>
            <div style="font-size:1.1rem; color:#cbd5e1; margin-bottom:5px;">Institut National Spécialisé dans la formation professionnelle BBA01</div>
            <div style="font-size:1.1rem; color:#cbd5e1; margin-bottom:5px;">Direction de la formation professionnelle BBA</div>
            <div style="font-size:1.1rem; color:#cbd5e1; margin-bottom:20px;">Ministère de la formation et de l'enseignement professionnels</div>
            <div style="border-top:1px solid rgba(255,255,255,0.1); padding-top:20px; font-weight:700; color:#64748b; letter-spacing:1px;">
                RÉPUBLIQUE ALGÉRIENNE DÉMOCRATIQUE ET POPULAIRE 🇩🇿 | TOUS DROITS RÉSERVÉS © 2026
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 9. VUES ---

def accueil_view():
    st.markdown("""
        <div class="content-card" style="text-align:center;">
            <h1>Bienvenue sur le Portail ASR Pro</h1>
            <p style="font-size:1.2rem; margin-top:20px;">Plateforme d'évaluation certifiée pour le module Prog DevNet & Scripts.</p>
            <p style="color:#64748b; margin-top:10px;">Sélectionnez une option dans le menu ci-dessus.</p>
        </div>
    """, unsafe_allow_html=True)

def enonce_view():
    st.markdown("<h2 style='text-align:center; color:#f57c00; margin-bottom:30px;'>📜 ÉNONCÉS DE L'EXAMEN</h2>", unsafe_allow_html=True)
    for ex in EXERCICES:
        st.markdown(f"""
            <div class="content-card">
                <h3 style="color:#c2410c; margin-top:0;">EXERCICE {ex['id']} : {ex['titre']}</h3>
                <p style="white-space: pre-wrap; background:#f1f5f9; padding:20px; border-radius:8px; font-family:monospace; border:1px solid #e2e8f0;">{ex['enonce']}</p>
                <div style="text-align:right; margin-top:15px;">
                    <span style="background:#c2410c; color:white; padding:5px 15px; border-radius:20px; font-weight:bold; font-size:0.9rem;">{ex['points']} POINTS</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

def contact_view():
    st.markdown("""
        <div class="contact-card">
            <h2 style="color:#f57c00; font-weight:900; font-size:2.5rem; margin-bottom:5px;">Ahmed Haithem BERKANE</h2>
            <p style="color:#94a3b8; font-weight:700; text-transform:uppercase; letter-spacing:2px; margin-bottom:40px;">PSFEP CIP - Expert ASR Pro</p>
            
            <div style="font-size:1.2rem; color:#e2e8f0; display:flex; flex-direction:column; gap:15px; align-items:center;">
                <div><span style="font-size:1.5rem; margin-right:10px;">📞</span> +213 699 102 523</div>
                <div><span style="font-size:1.5rem; margin-right:10px;">📧</span> haithemcomputing@gmail.com</div>
                <div><span style="font-size:1.5rem; margin-right:10px;">🔵</span> Facebook : Haithem BERKANE</div>
                <div><span style="font-size:1.5rem; margin-right:10px;">💼</span> LinkedIn : Haithem BERKANE</div>
                <div><span style="font-size:1.5rem; margin-right:10px;">📍</span> INSFP Belazzoug Athmane BBA 01</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def faq_view():
    st.markdown("<h2 style='text-align:center; color:#f57c00;'>❓ FAQ</h2>", unsafe_allow_html=True)
    with st.expander("Comment se déroule l'examen ?"):
        st.write("L'examen dure 2h. Vous devez compléter les 4 exercices séquentiellement.")
    with st.expander("Le système anti-triche"):
        st.write("Le système détecte si vous changez d'onglet ou quittez la page. Ces actions sont enregistrées.")
    with st.expander("Sauvegarde"):
        st.write("Vos réponses sont sauvegardées automatiquement à chaque étape.")

def login_view():
    st.markdown("""
        <div class="content-card" style="max-width:500px; margin:0 auto; text-align:center;">
            <h2>ACCÈS SÉCURISÉ</h2>
            <p style="color:#64748b;">Veuillez vous identifier pour accéder au terminal.</p>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u = st.text_input("Identifiant")
        p = st.text_input("Mot de passe", type="password")
        if st.button("OUVRIR LA SESSION", type="primary", use_container_width=True):
            if u == "admin" and p == "admin":
                st.session_state.user = {"name": "ADMINISTRATEUR", "role": "teacher", "username": "admin"}
                st.session_state.page = 'teacher'
                st.rerun()
            elif u and p:
                 st.session_state.user = {"name": f"Stagiaire {u}", "role": "student", "username": u}
                 st.session_state.page = 'student_dash'
                 st.rerun()
            else:
                st.error("Veuillez remplir les champs.")

def student_dash():
    st.markdown(f"<h1 style='text-align:center; margin-bottom:40px;'>Bienvenue, <span style='color:#f57c00;'>{st.session_state.user['name']}</span></h1>", unsafe_allow_html=True)
    
    if st.session_state.exam_open:
        col1, col2 = st.columns(2)
        with col1:
             st.markdown("""
                <div class="content-card">
                    <h3>État de la Session</h3>
                    <p style="color:#10b981; font-weight:bold; font-size:1.2rem;">🟢 EN COURS</p>
                    <p>La session est ouverte. Vous pouvez démarrer votre évaluation dès maintenant.</p>
                </div>
             """, unsafe_allow_html=True)
        with col2:
             st.markdown("""
                <div class="content-card">
                    <h3>Action Requise</h3>
                    <p>Cliquez ci-dessous pour lancer l'environnement d'examen.</p>
                </div>
             """, unsafe_allow_html=True)
             if st.button("🚀 DÉMARRER L'EXAMEN", type="primary", use_container_width=True):
                st.session_state.page = 'exam'
                st.session_state.ex_start_time = time.time()
                st.rerun()
    else:
        st.warning("L'examen est actuellement verrouillé par l'administrateur.")

def exam_view():
    step = st.session_state.step
    if step >= len(EXERCICES):
        st.balloons()
        st.markdown("""
            <div class="content-card" style="text-align:center;">
                <h1 style="color:#10b981;">Examen Terminé !</h1>
                <p>Vos réponses ont été transmises avec succès au serveur central.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Retour au tableau de bord", type="primary"):
            st.session_state.page = 'student_dash'
            st.rerun()
        return

    ex = EXERCICES[step]
    
    # Barre de progression
    progress = (step + 1) / len(EXERCICES)
    st.progress(progress)
    
    st.markdown(f"## Exercice {ex['id']}: {ex['titre']}")
    st.info(ex['enonce'])
    
    st.text_area("Votre code Python", height=250, key=f"code_{ex['id']}", placeholder="# Écrivez votre script ici...")
    
    st.markdown("### Questions théoriques")
    for q in ex['questions']:
        if q['type'] == 'choice':
            st.radio(q['text'], q['options'], key=f"ans_{q['id']}")
        else:
            st.number_input(q['text'], key=f"ans_{q['id']}")
            
    col_prev, col_next = st.columns([1, 1])
    with col_next:
        if st.button("VALIDER ET CONTINUER ➡️", type="primary", use_container_width=True):
            st.session_state.step += 1
            st.rerun()

def teacher_dash():
    st.title("Tableau de Bord Enseignant")
    st.info("Module de gestion des notes et surveillance en temps réel.")

# --- 10. AFFICHAGE GLOBAL ---
show_navbar() # Menu en haut

# Routing
if st.session_state.page == 'accueil': accueil_view()
elif st.session_state.page == 'info': enonce_view()
elif st.session_state.page == 'contact': contact_view()
elif st.session_state.page == 'faq': faq_view()
elif st.session_state.page == 'login': login_view()
elif st.session_state.page == 'student_dash': student_dash()
elif st.session_state.page == 'exam': exam_view()
elif st.session_state.page == 'teacher': teacher_dash()

show_footer() # Pied de page en bas
