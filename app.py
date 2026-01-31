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

# --- 3. DESIGN SYSTEM "METRO ELITE" (CENTRE & RESPONSIVE) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
    
    :root {
        --midnight: #0a192f;
        --navy: #112240;
        --orange-dark: #c2410c;
        --orange-light: #f57c00;
        --white: #ffffff;
    }

    /* Suppression Sidebar native */
    [data-testid="stSidebar"] { display: none !important; }

    html, body, [data-testid="stAppViewContainer"], .main {
        background-color: var(--midnight) !important;
        color: var(--white) !important;
        font-family: 'Inter', sans-serif;
    }

    /* --- CONTAINER CENTRAL METRO --- */
    .metro-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 100%;
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }

    /* --- TUILES METRO (DESIGN BOUTONS NAVIGATION) --- */
    .stButton > button {
        width: 100% !important;
        aspect-ratio: 1 / 1; /* Tuiles carrées sur tablette/desktop */
        background-color: var(--navy) !important;
        color: var(--white) !important;
        border: 2px solid rgba(255,255,255,0.05) !important;
        border-radius: 4px !important;
        font-weight: 900 !important;
        font-size: 1.2rem !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
        margin-bottom: 15px !important;
    }

    @media (max-width: 768px) {
        .stButton > button {
            aspect-ratio: auto !important;
            height: 100px !important;
            font-size: 1rem !important;
        }
    }

    .stButton > button:hover {
        background-color: var(--orange-dark) !important;
        border-color: var(--orange-light) !important;
        transform: scale(1.03) !important;
        box-shadow: 0 10px 30px rgba(194, 65, 12, 0.4) !important;
    }

    /* --- BOUTON CONNEXION / ACTION SPECIALE --- */
    .login-tile button {
        background-color: var(--orange-dark) !important;
        border-color: var(--orange-light) !important;
    }

    /* BOUTONS INTERNES AU CONTENU (EXAMEN) */
    .main-action button {
        aspect-ratio: auto !important;
        height: 65px !important;
        background-color: var(--orange-dark) !important;
        border-radius: 8px !important;
        margin-top: 20px !important;
    }

    /* --- LOGO ET TYPOGRAPHIE --- */
    .hb-logo {
        width: 100px; height: 100px; background: white; border: 6px solid var(--orange-light);
        border-radius: 50%; display: flex; align-items: center; justify-content: center;
        color: #0047AB; font-weight: 900; font-size: 2.8rem; box-shadow: 0 0 30px rgba(245, 124, 0, 0.6);
        margin: 0 auto 20px auto;
    }

    .white-card, [data-testid="stMetric"], .report-card {
        background-color: var(--white) !important;
        padding: 40px !important;
        border-radius: 15px !important;
        border-left: 15px solid var(--orange-light) !important;
        color: var(--midnight) !important;
        box-shadow: 0 15px 40px rgba(0,0,0,0.5) !important;
    }
    .white-card *, .report-card * { color: var(--midnight) !important; }

    h1, h4, [data-testid="stWidgetLabel"] p {
        color: var(--orange-light) !important;
        font-weight: 900 !important;
        text-align: center;
    }
    
    .stMarkdown p, .stRadio label, .stRadio div p {
        font-size: 1.4rem !important; 
        font-weight: 700 !important;
    }

    /* FOOTER */
    .footer-wrapper {
        width: 100vw; position: relative; left: 50%; right: 50%; margin-left: -50vw; margin-right: -50vw;
        background-color: var(--navy); border-top: 8px solid var(--orange-light); margin-top: 100px; padding: 60px 0;
    }

    /* MASQUAGE ABSOLU DU TRIGGER SÉCURITÉ */
    .hidden-zone {
        position: fixed !important;
        top: -2000px !important;
        left: -2000px !important;
        width: 1px !important;
        height: 1px !important;
        opacity: 0 !important;
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
    except Exception as e:
        st.error(f"❌ Erreur Firebase.")
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

def check_exam_status():
    doc = db.collection('artifacts').document(PROJET_ID).collection('public').document('data').collection('settings').document('status').get()
    if doc.exists:
        st.session_state.exam_open = doc.to_dict().get('is_open', True)

check_exam_status()

# --- 6. CLASSES ET HELPERS ---
class PDF(FPDF):
    def header(self):
        self.set_fill_color(0, 102, 51); self.rect(0, 0, 105, 10, 'F')
        self.set_fill_color(255, 255, 255); self.rect(105, 0, 105, 10, 'F')
        self.set_fill_color(204, 0, 0); self.ellipse(103, 3, 4, 4, 'F')
        self.set_y(15); self.set_font('Arial', 'B', 8); self.set_text_color(0, 0, 0)
        self.cell(0, 5, "REPUBLIQUE ALGERIENNE DEMOCRATIQUE ET POPULAIRE", 0, 1, 'C')
        self.cell(0, 5, "MINISTERE DE LA FORMATION ET DE L'ENSEIGNEMENT PROFESSIONNELS", 0, 1, 'C')
        self.set_font('Arial', 'B', 7)
        self.cell(0, 5, "Institut National Spécialisé de la Formation Professionnelle Belazzoug Athmane BBA 01", 0, 1, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-20); self.set_font('Arial', 'B', 7); self.set_text_color(150, 150, 150)
        self.cell(0, 10, "RÉALISÉ PAR HAITHEM BERKANE | INSFP Belazzoug Athmane BBA 01", 0, 0, 'C')

def get_col(name): return db.collection('artifacts').document(PROJET_ID).collection('public').document('data').collection(name)
def generate_pw(l=8): return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(l))

def generate_pdf_credentials(users_list):
    pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(245, 124, 0); pdf.set_text_color(255, 255, 255)
    pdf.cell(75, 12, "Nom & Prenom", 1, 0, 'C', 1); pdf.cell(45, 12, "Identifiant", 1, 0, 'C', 1)
    pdf.cell(35, 12, "Mot de Passe", 1, 0, 'C', 1); pdf.cell(35, 12, "Emargement", 1, 1, 'C', 1)
    pdf.set_font("Arial", '', 11); pdf.set_text_color(0, 0, 0)
    for u in users_list:
        pdf.cell(75, 12, u.get('name'), 1); pdf.cell(45, 12, u.get('username'), 1)
        pdf.cell(35, 12, u.get('password'), 1); pdf.cell(35, 12, "", 1, 1)
    return pdf.output(dest='S').encode('latin-1')

# --- 7. DONNÉES EXAMEN COMPLETES ---
EXERCICES = [
    {"id": 1, "titre": "Algorithmique - Contrôle d'Accès", "points": 5, "enonce": "Écrivez un programme qui demande l'année de naissance de l'utilisateur.\n1. Calculez son âge (année de référence 2026).\n2. Si l'utilisateur a 18 ans ou plus, affichez: 'Accès autorisé. Bienvenue !'.\n3. Sinon, affichez: 'Accès refusé. Vous devez être majeur.'.", "questions": [{"id":"q1_1","text":"Âge calculé pour naissance en 2010 ?", "type":"number", "correct":16}, {"id":"q1_2","text":"Message retourné pour 16 ans ?", "type":"choice", "options":["Accès autorisé. Bienvenue !", "Accès refusé. Vous devez être majeur."], "correct":"Accès refusé. Vous devez être majeur."}]},
    {"id": 2, "titre": "Physique - État de l'eau", "points": 5, "enonce": "Demandez la température T de l'eau (°C) et affichez son état :\n- T <= 0 : Glace\n- 0 < T < 100 : Liquide\n- T >= 100 : Vapeur\n- Bonus : Si T > 300, affichez 'Attention : Température critique !'.", "questions": [{"id":"q2_1","text":"État physique à 100°C pile ?", "type":"choice", "options":["Glace", "Liquide", "Vapeur"], "correct":"Vapeur"}]},
    {"id": 3, "titre": "Gestion - Assurance Auto", "points": 5, "enonce": "Calculez le tarif d'assurance :\n- Tarif de base : 500 €.\n- Si le conducteur a moins de 25 ans ET moins de 2 ans de permis : + 200 €.\n- Si le conducteur a plus de 25 ans OU plus de 5 ans de permis : - 50 €.", "questions": [{"id":"q3_1","text":"Prix final pour 22 ans et 1 an de permis ?", "type":"number", "correct":700}]},
    {"id": 4, "titre": "Ingénierie Financière - Crédit", "points": 5, "enonce": "Vérifiez l'éligibilité au crédit :\n- Épargne (Revenu - Dépenses) <= 0 : Refus (Fonds insuffisants).\n- Taux d'endettement (Mensualité / Revenu) > 33% : Refus (Taux > 33%).\n- Sinon : Pré-approuvé.", "questions": [{"id":"q4_1","text":"Revenu 2000, Dépenses 2000. Décision ?", "type":"choice", "options":["Fonds insuffisants", "Taux > 33%"], "correct":"Fonds insuffisants"}]}
]

# --- 8. VUES ---

def metro_nav():
    # NAVIGATION STYLE TABLETTE METRO AU MILIEU
    st.markdown('<div class="metro-container">', unsafe_allow_html=True)
    cols = st.columns([1, 1, 1])
    
    with cols[0]:
        if st.button("🏠\nACCUEIL"): st.session_state.page = 'accueil'; st.rerun()
        if st.button("ℹ️\nINFO"): st.session_state.page = 'info'; st.rerun()
    with cols[1]:
        if not st.session_state.user:
            st.markdown('<div class="login-tile">', unsafe_allow_html=True)
            if st.button("🔐\nSE CONNECTER"): st.session_state.page = 'login'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="login-tile">', unsafe_allow_html=True)
            if st.button(f"👤\n{st.session_state.user['name'].split()[0]}"): 
                if st.session_state.user['role'] == 'teacher': st.session_state.page = 'teacher'
                else: st.session_state.page = 'student_dash'
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("🚪\nQUITTER"): st.session_state.user = None; st.session_state.page = 'accueil'; st.rerun()
    with cols[2]:
        if st.button("❓\nFAQ"): st.session_state.page = 'faq'; st.rerun()
        if st.button("📞\nCONTACT"): st.session_state.page = 'contact'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def show_header_metro():
    st.markdown('<div class="hb-logo">HB</div>', unsafe_allow_html=True)
    st.markdown("""
        <h1>ASR PRO - EXCELLENCE</h1>
        <p style="text-align:center; opacity:0.6; font-size:1rem; letter-spacing:3px; text-transform:uppercase;">INSFP Belazzoug Athmane BBA 01</p>
        <hr style="border:1px solid rgba(255,255,255,0.05); margin:30px 0;">
    """, unsafe_allow_html=True)

def show_footer():
    st.markdown("""
        <div class="footer-wrapper">
            <div style="text-align:center; color:white;">
                <h3 style="font-weight:900;">HAITHEM BERKANE</h3>
                <p style="opacity:0.7;">Institut National Spécialisé de la Formation Professionnelle | 2026</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

# VUES CONTENU
def teacher_dash():
    show_header_metro()
    u_docs = get_col('users').where('role', '==', 'student').get()
    r_docs = get_col('results').get()
    u_list = [u.to_dict() for u in u_docs]; r_list = [r.to_dict() for r in r_docs]
    
    t1, t2, t3 = st.tabs(["📊 STATS", "👥 USERS", "📑 AUDIT"])
    with t1:
        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        cl1, cl2 = st.columns([2, 1])
        cl1.info(f"Session : **{'OUVERT' if st.session_state.exam_open else 'FERMÉ'}**")
        if cl2.button("BASCULER"):
            ns = not st.session_state.exam_open
            db.collection('artifacts').document(PROJET_ID).collection('public').document('data').collection('settings').document('status').update({'is_open': ns})
            st.session_state.exam_open = ns; st.rerun()
        st.divider(); col_m = st.columns(3)
        col_m[0].metric("Inscrits", len(u_list)); col_m[1].metric("Rendus", len(r_list))
        col_m[2].metric("Moyenne", f"{pd.DataFrame(r_list)['score'].mean():.2f}" if r_list else "0.00")
        st.markdown('</div>', unsafe_allow_html=True)
    with t3:
        if r_list:
            df_res = pd.DataFrame([{"Nom": r.to_dict()['name'], "Note": r.to_dict()['score']} for r in r_docs])
            st.dataframe(df_res, use_container_width=True)
    show_footer()

def exam_view():
    if not st.session_state.exam_open: show_header_metro(); st.error("🔒 Session verrouillée."); return
    show_header_metro(); step = st.session_state.step; ex = EXERCICES[step]
    st.progress((step + 1) / 4)
    st.markdown(f'<div class="white-card"><h4>{ex["titre"]}</h4><p>{ex["enonce"]}</p></div>', unsafe_allow_html=True)
    st.session_state.codes[ex['id']] = st.text_area("Console Python :", height=300, key=f"c_{ex['id']}")
    
    for q in ex['questions']:
        if q['type'] == 'choice': st.session_state.answers[q['id']] = st.radio(q['text'], q['options'], key=f"ans_{q['id']}")
        else: st.session_state.answers[q['id']] = st.number_input(q['text'], key=f"ans_{q['id']}", value=0)
    
    st.markdown('<div class="main-action">', unsafe_allow_html=True)
    if st.button("SUIVANT ➡️" if step < 3 else "🎯 TERMINER"):
        st.session_state.durations[ex['id']] = round(time.time() - st.session_state.ex_start_time, 1)
        if step < 3: st.session_state.step += 1; st.session_state.ex_start_time = time.time(); st.rerun()
        else:
            total = 0
            for e in EXERCICES:
                pts_q = sum(1.0/len(e['questions']) for q in e['questions'] if str(st.session_state.answers.get(q['id'])) == str(q['correct']))
                code_val = st.session_state.codes.get(e['id'], "").strip(); pts_c = 4.0 if len(code_val) > 15 else 0
                total += (pts_q + pts_c)
            get_col('results').add({"username": st.session_state.user['username'], "name": st.session_state.user['name'], "score": round(total, 1), "timestamp": time.time()})
            st.session_state.page = "student_dash"; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def login_view():
    show_header_metro()
    st.markdown('<div class="white-card" style="max-width:500px; margin:auto;">', unsafe_allow_html=True)
    u = st.text_input("Identifiant ARS"); p = st.text_input("Mot de passe", type="password")
    st.markdown('<div class="main-action">', unsafe_allow_html=True)
    if st.button("VALIDER L'ACCÈS"):
        if u == "admin" and p == "admin": 
            st.session_state.user = {"name": "Enseignant Admin", "role": "teacher", "username": "admin"}
            st.session_state.page = "teacher"; st.rerun()
        docs = get_col('users').where('username', '==', u).where('password', '==', p).get()
        if docs: 
            st.session_state.user = docs[0].to_dict()
            st.session_state.page = "student_dash"; st.rerun()
        else: st.error("Identifiants incorrects.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True); show_footer()

def student_dash():
    show_header_metro()
    u = st.session_state.user
    res_docs = get_col('results').where('username', '==', u['username']).get()
    if res_docs: 
        res = res_docs[0].to_dict(); st.success(f"### NOTE OBTENUE : {res['score']} / 20")
    elif st.session_state.exam_open:
        st.markdown('<div class="main-action">', unsafe_allow_html=True)
        if st.button("🚀 DÉMARRER L'ÉVALUATION"): 
            st.session_state.page = "exam"; st.session_state.ex_start_time = time.time(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else: st.warning("🔒 Session verrouillée."); show_footer()

def accueil_view():
    show_header_metro()
    st.markdown("""
        <div class="white-card">
            <h2 style="text-align:center; font-weight:900;">Portail Académique ASR</h2>
            <p style="text-align:center;">Bienvenue sur l'infrastructure d'évaluation de l'INSFP BBA 01.</p>
        </div>
    """, unsafe_allow_html=True)
    metro_nav()
    show_footer()

# --- 9. ROUTAGE ---
p = st.session_state.page
if p == 'teacher': teacher_dash()
elif p == 'exam': exam_view()
elif p == 'student_dash': student_dash()
elif p == 'login': login_view()
elif p == 'accueil': accueil_view()
elif p in ['info', 'faq', 'contact']:
    show_header_metro()
    st.markdown('<div class="white-card">', unsafe_allow_html=True)
    if p == 'info': st.markdown("<h2>Infos</h2><p>Examen de 60 min. 1pt théorie, 4pts code.</p>")
    if p == 'faq': st.markdown("<h2>FAQ</h2><p>Le système détecte chaque sortie d'onglet.</p>")
    if p == 'contact': st.markdown("<h2>Contact</h2><p>📧 haithemcomputing@gmail.com</p>")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-action">', unsafe_allow_html=True)
    if st.button("⬅️ RETOUR"): st.session_state.page = 'accueil'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    show_footer()

# --- 10. SÉCURITÉ INVISIBLE ---
st.markdown('<div class="hidden-zone">', unsafe_allow_html=True)
if st.button("INTEGRITY_TRIGGER", key="cheat_trigger_final"):
    st.session_state.cheats += 1
st.markdown('</div>', unsafe_allow_html=True)
