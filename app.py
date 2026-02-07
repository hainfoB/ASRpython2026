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

# --- 2. SÉCURITÉ & PROTECTION JS ---
st.components.v1.html("""
    <script>
    document.addEventListener('contextmenu', event => event.preventDefault());
    document.addEventListener('copy', e => e.preventDefault());
    document.addEventListener('paste', e => e.preventDefault());
    
    function triggerCheat() {
        const buttons = window.parent.document.querySelectorAll('button');
        for (let btn of buttons) {
            if (btn.innerText.includes('INTEGRITY_TRIGGER')) {
                btn.click();
                break;
            }
        }
    }

    window.addEventListener('blur', function() { triggerCheat(); });
    </script>
""", height=0)

# --- 3. DESIGN SYSTEM "ÉLITE" ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
    :root {
        --midnight: #0a192f; --navy: #112240; --orange-dark: #c2410c;
        --orange-light: #f57c00; --white: #ffffff;
    }
    html, body, [data-testid="stAppViewContainer"], .main {
        background-color: var(--midnight) !important; color: var(--white) !important;
        font-family: 'Inter', sans-serif;
    }
    [data-testid="stSidebar"] { display: none; }
    .stButton > button, .stDownloadButton > button {
        background-color: var(--orange-dark) !important; color: white !important;
        border-radius: 8px !important; height: 50px !important; font-weight: 800 !important;
    }
    .white-card {
        background-color: var(--white) !important; padding: 30px !important;
        border-radius: 16px !important; border-left: 10px solid var(--orange-light) !important;
        color: var(--midnight) !important; margin-bottom: 20px;
    }
    .white-card * { color: var(--midnight) !important; }
    [data-testid="stMetric"] {
        background-color: var(--white) !important; border-radius: 16px !important;
        border-left: 10px solid var(--orange-light) !important; padding: 20px !important;
    }
    [data-testid="stMetricValue"] div { color: var(--orange-dark) !important; font-size: 3.5rem !important; font-weight: 900 !important; }
    [data-testid="stMetricLabel"] p { color: var(--midnight) !important; font-weight: 800 !important; text-transform: uppercase; }
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
    except: pass

db = firestore.client()
PROJET_ID = "examen-asr-prod"

# --- 5. SESSION STATE ---
if 'page' not in st.session_state: st.session_state.page = '🏠 Accueil'
if 'user' not in st.session_state: st.session_state.user = None
if 'cheats' not in st.session_state: st.session_state.cheats = 0
if 'step' not in st.session_state: st.session_state.step = 0
if 'answers' not in st.session_state: st.session_state.answers = {}
if 'codes' not in st.session_state: st.session_state.codes = {}

if st.button("INTEGRITY_TRIGGER", key="cheat_trigger"): st.session_state.cheats += 1

# --- 6. HELPERS & PDF ---
def get_col(name): return db.collection('artifacts').document(PROJET_ID).collection('public').document('data').collection(name)

def get_alg_time(ts):
    try:
        dt = datetime.datetime.fromtimestamp(ts) + datetime.timedelta(hours=1)
        return dt.strftime("%H:%M:%S")
    except: return "--:--"

class PV_PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 5, "REPUBLIQUE ALGERIENNE DEMOCRATIQUE ET POPULAIRE", 0, 1, 'C')
        self.cell(0, 5, "INSFP BELAZZOUG ATHMANE BBA 01", 0, 1, 'C')
        self.ln(10)
        self.set_fill_color(245, 124, 0); self.set_text_color(255, 255, 255)
        self.cell(0, 12, "PROCES VERBAL D'EXAMEN - ASR PRO", 1, 1, 'C', 1)
        self.set_text_color(0, 0, 0); self.ln(5)

def generate_pv(stats, df):
    pdf = PV_PDF(); pdf.add_page()
    pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, "STATISTIQUES DE SESSION", 0, 1)
    pdf.set_font("Arial", "", 11)
    pdf.cell(60, 10, f"Presents: {stats['present']}", 1); pdf.cell(60, 10, f"Moyenne: {stats['moyenne']}", 1, 1)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10); pdf.cell(80, 10, "Nom & Prenom", 1); pdf.cell(30, 10, "Note/20", 1); pdf.cell(40, 10, "Heure", 1); pdf.cell(40, 10, "Obs.", 1, 1)
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        pdf.cell(80, 10, str(row['Nom']), 1)
        pdf.cell(30, 10, str(row['Note']), 1)
        pdf.cell(40, 10, str(row['Heure']), 1)
        pdf.cell(40, 10, "RAS" if row['Alertes']==0 else f"Alerte({row['Alertes']})", 1, 1)
    return pdf.output(dest='S').encode('latin-1')

# --- 7. DONNÉES EXAMEN ---
EXERCICES = [
    {"id": 1, "titre": "Algorithmique", "corrects": {"q1_1": 16, "q1_2": "Accès refusé. Vous devez être majeur."}},
    {"id": 2, "titre": "Physique", "corrects": {"q2_1": "Vapeur"}},
    {"id": 3, "titre": "Gestion", "corrects": {"q3_1": 700}},
    {"id": 4, "titre": "Ingénierie", "corrects": {"q4_1": "Fonds insuffisants"}}
]

# --- 8. VUES ---
def audit_view(data):
    st.markdown(f"### 🔍 Audit : {data['name']}")
    for ex in EXERCICES:
        with st.expander(f"Exercice {ex['id']} - {ex['titre']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Réponses QCM**")
                ans = data.get('answers', {})
                for qid, correct in ex['corrects'].items():
                    u_ans = ans.get(qid, "N/A")
                    color = "green" if str(u_ans) == str(correct) else "red"
                    st.markdown(f"<span style='color:{color}'>• {qid}: {u_ans} (Attendu: {correct})</span>", unsafe_allow_html=True)
            with col2:
                st.markdown("**Code Source**")
                st.code(data.get('codes', {}).get(str(ex['id']), "Aucun code"), "python")

def teacher_dash():
    st.title("📊 Tableau de Bord Formateur")
    u_list = [u.to_dict() for u in get_col('users').where('role', '==', 'student').get()]
    r_docs = get_col('results').get()
    r_list = [{"id": r.id, **r.to_dict()} for r in r_docs]

    # Traitement des doublons : On garde la dernière copie par utilisateur
    df_raw = pd.DataFrame(r_list)
    if not df_raw.empty:
        df_raw = df_raw.sort_values('timestamp', ascending=False)
        df_unique = df_raw.drop_duplicates(subset=['username'], keep='first')
        
        # Stats
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Inscrits", len(u_list))
        c2.metric("Présents", len(df_unique))
        c3.metric("Moyenne", f"{df_unique['score'].mean():.2f}")
        c4.metric("Alerte Fraude", len(df_unique[df_unique['cheats'] > 0]))

        # PV & Liste
        st.divider()
        data_pv = []
        for _, r in df_unique.sort_values('timestamp', ascending=True).iterrows():
            data_pv.append({
                "ID": r['id'], "Nom": r['name'], "Note": r['score'], 
                "Heure": get_alg_time(r['timestamp']), "Alertes": r.get('cheats',0),
                "ts": r['timestamp']
            })
        df_final = pd.DataFrame(data_pv)
        
        col_list, col_pdf = st.columns([3,1])
        with col_pdf:
            stats_pv = {"present": len(df_unique), "moyenne": f"{df_unique['score'].mean():.2f}"}
            st.download_button("📄 Télécharger PV Officiel (PDF)", generate_pv(stats_pv, df_final), "PV_ASR_PRO.pdf")
        
        with col_list:
            sel = st.dataframe(df_final.drop(columns=["ID", "ts"]), use_container_width=True, on_select="rerun", selection_mode="single-row")
            if sel and sel.selection.rows:
                idx = sel.selection.rows[0]
                audit_view(next(r for r in r_list if r['id'] == df_final.iloc[idx]['ID']))
    else:
        st.info("Aucun résultat pour le moment.")

def login_view():
    st.markdown("<div style='max-width:400px; margin:auto; padding-top:50px;'>", unsafe_allow_html=True)
    st.header("🔐 Connexion")
    u = st.text_input("Identifiant")
    p = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        if u == "admin" and p == "admin":
            st.session_state.user = {"name":"Formateur", "role":"teacher"}
            st.rerun()
        res = get_col('users').where('username','==',u).where('password','==',p).get()
        if res:
            st.session_state.user = res[0].to_dict()
            st.rerun()
        else: st.error("Identifiants incorrects")
    st.markdown("</div>", unsafe_allow_html=True)

# --- 9. ROUTAGE ---
if st.session_state.user:
    st.sidebar.button("🚪 Déconnexion", on_click=lambda: st.session_state.update({"user":None}))
    if st.session_state.user['role'] == 'teacher':
        teacher_dash()
    else:
        st.title(f"Candidat : {st.session_state.user['name']}")
        # Logic étudiant ici...
else:
    login_view()
