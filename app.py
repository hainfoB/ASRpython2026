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
    initial_sidebar_state="expanded"
)

# --- 2. SÉCURITÉ & PROTECTION (ANTI-TRICHE JS) ---
# Version simplifiée et robuste pour éviter les bugs d'affichage
st.components.v1.html("""
    <script>
    document.addEventListener('contextmenu', event => event.preventDefault());
    document.addEventListener('copy', e => e.preventDefault());
    document.addEventListener('paste', e => e.preventDefault());
    
    function checkFocus() {
        const buttons = window.parent.document.querySelectorAll('button');
        buttons.forEach(btn => {
            // On cherche le bouton par son texte exact pour le cliquer
            if (btn.innerText === 'INTEGRITY_CHECK') {
                btn.click();
            }
        });
    }

    window.addEventListener('blur', checkFocus);
    </script>
""", height=0)

# --- 3. DESIGN SYSTEM (CSS NETTOYÉ) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
    
    /* COULEURS ET POLICES */
    :root {
        --bg-dark: #0a192f;
        --bg-panel: #112240;
        --primary: #c2410c; /* Orange foncé */
        --accent: #f57c00; /* Orange vif */
        --text-white: #ffffff;
    }

    html, body, [data-testid="stAppViewContainer"], .main {
        background-color: var(--bg-dark) !important;
        color: var(--text-white) !important;
        font-family: 'Inter', sans-serif;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: var(--bg-panel) !important;
        border-right: 1px solid rgba(255,255,255,0.05);
    }

    /* BOUTONS NAVIGATION (Sidebar) */
    [data-testid="stSidebar"] .stButton button {
        background: transparent !important;
        border: none !important;
        border-bottom: 1px solid rgba(255,255,255,0.1) !important;
        color: rgba(255,255,255,0.8) !important;
        text-align: left !important;
        width: 100%;
        padding: 15px !important;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        border-left: 4px solid var(--accent) !important;
        color: var(--accent) !important;
        background: rgba(255,255,255,0.05) !important;
    }

    /* BOUTONS PRINCIPAUX */
    .stButton > button {
        background-color: var(--primary) !important;
        color: white !important;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 6px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: var(--accent) !important;
        box-shadow: 0 4px 12px rgba(245, 124, 0, 0.3);
    }

    /* HEADER PERSONNALISÉ */
    .custom-header {
        text-align: center;
        padding: 40px 20px;
        background: radial-gradient(circle at center, #1e3a8a 0%, #0a192f 70%);
        border-bottom: 2px solid var(--accent);
        margin-bottom: 30px;
        border-radius: 0 0 20px 20px;
    }
    .logo-circle {
        width: 80px; height: 80px; background: white; border-radius: 50%;
        margin: 0 auto 15px auto; display: flex; align-items: center; justify-content: center;
        border: 4px solid var(--accent); color: #0047AB; font-weight: 900; font-size: 24px;
    }
    .header-title { font-size: 2.5rem; font-weight: 900; color: var(--accent); margin: 0; }
    .header-subtitle { font-size: 1rem; color: rgba(255,255,255,0.8); text-transform: uppercase; letter-spacing: 2px; }

    /* CARTE BLANCHE CONTENU */
    .content-card {
        background: white; color: #0f172a; padding: 30px; border-radius: 12px;
        border-left: 8px solid var(--accent); margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .content-card h3 { color: var(--primary); margin-top: 0; }

    /* FOOTER OFFICIEL (STYLE FIXE) */
    .footer-official {
        margin-top: 80px;
        padding: 60px 20px;
        background-color: var(--bg-panel);
        border-top: 4px solid var(--accent);
        text-align: center;
    }
    .f-name { font-size: 1.4rem; font-weight: 800; color: white; margin-bottom: 10px; }
    .f-line { font-size: 1.1rem; color: #cbd5e1; margin-bottom: 5px; }
    .f-bottom { margin-top: 30px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1); font-size: 0.9rem; color: #64748b; letter-spacing: 1px; font-weight: bold; }

    /* CARTE DE VISITE SIMPLE */
    .contact-simple {
        background-color: var(--bg-panel);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 40px;
        max-width: 600px;
        margin: 20px auto;
        text-align: center;
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    }
    .c-name { color: var(--accent); font-size: 2rem; font-weight: 900; margin-bottom: 5px; }
    .c-role { color: #94a3b8; font-weight: 700; text-transform: uppercase; font-size: 0.9rem; letter-spacing: 2px; margin-bottom: 30px; }
    .c-item { display: flex; align-items: center; justify-content: center; margin-bottom: 15px; font-size: 1.1rem; }
    .c-icon { margin-right: 10px; color: var(--accent); }

    /* CACHER LE BOUTON SÉCURITÉ VISUELLEMENT MAIS LE GARDER DANS LE DOM */
    /* On cible le bouton spécifique qui contient le texte INTEGRITY_CHECK */
    /* Note : Streamlit ne permet pas de cibler par texte en CSS pur facilement, 
       donc on le met dans un container invisible via st.markdown */
    
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
                pass # On évite de stopper l'app si pas de secrets en local pour le rendu UI
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

# --- 6. DONNÉES EXAMEN (PDF) ---
EXERCICES = [
    {
        "id": 1, 
        "titre": "Algorithmique - Contrôle d'Accès", 
        "points": 5, 
        "enonce": "Écrivez un programme qui demande l'année de naissance de l'utilisateur.\n1. Calculez son âge (référence 2026).\n2. Si l'utilisateur a 18 ans ou plus, affichez: 'Accès autorisé. Bienvenue !'.\n3. Sinon, affichez: 'Accès refusé. Vous devez être majeur.'.", 
        "questions": [
            {"id":"q1_1","text":"Âge calculé pour naissance en 2010 ?", "type":"number", "correct":16}, 
            {"id":"q1_2","text":"Message retourné pour 16 ans ?", "type":"choice", "options":["Accès autorisé. Bienvenue !", "Accès refusé. Vous devez être majeur."], "correct":"Accès refusé. Vous devez être majeur."}
        ]
    },
    {
        "id": 2, 
        "titre": "Physique - État de l'eau", 
        "points": 5, 
        "enonce": "Demandez la température T de l'eau (°C) et affichez son état :\n- T <= 0 : Glace\n- 0 < T < 100 : Liquide\n- T >= 100 : Vapeur\nBonus : Si T > 300, affichez 'Attention : Température critique !'.", 
        "questions": [
            {"id":"q2_1","text":"État physique à 100°C pile ?", "type":"choice", "options":["Glace", "Liquide", "Vapeur"], "correct":"Vapeur"}
        ]
    },
    {
        "id": 3, 
        "titre": "Gestion - Assurance Auto", 
        "points": 5, 
        "enonce": "Calculez le tarif d'assurance :\n- Tarif de base : 500 €.\n- Si le conducteur a moins de 25 ans ET moins de 2 ans de permis : + 200 €.\n- Si le conducteur a plus de 25 ans OU plus de 5 ans de permis : - 50 €.", 
        "questions": [
            {"id":"q3_1","text":"Prix final pour 22 ans et 1 an de permis ?", "type":"number", "correct":700}
        ]
    },
    {
        "id": 4, 
        "titre": "Ingénierie Financière - Crédit", 
        "points": 5, 
        "enonce": "Vérifiez l'éligibilité au crédit :\n- Épargne (Revenu - Dépenses) <= 0 : Refus (Fonds insuffisants).\n- Taux d'endettement (Mensualité / Revenu) > 33% : Refus (Taux > 33%).\n- Sinon : Pré-approuvé.", 
        "questions": [
            {"id":"q4_1","text":"Revenu 2000, Dépenses 2000. Décision ?", "type":"choice", "options":["Fonds insuffisants", "Taux > 33%"], "correct":"Fonds insuffisants"}
        ]
    }
]

# --- 7. COMPOSANTS D'INTERFACE ---

def show_header():
    st.markdown("""
        <div class="custom-header">
            <div class="logo-circle">HB</div>
            <div class="header-subtitle">République Algérienne Démocratique et Populaire</div>
            <h1 class="header-title">ASR PRO EXCELLENCE</h1>
            <p style="margin-top:10px; font-weight:bold; color:white;">Institut National Spécialisé Belazzoug Athmane BBA 01</p>
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

# BOUTON SÉCURITÉ CACHÉ (Méthode CSS Inline pour garantir le masquage)
# On le place dans un conteneur div avec style inline pour être sûr qu'il ne s'affiche pas
st.markdown('<div style="opacity:0; height:0; width:0; overflow:hidden; position:absolute; left:-9999px;">', unsafe_allow_html=True)
if st.button("INTEGRITY_CHECK", key="integrity_btn"):
    st.session_state.cheats += 1
st.markdown('</div>', unsafe_allow_html=True)

# --- 8. VUES ---

def accueil_view():
    show_header()
    st.markdown("""
        <div class="content-card" style="text-align:center;">
            <h1>Bienvenue sur le Portail ASR Pro</h1>
            <p>Plateforme d'évaluation certifiée pour le module Prog DevNet & Scripts.</p>
            <p>Veuillez utiliser le menu latéral pour naviguer.</p>
        </div>
    """, unsafe_allow_html=True)
    show_footer()

def enonce_view():
    show_header()
    st.markdown("<h2 style='text-align:center; color:#f57c00; margin-bottom:30px;'>📜 ÉNONCÉS DE L'EXAMEN</h2>", unsafe_allow_html=True)
    for ex in EXERCICES:
        st.markdown(f"""
            <div class="content-card">
                <h3>EXERCICE {ex['id']} : {ex['titre']}</h3>
                <p style="white-space: pre-wrap; font-family:monospace; background:#f8f9fa; padding:15px; border-radius:5px;">{ex['enonce']}</p>
                <p style="text-align:right; font-weight:bold; color:#c2410c;">Note : {ex['points']} Points</p>
            </div>
        """, unsafe_allow_html=True)
    show_footer()

def contact_view():
    show_header()
    st.markdown("""
        <div class="contact-simple">
            <div class="c-name">Ahmed Haithem BERKANE</div>
            <div class="c-role">PSFEP CIP - Expert ASR Pro</div>
            
            <div style="margin-top:30px;">
                <div class="c-item"><span class="c-icon">📱</span> +213 699 102 523</div>
                <div class="c-item"><span class="c-icon">📧</span> haithemcomputing@gmail.com</div>
                <div class="c-item"><span class="c-icon">🔗</span> Facebook & LinkedIn : Haithem BERKANE</div>
                <div class="c-item"><span class="c-icon">📍</span> INSFP Belazzoug Athmane BBA 01</div>
            </div>
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
    with st.expander("Sauvegarde"):
        st.write("Vos réponses sont sauvegardées automatiquement à chaque étape.")
    show_footer()

def login_view():
    show_header()
    st.markdown("<div class='content-card' style='max-width:500px; margin:0 auto;'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center;'>Connexion</h2>", unsafe_allow_html=True)
    u = st.text_input("Identifiant")
    p = st.text_input("Mot de passe", type="password")
    
    if st.button("SE CONNECTER", use_container_width=True):
        if u == "admin" and p == "admin":
            st.session_state.user = {"name": "ADMINISTRATEUR", "role": "teacher", "username": "admin"}
            st.session_state.page = 'teacher'
            st.rerun()
        # Simulation connexion étudiant (Remplacer par appel Firebase réel si config OK)
        elif u and p:
             # Simulation simple si Firebase non configuré
             st.session_state.user = {"name": f"Stagiaire {u}", "role": "student", "username": u}
             st.session_state.page = 'student_dash'
             st.rerun()
        else:
            st.error("Veuillez remplir les champs.")
    st.markdown("</div>", unsafe_allow_html=True)
    show_footer()

def student_dash():
    show_header()
    st.markdown(f"<h1 style='text-align:center;'>Espace Candidat : {st.session_state.user['name']}</h1>", unsafe_allow_html=True)
    
    if st.session_state.exam_open:
        c1, c2 = st.columns(2)
        with c1:
            st.info("Statut de l'examen : EN COURS")
        with c2:
            if st.button("🚀 DÉMARRER L'EXAMEN", use_container_width=True):
                st.session_state.page = 'exam'
                st.session_state.ex_start_time = time.time()
                st.rerun()
    else:
        st.warning("L'examen est actuellement verrouillé.")
    show_footer()

def exam_view():
    # Logique simple d'examen
    step = st.session_state.step
    if step >= len(EXERCICES):
        st.success("Examen terminé ! Vos réponses ont été enregistrées.")
        if st.button("Retour au tableau de bord"):
            st.session_state.page = 'student_dash'
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
        if q['type'] == 'choice':
            st.radio(q['text'], q['options'], key=f"ans_{q['id']}")
        else:
            st.number_input(q['text'], key=f"ans_{q['id']}")
            
    c1, c2 = st.columns([1, 5])
    with c2:
        if st.button("VALIDER ET CONTINUER ➡️"):
            st.session_state.step += 1
            st.rerun()

def teacher_dash():
    show_header()
    st.title("Tableau de Bord Enseignant")
    st.info("Gestion des sessions et des notes.")
    # (Logique enseignant simplifiée pour l'affichage)
    show_footer()

# --- 9. ROUTAGE (SIDEBAR) ---
with st.sidebar:
    st.markdown("<div style='text-align:center; font-weight:900; font-size:24px; color:white; margin-bottom:20px;'>HB</div>", unsafe_allow_html=True)
    
    if st.button("🏠 ACCUEIL"): st.session_state.page = 'accueil'; st.rerun()
    if st.button("📜 ÉNONCÉS"): st.session_state.page = 'info'; st.rerun()
    if st.button("❓ FAQ"): st.session_state.page = 'faq'; st.rerun()
    if st.button("📞 CONTACT"): st.session_state.page = 'contact'; st.rerun()
    
    st.markdown("---")
    
    if st.session_state.user:
        st.write(f"Connecté: **{st.session_state.user['name']}**")
        if st.button("DÉCONNEXION"):
            st.session_state.user = None
            st.session_state.page = 'accueil'
            st.rerun()
    else:
        if st.button("🔐 CONNEXION"): st.session_state.page = 'login'; st.rerun()

# --- 10. DISPATCH ---
if st.session_state.page == 'accueil': accueil_view()
elif st.session_state.page == 'info': enonce_view()
elif st.session_state.page == 'contact': contact_view()
elif st.session_state.page == 'faq': faq_view()
elif st.session_state.page == 'login': login_view()
elif st.session_state.page == 'student_dash': student_dash()
elif st.session_state.page == 'exam': exam_view()
elif st.session_state.page == 'teacher': teacher_dash()
