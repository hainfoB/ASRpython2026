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
st.components.v1.html("""
    <script>
    document.addEventListener('contextmenu', event => event.preventDefault());
    document.addEventListener('copy', e => e.preventDefault());
    document.addEventListener('paste', e => e.preventDefault());
    
    function killSecurityButton() {
        const buttons = window.parent.document.querySelectorAll('button');
        buttons.forEach(btn => {
            if (btn.innerText.includes('INTEGRITY_TRIGGER')) {
                const container = btn.closest('div[data-testid="stButton"]');
                if (container) {
                    container.style.position = 'absolute';
                    container.style.left = '-9999px';
                    container.style.top = '-9999px';
                    container.style.visibility = 'hidden';
                }
            }
        });
    }

    window.addEventListener('blur', function() {
        const buttons = window.parent.document.querySelectorAll('button');
        for (let btn of buttons) {
            if (btn.innerText.includes('INTEGRITY_TRIGGER')) {
                btn.click();
                break;
            }
        }
    });

    setInterval(killSecurityButton, 400);
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

    [data-testid="stSidebar"] { 
        background-color: var(--navy) !important; 
        border-right: 1px solid rgba(255,255,255,0.05) !important;
    }
    
    /* STYLE DES BOUTONS DU CONTENU (ORANGE FONCÉ, TEXTE BLANC, HOVER CLAIR) */
    .stButton > button, [data-testid="stFormSubmitButton"] > button, .stDownloadButton > button {
        background-color: var(--orange-dark) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        height: 50px !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover, .stDownloadButton > button:hover {
        background-color: var(--orange-light) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(245, 124, 0, 0.4) !important;
    }

    /* MENU LATÉRAL (ON GARDE LE DESIGN RECTANGULAIRE DEMANDÉ) */
    [data-testid="stSidebar"] button {
        width: 100% !important;
        background-color: transparent !important;
        color: rgba(255,255,255,0.7) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 4px !important; 
        padding: 12px 15px !important;
        text-align: left !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        margin-bottom: 8px !important;
        text-transform: none !important;
        height: auto !important;
    }

    [data-testid="stSidebar"] button:hover {
        background-color: rgba(245, 124, 0, 0.1) !important;
        color: var(--orange-light) !important;
        border-color: var(--orange-light) !important;
        padding-left: 20px !important;
    }

    .menu-login-btn button {
        background-color: var(--orange-light) !important;
        color: white !important;
        border: none !important;
        margin-top: 15px !important;
        text-align: center !important;
        font-weight: 800 !important;
    }

    /* RESTAURATION DU DESIGN ÉLITE (TEXTES ET CARTES) */
    .hb-logo {
        width: 80px;
        height: 80px;
        background: white;
        border: 6px solid var(--orange-light);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--hb-blue);
        font-weight: 900;
        font-size: 2.2rem;
        box-shadow: 0 0 20px rgba(245, 124, 0, 0.5);
    }

    [data-testid="stAlert"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid var(--orange-light) !important;
    }
    [data-testid="stAlert"] p {
        color: white !important;
        font-size: 1.6rem !important;
        font-weight: 600 !important;
    }

    .stMarkdown p, .stRadio label, .stRadio div p {
        color: var(--white) !important;
        font-size: 1.8rem !important; 
        font-weight: 700 !important;
    }
    
    h4, [data-testid="stWidgetLabel"] p {
        font-size: 2.2rem !important;
        color: var(--orange-light) !important;
        font-weight: 900 !important;
    }

    .white-card, [data-testid="stMetric"], .report-card {
        background-color: var(--white) !important;
        padding: 30px !important;
        border-radius: 12px !important;
        border-left: 12px solid var(--orange-light) !important;
        color: var(--midnight) !important;
    }
    .white-card *, .report-card * { color: var(--midnight) !important; }

    .capacity-bright {
        background: linear-gradient(135deg, #fffbeb 0%, #fff7ed 100%) !important;
        border: 4px solid #fbbf24 !important;
        padding: 40px !important;
        border-radius: 20px !important;
        color: #92400e !important;
        font-size: 2.4rem !important; 
        font-weight: 900 !important;
        text-align: center;
    }

    /* FOOTER ARTISTIQUE PLEINE LARGEUR */
    .footer-wrapper {
        width: 100vw;
        position: relative;
        left: 50%;
        right: 50%;
        margin-left: -50vw;
        margin-right: -50vw;
        background-color: var(--navy);
        border-top: 8px solid var(--orange-light);
        margin-top: 80px;
        padding: 60px 0;
    }
    .footer-content {
        max-width: 1200px;
        margin: 0 auto;
        text-align: center;
        color: white;
    }

    div[data-testid="stButton"]:has(button:contains("INTEGRITY_TRIGGER")) {
        display: none !important;
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
                st.error("⚠️ Configuration Firebase non détectée.")
                st.stop()
    except Exception as e:
        st.error(f"❌ Erreur Firebase: {e}")
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

# BOUTON SÉCURITÉ (MASQUÉ)
if st.button("INTEGRITY_TRIGGER", key="cheat_trigger"):
    st.session_state.cheats += 1

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
        self.cell(0, 10, "TOUS DROITS RÉSERVÉS © 2026 - INSFP BBA 01 - HAITHEM BERKANE", 0, 0, 'C')

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

# --- 7. DONNÉES EXAMEN ---
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
            <h1 style="color:#f57c00; font-size:2.4rem; margin:10px 0; font-weight:900;">Institut National Spécialisé Belazzoug Athmane BBA 01</h1>
            <p style="font-weight:700; color:white; margin-top:10px; letter-spacing:5px;">PLATEFORME D'EXAMEN ASR PRO</p>
        </div>
    """, unsafe_allow_html=True)

def show_footer():
    st.markdown("""
        <div class="footer-wrapper">
            <div class="footer-content">
                <div class="footer-hb" style="width:65px; height:65px; background:white; border:4px solid #f57c00; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; color:#0047AB; font-weight:900; font-size:1.6rem; margin-bottom:20px; box-shadow:0 4px 15px rgba(0,0,0,0.3);">HB</div>
                <h2 style="color:white !important; margin-bottom:15px; font-weight:900; letter-spacing:1px;">RÉALISÉ PAR HAITHEM BERKANE | TOUS DROITS RÉSERVÉS © 2026</h2>
                <div style="font-size:1.3rem; font-weight:700; opacity:0.95; margin-bottom:10px;">Institut National Spécialisé Belazzoug Athmane BBA 01</div>
                <p style="font-size:1rem; opacity:0.7; font-weight:400;">Ministère de la Formation et de l'Enseignement Professionnels 🇩🇿</p>
                <div style="height:4px; background:#f57c00; width:200px; margin:35px auto; border-radius:10px;"></div>
                <p style="font-size:1rem; opacity:0.7; font-weight:400;">République Algérienne Démocratique et Populaire 🇩🇿</p>
                
                
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
                        <div style="padding:10px; border-radius:5px; border-left:4px solid {color}; margin-bottom:10px; background:rgba(255,255,255,0.03);">
                            <small style="color:gray;">{q['text']}</small><br>
                            <span style="color:{color}; font-weight:bold;">Saisi : {user_ans}</span><br>
                            <small style="color:gray;">Attendu : {q['correct']}</small>
                        </div>
                    """, unsafe_allow_html=True)
            with col_c:
                st.markdown("#### 💻 Script Python Implémenté")
                code = data.get('codes', {}).get(str(ex['id']), "")
                cpm = data.get('cpm_data', {}).get(str(ex['id']), 0)
                if cpm > 300: st.error(f"🚩 Alerte Plagiat / IA probable ({int(cpm)} CPM)")
                else: st.info(f"🟢 Saisie normale ({int(cpm)} CPM)")
                st.code(code, "python")

def teacher_dash():
    show_header()
    u_docs = get_col('users').where('role', '==', 'student').get()
    r_docs = get_col('results').get()
    u_list = [u.to_dict() for u in u_docs]; r_list = [r.to_dict() for r in r_docs]
    t1, t2, t3 = st.tabs(["📊 ANALYSE STATISTIQUE", "👥 GESTION SECTION", "📑 AUDIT DES COPIES"])
    
    with t1:
        st.markdown("### 🔒 Contrôle Administratif")
        cl1, cl2 = st.columns([2, 1])
        cl1.info(f"État actuel : **{'OUVERT' if st.session_state.exam_open else 'FERMÉ'}**")
        if cl2.button("BASQUER ÉTAT SESSION"):
            ns = not st.session_state.exam_open
            db.collection('artifacts').document(PROJET_ID).collection('public').document('data').collection('settings').document('status').update({'is_open': ns})
            st.session_state.exam_open = ns; st.rerun()
            
        st.divider(); col_m = st.columns(4)
        col_m[0].metric("Inscrits", len(u_list)); col_m[1].metric("Présents", len(r_list))
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
            up_f = st.file_uploader("🚀 IMPORTER SECTION", type=['xlsx'])
            if up_f and st.button("LANCER IMPORTATION"):
                df = pd.read_excel(up_f)
                for name in df.iloc[:, 0].dropna():
                    uid = name.lower().replace(" ", ".") + str(random.randint(10,99))
                    get_col('users').add({"name": name, "username": uid, "password": generate_pw(), "role": "student"})
                st.rerun()
        with c_i2:
            if u_list: st.download_button("📥 GÉNÉRER FICHES ACCÈS (PDF)", generate_pdf_credentials(u_list), "Acces_ASR.pdf")
            st.dataframe(pd.DataFrame(u_list)[['name', 'username', 'password']], use_container_width=True)
            
    with t3:
        if r_list:
            df_res = pd.DataFrame([{"ID": r.id, "Nom": r.to_dict()['name'], "Note": r.to_dict()['score'], "Alertes": r.to_dict().get('cheats',0)} for r in r_docs])
            sel = st.dataframe(df_res.drop(columns=["ID"]), use_container_width=True, on_select="rerun", selection_mode="single-row")
            if sel and sel.selection.rows:
                doc_t = r_docs[sel.selection.rows[0]]; data = doc_t.to_dict()
                st.markdown(f'<div class="report-card"><h2>COPIE : {data["name"]}</h2><h1>{data["score"]} / 20</h1></div>', unsafe_allow_html=True)
                new_s = st.number_input("Ajuster Note :", 0.0, 20.0, float(data['score']), 0.25)
                if st.button("SAUVEGARDER"):
                    get_col('results').document(doc_t.id).update({"score": new_s}); st.success("Mis à jour !"); time.sleep(1); st.rerun()
                st.divider(); audit_results_detailed(data)
    show_footer()

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
            st.session_state.page = "student_dash"; st.rerun()

def login_view():
    show_header()
    st.markdown('<div class="white-card" style="max-width:500px; margin:auto;">', unsafe_allow_html=True)
    st.markdown('<h2 style="text-align:center; margin-bottom:30px; font-weight:900;">Authentification Sécurisée</h2>', unsafe_allow_html=True)
    u = st.text_input("Identifiant ARS")
    p = st.text_input("Mot de passe", type="password")
    if st.button("ACCÉDER À LA SESSION"):
        if u == "admin" and p == "admin": st.session_state.user = {"name": "Administrateur", "role": "teacher", "username": "admin"}; st.session_state.page = "teacher"; st.rerun()
        docs = get_col('users').where('username', '==', u).where('password', '==', p).get()
        if docs: st.session_state.user = docs[0].to_dict(); st.session_state.page = "student_dash"; st.rerun()
        else: st.error("Identifiants incorrects.")
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
                Veuillez utiliser le menu latéral pour vous identifier et accéder à votre terminal d'examen.
            </p>
        </div>
    """, unsafe_allow_html=True); show_footer()

# --- 9. ROUTAGE ET MENU ---
with st.sidebar:
    st.markdown('<div class="hb-logo-container" style="display:flex; justify-content:center; margin-bottom:30px;"><div class="hb-logo">HB</div></div>', unsafe_allow_html=True)
    if st.button("🏠 ACCUEIL"): st.session_state.page = 'accueil'; st.rerun()
    if st.button("ℹ️ INFO"): st.session_state.page = 'info'; st.rerun()
    if st.button("❓ FAQ"): st.session_state.page = 'faq'; st.rerun()
    
    st.markdown('<div style="margin:20px 0; border-top:1px solid rgba(255,255,255,0.1);"></div>', unsafe_allow_html=True)
    if not st.session_state.user:
        st.markdown('<div class="menu-login-btn">', unsafe_allow_html=True)
        if st.button("🔐 SE CONNECTER"): st.session_state.page = 'login'; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<p style="text-align:center; color:#f57c00; font-weight:800;">{st.session_state.user["name"]}</p>', unsafe_allow_html=True)
        if st.button("🚪 DÉCONNEXION"): st.session_state.user = None; st.session_state.page = 'accueil'; st.rerun()

p = st.session_state.page
if p == 'teacher': teacher_dash()
elif p == 'exam': exam_view()
elif p == 'student_dash': student_dash()
elif p == 'login': login_view()
elif p == 'info': show_header(); st.markdown('<div class="white-card"><h2>Modalités</h2><p>Le barème favorise l\'implémentation (4/5) et la théorie (1/5).</p></div>', unsafe_allow_html=True); show_footer()
elif p == 'faq': show_header(); st.markdown('<div class="white-card"><h2>FAQ</h2><p>Perte de focus = -3 points.</p></div>', unsafe_allow_html=True); show_footer()
else: accueil_view()
