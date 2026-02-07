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
    page_title="ASR Pro - Excellence Pédagogique (LEGACY + RATTRAPAGE)",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SÉCURITÉ & PROTECTION ---
st.markdown("""
    <style>
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
        if (document.hidden) { triggerCheat(); }
    });

    window.addEventListener('blur', function() { triggerCheat(); });
    </script>
""", height=0)

# --- 3. DESIGN SYSTEM "ÉLITE" ---
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
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        margin-bottom: 10px !important;
    }
    
    .stTextInput input {
        color: #333 !important;
        font-weight: bold;
    }

    .white-card {
        background-color: var(--white) !important;
        padding: 40px !important;
        border-radius: 16px !important;
        border-left: 10px solid var(--orange-light) !important;
        color: var(--midnight) !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3) !important;
        margin-bottom: 20px;
    }
    .white-card *, .white-card h1, .white-card h2, .white-card h3 { color: var(--midnight) !important; }
    
    [data-testid="stMetric"] {
        background-color: var(--white) !important;
        padding: 25px 10px !important;
        border-radius: 16px !important;
        border-left: 10px solid var(--orange-light) !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3) !important;
        margin-bottom: 20px;
        text-align: center !important;
    }
    
    [data-testid="stMetricLabel"] p {
        color: var(--midnight) !important;
        font-size: 1.1rem !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
    }

    [data-testid="stMetricValue"] div {
        color: var(--orange-dark) !important;
        font-size: 2.8rem !important;
        font-weight: 900 !important;
    }
    
    .capacity-bright {
        background: linear-gradient(135deg, #fffbeb 0%, #fff7ed 100%) !important;
        border: 4px solid #fbbf24 !important;
        padding: 40px !important;
        border-radius: 20px !important;
        color: #92400e !important;
        font-size: 1.5rem !important; 
        font-weight: 900 !important;
        text-align: center;
    }

    .footer-wrapper {
        width: 100%; background-color: var(--navy); border-top: 8px solid var(--orange-light);
        margin-top: 80px; padding: 60px 0; text-align: center;
    }
    
    .nav-fallback {
        background-color: var(--navy); padding: 15px; border-radius: 12px;
        display: flex; justify-content: center; gap: 15px; margin-bottom: 40px;
        border-bottom: 4px solid var(--orange-light);
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. INITIALISATION FIREBASE ---
db = None
PROJET_ID = "examen-asr-prod"

if not firebase_admin._apps:
    try:
        if os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
        elif "FIREBASE_JSON" in st.secrets:
            cred = credentials.Certificate(json.loads(st.secrets["FIREBASE_JSON"]))
            firebase_admin.initialize_app(cred)
    except Exception: pass
try: db = firestore.client()
except: pass

# --- 5. INITIALISATION SESSION STATE ---
def init_session():
    keys = ['user', 'page', 'step', 'answers', 'codes', 'durations', 'ex_start_time', 'cheats', 
            'exam_open_normal', 'exam_open_rattrapage', 'current_exam_mode', 'consult_data']
    for k in keys:
        if k not in st.session_state:
            if k in ['step', 'cheats']: st.session_state[k] = 0
            elif k in ['answers', 'codes', 'durations']: st.session_state[k] = {}
            elif k.startswith('exam_open'): st.session_state[k] = False
            elif k == 'page': st.session_state[k] = '🏠 Accueil'
            else: st.session_state[k] = None

init_session()

def check_exam_status():
    if not db: return
    try:
        doc = db.collection('artifacts').document(PROJET_ID).collection('public').document('data').collection('settings').document('config').get()
        if doc.exists:
            d = doc.to_dict()
            st.session_state.exam_open_normal = d.get('open_normal', False)
            st.session_state.exam_open_rattrapage = d.get('open_rattrapage', False)
        else:
             db.collection('artifacts').document(PROJET_ID).collection('public').document('data').collection('settings').document('config').set({
                 'open_normal': False, 'open_rattrapage': False
             })
    except: pass

check_exam_status()

if st.button("INTEGRITY_TRIGGER", key="cheat_trigger"): st.session_state.cheats += 1

# --- 6. CLASSES ET HELPERS ---
def get_algeria_time_str(timestamp):
    try:
        if not timestamp: return "--:--"
        if isinstance(timestamp, (datetime.datetime, datetime.date)):
             utc_dt = timestamp
        else:
            ts = float(timestamp)
            utc_dt = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)
        alg_dt = utc_dt + datetime.timedelta(hours=1)
        return alg_dt.strftime("%H:%M:%S")
    except: return "--:--"

def normalize_name(name): return str(name).strip().lower()

class ReportPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 5, "REPUBLIQUE ALGERIENNE DEMOCRATIQUE ET POPULAIRE", 0, 1, 'C')
        self.cell(0, 5, "INSFP BELAZZOUG ATHMANE BBA 01", 0, 1, 'C'); self.ln(10)
        self.set_fill_color(245, 124, 0); self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 12, "PV D'EXAMEN - ASR PRO", 1, 1, 'C', 1)
        self.set_text_color(0, 0, 0); self.ln(5)
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_final_report_pdf(stats, results_df):
    pdf = ReportPDF(); pdf.add_page()
    pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, "1. STATISTIQUES", 0, 1)
    pdf.set_font("Arial", "", 11)
    pdf.cell(90, 10, f"Copies: {stats['present']}", 1); pdf.cell(90, 10, f"Moyenne: {stats['moyenne']}/20", 1, 1)
    pdf.ln(10); pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, "2. LISTE", 0, 1)
    pdf.set_fill_color(220, 220, 220); pdf.set_font("Arial", "B", 10)
    pdf.cell(70, 10, "Nom", 1, 0, 'C', 1); pdf.cell(30, 10, "Note", 1, 0, 'C', 1); pdf.cell(40, 10, "Heure", 1, 1, 'C', 1)
    pdf.set_font("Arial", "", 10)
    for index, row in results_df.iterrows():
        pdf.cell(70, 10, str(row['Nom']), 1)
        pdf.cell(30, 10, str(row['Note']), 1, 0, 'C')
        pdf.cell(40, 10, str(row['Heure']), 1, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')

def get_col(name): 
    if not db: return None
    return db.collection('artifacts').document(PROJET_ID).collection('public').document('data').collection(name)

def generate_pw(l=8): return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(l))

def generate_pdf_credentials(users_list):
    pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", 'B', 11)
    pdf.cell(75, 12, "Nom", 1); pdf.cell(45, 12, "User", 1); pdf.cell(35, 12, "Pass", 1, 1)
    pdf.set_font("Arial", '', 11)
    for u in users_list:
        pdf.cell(75, 12, u.get('name'), 1); pdf.cell(45, 12, u.get('username'), 1); pdf.cell(35, 12, u.get('password'), 1, 1)
    return pdf.output(dest='S').encode('latin-1')

def generate_pedagogical_insight(score):
    if score < 5: return "🔴 **Niveau Critique** : Lacunes fondamentales. Reprise totale des bases nécessaire."
    elif score < 10: return "🟠 **Niveau Insuffisant** : Concepts partiellement compris mais application défaillante."
    elif score < 14: return "🟡 **Niveau Moyen** : L'essentiel est acquis, mais manque de rigueur ou de profondeur."
    elif score < 18: return "🟢 **Bon Niveau** : Bonne maîtrise technique et théorique."
    else: return "🔵 **Excellent** : Maîtrise parfaite du sujet."

# --- 7. DONNÉES EXAMENS (NORMAL & RATTRAPAGE) ---
EXAM_NORMAL = [
    {"id": "n1", "titre": "Algorithmique - Contrôle d'Accès", "points": 5, "enonce": "Écrivez un programme qui demande l'année de naissance de l'utilisateur.\n1. Calculez son âge (référence 2026).\n2. Si l'utilisateur a 18 ans ou plus: Affichez 'Accès autorisé'.\n3. Sinon: Affichez 'Accès refusé'.", "questions": [{"id":"qn1_1","text":"Âge pour naissance en 2010 ?", "type":"number", "correct":16}, {"id":"qn1_2","text":"Message pour 16 ans ?", "type":"choice", "options":["Accès autorisé", "Accès refusé"], "correct":"Accès refusé"}]},
    {"id": "n2", "titre": "Physique - État de l'eau", "points": 5, "enonce": "Demandez la température T de l'eau (°C) :\n- Si T <= 0 : Affichez 'Glace'\n- Si 0 < T < 100 : Affichez 'Liquide'\n- Si T >= 100 : Affichez 'Vapeur'", "questions": [{"id":"qn2_1","text":"État à 100°C pile ?", "type":"choice", "options":["Glace", "Liquide", "Vapeur"], "correct":"Vapeur"}]},
    {"id": "n3", "titre": "Gestion - Assurance Auto", "points": 5, "enonce": "Tarif de base : 500€.\n- Si le conducteur a < 25 ans ET < 2 ans de permis : Ajouter 200€.\n- Si le conducteur a > 25 ans OU > 5 ans de permis : Retirer 50€.\nCalculez le tarif final.", "questions": [{"id":"qn3_1","text":"Conducteur 22 ans, 1 an permis. Prix final ?", "type":"number", "correct":700}]},
    {"id": "n4", "titre": "Ingénierie - Crédit Bancaire", "points": 5, "enonce": "Vérifiez l'éligibilité au crédit :\n- Si Épargne <= 0 : Refus.\n- Si Taux d'endettement > 33% : Refus.\n- Sinon : Crédit Accepté.", "questions": [{"id":"qn4_1","text":"Revenu 2000, Dépenses 2000 (donc pas d'épargne). Décision ?", "type":"choice", "options":["Refus", "Crédit Accepté"], "correct":"Refus"}]}
]

EXAM_RATTRAPAGE = [
    {"id": "r1", "titre": "Questions Théoriques", "points": 8, "mode_affichage": "qcm_only", "enonce": "Répondez aux questions sur Python.", "questions": [
        {"id":"q1_1","text":"Q1. Type de `42` ?", "type":"choice", "options":["int", "float", "str", "bool"], "correct":"int"},
        {"id":"q1_2","text":"Q2. Type de `\"42.5\"` ?", "type":"choice", "options":["int", "float", "str", "bool"], "correct":"str"},
        {"id":"q1_3","text":"Q3. Type de `42.0` ?", "type":"choice", "options":["int", "float", "str", "bool"], "correct":"float"},
        {"id":"q1_4","text":"Q4. Type de `10 > 5` ?", "type":"choice", "options":["int", "float", "str", "bool"], "correct":"bool"},
        {"id":"q1_5","text":"Q5. Valeur de z ? (x=10, y=5, z=x+y, if x>15: z*2 else: z+10)", "type":"number", "correct":30, "code": "x=10\ny=5\nz=x+y\nif x>15: z=z*2\nelse: z=z+10\nprint(z)"}
    ]},
    {"id": "r2", "titre": "Calculateur Assurance Auto", "points": 12, "mode_affichage": "code_only", "enonce": "Programme 'AssurAuto'. Tarif base : 500€.\n- Jeune conducteur (<25 ans) : +100€.\n- Malus (Accident 'Oui') : +200€.\n- Bonus (>5 ans de permis) : -50€.\nCalculez le tarif final.", "questions": []}
]

EXAMS_DB = {"normal": EXAM_NORMAL, "rattrapage": EXAM_RATTRAPAGE}

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
    st.markdown("""<div class="footer-wrapper"><p style="color:white; opacity:0.8;">Réalisé par le Formateur : <strong>Haithem Berkane</strong></p></div>""", unsafe_allow_html=True)

def audit_results_detailed(data):
    e_type = data.get('exam_type', 'normal')
    schema = EXAMS_DB.get(e_type, EXAM_NORMAL)
    st.markdown(f"### 🔍 Analyse de la Copie ({e_type.upper()})")
    
    score = data.get('score', 0)
    insight = generate_pedagogical_insight(score)
    st.markdown(f"<div style='background:#f0f9ff; border:1px solid #bae6fd; color:#0369a1; padding:15px; border-radius:8px; margin-bottom:15px;'>{insight}</div>", unsafe_allow_html=True)
    
    # RECURSIVE KEYS SEARCH (POUR RÉCUPÉRER LES SOLUTIONS)
    # Chercher dans answers ou reponses
    saved_answers = data.get('answers') or data.get('reponses') or {}
    # Chercher dans codes ou scripts
    saved_codes = data.get('codes') or data.get('scripts') or {}
    
    def smart_get(d, key):
        if not d: return None
        # Cas 1: Match exact (qn1_1)
        if key in d: return d[key]
        # Cas 2: Match fuzzy (qn1_1 -> q1_1)
        fuzzy_key = key.replace('qn', 'q')
        if fuzzy_key in d: return d[fuzzy_key]
        # Cas 3: Match numérique (qn1_1 -> 1_1)
        num_key = fuzzy_key.replace('q', '')
        if num_key in d: return d[num_key]
        return None

    for ex in schema:
        with st.expander(f"Exercice : {ex['titre']}"):
            col_q, col_c = st.columns([1, 1.5])
            with col_q:
                if ex.get('mode_affichage') != 'code_only':
                    for q in ex['questions']:
                        val = smart_get(saved_answers, q['id'])
                        if val is None: val = "Donnée non trouvée"
                        is_correct = str(val) == str(q['correct'])
                        color = "#10b981" if is_correct else "#ef4444"
                        st.markdown(f"<div style='padding:10px; border-left:5px solid {color}; margin-bottom:10px; background:rgba(255,255,255,0.05);'><small>{q['text']}</small><br><b>Saisi : {val}</b><br><small style='color:gray;'>Correct : {q['correct']}</small></div>", unsafe_allow_html=True)
            with col_c:
                if ex.get('mode_affichage') != 'qcm_only':
                    code_id = str(ex['id'])
                    code = smart_get(saved_codes, code_id)
                    if not code:
                        # Test index numérique pur (n1 -> 1)
                        clean_id = code_id.strip('nr')
                        code = smart_get(saved_codes, clean_id)
                    
                    if code: st.code(code, "python")
                    else: st.warning("Solution code manquante ou non soumise.")

@st.cache_data(ttl=60)
def fetch_dashboard_data():
    if not db: return [], []
    u_docs = get_col('users').where('role', '==', 'student').get()
    r_docs = get_col('results').get()
    return [{"id": u.id, **u.to_dict()} for u in u_docs], [{"id": r.id, **r.to_dict()} for r in r_docs]

def teacher_dash():
    u_list, r_list = fetch_dashboard_data()
    if st.button("🔄 Actualiser les données"): fetch_dashboard_data.clear(); st.rerun()
    t1, t2, t3, t4 = st.tabs(["📊 STATISTIQUES", "👥 GESTION ÉTUDIANTS", "📑 AUDIT DES COPIES", "📦 MIGRATION JSON"])
    
    with t1:
        st.markdown("### 🔒 État des Sessions")
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"NORMAL : {'🟢 OUVERT' if st.session_state.exam_open_normal else '🔴 FERMÉ'}")
            if st.button("BASCULER NORMAL"):
                ns = not st.session_state.exam_open_normal
                if db: get_col('settings').document('config').set({'open_normal': ns}, merge=True)
                st.session_state.exam_open_normal = ns; st.rerun()
        with c2:
            st.info(f"RATTRAPAGE : {'🟢 OUVERT' if st.session_state.exam_open_rattrapage else '🔴 FERMÉ'}")
            if st.button("BASCULER RATTRAPAGE"):
                ns = not st.session_state.exam_open_rattrapage
                if db: get_col('settings').document('config').set({'open_rattrapage': ns}, merge=True)
                st.session_state.exam_open_rattrapage = ns; st.rerun()
        
        st.divider()
        stat_view = st.radio("Filtre d'analyse :", ["Global", "Session Normale", "Session Rattrapage"], horizontal=True)
        
        filtered_r = r_list
        if stat_view == "Session Normale": filtered_r = [r for r in r_list if r.get('exam_type') == 'normal' or 'exam_type' not in r]
        elif stat_view == "Session Rattrapage": filtered_r = [r for r in r_list if r.get('exam_type') == 'rattrapage']
        
        # CALCULS STATS SANS DOUBLONS
        unique_users = set(r.get('username') for r in filtered_r)
        inscrits = len(u_list)
        presents_uniques = len(unique_users)
        absents = max(0, inscrits - presents_uniques)
        moyenne = pd.DataFrame(filtered_r)['score'].mean() if filtered_r else 0
        
        # AFFICHAGE 4 COLONNES PLEINES
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Inscrits", inscrits)
        m2.metric("Présents (Indiv.)", presents_uniques)
        m3.metric("Absents", absents)
        m4.metric("Moyenne /20", f"{moyenne:.2f}")
        
        if len(filtered_r) > presents_uniques:
            st.warning(f"⚠️ Note : {len(filtered_r) - presents_uniques} copies multiples détectées. Les stats individuelles sont préservées.")

    with t2:
        c_i1, c_i2 = st.columns(2)
        with c_i1:
            up_f = st.file_uploader("Importer Liste (Excel)", type=['xlsx'])
            if up_f and st.button("LANCER IMPORTATION"):
                df = pd.read_excel(up_f)
                for name in df.iloc[:, 0].dropna():
                    uid = str(name).strip().lower().replace(" ", ".") + str(random.randint(10,99))
                    if db: get_col('users').add({"name": str(name).strip(), "username": uid, "password": generate_pw(), "role": "student"})
                fetch_dashboard_data.clear(); st.rerun()
        with c_i2:
            if u_list: st.download_button("Télécharger Convocation (PDF)", generate_pdf_credentials(u_list), "Acces_ASR.pdf")
            st.dataframe(pd.DataFrame(u_list)[['name', 'username', 'password']], use_container_width=True, hide_index=True)

    with t3:
        st.markdown("### 📑 Grille de Progression Interactive")
        full_data = []
        for u in u_list:
            u_copies = [r for r in r_list if r['username'] == u['username']]
            rn = next((r for r in u_copies if r.get('exam_type') == 'normal' or 'exam_type' not in r), None)
            rr = next((r for r in u_copies if r.get('exam_type') == 'rattrapage'), None)
            sn = rn['score'] if rn else 0
            sr = rr['score'] if rr else 0
            full_data.append({
                "Username": u['username'], 
                "Nom Complet": u['name'], 
                "Note Normale": sn, 
                "Note Rattrapage": sr if rr else "-", 
                "Note Finale": max(sn, sr),
                "Statut": "ADMIS ✅" if max(sn, sr) >= 10 else "AJOURNÉ ❌"
            })
        
        df_grid = pd.DataFrame(full_data)
        event = st.dataframe(df_grid, use_container_width=True, on_select="rerun", selection_mode="single-row", hide_index=True)
        
        if event.selection.rows:
            sel_idx = event.selection.rows[0]
            sel_user = df_grid.iloc[sel_idx]["Username"]
            u_copies = [r for r in r_list if r['username'] == sel_user]
            rn = next((r for r in u_copies if r.get('exam_type') == 'normal' or 'exam_type' not in r), None)
            rr = next((r for r in u_copies if r.get('exam_type') == 'rattrapage'), None)
            
            st.divider()
            st.subheader(f"Détails : {df_grid.iloc[sel_idx]['Nom Complet']}")
            ca, cb = st.columns(2)
            with ca: 
                if rn: audit_results_detailed(rn)
                else: st.warning("Aucune copie pour la session normale.")
            with cb:
                if rr: audit_results_detailed(rr)
                else: st.warning("Aucune copie pour la session rattrapage.")

    with t4:
        st.markdown("### 📦 Sauvegarde et Migration")
        if st.button("EXTRAIRE TOUTES LES COPIES (JSON)"):
            clean = []
            for r in r_list:
                item = dict(r)
                if isinstance(item.get('timestamp'), (datetime.datetime, datetime.date)):
                     item['timestamp'] = item['timestamp'].timestamp()
                clean.append(item)
            st.download_button("TÉLÉCHARGER JSON", json.dumps(clean, indent=2, default=str), f"backup_asr_{datetime.date.today()}.json", "application/json")
        
        st.divider()
        up_j = st.file_uploader("Charger un JSON pour restauration", type=['json'])
        if up_j and st.button("RESTAURER MAINTENANT"):
            data = json.load(up_j)
            count = 0
            for item in data:
                if db: 
                    get_col('results').add(item)
                    count += 1
            st.success(f"Restauration terminée : {count} copies ajoutées !"); time.sleep(1); st.rerun()

def exam_view():
    mode = st.session_state.current_exam_mode
    data_exam = EXAMS_DB.get(mode, EXAM_NORMAL)
    show_header(); st.markdown(f"### EXAMEN : {mode.upper()}")
    step = st.session_state.step
    if step >= len(data_exam):
        total, br = 0, {}
        for e in data_exam:
            pts = 0
            if e['questions']:
                w = e['points'] * (0.4 if e.get('mode_affichage')!='qcm_only' else 1.0)
                good = sum(1 for q in e['questions'] if str(st.session_state.answers.get(q['id'])) == str(q['correct']))
                pts += (good/len(e['questions'])) * w
            if e.get('mode_affichage') != 'qcm_only':
                w = e['points'] * (0.6 if e['questions'] else 1.0)
                if len(st.session_state.codes.get(e['id'], "").strip()) > 10: pts += w
            br[str(e['id'])] = round(pts, 2); total += pts
        if db:
            get_col('results').add({
                "username": st.session_state.user['username'], "name": st.session_state.user['name'],
                "score": round(total, 2), "breakdown": br, "exam_type": mode, 
                "answers": st.session_state.answers, "codes": st.session_state.codes, "timestamp": time.time()
            })
        st.session_state.page = "👤 Espace Candidat"; st.rerun()
        return

    ex = data_exam[step]; st.progress((step + 1) / len(data_exam))
    st.markdown(f'<div class="white-card"><h3>{ex["titre"]}</h3><pre style="white-space:pre-wrap;">{ex["enonce"]}</pre></div>', unsafe_allow_html=True)
    if ex.get('mode_affichage') != 'code_only':
        for q in ex['questions']:
            st.markdown(f"**{q['text']}**")
            if 'code' in q: st.code(q['code'], 'python')
            if q['type'] == 'choice': st.session_state.answers[q['id']] = st.radio("Réponse :", q['options'], key=f"ans_{q['id']}")
            else: st.session_state.answers[q['id']] = st.number_input("Réponse :", key=f"ans_{q['id']}")
    if ex.get('mode_affichage') != 'qcm_only':
        st.session_state.codes[ex['id']] = st.text_area("Script Python :", height=250, key=f"c_{ex['id']}")
    if st.button("ÉTAPE SUIVANTE" if step < len(data_exam)-1 else "SOUMETTRE LA COPIE"):
        st.session_state.step += 1; st.rerun()

def student_dash():
    show_header(); u = st.session_state.user; st.markdown(f"<h2>Bonjour, {u['name']}</h2>", unsafe_allow_html=True)
    my_res = []
    if db: my_res = [r.to_dict() for r in get_col('results').where('username', '==', u['username']).get()]
    rn = next((r for r in my_res if r.get('exam_type')=='normal' or 'exam_type' not in r), None)
    rr = next((r for r in my_res if r.get('exam_type')=='rattrapage'), None)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="white-card"><h3>📅 SESSION NORMALE</h3>', unsafe_allow_html=True)
        if rn: st.success(f"Score : {rn['score']}/20")
        elif st.session_state.exam_open_normal:
            if st.button("LANCER L'ÉPREUVE NORMALE"): st.session_state.current_exam_mode="normal"; st.session_state.page="exam"; st.session_state.step=0; st.rerun()
        else: st.warning("Session actuellement fermée.")
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="white-card"><h3>🚑 SESSION RATTRAPAGE</h3>', unsafe_allow_html=True)
        if rr: st.success(f"Score : {rr['score']}/20")
        elif st.session_state.exam_open_rattrapage:
             if st.button("LANCER LE RATTRAPAGE"): st.session_state.current_exam_mode="rattrapage"; st.session_state.page="exam"; st.session_state.step=0; st.rerun()
        else: st.warning("Session actuellement fermée.")
        st.markdown('</div>', unsafe_allow_html=True)
    show_footer()

def login_view():
    show_header(); u = st.text_input("Identifiant"); p = st.text_input("Mot de passe", type="password")
    if st.button("SE CONNECTER"):
        if u == "admin" and p == "admin": st.session_state.user = {"name": "Formateur", "role": "teacher", "username": "admin"}; st.session_state.page = "📊 STATISTIQUES"; st.rerun()
        if db:
            docs = get_col('users').where('username', '==', u).where('password', '==', p).get()
            if docs: st.session_state.user = docs[0].to_dict(); st.session_state.page = "👤 Espace Candidat"; st.rerun()

def enonce_view():
    show_header()
    for t, d in EXAMS_DB.items():
        st.markdown(f"## {t.upper()}")
        for ex in d:
            with st.expander(ex['titre']): st.markdown(f"```text\n{ex['enonce']}\n```")

def faq_view():
    show_header(); st.markdown("<div class='white-card'><h2>Aide technique</h2><p>Contactez le surveillant en cas de déconnexion.</p></div>", unsafe_allow_html=True)

def accueil_view():
    show_header()
    st.markdown("""
        <div class="white-card">
            <h1>Bienvenue sur ASR Pro</h1>
            <p>Plateforme sécurisée d'évaluation pour l'INSFP Belazzoug Athmane.</p>
            <p>Veuillez vous authentifier pour accéder à votre espace personnel.</p>
        </div>
    """, unsafe_allow_html=True)
    show_footer()

# --- 9. ROUTAGE ---
pages = ["🏠 Accueil", "📜 Énoncés", "❓ FAQ"]
if st.session_state.user: pages += ["📊 STATISTIQUES"] if st.session_state.user['role'] == 'teacher' else ["👤 Espace Candidat"]; pages += ["🚪 Déconnexion"]
else: pages += ["🔐 Connexion"]

st.markdown('<div class="nav-fallback">', unsafe_allow_html=True)
cols = st.columns(len(pages))
for i, p_name in enumerate(pages):
    if cols[i].button(p_name, use_container_width=True):
        if "Déconnexion" in p_name: st.session_state.user=None; st.session_state.page="🏠 Accueil"
        else: st.session_state.page = p_name
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

p = st.session_state.page
if p == '📊 STATISTIQUES': teacher_dash()
elif p == 'exam': exam_view()
elif p == '👤 Espace Candidat': student_dash()
elif p == '🔐 Connexion': login_view()
elif p == '📜 Énoncés': enonce_view()
elif p == '❓ FAQ': faq_view()
else: accueil_view()
