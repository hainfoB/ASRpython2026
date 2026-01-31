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
                    container.style.position = 'fixed';
                    container.style.left = '-9999px';
                    container.style.top = '-9999px';
                    container.style.opacity = '0';
                    container.style.pointerEvents = 'none';
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

    setInterval(killSecurityButton, 100);
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
    
    /* STYLE DES BOUTONS DU CONTENU */
    .stButton > button, [data-testid="stFormSubmitButton"] > button, .stDownloadButton > button {
        background-color: var(--orange-dark) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        height: 55px !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        background-color: var(--orange-light) !important;
        box-shadow: 0 4px 15px rgba(245, 124, 0, 0.4) !important;
    }

    /* MENU LATÉRAL */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0px !important;
        padding: 0px !important;
    }

    [data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        background-color: transparent !important;
        color: rgba(255,255,255,0.8) !important;
        border: none !important;
        border-bottom: 1px solid rgba(255,255,255,0.05) !important;
        border-radius: 0px !important; 
        padding: 20px 15px !important;
        text-align: left !important;
        font-weight: 600 !important;
        height: 65px !important;
        margin: 0px !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(245, 124, 0, 0.1) !important;
        color: var(--orange-light) !important;
        border-left: 5px solid var(--orange-light) !important;
    }

    .menu-login-btn button {
        background-color: var(--orange-light) !important;
        color: white !important;
        margin-top: 15px !important;
        text-align: center !important;
        font-weight: 900 !important;
        border-radius: 4px !important;
    }

    /* DESIGN ÉLITE */
    .hb-logo {
        width: 85px; height: 85px; background: white; border: 6px solid var(--orange-light);
        border-radius: 50%; display: flex; align-items: center; justify-content: center;
        color: var(--hb-blue); font-weight: 900; font-size: 2.4rem; box-shadow: 0 0 25px rgba(245, 124, 0, 0.6);
    }

    .white-card, [data-testid="stMetric"], .report-card {
        background-color: var(--white) !important; padding: 35px !important; border-radius: 12px !important;
        border-left: 15px solid var(--orange-light) !important; color: var(--midnight) !important;
        margin-bottom: 20px;
    }
    .white-card *, .report-card * { color: var(--midnight) !important; }

    /* CARTE DE VISITE 4K DESIGN */
    .business-card {
        background: linear-gradient(135deg, #112240 0%, #0a192f 100%);
        border: 2px solid #f57c00;
        border-radius: 20px;
        padding: 40px;
        max-width: 600px;
        margin: 40px auto;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
    }
    .business-card::before {
        content: ""; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
        background: radial-gradient(circle, rgba(245,124,0,0.1) 0%, transparent 70%);
    }
    .card-header-logo {
        background: white; color: #0047AB; width: 60px; height: 60px;
        border-radius: 50%; display: flex; align-items: center; justify-content: center;
        font-weight: 900; font-size: 1.5rem; margin-bottom: 20px; border: 3px solid #f57c00;
    }
    .contact-item { display: flex; align-items: center; margin-bottom: 15px; color: #e2e8f0; font-size: 1.1rem; }
    .contact-icon { color: #f57c00; margin-right: 15px; font-weight: bold; width: 25px; }

    /* CACHE RADICAL DU BOUTON TRIGGER */
    #integrity-container {
        position: absolute; left: -9999px; top: -9999px; width: 1px; height: 1px; overflow: hidden;
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

# BOUTON SÉCURITÉ (PLACEMENT HORS-CHAMP)
st.markdown('<div id="integrity-container">', unsafe_allow_html=True)
if st.button("INTEGRITY_TRIGGER", key="cheat_trigger"):
    st.session_state.cheats += 1
st.markdown('</div>', unsafe_allow_html=True)

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

# --- 7. DONNÉES EXAMEN ---
EXERCICES = [
    {"id": 1, "titre": "Algorithmique - Contrôle d'Accès", "points": 5, "enonce": "Écrivez un programme qui demande l'année de naissance de l'utilisateur.\n1. Calculez son âge (référence 2026).\n2. Si l'utilisateur a 18 ans ou plus: 'Accès autorisé. Bienvenue !', sinon 'Accès refusé. Vous devez être majeur.'.", "questions": [{"id":"q1_1","text":"Âge pour naissance en 2010 ?", "type":"number", "correct":16}, {"id":"q1_2","text":"Message pour 16 ans ?", "type":"choice", "options":["Accès autorisé. Bienvenue !", "Accès refusé. Vous devez être majeur."], "correct":"Accès refusé. Vous devez être majeur."}]},
    {"id": 2, "titre": "Physique - État de l'eau", "points": 5, "enonce": "Demandez la température T de l'eau (°C) et affichez son état physique :\n- T <= 0 : Glace\n- 0 < T < 100 : Liquide\n- T >= 100 : Vapeur\nBonus: Alerte si T > 300°C: 'Attention : Température critique !'", "questions": [{"id":"q2_1","text":"État à 100°C pile ?", "type":"choice", "options":["Glace", "Liquide", "Vapeur"], "correct":"Vapeur"}]},
    {"id": 3, "titre": "Gestion - Assurance Auto", "points": 5, "enonce": "Tarif base 500€.\n- Si < 25 ans ET < 2 ans permis: +200€.\n- Si > 25 ans OU > 5 ans permis: -50€.\nSinon: Tarif de base.", "questions": [{"id":"q3_1","text":"Conducteur de 22 ans, 1 an permis. Prix final ?", "type":"number", "correct":700}]},
    {"id": 4, "titre": "Ingénierie Financière - Crédit", "points": 5, "enonce": "Vérifiez l'éligibilité au crédit :\n- Épargne (Revenu - Dépenses) <= 0 : Refus (Fonds insuffisants).\n- Taux endettement (Mensualité / Revenu) > 33% : Refus.\n- Si Durée > 120 mois : 'Accepté sous réserve'. Sinon: 'Pré-approuvé'.", "questions": [{"id":"q4_1","text":"Revenu 2000, Dépenses 2000. Décision ?", "type":"choice", "options":["Fonds insuffisants", "Taux > 33%"], "correct":"Fonds insuffisants"}]}
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
                <h2 style="color:white !important; margin-bottom:15px; font-weight:900; letter-spacing:1px;">RÉALISÉ PAR HAITHEM BERKANE</h2>
                <div style="font-size:1.3rem; font-weight:700; opacity:0.95; margin-bottom:10px;">Institut National Spécialisé Belazzoug Athmane BBA 01</div>
                <div style="height:4px; background:#f57c00; width:200px; margin:35px auto; border-radius:10px;"></div>
                <p style="font-size:0.85rem; opacity:0.5; letter-spacing:1px;">TOUS DROITS RÉSERVÉS © 2026</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

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
            st.dataframe(pd.DataFrame(u_list)[['name', 'username', 'password']], use_container_width=True)
            
    with t3:
        if r_list:
            df_res = pd.DataFrame([{"ID": r.id, "Nom": r.to_dict()['name'], "Note": r.to_dict()['score'], "Alertes": r.to_dict().get('cheats',0)} for r in r_docs])
            st.dataframe(df_res.drop(columns=["ID"]), use_container_width=True)
    show_footer()

def exam_view():
    if not st.session_state.exam_open: show_header(); st.error("🔒 Session verrouillée."); show_footer(); return
    show_header(); step = st.session_state.step; ex = EXERCICES[step]; st.progress((step + 1) / 4); st.info(ex['enonce'])
    st.session_state.codes[ex['id']] = st.text_area("Console Python :", height=380, key=f"c_{ex['id']}")
    for q in ex['questions']:
        if q['type'] == 'choice': st.session_state.answers[q['id']] = st.radio(q['text'], q['options'], key=f"ans_{q['id']}")
        else: st.session_state.answers[q['id']] = st.number_input(q['text'], key=f"ans_{q['id']}", value=0)
    
    if st.button("SUIVANT ➡️" if step < 3 else "🎯 RENDRE LA COPIE"):
        st.session_state.durations[ex['id']] = round(time.time() - st.session_state.ex_start_time, 1)
        if step < 3: st.session_state.step += 1; st.session_state.ex_start_time = time.time(); st.rerun()
        else:
            total, br, cpm_d = 0, {}, {}
            for e in EXERCICES:
                pts_q = sum(1.25 for q in e['questions'] if str(st.session_state.answers.get(q['id'])) == str(q['correct']))
                code_val = st.session_state.codes.get(e['id'], "").strip(); pts_c = 3.75 if len(code_val) > 15 else 0
                br[str(e['id'])] = round(pts_q + pts_c, 2); total += (pts_q + pts_c)
            get_col('results').add({"username": str(st.session_state.user['username']), "name": str(st.session_state.user['name']), "score": round(total, 1), "breakdown": br, "answers": st.session_state.answers, "codes": {str(k):v for k,v in st.session_state.codes.items()}, "timestamp": time.time(), "cheats": st.session_state.cheats})
            st.session_state.page = "student_dash"; st.rerun()

def login_view():
    show_header()
    st.markdown('<div class="white-card" style="max-width:550px; margin:auto;">', unsafe_allow_html=True)
    st.markdown('<h2 style="text-align:center; margin-bottom:30px; font-weight:900;">Accès Sécurisé</h2>', unsafe_allow_html=True)
    u = st.text_input("Identifiant ARS")
    p = st.text_input("Mot de passe", type="password")
    if st.button("OUVRIR LE TERMINAL"):
        if u == "admin" and p == "admin": st.session_state.user = {"name": "Administrateur", "role": "teacher", "username": "admin"}; st.session_state.page = "teacher"; st.rerun()
        docs = get_col('users').where('username', '==', u).where('password', '==', p).get()
        if docs: st.session_state.user = docs[0].to_dict(); st.session_state.page = "student_dash"; st.rerun()
        else: st.error("Identifiants incorrects.")
    st.markdown('</div>', unsafe_allow_html=True); show_footer()

def student_dash():
    show_header(); u = st.session_state.user; st.markdown(f"<h1>Candidat : {u['name']}</h1>", unsafe_allow_html=True)
    res_docs = get_col('results').where('username', '==', u['username']).get()
    if res_docs: 
        res = res_docs[0].to_dict(); st.success(f"### NOTE FINALE : {res['score']} / 20")
    elif st.session_state.exam_open:
        if st.button("🚀 LANCER L'ÉPREUVE"): st.session_state.page = "exam"; st.session_state.ex_start_time = time.time(); st.rerun()
    else: st.warning("🔒 L'examen est verrouillé."); show_footer()

def accueil_view():
    show_header()
    st.markdown("""
        <div class="white-card">
            <h1 style="font-weight:900; margin-bottom:20px;">Portail Académique ASR Pro</h1>
            <p style="font-size:1.4rem; line-height:1.6; color:#444;">
                Bienvenue sur l'infrastructure d'évaluation de l'INSFP Belazzoug Athmane BBA 01.<br><br>
                Ce système gère en temps réel vos scripts Python et vos réponses théoriques sous haute surveillance d'intégrité.
            </p>
        </div>
    """, unsafe_allow_html=True); show_footer()

def enonce_view():
    show_header()
    st.markdown("<h2 style='text-align:center;'>📜 ÉNONCÉ OFFICIEL DE L'EXAMEN</h2>", unsafe_allow_html=True)
    for ex in EXERCICES:
        st.markdown(f"""
            <div class="white-card">
                <h3 style="color:#c2410c;">EXERCICE {ex['id']} : {ex['titre']}</h3>
                <p style="font-size:1.1rem; white-space:pre-wrap;">{ex['enonce']}</p>
                <p style="font-weight:bold; color:#0047AB;">Barème : {ex['points']} Points</p>
            </div>
        """, unsafe_allow_html=True)
    show_footer()

def faq_view():
    show_header()
    st.markdown("<h2 style='text-align:center;'>❓ FOIRE AUX QUESTIONS</h2>", unsafe_allow_html=True)
    faqs = [
        ("Comment démarrer ?", "Connectez-vous avec vos identifiants, puis cliquez sur 'Démarrer l'épreuve' dans votre tableau de bord."),
        ("Le système anti-triche", "Toute sortie de l'onglet (perte de focus) est enregistrée. Plus de 3 sorties peuvent invalider votre copie."),
        ("Sauvegarde des données", "Vos réponses sont synchronisées avec Firebase à chaque fois que vous cliquez sur 'Suivant'."),
        ("Barème de notation", "Chaque exercice est noté sur 5 points. La qualité du script Python compte pour 75% de la note de l'exercice."),
        ("Résultats", "Votre note s'affiche instantanément après la soumission finale, sauf si l'enseignant décide de l'ajuster.")
    ]
    for q, a in faqs:
        with st.expander(q):
            st.write(a)
    show_footer()

def contact_view():
    show_header()
    st.markdown(f"""
        <div class="business-card">
            <div class="card-header-logo">HB</div>
            <h2 style="color:#f57c00; margin-bottom:5px; font-weight:900; font-size:1.8rem;">Haithem BERKANE</h2>
            <p style="color:#94a3b8; font-weight:700; margin-bottom:30px; text-transform:uppercase; letter-spacing:2px;">Enseignant Expert - ASR Pro</p>
            
            <div class="contact-item">
                <span class="contact-icon">📱</span> +213 699 102 523 (WhatsApp)
            </div>
            <div class="contact-item">
                <span class="contact-icon">📧</span> haithemcomputing@gmail.com
            </div>
            <div class="contact-item">
                <span class="contact-icon">🔗</span> Facebook & LinkedIn : Haithem BERKANE
            </div>
            
            <div style="margin-top:40px; border-top:1px solid rgba(245,124,0,0.3); padding-top:20px; font-size:0.9rem; opacity:0.6;">
                INSFP Belazzoug Athmane BBA 01 | RADP
            </div>
        </div>
    """, unsafe_allow_html=True)
    show_footer()

# --- 9. ROUTAGE ET MENU ---
with st.sidebar:
    st.markdown('<div class="hb-logo-container" style="display:flex; justify-content:center; margin-bottom:30px;"><div class="hb-logo">HB</div></div>', unsafe_allow_html=True)
    if st.button("🏠 ACCUEIL"): st.session_state.page = 'accueil'; st.rerun()
    if st.button("📜 ÉNONCÉ EXAMEN"): st.session_state.page = 'info'; st.rerun()
    if st.button("❓ FAQ"): st.session_state.page = 'faq'; st.rerun()
    if st.button("📞 CONTACT"): st.session_state.page = 'contact'; st.rerun()
    st.markdown('<div style="margin:20px 0; border-top:1px solid rgba(255,255,255,0.1);"></div>', unsafe_allow_html=True)
    if not st.session_state.user:
        st.markdown('<div class="menu-login-btn">')
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
elif p == 'info': enonce_view()
elif p == 'faq': faq_view()
elif p == 'contact': contact_view()
else: accueil_view()
