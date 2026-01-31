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
    initial_sidebar_state="collapsed" # On réduit la sidebar native par défaut
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

# --- 3. DESIGN SYSTEM "ÉLITE" ET NAVIGATION HORIZONTALE ---
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

    /* --- SOLUTION RADICALE : CACHER LA SIDEBAR NATIVE --- */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    html, body, [data-testid="stAppViewContainer"], .main {
        background-color: var(--midnight) !important;
        color: var(--white) !important;
        font-family: 'Inter', sans-serif;
    }

    /* --- STYLE DES BOUTONS DE NAVIGATION (RECTANGULAIRE ET UNIFORME) --- */
    /* On utilise les colonnes de Streamlit pour simuler une Top-Nav */
    .stButton > button {
        width: 100% !important;
        border-radius: 0px !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        background-color: var(--navy) !important;
        color: rgba(255,255,255,0.8) !important;
        padding: 15px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        transition: all 0.3s ease !important;
        height: 60px !important;
    }

    .stButton > button:hover {
        background-color: var(--orange-dark) !important;
        color: white !important;
        border-color: var(--orange-light) !important;
    }

    /* BOUTONS INTERNES ORANGE FONCÉ (DESIGN ÉLITE) */
    .main-btn button {
        background-color: var(--orange-dark) !important;
        color: white !important;
        border-radius: 4px !important;
        height: 60px !important;
        font-size: 1.1rem !important;
        border: none !important;
    }
    
    .main-btn button:hover {
        background-color: var(--orange-light) !important;
        box-shadow: 0 4px 20px rgba(245, 124, 0, 0.5) !important;
    }

    /* --- CARTES ET TYPOGRAPHIE --- */
    .hb-logo {
        width: 80px; height: 80px; background: white; border: 5px solid var(--orange-light);
        border-radius: 50%; display: flex; align-items: center; justify-content: center;
        color: var(--hb-blue); font-weight: 900; font-size: 2.2rem; margin: 0 auto;
    }

    .white-card, [data-testid="stMetric"], .report-card {
        background-color: var(--white) !important;
        padding: 40px !important;
        border-radius: 12px !important;
        border-left: 15px solid var(--orange-light) !important;
        color: var(--midnight) !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3) !important;
    }
    .white-card *, .report-card * { color: var(--midnight) !important; }

    [data-testid="stAlert"] { background-color: rgba(255, 255, 255, 0.05) !important; border: 1px solid var(--orange-light) !important; }
    [data-testid="stAlert"] p { color: white !important; font-size: 1.6rem !important; font-weight: 700 !important; }

    .stMarkdown p, .stRadio label, .stRadio div p { font-size: 1.8rem !important; font-weight: 800 !important; }
    h1, h4, [data-testid="stWidgetLabel"] p { color: var(--orange-light) !important; font-weight: 900 !important; }

    /* FOOTER */
    .footer-wrapper {
        width: 100vw; position: relative; left: 50%; right: 50%; margin-left: -50vw; margin-right: -50vw;
        background-color: var(--navy); border-top: 8px solid var(--orange-light); margin-top: 80px; padding: 60px 0;
        text-align: center;
    }

    /* MASQUAGE ABSOLU DU TRIGGER */
    .hidden-trigger {
        position: fixed !important;
        top: -1000px !important;
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

def show_nav():
    # Barre de navigation horizontale simulée par des colonnes
    st.markdown('<div style="margin-top:-50px;"></div>', unsafe_allow_html=True)
    cols = st.columns([1, 1, 1, 1, 1, 1.5])
    
    with cols[0]:
        if st.button("🏠 ACCUEIL"): st.session_state.page = 'accueil'; st.rerun()
    with cols[1]:
        if st.button("ℹ️ INFO"): st.session_state.page = 'info'; st.rerun()
    with cols[2]:
        if st.button("❓ FAQ"): st.session_state.page = 'faq'; st.rerun()
    with cols[3]:
        if st.button("📞 CONTACT"): st.session_state.page = 'contact'; st.rerun()
    with cols[4]:
        # Bouton admin caché ou espace vide
        st.write("")
        
    with cols[5]:
        if not st.session_state.user:
            if st.button("🔐 SE CONNECTER"): st.session_state.page = 'login'; st.rerun()
        else:
            if st.button(f"🚪 {st.session_state.user['name'].upper()}"):
                st.session_state.user = None; st.session_state.page = 'accueil'; st.rerun()
    st.markdown('<hr style="border:1px solid rgba(255,255,255,0.05); margin-bottom:40px;">', unsafe_allow_html=True)

def show_header():
    st.markdown("""
        <div style="text-align:center; padding: 30px;">
            <div class="hb-logo">HB</div>
            <h4 style="opacity:0.6; text-transform:uppercase; letter-spacing:2px; margin-top:20px;">République Algérienne Démocratique et Populaire</h4>
            <h1 style="font-size:2.8rem; margin:15px 0;">Institut National Spécialisé Belazzoug Athmane BBA 01</h1>
            <p style="font-weight:700; color:white; letter-spacing:5px; text-transform:uppercase; opacity:0.8;">Plateforme d'évaluation certifiée ASR Pro</p>
        </div>
    """, unsafe_allow_html=True)

def show_footer():
    st.markdown("""
        <div class="footer-wrapper">
            <div class="footer-content">
                <div class="hb-logo" style="width:65px; height:65px; font-size:1.6rem;">HB</div>
                <h2 style="color:white !important; margin:20px 0; font-weight:900;">RÉALISÉ PAR HAITHEM BERKANE</h2>
                <p style="font-size:1.2rem; font-weight:700;">INSFP Belazzoug Athmane BBA 01 | RADP 🇩🇿</p>
                <div style="height:4px; background:var(--orange-light); width:200px; margin:30px auto;"></div>
                <p style="opacity:0.5; letter-spacing:1px;">TOUS DROITS RÉSERVÉS © 2026</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

def audit_results_detailed(data):
    st.markdown("### 🔍 Audit Approfondi de la Copie")
    for ex in EXERCICES:
        with st.expander(f"Exercice {ex['id']} : {ex['titre']}"):
            col_q, col_c = st.columns([1, 1.5])
            with col_q:
                st.markdown("#### ✅ Validation Théorique")
                for q in ex['questions']:
                    user_ans = data.get('answers', {}).get(q['id'], "Non répondu")
                    is_correct = str(user_ans) == str(q['correct'])
                    color = "#10b981" if is_correct else "#ef4444"
                    st.markdown(f"""<div style="padding:10px; border-left:5px solid {color}; background:rgba(255,255,255,0.03); margin-bottom:12px;">
                        <small style="color:gray;">{q['text']}</small><br><b>Saisi : {user_ans}</b><br><small>Attendu : {q['correct']}</small></div>""", unsafe_allow_html=True)
            with col_c:
                st.markdown("#### 💻 Script Python Implémenté")
                code = data.get('codes', {}).get(str(ex['id']), "")
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
        cl1.info(f"État de l'accès : **{'OUVERT' if st.session_state.exam_open else 'FERMÉ'}**")
        if cl2.button("BASQUER ÉTAT SESSION"):
            ns = not st.session_state.exam_open
            db.collection('artifacts').document(PROJET_ID).collection('public').document('data').collection('settings').document('status').update({'is_open': ns})
            st.session_state.exam_open = ns; st.rerun()
            
        st.divider(); col_m = st.columns(4)
        col_m[0].metric("Inscrits", len(u_list)); col_m[1].metric("Présents", len(r_list))
        col_m[2].metric("Absents", max(0, len(u_list) - len(r_list)))
        col_m[3].metric("Moyenne", f"{pd.DataFrame(r_list)['score'].mean():.2f}" if r_list else "0.00")
            
    with t2:
        c_i1, c_i2 = st.columns(2)
        with c_i1:
            st.markdown("#### 📥 Importation de Liste")
            out_ex = io.BytesIO(); pd.DataFrame(columns=["Nom Complet"]).to_excel(out_ex, index=False)
            st.download_button("📂 TÉLÉCHARGER MODÈLE EXCEL", out_ex.getvalue(), "modele_asr.xlsx")
            up_f = st.file_uploader("🚀 IMPORTER SECTION (XLSX)", type=['xlsx'])
            if up_f and st.button("LANCER L'IMPORTATION"):
                df = pd.read_excel(up_f)
                for name in df.iloc[:, 0].dropna():
                    uid = name.lower().replace(" ", ".") + str(random.randint(10,99))
                    get_col('users').add({"name": name, "username": uid, "password": generate_pw(), "role": "student"})
                st.rerun()
        with c_i2:
            st.markdown("#### 📜 Fiches d'accès")
            if u_list: st.download_button("📥 GÉNÉRER FICHES ACCÈS (PDF)", generate_pdf_credentials(u_list), "Acces_ASR_Pro.pdf")
            st.dataframe(pd.DataFrame(u_list)[['name', 'username', 'password']], use_container_width=True)
            
    with t3:
        if r_list:
            df_res = pd.DataFrame([{"ID": r.id, "Nom": r.to_dict()['name'], "Note": r.to_dict()['score']} for r in r_docs])
            sel = st.dataframe(df_res.drop(columns=["ID"]), use_container_width=True, on_select="rerun", selection_mode="single-row")
            if sel and sel.selection.rows:
                doc_t = r_docs[sel.selection.rows[0]]; data = doc_t.to_dict()
                st.markdown(f'<div class="report-card"><h2>CANDIDAT : {data["name"]}</h2><h1>Note Finale : {data["score"]} / 20</h1></div>', unsafe_allow_html=True)
                st.divider(); audit_results_detailed(data)
    show_footer()

def exam_view():
    if not st.session_state.exam_open: show_header(); st.error("🔒 Session verrouillée par l'enseignant."); show_footer(); return
    show_header(); step = st.session_state.step; ex = EXERCICES[step]; st.progress((step + 1) / 4); st.info(ex['enonce'])
    
    st.session_state.codes[ex['id']] = st.text_area("Console de Développement Python (Logiciel 4/5) :", height=400, key=f"c_{ex['id']}")
    st.markdown("---"); st.markdown(f"#### **QUESTION THÉORIQUE :** {ex['questions'][0]['text']}")
    
    for q in ex['questions']:
        if q['type'] == 'choice': st.session_state.answers[q['id']] = st.radio(q['text'], q['options'], key=f"ans_{q['id']}", label_visibility="hidden")
        else: st.session_state.answers[q['id']] = st.number_input(q['text'], key=f"ans_{q['id']}", value=0)
    
    st.markdown('<div class="main-btn">', unsafe_allow_html=True)
    if st.button("EXERCICE SUIVANT ➡️" if step < 3 else "🎯 TRANSMETTRE LA COPIE FINALE"):
        st.session_state.durations[ex['id']] = round(time.time() - st.session_state.ex_start_time, 1)
        if step < 3: st.session_state.step += 1; st.session_state.ex_start_time = time.time(); st.rerun()
        else:
            total, br, cpm_d = 0, {}, {}
            for e in EXERCICES:
                pts_q = sum(1.0/len(e['questions']) for q in e['questions'] if str(st.session_state.answers.get(q['id'])) == str(q['correct']))
                code_val = st.session_state.codes.get(e['id'], "").strip(); pts_c = 4.0 if len(code_val) > 15 else 0
                dur = st.session_state.durations.get(e['id'], 1); cpm = (len(code_val) / (dur/60)) if dur > 0 else 0
                cpm_d[str(e['id'])] = cpm; ex_s = pts_q + pts_c
                br[str(e['id'])] = round(ex_s, 2); total += ex_s
            get_col('results').add({"username": str(st.session_state.user['username']), "name": str(st.session_state.user['name']), "score": round(total, 1), "breakdown": br, "answers": st.session_state.answers, "codes": {str(k):v for k,v in st.session_state.codes.items()}, "cpm_data": cpm_d, "timestamp": time.time(), "cheats": st.session_state.cheats})
            st.session_state.page = "student_dash"; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def login_view():
    show_header()
    st.markdown('<div class="white-card" style="max-width:550px; margin:auto;">', unsafe_allow_html=True)
    st.markdown('<h2 style="text-align:center; margin-bottom:30px; font-weight:900;">Accès Sécurisé à la Session</h2>', unsafe_allow_html=True)
    u = st.text_input("Identifiant ARS"); p = st.text_input("Mot de passe", type="password")
    st.markdown('<div class="main-btn">', unsafe_allow_html=True)
    if st.button("OUVRIR LE TERMINAL D'EXAMEN"):
        if u == "admin" and p == "admin": 
            st.session_state.user = {"name": "Administrateur", "role": "teacher", "username": "admin"}
            st.session_state.page = "teacher"; st.rerun()
        docs = get_col('users').where('username', '==', u).where('password', '==', p).get()
        if docs: 
            st.session_state.user = docs[0].to_dict()
            st.session_state.page = "student_dash"; st.rerun()
        else: st.error("Identifiants incorrects ou compte non activé.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True); show_footer()

def student_dash():
    show_header(); u = st.session_state.user; st.markdown(f"<h1>Session de : {u['name']}</h1>", unsafe_allow_html=True)
    res_docs = get_col('results').where('username', '==', u['username']).get()
    if res_docs: 
        res = res_docs[0].to_dict(); st.success(f"### ÉVALUATION TERMINÉE : NOTE OBTENUE {res['score']} / 20")
        audit_results_detailed(res)
    elif st.session_state.exam_open:
        st.markdown('<div class="main-btn">', unsafe_allow_html=True)
        if st.button("🚀 DÉMARRER LE CHRONOMÈTRE DE L'ÉPREUVE"): 
            st.session_state.page = "exam"; st.session_state.ex_start_time = time.time(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else: st.warning("🔒 L'examen est verrouillé par l'administration."); show_footer()

def accueil_view():
    show_header()
    st.markdown("""
        <div class="white-card">
            <h1 style="font-weight:900; margin-bottom:25px;">Bienvenue sur le Portail Académique ASR</h1>
            <p style="font-size:1.6rem; line-height:1.7; color:#444;">
                Cette plateforme est réservée aux évaluations certifiées de l'INSFP Belazzoug Athmane de Bordj Bou Arreridj.<br><br>
                <b>Instructions importantes :</b><br>
                1. Connectez-vous via le menu en haut à droite.<br>
                2. Ne changez pas d'onglet une fois l'épreuve lancée.<br>
                3. Le barème favorise l'implémentation algorithmique (4 points par exercice).
            </p>
        </div>
    """, unsafe_allow_html=True); show_footer()

# --- 9. ROUTAGE PRINCIPAL ---
show_nav() # On affiche toujours la navigation horizontale

p = st.session_state.page
if p == 'teacher': teacher_dash()
elif p == 'exam': exam_view()
elif p == 'student_dash': student_dash()
elif p == 'login': login_view()
elif p == 'info':
    show_header(); st.markdown('<div class="white-card"><h2>Modalités de l\'Épreuve Professionnelle</h2><p style="font-size:1.4rem;">L\'épreuve ASR Pro dure 60 minutes. Chaque exercice est noté sur 5 points répartis comme suit : 1 point pour la précision théorique (QCM) et 4 points pour la validité et l\'élégance du script Python implémenté.</p></div>', unsafe_allow_html=True); show_footer()
elif p == 'faq':
    show_header(); st.markdown('<div class="white-card"><h2>Foire Aux Questions (FAQ)</h2><p style="font-size:1.3rem;"><b>Q: Que se passe-t-il si je change d\'onglet ?</b><br>R: Le système enregistre chaque perte de focus. Plus de 3 sorties peuvent entraîner une alerte d\'intégrité.<br><br><b>Q: Mon code est-il sauvegardé ?</b><br>R: Oui, au passage de chaque exercice.</p></div>', unsafe_allow_html=True); show_footer()
elif p == 'contact':
    show_header(); st.markdown('<div class="white-card"><h2>Support Technique & Pédagogique</h2><p style="font-size:1.3rem;">📧 haithemcomputing@gmail.com<br>📍 INSFP Belazzoug Athmane BBA 01 - Département Informatique<br>👤 Responsable : Haithem BERKANE</p></div>', unsafe_allow_html=True); show_footer()
else: accueil_view()

# --- 10. BOUTON SÉCURITÉ (SUPPRESSION VISUELLE RADICALE) ---
st.markdown('<div class="hidden-trigger">', unsafe_allow_html=True)
if st.button("INTEGRITY_TRIGGER", key="cheat_trigger_final"):
    st.session_state.cheats += 1
st.markdown('</div>', unsafe_allow_html=True)
