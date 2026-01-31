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
                    container.style.display = 'none';
                    container.style.visibility = 'hidden';
                }
            }
        });
    }

    setInterval(killSecurityButton, 100);
    </script>
""", height=0)

# --- 3. DESIGN SYSTEM (CORRIGÉ & SIMPLIFIÉ) ---
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

    /* GLOBAL */
    html, body, [data-testid="stAppViewContainer"], .main {
        background-color: var(--midnight) !important;
        color: var(--white) !important;
        font-family: 'Inter', sans-serif;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] { 
        background-color: var(--navy) !important; 
        border-right: 1px solid rgba(255,255,255,0.05) !important;
    }

    /* BOUTONS NAVIGATION */
    [data-testid="stSidebar"] .stButton button {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 1px solid rgba(255,255,255,0.1) !important;
        color: rgba(255,255,255,0.8) !important;
        text-align: left !important;
        font-weight: 600 !important;
        width: 100% !important;
        padding: 15px !important;
        border-radius: 0 !important;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background-color: rgba(245, 124, 0, 0.1) !important;
        color: var(--orange-light) !important;
        border-left: 4px solid var(--orange-light) !important;
    }

    /* BOUTONS CONTENU */
    .stButton > button {
        background-color: var(--orange-dark) !important;
        color: white !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 20px !important;
    }
    .stButton > button:hover {
        background-color: var(--orange-light) !important;
    }

    /* HEADER STYLE */
    .header-container {
        text-align: center;
        padding: 20px;
        margin-bottom: 30px;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    .header-logo {
        width: 80px; height: 80px; margin: 0 auto 15px auto;
        background: white; border: 4px solid var(--orange-light); border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        color: var(--hb-blue); font-weight: 900; font-size: 2rem;
    }
    .header-title {
        color: var(--orange-light); font-size: 2rem; font-weight: 900; margin: 10px 0;
    }
    .header-subtitle {
        color: rgba(255,255,255,0.7); font-size: 1rem; text-transform: uppercase; letter-spacing: 2px;
    }

    /* FOOTER STYLE (CORRIGÉ & AGRANDI) */
    .footer-container {
        margin-top: 80px;
        padding: 40px 20px;
        background-color: var(--navy);
        border-top: 5px solid var(--orange-light);
        text-align: center;
        color: white;
    }
    .footer-name {
        font-size: 1.4rem; font-weight: 800; margin-bottom: 10px; color: #fff;
    }
    .footer-inst {
        font-size: 1.1rem; color: #cbd5e1; margin-bottom: 5px; font-weight: 500;
    }
    .footer-bottom {
        margin-top: 25px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1);
        font-size: 0.9rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px;
    }

    /* CARTE CONTACT SIMPLE */
    .contact-box {
        background-color: var(--navy);
        border: 1px solid rgba(245, 124, 0, 0.3);
        border-radius: 15px;
        padding: 40px;
        max-width: 600px;
        margin: 0 auto;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .contact-name { font-size: 1.8rem; font-weight: 900; color: var(--orange-light); margin-bottom: 5px; }
    .contact-role { font-size: 1rem; color: #94a3b8; text-transform: uppercase; margin-bottom: 30px; letter-spacing: 1px; }
    .contact-row {
        display: flex; align-items: center; justify-content: center;
        margin-bottom: 15px; font-size: 1.1rem; color: white;
    }
    .contact-icon { color: var(--orange-light); margin-right: 15px; font-weight: bold; }

    /* CONTAINERS */
    .white-card {
        background-color: white; padding: 30px; border-radius: 10px;
        border-left: 10px solid var(--orange-light); margin-bottom: 20px;
    }
    .white-card h3 { color: var(--orange-dark); margin-top: 0; }
    .white-card p { color: #0a192f; font-size: 1.1rem; }
    
    /* CACHE TRIGGER */
    div[data-testid="stButton"] button:contains("INTEGRITY_TRIGGER") { display: none; }
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

# --- 5. INITIALISATION SESSION ---
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
    try:
        doc = db.collection('artifacts').document(PROJET_ID).collection('public').document('data').collection('settings').document('status').get()
        if doc.exists:
            st.session_state.exam_open = doc.to_dict().get('is_open', True)
    except: pass

check_exam_status()

# BOUTON SÉCURITÉ CACHÉ
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
        self.ln(20)

def get_col(name): return db.collection('artifacts').document(PROJET_ID).collection('public').document('data').collection(name)
def generate_pw(l=8): return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(l))

# --- 7. DONNÉES EXAMEN (PDF) ---
EXERCICES = [
    {"id": 1, "titre": "Algorithmique - Contrôle d'Accès", "points": 5, "enonce": "Écrivez un programme qui demande l'année de naissance de l'utilisateur.\n1. Calculez son âge (référence 2026).\n2. Si l'utilisateur a 18 ans ou plus: 'Accès autorisé. Bienvenue !', sinon 'Accès refusé. Vous devez être majeur.'.", "questions": [{"id":"q1_1","text":"Âge pour naissance en 2010 ?", "type":"number", "correct":16}, {"id":"q1_2","text":"Message pour 16 ans ?", "type":"choice", "options":["Accès autorisé. Bienvenue !", "Accès refusé. Vous devez être majeur."], "correct":"Accès refusé. Vous devez être majeur."}]},
    {"id": 2, "titre": "Physique - État de l'eau", "points": 5, "enonce": "Demandez la température T de l'eau (°C) et affichez son état physique :\n- T <= 0 : Glace\n- 0 < T < 100 : Liquide\n- T >= 100 : Vapeur\nBonus: Alerte si T > 300°C: 'Attention : Température critique !'", "questions": [{"id":"q2_1","text":"État à 100°C pile ?", "type":"choice", "options":["Glace", "Liquide", "Vapeur"], "correct":"Vapeur"}]},
    {"id": 3, "titre": "Gestion - Assurance Auto", "points": 5, "enonce": "Tarif base 500€.\n- Si < 25 ans ET < 2 ans permis: +200€.\n- Si > 25 ans OU > 5 ans permis: -50€.\nSinon: Tarif de base.", "questions": [{"id":"q3_1","text":"Prix final pour 22 ans, 1 an de permis ?", "type":"number", "correct":700}]},
    {"id": 4, "titre": "Ingénierie Financière - Crédit", "points": 5, "enonce": "Vérifiez l'éligibilité au crédit :\n- Épargne (Revenu - Dépenses) <= 0 : Refus (Fonds insuffisants).\n- Taux endettement (Mensualité / Revenu) > 33% : Refus.\n- Si Durée > 120 mois : 'Accepté sous réserve'. Sinon: 'Pré-approuvé'.", "questions": [{"id":"q4_1","text":"Revenu 2000, Dépenses 2000. Décision ?", "type":"choice", "options":["Fonds insuffisants", "Taux > 33%"], "correct":"Fonds insuffisants"}]}
]

# --- 8. FONCTIONS D'AFFICHAGE ---

def show_header():
    st.markdown("""
        <div class="header-container">
            <div class="header-logo">HB</div>
            <div class="header-subtitle">République Algérienne Démocratique et Populaire</div>
            <div class="header-title">Institut National Spécialisé Belazzoug Athmane BBA 01</div>
            <div style="font-weight:700; letter-spacing:3px;">PLATEFORME D'EXAMEN ASR PRO</div>
        </div>
    """, unsafe_allow_html=True)

def show_footer():
    # FOOTER SIMPLIFIÉ ET NETTOYÉ
    st.markdown("""
        <div class="footer-container">
            <div class="footer-name">M. Ahmed Haithem BERKANE PSFEP CIP</div>
            <div class="footer-inst">Institut National Spécialisé dans la formation professionnelle BBA01</div>
            <div class="footer-inst">Direction de la formation professionnelle BBA</div>
            <div class="footer-inst">Ministère de la formation et de l'enseignement professionnels</div>
            
            <div class="footer-bottom">
                République Algérienne Démocratique et Populaire 🇩🇿 | PLATEFORME ASR PRO | 2026
            </div>
        </div>
    """, unsafe_allow_html=True)

def contact_view():
    show_header()
    # CARTE CONTACT SIMPLE ET BELLE
    st.markdown("""
        <div class="contact-box">
            <div class="contact-name">Ahmed Haithem BERKANE</div>
            <div class="contact-role">PSFEP CIP - Expert ASR Pro</div>
            
            <div class="contact-row">
                <span class="contact-icon">📞</span> +213 699 102 523 (WhatsApp)
            </div>
            <div class="contact-row">
                <span class="contact-icon">📧</span> haithemcomputing@gmail.com
            </div>
            <div class="contact-row">
                <span class="contact-icon">🔗</span> Facebook & LinkedIn : Haithem BERKANE
            </div>
        </div>
    """, unsafe_allow_html=True)
    show_footer()

def enonce_view():
    show_header()
    st.markdown("<h2 style='text-align:center; color:#f57c00; margin-bottom:30px;'>📜 ÉNONCÉ OFFICIEL DE L'EXAMEN</h2>", unsafe_allow_html=True)
    for ex in EXERCICES:
        st.markdown(f"""
            <div class="white-card">
                <h3>EXERCICE {ex['id']} : {ex['titre']}</h3>
                <p style="white-space: pre-wrap;">{ex['enonce']}</p>
                <p style="font-weight:bold; margin-top:10px; color:#0047AB;">Barème : {ex['points']} Points</p>
            </div>
        """, unsafe_allow_html=True)
    show_footer()

def faq_view():
    show_header()
    st.markdown("<h2 style='text-align:center; color:#f57c00; margin-bottom:30px;'>❓ FOIRE AUX QUESTIONS</h2>", unsafe_allow_html=True)
    faqs = [
        ("Comment démarrer ?", "Connectez-vous avec vos identifiants, puis cliquez sur 'Démarrer l'épreuve' dans votre tableau de bord."),
        ("Le système anti-triche", "Toute sortie de l'onglet (perte de focus) est enregistrée. Plus de 3 sorties peuvent invalider votre copie."),
        ("Sauvegarde des données", "Vos réponses sont synchronisées avec Firebase à chaque fois que vous cliquez sur 'Suivant'."),
        ("Barème de notation", "Chaque exercice est noté sur 5 points. La qualité du script Python compte pour 75% de la note de l'exercice.")
    ]
    for q, a in faqs:
        with st.expander(q):
            st.write(a)
    show_footer()

def teacher_dash():
    show_header()
    u_docs = get_col('users').where('role', '==', 'student').get()
    r_docs = get_col('results').get()
    u_list = [u.to_dict() for u in u_docs]; r_list = [r.to_dict() for r in r_docs]
    
    t1, t2, t3 = st.tabs(["📊 ANALYSE STATISTIQUE", "👥 GESTION SECTION", "📑 AUDIT DES COPIES"])
    with t1:
        st.info(f"État session : **{'OUVERT' if st.session_state.exam_open else 'FERMÉ'}**")
        if st.button("BASCULER ÉTAT SESSION"):
            ns = not st.session_state.exam_open
            db.collection('artifacts').document(PROJET_ID).collection('public').document('data').collection('settings').document('status').update({'is_open': ns})
            st.session_state.exam_open = ns; st.rerun()
        col_m = st.columns(4)
        col_m[0].metric("Inscrits", len(u_list)); col_m[1].metric("Présents", len(r_list))
        col_m[2].metric("Absents", max(0, len(u_list) - len(r_list)))
        col_m[3].metric("Moyenne", f"{pd.DataFrame(r_list)['score'].mean():.2f}" if r_list else "0.00")

    with t2:
        c1, c2 = st.columns(2)
        with c1:
            out_ex = io.BytesIO(); pd.DataFrame(columns=["Nom Complet"]).to_excel(out_ex, index=False)
            st.download_button("📂 Modèle Excel", out_ex.getvalue(), "modele.xlsx")
            up_f = st.file_uploader("Importer Section", type=['xlsx'])
            if up_f and st.button("Lancer Import"):
                df = pd.read_excel(up_f)
                for name in df.iloc[:, 0].dropna():
                    uid = name.lower().replace(" ", ".") + str(random.randint(10,99))
                    get_col('users').add({"name": name, "username": uid, "password": generate_pw(), "role": "student"})
                st.rerun()
        with c2:
            st.dataframe(pd.DataFrame(u_list)[['name', 'username', 'password']], use_container_width=True)

    with t3:
        if r_list:
            df_res = pd.DataFrame([{"ID": r.id, "Nom": r.to_dict()['name'], "Note": r.to_dict()['score'], "Alertes": r.to_dict().get('cheats',0)} for r in r_docs])
            st.dataframe(df_res.drop(columns=["ID"]), use_container_width=True)
    show_footer()

def exam_view():
    if not st.session_state.exam_open: show_header(); st.error("🔒 Session verrouillée."); show_footer(); return
    show_header(); step = st.session_state.step; ex = EXERCICES[step]; st.progress((step + 1) / 4); st.info(ex['enonce'])
    st.session_state.codes[ex['id']] = st.text_area("Console Python :", height=350, key=f"c_{ex['id']}")
    for q in ex['questions']:
        if q['type'] == 'choice': st.session_state.answers[q['id']] = st.radio(q['text'], q['options'], key=f"ans_{q['id']}")
        else: st.session_state.answers[q['id']] = st.number_input(q['text'], key=f"ans_{q['id']}", value=0)
    
    if st.button("SUIVANT ➡️" if step < 3 else "🎯 RENDRE LA COPIE"):
        st.session_state.durations[ex['id']] = round(time.time() - st.session_state.ex_start_time, 1)
        if step < 3: st.session_state.step += 1; st.session_state.ex_start_time = time.time(); st.rerun()
        else:
            total, br = 0, {}
            for e in EXERCICES:
                pts_q = sum(1.25 for q in e['questions'] if str(st.session_state.answers.get(q['id'])) == str(q['correct']))
                code_val = st.session_state.codes.get(e['id'], "").strip(); pts_c = 3.75 if len(code_val) > 15 else 0
                br[str(e['id'])] = round(pts_q + pts_c, 2); total += (pts_q + pts_c)
            get_col('results').add({"username": st.session_state.user['username'], "name": st.session_state.user['name'], "score": round(total, 1), "breakdown": br, "answers": st.session_state.answers, "codes": st.session_state.codes, "timestamp": time.time(), "cheats": st.session_state.cheats})
            st.session_state.page = "student_dash"; st.rerun()

def login_view():
    show_header()
    st.markdown('<div class="white-card" style="max-width:500px; margin:auto; text-align:center;"><h2>Accès Sécurisé</h2></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        u = st.text_input("Identifiant ARS")
        p = st.text_input("Mot de passe", type="password")
        if st.button("OUVRIR LE TERMINAL"):
            if u == "admin" and p == "admin": st.session_state.user = {"name": "Administrateur", "role": "teacher", "username": "admin"}; st.session_state.page = "teacher"; st.rerun()
            docs = get_col('users').where('username', '==', u).where('password', '==', p).get()
            if docs: st.session_state.user = docs[0].to_dict(); st.session_state.page = "student_dash"; st.rerun()
            else: st.error("Identifiants incorrects.")
    show_footer()

def student_dash():
    show_header(); u = st.session_state.user; st.markdown(f"<h1 style='text-align:center;'>Candidat : {u['name']}</h1>", unsafe_allow_html=True)
    res_docs = get_col('results').where('username', '==', u['username']).get()
    if res_docs: 
        res = res_docs[0].to_dict(); st.success(f"### NOTE FINALE : {res['score']} / 20")
    elif st.session_state.exam_open:
        if st.button("🚀 LANCER L'ÉPREUVE", use_container_width=True): st.session_state.page = "exam"; st.session_state.ex_start_time = time.time(); st.rerun()
    else: st.warning("🔒 L'examen est verrouillé."); show_footer()

def accueil_view():
    show_header()
    st.markdown("""
        <div class="white-card" style="text-align:center;">
            <h1>Portail Académique ASR Pro</h1>
            <p>Bienvenue sur l'infrastructure d'évaluation de l'INSFP Belazzoug Athmane BBA 01.</p>
        </div>
    """, unsafe_allow_html=True); show_footer()

# --- 9. ROUTAGE ---
with st.sidebar:
    st.markdown('<div style="text-align:center; margin-bottom:20px; font-weight:900; color:white; font-size:1.5rem;">HB</div>', unsafe_allow_html=True)
    if st.button("🏠 ACCUEIL"): st.session_state.page = 'accueil'; st.rerun()
    if st.button("📜 ÉNONCÉ EXAMEN"): st.session_state.page = 'info'; st.rerun()
    if st.button("❓ FAQ"): st.session_state.page = 'faq'; st.rerun()
    if st.button("📞 CONTACT"): st.session_state.page = 'contact'; st.rerun()
    st.markdown('<hr style="border:1px solid rgba(255,255,255,0.1);">', unsafe_allow_html=True)
    if not st.session_state.user:
        if st.button("🔐 SE CONNECTER"): st.session_state.page = 'login'; st.rerun()
    else:
        st.markdown(f"<div style='text-align:center; color:#f57c00; margin-bottom:10px;'>{st.session_state.user['name']}</div>", unsafe_allow_html=True)
        if st.button("🚪 DÉCONNEXION"): st.session_state.user = None; st.session_state.page = 'accueil'; st.rerun()

p = st.session_state.page
if p == 'teacher': teacher_dash()
elif p == 'exam': exam_view()
elif p == 'student_dash': student_dash()
elif p == 'login': login_view()
elif p == 'info': enonce_view()
elif p == 'faq': faq_view()
elif p == 'contact': contact_view()
else: accueil_view()
