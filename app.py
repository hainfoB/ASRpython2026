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
    page_title="ASR Pro - Excellence Pédagogique",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SÉCURITÉ & PROTECTION (RENFORCÉE) ---
st.components.v1.html("""
    <script>
    document.addEventListener('contextmenu', event => event.preventDefault());
    document.addEventListener('copy', e => e.preventDefault());
    document.addEventListener('paste', e => e.preventDefault());
    
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            triggerCheat();
        }
    });

    function triggerCheat() {
        const buttons = window.parent.document.querySelectorAll('button');
        buttons.forEach(btn => {
            if (btn.innerText.includes('INTEGRITY_TRIGGER')) {
                btn.click();
            }
        });
    }
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
    .stButton > button:hover {
        background-color: var(--orange-light) !important;
        box-shadow: 0 4px 15px rgba(245, 124, 0, 0.4) !important;
    }

    .hb-logo {
        width: 90px; height: 90px; background: white;
        border: 6px solid var(--orange-light); border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        color: var(--hb-blue); font-weight: 900; font-size: 2.5rem;
        box-shadow: 0 0 25px rgba(245, 124, 0, 0.6);
    }

    [data-testid="stWidgetLabel"] p, label, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #ffffff !important;
        font-size: 1.5rem !important;
        font-weight: 700 !important;
    }
    
    .stTextInput input, .stNumberInput input {
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
    .white-card *, .white-card h1, .white-card h2 { color: var(--midnight) !important; }
    
    [data-testid="stMetric"] {
        background-color: var(--white) !important;
        padding: 30px 10px !important;
        border-radius: 16px !important;
        border-left: 10px solid var(--orange-light) !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3) !important;
        text-align: center !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        height: 100% !important;
    }
    [data-testid="stMetricLabel"] p {
        color: var(--midnight) !important;
        font-size: 1.6rem !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
    }
    [data-testid="stMetricValue"] div {
        color: var(--orange-dark) !important;
        font-size: 5rem !important;
        font-weight: 900 !important;
        line-height: 1.1 !important;
    }

    [data-testid="stFileUploaderDropzoneInstructions"], [data-testid="stFileUploaderDropzone"] div small { display: none !important; }
    [data-testid="stFileUploaderDropzone"] {
        border: 2px dashed var(--orange-dark) !important;
        background-color: rgba(255,255,255,0.05) !important;
        padding: 20px !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        background-color: var(--orange-dark) !important;
        color: white !important;
        border: none !important;
    }

    .nav-fallback {
        background-color: var(--navy);
        padding: 15px; border-radius: 12px;
        display: flex; justify-content: center; gap: 15px;
        margin-bottom: 40px; border-bottom: 4px solid var(--orange-light);
    }
    
    div[data-testid="stButton"]:has(button:contains("INTEGRITY_TRIGGER")) { display: none !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. FIREBASE & UTILS ---
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
    except: pass

db = firestore.client()
PROJET_ID = "asr-pro-dynamic"

def init_session():
    defaults = {
        'user': None, 'page': '🏠 Accueil', 'step': 0, 'answers': {}, 
        'codes': {}, 'durations': {}, 'ex_start_time': None, 'cheats': 0, 
        'exam_open': True, 'builder_questions': []
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

init_session()

# Vérification état examen
try:
    status_doc = db.collection('exam_config').document('status').get()
    if status_doc.exists: st.session_state.exam_open = status_doc.to_dict().get('is_open', True)
except: pass

# --- LOGIQUE ANTI-TRICHE ---
if st.button("INTEGRITY_TRIGGER", key="cheat_trigger"):
    st.session_state.cheats += 1
    st.rerun()

# Helpers
def get_col(name): return db.collection('artifacts').document(PROJET_ID).collection(name)
def generate_pw(l=8): return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(l))

def get_algeria_time_str(timestamp):
    utc_dt = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)
    alg_dt = utc_dt + datetime.timedelta(hours=1)
    return alg_dt.strftime("%H:%M:%S")

# --- 5. LOGIQUE MÉTIER DYNAMIQUE ---
def save_exam_config(title, pdf_b64, questions):
    data = {
        "title": title, "pdf_b64": pdf_b64, "questions": questions,
        "created_at": time.time(), "is_active": True
    }
    try:
        db.collection('exam_config').document('active_exam').set(data)
        return True
    except Exception as e:
        st.error(f"Erreur de sauvegarde: {e}")
        return False

def get_active_exam():
    try:
        doc = db.collection('exam_config').document('active_exam').get()
        if doc.exists: return doc.to_dict()
    except: pass
    return None

def display_pdf(b64_string):
    if b64_string:
        pdf_display = f'<iframe src="data:application/pdf;base64,{b64_string}" width="100%" height="800" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.warning("PDF non disponible.")

# --- 6. GÉNÉRATION DE RAPPORTS ---
class ReportPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, "REPUBLIQUE ALGERIENNE DEMOCRATIQUE ET POPULAIRE", 0, 1, 'C')
        self.cell(0, 10, "INSFP BELAZZOUG ATHMANE BBA 01", 0, 1, 'C')
        self.ln(5)
        self.set_fill_color(245, 124, 0) # Orange
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "PROCES VERBAL D'EXAMEN - ASR PRO", 1, 1, 'C', 1)
        self.set_text_color(0, 0, 0)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_final_report_pdf(stats, results_df):
    pdf = ReportPDF()
    pdf.add_page()
    
    # 1. Statistiques Globales
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "1. STATISTIQUES GLOBALES", 0, 1)
    pdf.set_font("Arial", "", 11)
    pdf.cell(50, 10, f"Nombre de presents: {stats['present']}")
    pdf.cell(50, 10, f"Moyenne de section: {stats['moyenne']}/20", 0, 1)
    pdf.cell(50, 10, f"Meilleure note: {stats['max']}/20")
    pdf.cell(50, 10, f"Note minimale: {stats['min']}/20", 0, 1)
    pdf.ln(10)

    # 2. Liste des Résultats
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "2. LISTE DETAILLEE DES RESULTATS", 0, 1)
    
    # Table Header
    pdf.set_fill_color(200, 200, 200)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(80, 10, "Nom & Prenom", 1, 0, 'C', 1)
    pdf.cell(30, 10, "Note /20", 1, 0, 'C', 1)
    pdf.cell(40, 10, "Heure Remise", 1, 0, 'C', 1)
    pdf.cell(40, 10, "Obs (Triche)", 1, 1, 'C', 1)
    
    # Table Rows
    pdf.set_font("Arial", "", 10)
    for index, row in results_df.iterrows():
        pdf.cell(80, 10, str(row['Nom']), 1)
        pdf.cell(30, 10, str(row['Note']), 1, 0, 'C')
        pdf.cell(40, 10, str(row['Heure']), 1, 0, 'C')
        obs = f"{row['Alertes']} alerte(s)" if row['Alertes'] > 0 else "RAS"
        pdf.cell(40, 10, obs, 1, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

def generate_pdf_credentials(users_list):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(245, 124, 0); pdf.set_text_color(255, 255, 255)
    pdf.cell(75, 12, "Nom & Prenom", 1, 0, 'C', 1); pdf.cell(45, 12, "Identifiant", 1, 0, 'C', 1)
    pdf.cell(35, 12, "Mot de Passe", 1, 0, 'C', 1); pdf.cell(35, 12, "Emargement", 1, 1, 'C', 1)
    pdf.set_font("Arial", '', 11); pdf.set_text_color(0, 0, 0)
    for u in users_list:
        pdf.cell(75, 12, u.get('name', 'Inconnu'), 1); pdf.cell(45, 12, u.get('username', ''), 1)
        pdf.cell(35, 12, u.get('password', ''), 1); pdf.cell(35, 12, "", 1, 1)
    return pdf.output(dest='S').encode('latin-1')

# --- 7. VUES ---
def show_header():
    st.markdown("""
        <div style="text-align:center; margin-bottom: 40px;">
            <div style="display:flex; justify-content:center; margin-bottom:20px;">
                <div class="hb-logo">HB</div>
            </div>
            <h4 style="color:rgba(255,255,255,0.7); letter-spacing:2px; text-transform:uppercase;">République Algérienne Démocratique et Populaire</h4>
            <h1 style="color:#f57c00; font-size:2.8rem; margin:15px 0; font-weight:900;">INSFP Belazzoug Athmane BBA 01</h1>
            <p style="color:white; letter-spacing:5px; font-size:1.5rem; font-weight:700;">PLATEFORME D'EXAMEN DYNAMIQUE ASR PRO</p>
        </div>
    """, unsafe_allow_html=True)

# Cache pour fluidité
@st.cache_data(ttl=60)
def fetch_dashboard_data():
    try:
        u_docs = get_col('users').where('role', '==', 'student').get()
        r_docs = get_col('results').get()
        return [{"id":d.id, **d.to_dict()} for d in u_docs], [{"id":d.id, **d.to_dict()} for d in r_docs]
    except: return [], []

def teacher_dash():
    show_header()
    u_list, r_list = fetch_dashboard_data()
    
    if st.button("🔄 Actualiser les données"):
        fetch_dashboard_data.clear()
        st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["⚙️ CRÉATION EXAMEN", "📊 STATISTIQUES", "👥 GESTION", "📑 CORRECTION & RAPPORT"])

    # --- ONGLET 1 : CONSTRUCTEUR D'EXAMEN ---
    with tab1:
        st.markdown("### 🛠️ Constructeur d'Examen Dynamique")
        with st.form("exam_builder"):
            exam_title = st.text_input("Titre de l'examen", "Examen Final")
            uploaded_pdf = st.file_uploader("Sujet PDF", type=['pdf'])
            st.markdown("#### 📝 Configuration des Questions (JSON)")
            questions_json = st.text_area("Questions JSON", value='[\n  {"id": 1, "text": "Exercice 1", "type": "code", "points": 10, "correct": "print"}\n]', height=150)
            
            if st.form_submit_button("💾 PUBLIER"):
                pdf_b64 = ""
                if uploaded_pdf:
                    try: pdf_b64 = base64.b64encode(uploaded_pdf.read()).decode('utf-8')
                    except: pass
                try:
                    q_data = json.loads(questions_json)
                    if save_exam_config(exam_title, pdf_b64, q_data):
                        st.success("Publié !"); time.sleep(1); st.rerun()
                except: st.error("Erreur JSON")

    # --- ONGLET 2 : STATS ---
    with tab2:
        cl1, cl2 = st.columns([2, 1])
        cl1.info(f"État Session : **{'OUVERT' if st.session_state.exam_open else 'FERMÉ'}**")
        if cl2.button("BASCULER ÉTAT"):
            ns = not st.session_state.exam_open
            db.collection('exam_config').document('status').set({'is_open': ns})
            st.session_state.exam_open = ns; st.rerun()
        
        st.divider()
        col_m = st.columns(4)
        col_m[0].metric("Inscrits", len(u_list))
        col_m[1].metric("Présents", len(r_list))
        col_m[2].metric("Absents", max(0, len(u_list) - len(r_list)))
        avg = pd.DataFrame(r_list)['score'].mean() if r_list else 0
        col_m[3].metric("Moyenne", f"{avg:.2f}")

    # --- ONGLET 3 : GESTION (AVEC ANTI-DOUBLON) ---
    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            up_f = st.file_uploader("Importer fichier Excel", type=['xlsx'])
            if up_f and st.button("LANCER IMPORTATION"):
                df = pd.read_excel(up_f)
                existing_names = [u['name'] for u in u_list]
                count_added = 0
                
                for name in df.iloc[:, 0].dropna():
                    if name not in existing_names: 
                        uid = name.lower().replace(" ", ".") + str(random.randint(10,99))
                        get_col('users').add({"name": name, "username": uid, "password": generate_pw(), "role": "student"})
                        count_added += 1
                
                fetch_dashboard_data.clear()
                st.success(f"{count_added} nouveaux étudiants ajoutés.")
                time.sleep(1); st.rerun()
        with c2:
            if u_list: 
                st.download_button("📥 FICHES ACCÈS (PDF)", generate_pdf_credentials(u_list), "Acces_ASR.pdf")
                # Correction KeyError : Création sécurisée du DataFrame
                df_users = pd.DataFrame(u_list)
                # On s'assure que les colonnes existent
                required_cols = ['name', 'username', 'password']
                for c in required_cols:
                    if c not in df_users.columns: df_users[c] = ""
                # Affichage sûr
                st.dataframe(df_users[required_cols], use_container_width=True)
            else:
                st.info("Aucun étudiant inscrit.")

    # --- ONGLET 4 : CORRECTION & RAPPORT (TRI TEMPOREL) ---
    with tab4:
        if r_list:
            data_for_df = []
            for r in r_list:
                ts = r.get('timestamp', 0)
                data_for_df.append({
                    "ID": r['id'],
                    "Nom": r['name'],
                    "Note": r['score'],
                    "Alertes": r.get('cheats', 0),
                    "Heure": get_algeria_time_str(ts),
                    "timestamp": ts 
                })
            
            df_res = pd.DataFrame(data_for_df)
            df_res = df_res.sort_values(by='timestamp', ascending=True)
            
            stats = {
                "present": len(r_list),
                "moyenne": f"{df_res['Note'].mean():.2f}",
                "max": df_res['Note'].max(),
                "min": df_res['Note'].min()
            }
            pdf_report = generate_final_report_pdf(stats, df_res)
            st.download_button("📄 TÉLÉCHARGER PROCES VERBAL OFFICIEL (PDF)", pdf_report, "PV_Examen_ASR.pdf", mime="application/pdf")
            
            st.markdown("### Liste des copies (Triée par ordre de remise)")
            sel = st.dataframe(df_res.drop(columns=["ID", "timestamp"]), use_container_width=True, on_select="rerun", selection_mode="single-row")
            
            if sel and sel.selection.rows:
                selected_row_idx = sel.selection.rows[0]
                selected_data = df_res.iloc[selected_row_idx]
                doc_id = selected_data['ID']
                
                full_data = next((item for item in r_list if item["id"] == doc_id), None)
                
                if full_data:
                    st.markdown(f'<div class="white-card"><h2>{full_data["name"]}</h2><h1>{full_data["score"]} / 20</h1></div>', unsafe_allow_html=True)
                    st.markdown(f"**Remis à :** {get_algeria_time_str(full_data.get('timestamp',0))}")
                    
                    st.markdown("### Réponses Soumises")
                    for q_id, ans in full_data.get('answers', {}).items():
                        st.markdown(f"**Q{q_id}**: {ans}")
                    for q_id, code in full_data.get('codes', {}).items():
                        st.code(code, language='python')

def info_view():
    show_header()
    st.markdown("""
        <div class="white-card">
            <h2>ℹ️ Informations & Modalités</h2>
            <p>Bienvenue sur la plateforme d'examen numérique ASR Pro.</p>
            <ul>
                <li><strong>Format :</strong> Examen pratique dynamique. Le sujet est affiché au format PDF.</li>
                <li><strong>Outils :</strong> Vous disposez d'un environnement Python intégré et de champs de réponse.</li>
                <li><strong>Règles :</strong> Travail strictement individuel. La surveillance est active (détection de sortie).</li>
                <li><strong>Validation :</strong> Pensez à cliquer sur "TERMINER" pour soumettre votre copie.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

def faq_view():
    show_header()
    st.markdown("""
        <div class="white-card">
            <h2>❓ Foire Aux Questions</h2>
            <ul>
                <li><strong>Comment se connecter ?</strong> Utilisez les identifiants fournis par votre enseignant ou sur la fiche d'accès.</li>
                <li><strong>Que faire si le sujet ne s'affiche pas ?</strong> Actualisez la page (F5) ou contactez le surveillant.</li>
                <li><strong>Puis-je sortir de la page pour aller sur Google ?</strong> Non, le système détecte toute sortie et cela peut être sanctionné.</li>
                <li><strong>La sauvegarde est-elle automatique ?</strong> Non, vous devez cliquer sur "TERMINER" pour envoyer votre copie finale.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

def exam_view():
    if not st.session_state.exam_open: show_header(); st.error("🔒 Examen verrouillé."); return
    exam_config = get_active_exam()
    if not exam_config: st.error("Pas d'examen configuré."); return

    col_pdf, col_form = st.columns([1, 1])
    with col_pdf:
        st.markdown("### 📄 Sujet")
        if exam_config.get('pdf_b64'): display_pdf(exam_config['pdf_b64'])
        else: st.info("Sujet papier.")
    
    with col_form:
        st.markdown(f"### ✍️ Réponses ({st.session_state.cheats} 🚩)")
        with st.form("exam_sub"):
            for q in exam_config.get('questions', []):
                qid = str(q['id'])
                st.markdown(f"**{q['text']}** ({q['points']} pts)")
                if q['type'] == 'code': st.session_state.codes[qid] = st.text_area("Code", key=f"c_{qid}")
                else: st.session_state.answers[qid] = st.text_input("Réponse", key=f"t_{qid}")
            
            if st.form_submit_button("TERMINER"):
                score = 0
                max_score = 0
                for q in exam_config.get('questions', []):
                    pts = q['points']; max_score += pts
                    qid = str(q['id'])
                    if q['type'] == 'code':
                        if len(st.session_state.codes.get(qid,"")) > 10: score += pts
                    elif str(st.session_state.answers.get(qid,"")).lower() == str(q['correct']).lower():
                        score += pts
                
                final_score = max(0, score - (st.session_state.cheats * 3))
                get_col('results').add({
                    "username": st.session_state.user['username'],
                    "name": st.session_state.user['name'],
                    "score": final_score,
                    "answers": st.session_state.answers, "codes": st.session_state.codes,
                    "cheats": st.session_state.cheats,
                    "timestamp": time.time()
                })
                st.success("Envoyé !"); time.sleep(2); st.session_state.page = "👤 Espace Candidat"; st.rerun()

def login_view():
    show_header()
    st.markdown('<div style="max-width:500px; margin:auto;">', unsafe_allow_html=True)
    st.markdown('<h2 style="text-align:center; color:white;">Authentification Sécurisée</h2>', unsafe_allow_html=True)
    u = st.text_input("Identifiant ARS")
    p = st.text_input("Mot de passe", type="password")
    if st.button("ACCÉDER"):
        if u == "admin" and p == "admin": 
            st.session_state.user = {"name": "Admin", "role": "teacher", "username": "admin"}
            st.session_state.page = "📊 Tableau de Bord"; st.rerun()
        try:
            docs = get_col('users').where('username', '==', u).where('password', '==', p).get()
            if docs: 
                st.session_state.user = docs[0].to_dict()
                st.session_state.page = "👤 Espace Candidat"; st.rerun()
            else: st.error("Erreur login")
        except: st.error("Erreur technique")
    st.markdown('</div>', unsafe_allow_html=True)

# --- ROUTAGE ---
pages = ["🏠 Accueil", "ℹ️ Infos", "❓ FAQ"]
if st.session_state.user:
    if st.session_state.user.get('role') == 'teacher': pages.append("📊 Tableau de Bord")
    else: pages.append("👤 Espace Candidat")
    pages.append("🚪 Déconnexion")
else: pages.append("🔐 Connexion")

try:
    from streamlit_navigation_bar import st_navbar
    styles = {
        "nav": {"background-color": "#112240", "justify-content": "center"},
        "span": {"color": "white"},
        "active": {"background-color": "#f57c00", "color": "white"}
    }
    selected_page = st_navbar(pages, styles=styles, options={"show_menu":False})
except:
    st.markdown('<div class="nav-fallback">', unsafe_allow_html=True)
    cols = st.columns(len(pages))
    selected_page = st.session_state.page
    for i, p in enumerate(pages):
        with cols[i]: 
            if st.button(p, key=f"n_{p}", use_container_width=True): selected_page = p
    st.markdown('</div>', unsafe_allow_html=True)

if selected_page == "🚪 Déconnexion": st.session_state.user=None; st.session_state.page="🏠 Accueil"; st.rerun()
elif selected_page != st.session_state.page: st.session_state.page = selected_page; st.rerun()

p = st.session_state.page
if p == '📊 Tableau de Bord': teacher_dash()
elif p == 'exam': exam_view()
elif p == 'ℹ️ Infos': info_view()
elif p == '❓ FAQ': faq_view()
elif p == '👤 Espace Candidat': 
    show_header()
    if st.session_state.exam_open:
        if st.button("🚀 LANCER L'EXAMEN"): st.session_state.page = "exam"; st.rerun()
    else: st.warning("Session fermée")
elif p == '🔐 Connexion': login_view()
else: 
    show_header()
    st.markdown('<div class="white-card"><h2 style="color:#0a192f">Bienvenue sur ASR Pro</h2></div>', unsafe_allow_html=True)
