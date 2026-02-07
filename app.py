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
import base64
from fpdf import FPDF

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="ASR Pro - Excellence Pédagogique (LEGACY)",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SÉCURITÉ & PROTECTION (CORRECTIF ANTI-TRICHE & MASQUAGE) ---

# A. MASQUAGE CSS (Immédiat)
st.markdown("""
    <style>
    /* Masquer le bouton spécifique qui contient le texte INTEGRITY_TRIGGER */
    div[data-testid="stButton"]:has(button:contains("INTEGRITY_TRIGGER")) {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        position: absolute !important;
        left: -9999px !important;
    }
    </style>
""", unsafe_allow_html=True)

# B. SCRIPT DE PROTECTION JS (Persistant)
st.components.v1.html("""
    <script>
    document.addEventListener('contextmenu', event => event.preventDefault());
    document.addEventListener('copy', e => e.preventDefault());
    document.addEventListener('paste', e => e.preventDefault());
    
    function hideTriggerButton() {
        const buttons = window.parent.document.querySelectorAll('button');
        for (const btn of buttons) {
            if (btn.innerText.includes('INTEGRITY_TRIGGER')) {
                const container = btn.closest('div[data-testid="stButton"]');
                if (container) {
                    container.style.display = 'none';
                    container.style.visibility = 'hidden';
                    container.style.position = 'absolute';
                }
            }
        }
    }

    function triggerCheat() {
        const buttons = window.parent.document.querySelectorAll('button');
        for (const btn of buttons) {
            if (btn.innerText.includes('INTEGRITY_TRIGGER')) {
                btn.click();
                break;
            }
        }
    }

    setInterval(hideTriggerButton, 50);

    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            triggerCheat();
        }
    });

    window.addEventListener('blur', function() {
        triggerCheat();
    });
    </script>
""", height=0)

# --- 3. DESIGN SYSTEM "ÉLITE" ET UI/UX ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
    
    :root {
        --midnight: #0a192f;
        --navy: #112240;
        --orange-dark: #c2410c;
        --orange-light: #f57c00;
        --white: #ffffff;
        --hb-blue: #0047AB;
    }

    html, body, [data-testid="stAppViewContainer"], .main {
        background-color: var(--midnight) !important;
        color: var(--white) !important;
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stSidebar"] { display: none; }
    
    .stButton > button, [data-testid="stFormSubmitButton"] > button, .stDownloadButton > button {
        background-color: var(--orange-dark) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        height: 50px !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        width: 100% !important;
        font-size: 1.1rem !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover, .stDownloadButton > button:hover {
        background-color: var(--orange-light) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(245, 124, 0, 0.4) !important;
    }

    .hb-logo {
        width: 90px; height: 90px; background: white;
        border: 6px solid var(--orange-light); border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        color: var(--hb-blue); font-weight: 900; font-size: 2.5rem;
        box-shadow: 0 0 25px rgba(245, 124, 0, 0.6);
    }

    [data-testid="stWidgetLabel"] p, label {
        color: #ffffff !important;
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        margin-bottom: 10px !important;
    }
    
    .stTextInput input {
        color: #333 !important;
        font-weight: bold;
    }

    .white-card, .report-card {
        background-color: var(--white) !important;
        padding: 40px !important;
        border-radius: 16px !important;
        border-left: 10px solid var(--orange-light) !important;
        color: var(--midnight) !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3) !important;
        margin-bottom: 20px;
    }
    .white-card *, .report-card * { 
        color: var(--midnight) !important; 
    }
    .white-card h1, .white-card h2, .white-card h3 {
        color: var(--orange-dark) !important;
    }
    
    [data-testid="stMetric"] {
        background-color: var(--white) !important;
        padding: 30px 10px !important;
        border-radius: 16px !important;
        border-left: 10px solid var(--orange-light) !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3) !important;
        margin-bottom: 20px;
        text-align: center !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        height: 100% !important;
    }
    
    [data-testid="stMetricLabel"] {
        width: 100% !important;
        justify-content: center !important;
    }
    [data-testid="stMetricLabel"] p {
        color: var(--midnight) !important;
        font-size: 1.6rem !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }

    [data-testid="stMetricValue"] div {
        color: var(--orange-dark) !important;
        font-size: 5rem !important;
        font-weight: 900 !important;
        line-height: 1.1 !important;
        margin-top: 15px !important;
    }
    
    [data-testid="stFileUploaderDropzoneInstructions"], [data-testid="stFileUploaderDropzone"] div small {
        display: none !important;
    }
    
    [data-testid="stFileUploaderDropzone"] {
        border: 2px dashed var(--orange-dark) !important;
        background-color: rgba(255,255,255,0.05) !important;
        padding: 20px !important;
        min-height: auto !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    [data-testid="stFileUploaderDropzone"] button {
        background-color: var(--orange-dark) !important;
        color: white !important;
        border: none !important;
        font-weight: 800 !important;
        font-size: 1.1rem !important;
        padding: 10px 25px !important;
        border-radius: 8px !important;
        width: auto !important;
        margin: 0 auto !important;
        display: block !important;
    }
    [data-testid="stFileUploaderDropzone"] button:hover {
        background-color: var(--orange-light) !important;
    }

    p, li {
        font-size: 1.2rem !important;
        line-height: 1.6 !important;
    }

    .capacity-bright {
        background: linear-gradient(135deg, #fffbeb 0%, #fff7ed 100%) !important;
        border: 4px solid #fbbf24 !important;
        padding: 40px !important;
        border-radius: 20px !important;
        color: #92400e !important;
        font-size: 2rem !important; 
        font-weight: 900 !important;
        text-align: center;
    }

    .footer-wrapper {
        width: 100vw; position: relative; left: 50%; right: 50%;
        margin-left: -50vw; margin-right: -50vw;
        background-color: var(--navy); border-top: 8px solid var(--orange-light);
        margin-top: 80px; padding: 60px 0;
    }
    .footer-content { max-width: 1200px; margin: 0 auto; text-align: center; color: white; }

    .nav-fallback {
        background-color: var(--navy);
        padding: 15px;
        border-radius: 12px;
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 15px;
        margin-bottom: 40px;
        border-bottom: 4px solid var(--orange-light);
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
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
            except: pass 
    except Exception as e: pass

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
            elif k == 'page': st.session_state[k] = '🏠 Accueil'
            else: st.session_state[k] = None

init_session()

def check_exam_status():
    try:
        doc = db.collection('artifacts').document(PROJET_ID).collection('public').document('data').collection('settings').document('status').get()
        if doc.exists:
            st.session_state.exam_open = doc.to_dict().get('is_open', True)
    except: pass

check_exam_status()

# BOUTON SÉCURITÉ (CLIQUE PAR JS)
if st.button("INTEGRITY_TRIGGER", key="cheat_trigger"):
    st.session_state.cheats += 1

# --- 6. CLASSES ET HELPERS ---
def get_algeria_time_str(timestamp):
    """Convertit un timestamp en heure Algérie (UTC+1) de manière sécurisée"""
    try:
        if not timestamp: return "--:--"
        ts = float(timestamp)
        utc_dt = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)
        alg_dt = utc_dt + datetime.timedelta(hours=1)
        return alg_dt.strftime("%H:%M:%S")
    except:
        return "--:--"

def normalize_name(name):
    """Normalise un nom pour la comparaison"""
    return str(name).strip().lower()

class ReportPDF(FPDF):
    def header(self):
        # En-tête officiel
        self.set_font('Arial', 'B', 10)
        self.cell(0, 5, "REPUBLIQUE ALGERIENNE DEMOCRATIQUE ET POPULAIRE", 0, 1, 'C')
        self.cell(0, 5, "MINISTERE DE LA FORMATION ET DE L'ENSEIGNEMENT PROFESSIONNELS", 0, 1, 'C')
        self.set_font('Arial', 'B', 9)
        self.cell(0, 5, "INSFP BELAZZOUG ATHMANE BBA 01", 0, 1, 'C')
        self.ln(10)
        
        # Titre
        self.set_fill_color(245, 124, 0) # Orange Pro
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 12, "PROCES VERBAL D'EXAMEN - ASR PRO", 1, 1, 'C', 1)
        self.set_text_color(0, 0, 0)
        self.ln(5)
        
        # Date
        self.set_font('Arial', 'I', 10)
        now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
        self.cell(0, 10, f"Genere le : {now.strftime('%d/%m/%Y à %H:%M')}", 0, 1, 'R')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_final_report_pdf(stats, results_df):
    pdf = ReportPDF()
    pdf.add_page()
    
    # 1. Stats
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "1. STATISTIQUES DE LA SESSION", 0, 1)
    pdf.set_font("Arial", "", 11)
    pdf.cell(90, 10, f"Presents (Indiv.): {stats['present']}", 1)
    pdf.cell(90, 10, f"Moyenne de Section: {stats['moyenne']}/20", 1, 1)
    pdf.cell(90, 10, f"Meilleure Note: {stats['max']}/20", 1)
    pdf.cell(90, 10, f"Note Minimale: {stats['min']}/20", 1, 1)
    pdf.ln(10)

    # 2. Tableau
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "2. LISTE DETAILLEE (Copies uniques retenues)", 0, 1)
    
    # Header
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(70, 10, "Nom & Prenom", 1, 0, 'C', 1)
    pdf.cell(30, 10, "Note /20", 1, 0, 'C', 1)
    pdf.cell(40, 10, "Heure Remise", 1, 0, 'C', 1)
    pdf.cell(50, 10, "Observations", 1, 1, 'C', 1)
    
    pdf.set_font("Arial", "", 10)
    for index, row in results_df.iterrows():
        pdf.cell(70, 10, str(row['Nom']), 1)
        try:
            if float(row['Note']) < 10: pdf.set_text_color(200, 0, 0)
        except: pass
        pdf.cell(30, 10, str(row['Note']), 1, 0, 'C')
        pdf.set_text_color(0, 0, 0)
        pdf.cell(40, 10, str(row['Heure']), 1, 0, 'C')
        
        obs = "RAS"
        try:
            if int(row['Alertes']) > 0:
                obs = f"ALERTE ({int(row['Alertes'])})"
                pdf.set_text_color(255, 0, 0)
                pdf.set_font("Arial", "B", 10)
        except: pass
        pdf.cell(50, 10, obs, 1, 1, 'C')
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "", 10)

    return pdf.output(dest='S').encode('latin-1')

def get_col(name): return db.collection('artifacts').document(PROJET_ID).collection('public').document('data').collection(name)
def generate_pw(l=8): return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(l))

def generate_pdf_credentials(users_list):
    pdf = FPDF()
    pdf.add_page(); pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(245, 124, 0); pdf.set_text_color(255, 255, 255)
    pdf.cell(75, 12, "Nom & Prenom", 1, 0, 'C', 1); pdf.cell(45, 12, "Identifiant", 1, 0, 'C', 1)
    pdf.cell(35, 12, "Mot de Passe", 1, 0, 'C', 1); pdf.cell(35, 12, "Emargement", 1, 1, 'C', 1)
    pdf.set_font("Arial", '', 11); pdf.set_text_color(0, 0, 0)
    for u in users_list:
        pdf.cell(75, 12, u.get('name'), 1); pdf.cell(45, 12, u.get('username'), 1)
        pdf.cell(35, 12, u.get('password'), 1); pdf.cell(35, 12, "", 1, 1)
    return pdf.output(dest='S').encode('latin-1')

# --- 7. DONNÉES EXAMEN (HARDCODED) ---
EXERCICES = [
    {"id": 1, "titre": "Algorithmique - Contrôle d'Accès", "points": 5, "enonce": "Écrivez un programme qui demande l'année de naissance de l'utilisateur.\n1. Calculez son âge (référence 2026).\n2. Si l'utilisateur a 18 ans ou plus: 'Accès autorisé', sinon 'Accès refusé'.", "questions": [{"id":"q1_1","text":"Âge pour naissance en 2010 ?", "type":"number", "correct":16}, {"id":"q1_2","text":"Message pour 16 ans ?", "type":"choice", "options":["Accès autorisé. Bienvenue !", "Accès refusé. Vous devez être majeur."], "correct":"Accès refusé. Vous devez être majeur."}]},
    {"id": 2, "titre": "Physique - État de l'eau", "points": 5, "enonce": "Demandez la température T de l'eau (°C) :\n- T <= 0 : Glace\n- 0 < T < 100 : Liquide\n- T >= 100 : Vapeur", "questions": [{"id":"q2_1","text":"État à 100°C pile ?", "type":"choice", "options":["Glace", "Liquide", "Vapeur"], "correct":"Vapeur"}]},
    {"id": 3, "titre": "Gestion - Assurance Auto", "points": 5, "enonce": "Tarif base 500€.\n- Si < 25 ans ET < 2 ans permis: +200€.\n- Si > 25 ans OU > 5 ans permis: -50€.", "questions": [{"id":"q3_1","text":"Conducteur de 22 ans, 1 an permis. Prix final ?", "type":"number", "correct":700}]},
    {"id": 4, "titre": "Ingénierie Financière - Crédit", "points": 5, "enonce": "Vérifiez l'éligibilité :\n- Épargne <= 0 : Refus.\n- Taux endettement > 33% : Refus.\n- Sinon: Pré-approuvé.", "questions": [{"id":"q4_1","text":"Revenu 2000, Dépenses 2000. Décision ?", "type":"choice", "options":["Fonds insuffisants", "Taux > 33%"], "correct":"Fonds insuffisants"}]}
]

# --- 8. VUES ---

def show_header():
    st.markdown("""
        <div class="official-header" style="text-align:center;">
            <div class="hb-logo-container" style="display:flex; justify-content:center; margin-bottom:20px;">
                <div class="hb-logo">HB</div>
            </div>
            <h4 style="opacity:0.7; letter-spacing:2px; text-transform:uppercase;">République Algérienne Démocratique et Populaire</h4>
            <h1 style="color:#f57c00; font-size:2.8rem; margin:15px 0; font-weight:900;">Institut National Spécialisé Belazzoug Athmane BBA 01</h1>
            <p style="font-weight:700; color:white; margin-top:10px; letter-spacing:5px; font-size:1.5rem;">PLATEFORME D'EXAMEN ASR PRO</p>
        </div>
    """, unsafe_allow_html=True)

def show_footer():
    st.markdown("""
        <div class="footer-wrapper">
            <div class="footer-content">
                <div class="footer-hb" style="width:70px; height:70px; background:white; border:4px solid #f57c00; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; color:#0047AB; font-weight:900; font-size:1.8rem; margin-bottom:20px; box-shadow:0 4px 15px rgba(0,0,0,0.3);">HB</div>
                <h2 style="color:white !important; margin-bottom:15px; font-weight:900; letter-spacing:1px; font-size:1.8rem;">RÉALISÉ PAR HAITHEM BERKANE</h2>
                <div style="font-size:1.4rem; font-weight:700; opacity:0.95; margin-bottom:10px;">Institut National Spécialisé Belazzoug Athmane BBA 01</div>
                <p style="font-size:1.2rem; opacity:0.7; font-weight:400;">Ministère de la Formation et de l'Enseignement Professionnels 🇩🇿</p>
                <div style="height:4px; background:#f57c00; width:200px; margin:35px auto; border-radius:10px;"></div>
                <p style="font-size:1.2rem; opacity:0.7; font-weight:400;">République Algérienne Démocratique et Populaire 🇩🇿</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

def audit_results_detailed(data):
    st.markdown("### 🔍 Analyse Pédagogique des Résultats")
    for ex in EXERCICES:
        with st.expander(f"Exercice {ex['id']} : {ex['titre']}"):
            col_q, col_c = st.columns([1, 1.5])
            with col_q:
                st.markdown("#### ✅ Validation Théorique")
                for q in ex['questions']:
                    user_ans = data.get('answers', {}).get(q['id'], "Non répondu")
                    is_correct = str(user_ans) == str(q['correct'])
                    color = "#10b981" if is_correct else "#ef4444"
                    st.markdown(f"""
                        <div style="padding:15px; border-radius:8px; border-left:6px solid {color}; margin-bottom:15px; background:rgba(255,255,255,0.05);">
                            <small style="color:#ddd; font-size:1.1rem; font-weight:bold;">{q['text']}</small><br>
                            <span style="color:white; font-weight:900; font-size:1.4rem;">Saisi : {user_ans}</span><br>
                            <small style="color:#ddd; font-size:1.1rem;">Attendu : {q['correct']}</small>
                        </div>
                    """, unsafe_allow_html=True)
            with col_c:
                st.markdown("#### 💻 Script Python Implémenté")
                code = data.get('codes', {}).get(str(ex['id']), "")
                cpm = data.get('cpm_data', {}).get(str(ex['id']), 0)
                if cpm > 300: st.error(f"🚩 Alerte Plagiat / IA probable ({int(cpm)} CPM)")
                else: st.info(f"🟢 Saisie normale ({int(cpm)} CPM)")
                st.code(code, "python")

@st.cache_data(ttl=60)
def fetch_dashboard_data():
    u_docs = get_col('users').where('role', '==', 'student').get()
    r_docs = get_col('results').get()
    return [{"id": u.id, **u.to_dict()} for u in u_docs], [{"id": r.id, **r.to_dict()} for r in r_docs]

def teacher_dash():
    u_list, r_all_raw = fetch_dashboard_data()
    
    # 1. NETTOYAGE ET DÉDOUBLONNAGE (CONSERVER UNIQUEMENT LA DERNIÈRE COPIE PAR ÉTUDIANT)
    processed_results = {}
    for r in r_all_raw:
        # Nettoyage timestamp
        if 'timestamp' not in r or r['timestamp'] is None:
            ts = 0.0
        else:
            try: ts = float(r['timestamp'])
            except: ts = 0.0
        r['timestamp'] = ts
        
        # Logique de conservation : on garde la copie si elle est plus récente pour cet username
        uname = r.get('username', 'unknown')
        if uname not in processed_results or ts > processed_results[uname]['timestamp']:
            processed_results[uname] = r

    # Liste finale des résultats sans doublons
    r_list = list(processed_results.values())
    # Tri par ordre chronologique pour le PV
    r_list.sort(key=lambda x: x['timestamp'])

    if st.button("🔄 Actualiser les données"):
        fetch_dashboard_data.clear()
        st.rerun()

    t1, t2, t3, t4 = st.tabs(["📊 ANALYSE STATISTIQUE", "👥 GESTION SECTION", "📑 AUDIT DES COPIES", "📦 EXPORT / MIGRATION"])
    
    with t1:
        st.markdown("### 🔒 Contrôle Administratif")
        cl1, cl2 = st.columns([2, 1])
        cl1.info(f"État actuel : **{'OUVERT' if st.session_state.exam_open else 'FERMÉ'}**")
        if cl2.button("BASCULER ÉTAT SESSION"):
            ns = not st.session_state.exam_open
            try: db.collection('artifacts').document(PROJET_ID).collection('public').document('data').collection('settings').document('status').update({'is_open': ns})
            except: pass
            st.session_state.exam_open = ns; st.rerun()
            
        st.divider(); col_m = st.columns(4)
        col_m[0].metric("Inscrits", len(u_list))
        
        # Stats basées sur les copies uniques
        col_m[1].metric("Présents (Indiv.)", len(r_list))
        col_m[2].metric("Absents", max(0, len(u_list) - len(r_list)))
        col_m[3].metric("Moyenne", f"{pd.DataFrame(r_list)['score'].mean():.2f}" if r_list else "0.00")
        
        if r_list:
            df_s = pd.DataFrame(r_list); st.divider(); c_a = st.columns(3)
            with c_a[0]: st.metric("Note Max", f"{df_s['score'].max()} / 20")
            with c_a[1]: st.metric("Note Min", f"{df_s['score'].min()} / 20")
            df_br = pd.DataFrame([r['breakdown'] for r in r_list]); best_id = df_br.mean().idxmax()
            best_name = next(e['titre'] for e in EXERCICES if str(e['id']) == str(best_id))
            with c_a[2]: st.metric("Meilleur Axe", f"Ex {best_id}")
            st.markdown(f"""
                <div class="capacity-bright">
                    💡 ANALYSE DE CAPACITÉ MÉTIER<br>
                    <span style="font-size:1.6rem; opacity:0.8;">L'exercice <b>'{best_name}'</b> présente le meilleur taux de maîtrise.</span>
                </div>
            """, unsafe_allow_html=True)
            
    with t2:
        c_i1, c_i2 = st.columns(2)
        with c_i1:
            out_ex = io.BytesIO(); pd.DataFrame(columns=["Nom Complet"]).to_excel(out_ex, index=False)
            st.download_button("📂 MODÈLE EXCEL", out_ex.getvalue(), "modele.xlsx")
            
            up_f = st.file_uploader("Importer fichier Excel à charger", type=['xlsx'], label_visibility="visible")
            
            if up_f and st.button("LANCER IMPORTATION"):
                try:
                    df = pd.read_excel(up_f)
                    existing_names = {normalize_name(u['name']) for u in u_list}
                    count_added = 0
                    for name in df.iloc[:, 0].dropna():
                        clean_name = str(name).strip()
                        if normalize_name(clean_name) not in existing_names:
                            uid = clean_name.lower().replace(" ", ".") + str(random.randint(10,99))
                            get_col('users').add({"name": clean_name, "username": uid, "password": generate_pw(), "role": "student"})
                            existing_names.add(normalize_name(clean_name))
                            count_added += 1
                    fetch_dashboard_data.clear()
                    if count_added > 0: st.success(f"{count_added} étudiants ajoutés.")
                    else: st.warning("Aucun nouvel étudiant (doublons détectés).")
                    time.sleep(1); st.rerun()
                except Exception as e: st.error(f"Erreur: {e}")

            st.divider()
            if st.button("🧹 NETTOYER DOUBLONS (Inscriptions)"):
                with st.spinner("Nettoyage en cours..."):
                    all_users = get_col('users').stream()
                    seen_names = set(); deleted_count = 0
                    for doc in all_users:
                        data = doc.to_dict(); name_norm = normalize_name(data.get('name', ''))
                        if name_norm in seen_names: doc.reference.delete(); deleted_count += 1
                        else: seen_names.add(name_norm)
                    fetch_dashboard_data.clear()
                    st.success(f"{deleted_count} inscriptions en doublon supprimées.")
                    time.sleep(1); st.rerun()

        with c_i2:
            if u_list: st.download_button("📥 GÉNÉRER FICHES ACCÈS (PDF)", generate_pdf_credentials(u_list), "Acces_ASR.pdf")
            st.dataframe(pd.DataFrame(u_list)[['name', 'username', 'password']], use_container_width=True)

    with t3:
        if r_list:
            # Préparation des données uniques pour l'affichage et le PDF
            data_for_df = []
            for r in r_list:
                data_for_df.append({
                    "ID": r['id'],
                    "Nom": r['name'],
                    "Note": r['score'],
                    "Alertes": r.get('cheats', 0),
                    "Heure": get_algeria_time_str(r['timestamp']),
                    "timestamp": r['timestamp']
                })
            df_res = pd.DataFrame(data_for_df)

            # PDF OFFICIEL SANS RÉPÉTITIONS
            stats = {"present": len(r_list), "moyenne": f"{df_res['Note'].mean():.2f}", "max": df_res['Note'].max(), "min": df_res['Note'].min()}
            pdf_data = generate_final_report_pdf(stats, df_res)
            st.download_button("📄 TÉLÉCHARGER PV OFFICIEL SANS DOUBLONS (PDF)", pdf_data, "PV_Examen_Unique.pdf", mime="application/pdf")

            st.markdown("### Liste des copies (Derniers envois par étudiant)")
            sel = st.dataframe(df_res.drop(columns=["ID", "timestamp"]), use_container_width=True, on_select="rerun", selection_mode="single-row")
            if sel and sel.selection.rows:
                idx = sel.selection.rows[0]; doc_id = df_res.iloc[idx]['ID']
                data = next(r for r in r_list if r['id'] == doc_id)
                st.markdown(f'<div class="white-card"><h2>COPIE : {data["name"]}</h2><h1>{data["score"]} / 20</h1></div>', unsafe_allow_html=True)
                new_s = st.number_input("Ajuster Note :", 0.0, 20.0, float(data['score']), 0.25)
                if st.button("SAUVEGARDER"):
                    get_col('results').document(doc_id).update({"score": new_s}); st.success("Mis à jour !"); time.sleep(1); 
                    fetch_dashboard_data.clear(); st.rerun()
                st.divider(); audit_results_detailed(data)
                
    with t4:
        st.markdown("### 📦 MIGRATION ET BACKUP")
        if st.button("GÉNÉRER LE JSON COMPLET"):
            try:
                data_export = [doc.to_dict() for doc in get_col('results').stream()]
                json_str = json.dumps(data_export, indent=2, default=str)
                st.download_button("📥 TÉLÉCHARGER JSON", json_str, "backup_results.json", "application/json")
            except Exception as e: st.error(f"Erreur export: {e}")

def exam_view():
    if not st.session_state.exam_open: show_header(); st.error("🔒 Session verrouillée."); show_footer(); return
    show_header(); step = st.session_state.step; ex = EXERCICES[step]; st.progress((step + 1) / 4); st.info(ex['enonce'])
    st.session_state.codes[ex['id']] = st.text_area("Console Python (Logiciel 4/5) :", height=380, key=f"c_{ex['id']}")
    st.markdown("---"); st.markdown(f"#### **QUESTION :** {ex['questions'][0]['text']}")
    for q in ex['questions']:
        if q['type'] == 'choice': st.session_state.answers[q['id']] = st.radio(q['text'], q['options'], key=f"ans_{q['id']}", label_visibility="hidden")
        else: st.session_state.answers[q['id']] = st.number_input(q['text'], key=f"ans_{q['id']}", value=0)
    
    if st.button("SUIVANT ➡️" if step < 3 else "🎯 RENDRE LA COPIE"):
        st.session_state.durations[ex['id']] = round(time.time() - st.session_state.ex_start_time, 1)
        if step < 3: st.session_state.step += 1; st.session_state.ex_start_time = time.time(); st.rerun()
        else:
            total, br, cpm_d = 0, {}, {}
            for e in EXERCICES:
                pts_q = sum(1.0/len(e['questions']) for q in e['questions'] if str(st.session_state.answers.get(q['id'])) == str(q['correct']))
                code_val = st.session_state.codes.get(e['id'], "").strip(); pts_c = 4.0 if len(code_val) > 15 else 0
                dur = st.session_state.durations.get(e['id'], 1); cpm = (len(code_val) / (dur/60)) if dur > 0 else 0
                cpm_d[str(e['id'])] = cpm; ex_s = pts_q + pts_c
                if cpm > 300: ex_s = max(0, ex_s - 1.5)
                br[str(e['id'])] = round(ex_s, 2); total += ex_s
            fs = max(0, total - (st.session_state.cheats * 3))
            get_col('results').add({"username": str(st.session_state.user['username']), "name": str(st.session_state.user['name']), "score": round(fs, 1), "breakdown": br, "answers": st.session_state.answers, "durations": {str(k):v for k,v in st.session_state.durations.items()}, "codes": {str(k):v for k,v in st.session_state.codes.items()}, "cpm_data": cpm_d, "timestamp": time.time(), "cheats": st.session_state.cheats})
            st.session_state.page = "👤 Espace Candidat"; st.rerun()

def login_view():
    show_header()
    st.markdown('<div style="max-width:500px; margin:auto;">', unsafe_allow_html=True)
    st.markdown('<h2 style="text-align:center; margin-bottom:30px; font-weight:900; color:white;">Authentification Sécurisée</h2>', unsafe_allow_html=True)
    u = st.text_input("Identifiant ARS")
    p = st.text_input("Mot de passe", type="password")
    if st.button("ACCÉDER À LA SESSION"):
        if u == "admin" and p == "admin": st.session_state.user = {"name": "Administrateur", "role": "teacher", "username": "admin"}; st.session_state.page = "📊 Tableau de Bord"; st.rerun()
        try:
            docs = get_col('users').where('username', '==', u).where('password', '==', p).get()
            if docs: st.session_state.user = docs[0].to_dict(); st.session_state.page = "👤 Espace Candidat"; st.rerun()
            else: st.error("Identifiants incorrects.")
        except: st.error("Erreur de connexion. Vérifiez la configuration.")
    st.markdown('</div>', unsafe_allow_html=True); show_footer()

def student_dash():
    show_header(); u = st.session_state.user; st.markdown(f"<h1>Session : {u['name']}</h1>", unsafe_allow_html=True)
    res_docs = get_col('results').where('username', '==', u['username']).get()
    if res_docs: 
        res = res_docs[0].to_dict(); st.success(f"### NOTE OBTENUE : {res['score']} / 20")
        st.divider(); audit_results_detailed(res)
    elif st.session_state.exam_open:
        if st.button("🚀 DÉMARRER L'ÉPREUVE"): st.session_state.page = "exam"; st.session_state.ex_start_time = time.time(); st.rerun()
    else: st.warning("🔒 L'examen est verrouillé."); show_footer()

def accueil_view():
    show_header()
    st.markdown("""
        <div class="white-card">
            <h1 style="font-weight:900; margin-bottom:20px;">Portail Académique ASR</h1>
            <p style="font-size:1.4rem; line-height:1.6; color:#444;">
                Bienvenue sur l'infrastructure d'évaluation certifiée de l'Institut National Spécialisé Belazzoug Athmane.<br><br>
                Veuillez utiliser le menu de navigation ci-dessus pour vous identifier et accéder à votre terminal d'examen.
            </p>
        </div>
    """, unsafe_allow_html=True); show_footer()

def enonce_view():
    show_header()
    st.markdown('<div class="white-card"><h2>Énoncés & Modalités</h2><p>Le barème favorise l\'implémentation (4/5) et la théorie (1/5).</p></div>', unsafe_allow_html=True)
    for ex in EXERCICES:
        st.markdown(f"""
            <div class="white-card" style="margin-top:20px;">
                <h3 style="color:#c2410c;">Exercice {ex['id']} : {ex['titre']} ({ex['points']} pts)</h3>
                <pre style="background:#f1f5f9; padding:15px; border-radius:8px; font-family:monospace; color:#333; white-space:pre-wrap;">{ex['enonce']}</pre>
            </div>
        """, unsafe_allow_html=True)
    show_footer()

def faq_view():
    show_header()
    st.markdown("""
        <div class="white-card">
            <h2>FAQ - Foire Aux Questions</h2>
            <ul>
                <li><strong>Durée de l'examen :</strong> 2 heures.</li>
                <li><strong>Système anti-triche :</strong> La perte de focus (changement d'onglet) est détectée et sanctionnée (-3 points).</li>
                <li><strong>Sauvegarde :</strong> Automatique à chaque étape.</li>
                <li><strong>Problème technique :</strong> Signalez-le immédiatement au surveillant.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
    show_footer()

# --- 9. ROUTAGE AVEC NAVIGATION ---
pages = ["🏠 Accueil", "📜 Énoncés", "❓ FAQ"]
if st.session_state.user:
    if st.session_state.user.get('role') == 'teacher':
        pages.append("📊 Tableau de Bord")
    else:
        pages.append("👤 Espace Candidat")
    pages.append("🚪 Déconnexion")
else:
    pages.append("🔐 Connexion")

try:
    from streamlit_navigation_bar import st_navbar
    styles = {
        "nav": {"background-color": "#112240", "justify-content": "center"},
        "span": {"color": "white", "padding": "14px"},
        "active": {"background-color": "#f57c00", "color": "white", "font-weight": "bold", "padding": "14px"}
    }
    selected_page = st_navbar(pages, styles=styles, options={"show_menu": False, "show_sidebar": False})
except ImportError:
    st.markdown('<div class="nav-fallback">', unsafe_allow_html=True)
    cols = st.columns(len(pages))
    selected_page = st.session_state.page
    for i, p_name in enumerate(pages):
        if cols[i].button(p_name, key=f"nav_{p_name}", use_container_width=True):
            selected_page = p_name
    st.markdown('</div>', unsafe_allow_html=True)

if selected_page == "🚪 Déconnexion":
    st.session_state.user = None
    st.session_state.page = "🏠 Accueil"
    st.rerun()
elif selected_page != st.session_state.page:
    st.session_state.page = selected_page
    st.rerun()

p = st.session_state.page
if p == '📊 Tableau de Bord' and st.session_state.user and st.session_state.user['role'] == 'teacher': teacher_dash()
elif p == 'exam': exam_view()
elif p == '👤 Espace Candidat' and st.session_state.user: student_dash()
elif p == '🔐 Connexion': login_view()
elif p == '📜 Énoncés': enonce_view()
elif p == '❓ FAQ': faq_view()
else: accueil_view()
