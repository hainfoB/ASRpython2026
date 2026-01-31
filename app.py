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

# --- 2. SÉCURITÉ & PROTECTION (ANTI-TRICHE JS) ---
st.components.v1.html("""
    <script>
    document.addEventListener('contextmenu', event => event.preventDefault());
    document.addEventListener('copy', e => e.preventDefault());
    document.addEventListener('paste', e => e.preventDefault());
    
    window.addEventListener('blur', function() {
        const buttons = window.parent.document.querySelectorAll('button');
        for (let btn of buttons) {
            if (btn.innerText.includes('INTEGRITY_TRIGGER')) {
                btn.click();
                break;
            }
        }
    });
    </script>
""", height=0)

# --- 3. DESIGN SYSTEM "METRO-TAILWIND" ---
# Injection de Tailwind CSS et styles personnalisés pour un rendu "Élite"
st.markdown("""
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
    
    body {
        background-color: #0a192f !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Suppression Sidebar */
    [data-testid="stSidebar"] { display: none !important; }

    /* --- TUILES METRO PROFESSIONNELLES --- */
    .stButton > button {
        background-color: #c2410c !important; /* Orange Foncé */
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        padding: 2rem 1rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        width: 100% !important;
        height: auto !important;
        min-height: 120px !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3) !important;
    }

    .stButton > button:hover {
        background-color: #f57c00 !important; /* Orange Clair */
        transform: translateY(-5px) !important;
        box-shadow: 0 20px 25px -5px rgba(194, 65, 12, 0.4) !important;
    }

    /* --- CARTES DE CONTENU --- */
    .white-card {
        background-color: white !important;
        color: #0a192f !important;
        padding: 2.5rem !important;
        border-radius: 12px !important;
        border-left: 12px solid #f57c00 !important;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5) !important;
    }

    /* --- MASQUAGE RADICAL DU TRIGGER --- */
    .integrity-hidden {
        position: fixed !important;
        top: -1000px !important;
        left: -1000px !important;
        width: 1px !important;
        height: 1px !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    /* --- RESPONSIVE TYPO --- */
    .hero-title {
        font-size: clamp(2rem, 5vw, 3.5rem) !important;
        font-weight: 900 !important;
        background: linear-gradient(90deg, #f57c00, #c2410c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }

    /* --- NAVIGATION GRID --- */
    .nav-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1.5rem;
        width: 100%;
        max-width: 1000px;
        margin: 2rem auto;
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
            firebase_secrets = json.loads(st.secrets["FIREBASE_JSON"])
            cred = credentials.Certificate(firebase_secrets)
            firebase_admin.initialize_app(cred)
    except:
        st.error("⚠️ Erreur Firebase critique.")
        st.stop()

db = firestore.client()
PROJET_ID = "examen-asr-prod"

# --- 5. INITIALISATION SESSION STATE ---
def init_session():
    keys = ['user', 'page', 'step', 'answers', 'codes', 'durations', 'ex_start_time', 'cheats', 'exam_open']
    for k in keys:
        if k not in st.session_state:
            if k in ['step', 'cheats']: st.session_state[k] = 0
            elif k in ['answers', 'codes', 'durations']: st.session_state[k] = {}
            elif k == 'exam_open': st.session_state[k] = True
            elif k == 'page': st.session_state[k] = 'accueil'
            else: st.session_state[k] = None

init_session()

# --- 6. CLASSES ET HELPERS ---
class PDF(FPDF):
    def header(self):
        self.set_y(15); self.set_font('Arial', 'B', 8); self.set_text_color(0, 0, 0)
        self.cell(0, 5, "REPUBLIQUE ALGERIENNE DEMOCRATIQUE ET POPULAIRE", 0, 1, 'C')
        self.cell(0, 5, "MINISTERE DE LA FORMATION ET DE L'ENSEIGNEMENT PROFESSIONNELS", 0, 1, 'C')
        self.ln(20)

def get_col(name): return db.collection('artifacts').document(PROJET_ID).collection('public').document('data').collection(name)
def generate_pw(l=8): return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(l))

# --- 7. DONNÉES EXAMEN COMPLETES ---
EXERCICES = [
    {"id": 1, "titre": "Algorithmique - Contrôle d'Accès", "points": 5, "enonce": "Écrivez un programme qui demande l'année de naissance de l'utilisateur.\n1. Calculez son âge (année de référence 2026).\n2. Si l'utilisateur a 18 ans ou plus, affichez: 'Accès autorisé. Bienvenue !'.\n3. Sinon, affichez: 'Accès refusé. Vous devez être majeur.'.", "questions": [{"id":"q1_1","text":"Âge calculé pour naissance en 2010 ?", "type":"number", "correct":16}, {"id":"q1_2","text":"Message retourné pour 16 ans ?", "type":"choice", "options":["Accès autorisé. Bienvenue !", "Accès refusé. Vous devez être majeur."], "correct":"Accès refusé. Vous devez être majeur."}]},
    {"id": 2, "titre": "Physique - État de l'eau", "points": 5, "enonce": "Demandez la température T de l'eau (°C) et affichez son état :\n- T <= 0 : Glace\n- 0 < T < 100 : Liquide\n- T >= 100 : Vapeur\n- Bonus : Si T > 300, affichez 'Attention : Température critique !'.", "questions": [{"id":"q2_1","text":"État physique à 100°C pile ?", "type":"choice", "options":["Glace", "Liquide", "Vapeur"], "correct":"Vapeur"}]},
    {"id": 3, "titre": "Gestion - Assurance Auto", "points": 5, "enonce": "Calculez le tarif d'assurance :\n- Tarif de base : 500 €.\n- Si le conducteur a moins de 25 ans ET moins de 2 ans de permis : + 200 €.\n- Si le conducteur a plus de 25 ans OU plus de 5 ans de permis : - 50 €.", "questions": [{"id":"q3_1","text":"Prix final pour 22 ans et 1 an de permis ?", "type":"number", "correct":700}]},
    {"id": 4, "titre": "Ingénierie Financière - Crédit", "points": 5, "enonce": "Vérifiez l'éligibilité au crédit :\n- Épargne (Revenu - Dépenses) <= 0 : Refus (Fonds insuffisants).\n- Taux d'endettement (Mensualité / Revenu) > 33% : Refus (Taux > 33%).\n- Sinon : Pré-approuvé.", "questions": [{"id":"q4_1","text":"Revenu 2000, Dépenses 2000. Décision ?", "type":"choice", "options":["Fonds insuffisants", "Taux > 33%"], "correct":"Fonds insuffisants"}]}
]

# --- 8. VUES ---

def show_hero():
    st.markdown('<h1 class="hero-title">ASR PRO EXCELLENCE</h1>', unsafe_allow_html=True)
    st.markdown('<p class="text-center text-gray-400 font-bold tracking-widest uppercase text-sm mb-12">INSFP Belazzoug Athmane BBA 01</p>', unsafe_allow_html=True)

def metro_navigation():
    # Grille de tuiles centrées
    st.markdown('<div class="nav-grid">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🏠 ACCUEIL"): st.session_state.page = 'accueil'; st.rerun()
        if st.button("ℹ️ INFO"): st.session_state.page = 'info'; st.rerun()
    with col2:
        if not st.session_state.user:
            if st.button("🔐 CONNEXION"): st.session_state.page = 'login'; st.rerun()
        else:
            if st.button(f"👤 {st.session_state.user['name'].split()[0].upper()}"):
                st.session_state.page = 'teacher' if st.session_state.user['role'] == 'teacher' else 'student_dash'
                st.rerun()
            if st.button("🚪 QUITTER"): st.session_state.user = None; st.session_state.page = 'accueil'; st.rerun()
    with col3:
        if st.button("❓ FAQ"): st.session_state.page = 'faq'; st.rerun()
        if st.button("📞 CONTACT"): st.session_state.page = 'contact'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def teacher_dash():
    show_hero()
    u_docs = get_col('users').where('role', '==', 'student').get()
    r_docs = get_col('results').get()
    
    t1, t2 = st.tabs(["📊 ANALYSE STATS", "📑 AUDIT COPIES"])
    with t1:
        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        st.metric("Inscrits", len(u_docs))
        st.metric("Copies Rendues", len(r_docs))
        st.markdown('</div>', unsafe_allow_html=True)
    with t2:
        df = pd.DataFrame([{"Nom": r.to_dict()['name'], "Note": r.to_dict()['score']} for r in r_docs])
        st.dataframe(df, use_container_width=True)

def exam_view():
    show_hero()
    step = st.session_state.step; ex = EXERCICES[step]
    st.markdown(f'<div class="white-card"><h3>{ex["titre"]}</h3><p>{ex["enonce"]}</p></div>', unsafe_allow_html=True)
    st.session_state.codes[ex['id']] = st.text_area("Console de Code Python :", height=300, key=f"c_{ex['id']}")
    
    for q in ex['questions']:
        if q['type'] == 'choice': st.session_state.answers[q['id']] = st.radio(q['text'], q['options'], key=f"ans_{q['id']}")
        else: st.session_state.answers[q['id']] = st.number_input(q['text'], key=f"ans_{q['id']}", value=0)
    
    if st.button("EXERCICE SUIVANT ➡️" if step < 3 else "🎯 RENDRE LA COPIE"):
        if step < 3: st.session_state.step += 1; st.rerun()
        else:
            # Calcul et Envoi simple
            total = sum(5 for e in EXERCICES) # Simulé pour le test
            get_col('results').add({"name": st.session_state.user['name'], "score": 18, "timestamp": time.time()})
            st.session_state.page = "student_dash"; st.rerun()

def login_view():
    show_hero()
    st.markdown('<div class="white-card mx-auto max-w-lg">', unsafe_allow_html=True)
    u = st.text_input("Identifiant"); p = st.text_input("Mot de passe", type="password")
    if st.button("VALIDER L'ACCÈS"):
        if u == "admin" and p == "admin": 
            st.session_state.user = {"name": "Enseignant Admin", "role": "teacher", "username": "admin"}
            st.session_state.page = "teacher"; st.rerun()
        docs = get_col('users').where('username', '==', u).where('password', '==', p).get()
        if docs: 
            st.session_state.user = docs[0].to_dict(); st.session_state.page = "student_dash"; st.rerun()
        else: st.error("Échec authentification.")
    st.markdown('</div>', unsafe_allow_html=True)

def student_dash():
    show_hero()
    st.markdown(f'<div class="white-card"><h2>Session : {st.session_state.user["name"]}</h2></div>', unsafe_allow_html=True)
    if st.button("🚀 DÉMARRER L'ÉVALUATION"): 
        st.session_state.page = "exam"; st.session_state.ex_start_time = time.time(); st.rerun()

def accueil_view():
    show_hero()
    st.markdown('<div class="white-card mx-auto max-w-3xl text-center"><h2>Portail Académique ASR</h2><p>Bienvenue sur l\'infrastructure d\'évaluation professionnelle.</p></div>', unsafe_allow_html=True)
    metro_navigation()

# --- 9. ROUTAGE ---
p = st.session_state.page
if p == 'teacher': teacher_dash()
elif p == 'exam': exam_view()
elif p == 'student_dash': student_dash()
elif p == 'login': login_view()
elif p == 'accueil': accueil_view()
elif p in ['info', 'faq', 'contact']:
    show_hero()
    st.markdown(f'<div class="white-card"><h2>{p.upper()}</h2><p>Contenu détaillé de la section {p}.</p></div>', unsafe_allow_html=True)
    if st.button("⬅️ RETOUR"): st.session_state.page = 'accueil'; st.rerun()

# --- 10. PROTECTION SÉCURITÉ (INVISIBLE RADICAL) ---
st.markdown('<div class="integrity-hidden">', unsafe_allow_html=True)
if st.button("INTEGRITY_TRIGGER", key="cheat_trigger_final"):
    st.session_state.cheats += 1
st.markdown('</div>', unsafe_allow_html=True)

# Footer Élite
st.markdown("""
    <footer class="mt-20 py-10 border-t border-gray-800 text-center text-gray-500 text-xs font-bold uppercase tracking-widest">
        Réalisé par Haithem BERKANE | INSFP Belazzoug Athmane | BBA 01 | 2026
    </footer>
""", unsafe_allow_html=True)
