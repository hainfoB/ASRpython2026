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
    
    // Fonction pour forcer la disparition totale du bouton de sécurité
    function hideSecurityButton() {
        const buttons = window.parent.document.querySelectorAll('button');
        buttons.forEach(btn => {
            if (btn.innerText.includes('INTEGRITY_TRIGGER')) {
                const container = btn.closest('div[data-testid="stButton"]');
                if (container) {
                    container.style.position = 'absolute';
                    container.style.left = '-9999px';
                    container.style.top = '-9999px';
                    container.style.visibility = 'hidden';
                    container.style.width = '0';
                    container.style.height = '0';
                    container.style.opacity = '0';
                }
            }
        });
    }

    // Détection de perte de focus (Changement d'onglet ou fenêtre)
    window.addEventListener('blur', function() {
        const buttons = window.parent.document.querySelectorAll('button');
        for (let btn of buttons) {
            if (btn.innerText.includes('INTEGRITY_TRIGGER')) {
                btn.click();
                break;
            }
        }
    });

    // Exécution répétée pour contrer les rafraîchissements de Streamlit
    hideSecurityButton();
    setInterval(hideSecurityButton, 300);
    </script>
""", height=0)

# --- 3. DESIGN SYSTEM "ÉLITE" ET ÉLÉMENTS ARTISTIQUES ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
    
    :root {
        --midnight: #0a192f;
        --navy: #112240;
        --orange: #f57c00;
        --orange-dark: #c2410c;
        --white: #ffffff;
        --hb-blue: #0047AB;
    }

    html, body, [data-testid="stAppViewContainer"], .main {
        background-color: var(--midnight) !important;
        color: var(--white) !important;
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stSidebar"] { background-color: var(--navy) !important; }
    
    /* LOGO HB ARTISTIQUE */
    .hb-logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
    }
    .hb-logo {
        width: 80px;
        height: 80px;
        background: white;
        border: 6px solid var(--orange);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--hb-blue);
        font-weight: 900;
        font-size: 2.2rem;
        box-shadow: 0 0 20px rgba(245, 124, 0, 0.5);
    }

    /* ÉNONCÉS LISIBLES ET BLANCS */
    [data-testid="stAlert"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid var(--orange) !important;
    }
    [data-testid="stAlert"] p {
        color: white !important;
        font-size: 1.6rem !important;
        font-weight: 600 !important;
        line-height: 1.6;
    }

    /* QUESTIONS ET OPTIONS : +50%, GRAS ET BLANC */
    .stMarkdown p, .stRadio label, .stRadio div p {
        color: var(--white) !important;
        font-size: 1.8rem !important; 
        font-weight: 700 !important;
    }
    
    /* TITRE DE LA QUESTION EN ORANGE */
    h4, [data-testid="stWidgetLabel"] p {
        font-size: 2.2rem !important;
        color: var(--orange) !important;
        font-weight: 900 !important;
    }

    /* BOUTONS ORANGE STANDARDS */
    .stButton>button, [data-testid="stFormSubmitButton"]>button, .stDownloadButton>button, [data-testid="stSidebar"] button {
        width: 100% !important;
        background-color: var(--orange) !important;
        color: white !important;
        border-radius: 8px !important; 
        border: none !important;
        height: 55px !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
    }

    /* CIBLAGE CSS RADICAL POUR LE BOUTON INTEGRITY */
    div[data-testid="stButton"]:has(button:contains("INTEGRITY_TRIGGER")) {
        position: fixed !important;
        top: -1000px !important;
        left: -1000px !important;
        visibility: hidden !important;
        display: none !important;
    }

    /* CARTES ADMIN BLANCHES */
    .white-card, [data-testid="stMetric"], .report-card {
        background-color: var(--white) !important;
        padding: 30px !important;
        border-radius: 12px !important;
        border-left: 12px solid var(--orange) !important;
        color: var(--midnight) !important;
    }
    .white-card *, .report-card * { color: var(--midnight) !important; }

    /* ANALYSE DE CAPACITÉ LUMINEUSE */
    .capacity-bright {
        background: linear-gradient(135deg, #fffbeb 0%, #fff7ed 100%) !important;
        border: 4px solid #fbbf24 !important;
        padding: 40px !important;
        border-radius: 20px !important;
        color: #92400e !important;
        font-size: 2.4rem !important; 
        font-weight: 900 !important;
        text-align: center;
        box-shadow: 0 0 40px rgba(251, 191, 36, 0.5) !important;
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
        border-top: 8px solid var(--orange);
        margin-top: 80px;
        padding: 60px 0;
    }
    .footer-content {
        max-width: 1200px;
        margin: 0 auto;
        text-align: center;
        color: white;
    }
    .footer-hb {
        width: 65px;
        height: 65px;
        background: white;
        border: 4px solid var(--orange);
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: var(--hb-blue);
        font-weight: 900;
        font-size: 1.6rem;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
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
                st.error("⚠️ Configuration Firebase introuvable.")
                st.stop()
    except Exception as e:
        st.error(f"❌ Erreur Firebase: {e}")
        st.stop()

db = firestore.client()
PROJET_ID = "examen-asr-prod"

# --- 5. INITIALISATION SESSION STATE ---
def init_session():
    keys = ['user', 'page', 'step', 'answers', 'codes', 'durations', 'ex_start_time', 'cheats', 'exam_open']
    for key in keys:
        if key not in st.session_state:
            if key in ['step', 'cheats']: st.session_state[key] = 0
            elif key in ['answers', 'codes', 'durations']: st.session_state[key] = {}
            elif key == 'exam_open': st.session_state[key] = True
            else: st.session_state[key] = None

init_session()

# Synchronisation du statut de l'examen depuis Firestore
def check_exam_status():
    doc = db.collection('artifacts').document(PROJET_ID).collection('public').document('data').collection('settings').document('status').get()
    if doc.exists:
        st.session_state.exam_open = doc.to_dict().get('is_open', True)
    else:
        db.collection('artifacts').document(PROJET_ID).collection('public').document('data').collection('settings').document('status').set({'is_open': True})
        st.session_state.exam_open = True

check_exam_status()

# BOUTON DE SÉCURITÉ (Totalement délocalisé hors-écran par CSS et JS)
if st.button("INTEGRITY_TRIGGER", key="cheat_trigger"):
    st.session_state.cheats += 1
    st.toast("⚠️ Focus perdu détecté !")

# --- 6. CLASSES ET HELPERS ---
class PDF(FPDF):
    def header(self):
        # Drapeau Algérien stylisé
        self.set_fill_color(0, 102, 51); self.rect(0, 0, 105, 10, 'F')
        self.set_fill_color(255, 255, 255); self.rect(105, 0, 105, 10, 'F')
        self.set_fill_color(204, 0, 0); self.ellipse(103, 3, 4, 4, 'F')
        self.set_y(15); self.set_font('Arial', 'B', 8); self.set_text_color(0, 0, 0)
        self.cell(0, 5, "REPUBLIQUE ALGERIENNE DEMOCRATIQUE ET POPULAIRE", 0, 1, 'C')
        self.cell(0, 5, "MINISTERE DE LA FORMATION ET DE L'ENSEIGNEMENT PROFESSIONNELS", 0, 1, 'C')
        self.set_font('Arial', 'B', 7)
        self.cell(0, 5, "Institut National Spécialisé de la Formation Professionnelle Belazzoug Athmane BBA 01", 0, 1, 'C')
        self.set_draw_color(245, 124, 0); self.set_fill_color(255, 255, 255); self.ellipse(97.5, 38, 15, 15, 'DF')
        self.set_xy(97.5, 41); self.set_font('Arial', 'B', 12); self.set_text_color(0, 71, 171); self.cell(15, 10, "HB", 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-20); self.set_font('Arial', 'B', 7); self.set_text_color(150, 150, 150)
        self.cell(0, 10, "RÉALISÉ PAR HAITHEM BERKANE | Institut National Spécialisé Belazzoug Athmane BBA 01 | TOUS DROITS RÉSERVÉS", 0, 0, 'C')

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
    {"id": 2, "titre": "Physique - État de l'eau", "points": 5, "enonce": "Demandez la température T de l'eau (°C) :\n- T <= 0 : Glace\n- 0 < T < 100 : Liquide\n- T >= 100 : Vapeur\nAffichez également un message bonus si T > 300.", "questions": [{"id":"q2_1","text":"État à 100°C pile ?", "type":"choice", "options":["Glace", "Liquide", "Vapeur"], "correct":"Vapeur"}]},
    {"id": 3, "titre": "Gestion - Assurance Auto", "points": 5, "enonce": "Calculez le tarif final :\n- Base 500€.\n- Si < 25 ans ET < 2 ans de permis: +200€.\n- Si > 25 ans OU > 5 ans de permis: -50€.", "questions": [{"id":"q3_1","text":"Conducteur de 22 ans, 1 an permis. Prix final ?", "type":"number", "correct":700}]},
    {"id": 4, "titre": "Ingénierie Financière - Crédit", "points": 5, "enonce": "Vérifiez l'éligibilité :\n- Épargne (Revenu - Dépenses) <= 0 : Refus.\n- Taux endettement (Mensualité/Revenu) > 33% : Refus.\n- Sinon: Pré-approuvé.", "questions": [{"id":"q4_1","text":"Revenu 2000, Dépenses 2000. Décision ?", "type":"choice", "options":["Fonds insuffisants", "Taux > 33%"], "correct":"Fonds insuffisants"}]}
]

# --- 8. VUES ---

def show_header():
    st.markdown("""
        <div class="official-header" style="text-align:center;">
            <div class="hb-logo-container"><div class="hb-logo">HB</div></div>
            <h4 style="opacity:0.7; letter-spacing:2px; text-transform:uppercase;">République Algérienne Démocratique et Populaire</h4>
            <h1 style="color:#f57c00; font-size:2.4rem; margin:10px 0;">Institut National Spécialisé de la Formation Professionnelle Belazzoug Athmane BBA 01</h1>
            <p style="font-weight:700; color:white; margin-top:10px; letter-spacing:5px;">PLATEFORME D'EXAMEN ASR PRO</p>
        </div>
    """, unsafe_allow_html=True)

def show_footer():
    st.markdown("""
        <div class="footer-wrapper">
            <div class="footer-content">
                <div class="footer-hb">HB</div>
                <h2 style="color:white !important; margin-bottom:15px; font-weight:900; letter-spacing:1px;">RÉALISÉ PAR HAITHEM BERKANE</h2>
                <div style="font-size:1.3rem; font-weight:700; opacity:0.95; margin-bottom:10px;">
                    Institut National Spécialisé de la Formation Professionnelle Belazzoug Athmane BBA 01
                </div>
                <div style="font-size:1.1rem; font-weight:600; opacity:0.85; margin-bottom:10px;">
                    Direction de la Formation et de l'Enseignement Professionnels de Bordj Bou Arréridj
                </div>
                <div style="font-size:1rem; opacity:0.7; font-weight:400;">
                    Ministère de la Formation et de l'Enseignement Professionnels | République Algérienne Démocratique et Populaire 🇩🇿
                </div>
                <div style="height:4px; background:var(--orange); width:200px; margin:35px auto; border-radius:10px;"></div>
                <p style="font-size:0.85rem; opacity:0.5; letter-spacing:1px;">TOUS DROITS RÉSERVÉS © 2026</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

def audit_results_detailed(data):
    """Analyse pédagogique complète partagée entre le stagiaire et le professeur"""
    st.markdown("### 🔍 Analyse Pédagogique des Résultats")
    for ex in EXERCICES:
        with st.expander(f"Exercice {ex['id']} : {ex['titre']}"):
            col_q, col_c = st.columns([1, 1.5])
            with col_q:
                st.markdown("#### ✅ Validation de la Logique (QCS)")
                for q in ex['questions']:
                    user_ans = data.get('answers', {}).get(q['id'], "Non répondu")
                    is_correct = str(user_ans) == str(q['correct'])
                    color = "#10b981" if is_correct else "#ef4444"
                    st.markdown(f"""
                        <div style="padding:10px; border-radius:5px; border-left:4px solid {color}; margin-bottom:10px; background:rgba(255,255,255,0.03);">
                            <small style="color:gray;">{q['text']}</small><br>
                            <span style="color:{color}; font-weight:bold;">Saisi : {user_ans}</span><br>
                            <small style="color:gray;">Correction attendue : {q['correct']}</small>
                        </div>
                    """, unsafe_allow_html=True)
            with col_c:
                st.markdown("#### 💻 Script Python Implémenté")
                code = data.get('codes', {}).get(str(ex['id']), "")
                cpm = data.get('cpm_data', {}).get(str(ex['id']), 0)
                if cpm > 300: st.error(f"🚩 Alerte Intégrité : Vitesse de saisie anormale ({int(cpm)} CPM)")
                else: st.info(f"🟢 Saisie humaine détectée ({int(cpm)} CPM)")
                st.code(code, "python")

def teacher_dash():
    show_header()
    u_docs = get_col('users').where('role', '==', 'student').get()
    r_docs = get_col('results').get()
    u_list = [u.to_dict() for u in u_docs]; r_list = [r.to_dict() for r in r_docs]
    t1, t2, t3 = st.tabs(["📊 ANALYSE STATISTIQUE", "👥 GESTION SECTION", "📑 AUDIT DES COPIES"])
    
    with t1:
        st.markdown("### 🔒 Contrôle Administratif de la Session")
        c_l1, c_l2 = st.columns([2, 1])
        c_l1.info(f"État actuel de l'épreuve : **{'OUVERTE' if st.session_state.exam_open else 'VERROUILLÉE'}**")
        if c_l2.button("BASQUER ÉTAT DE LA SESSION"):
            ns = not st.session_state.exam_open
            db.collection('artifacts').document(PROJET_ID).collection('public').document('data').collection('settings').document('status').update({'is_open': ns})
            st.session_state.exam_open = ns; st.rerun()
            
        st.divider(); col_m = st.columns(4)
        col_m[0].metric("Inscrits", len(u_list)); col_m[1].metric("Présents", len(r_list))
        col_m[2].metric("Absents", max(0, len(u_list) - len(r_list)))
        col_m[3].metric("Moyenne Section", f"{pd.DataFrame(r_list)['score'].mean():.2f}" if r_list else "0.00")
        
        if r_list:
            df_s = pd.DataFrame(r_list); st.divider(); c_a = st.columns(3)
            with c_a[0]: st.metric("Note Maximale", f"{df_s['score'].max()} / 20")
            with c_a[1]: st.metric("Note Minimale", f"{df_s['score'].min()} / 20")
            df_br = pd.DataFrame([r['breakdown'] for r in r_list]); best_id = df_br.mean().idxmax()
            best_name = next(e['titre'] for e in EXERCICES if str(e['id']) == str(best_id))
            with c_a[2]: st.metric("Axe le mieux réussi", f"Ex {best_id}")
            st.markdown(f"""
                <div class="capacity-bright">
                    💡 ANALYSE DES CAPACITÉS MÉTIERS<br>
                    <span style="font-size:1.6rem; opacity:0.8;">L'exercice <b>'{best_name}'</b> présente le plus fort taux de réussite. Les stagiaires maîtrisent parfaitement les structures conditionnelles liées à cet axe.</span>
                </div>
            """, unsafe_allow_html=True)
            
    with t2:
        c_i1, c_i2 = st.columns(2)
        with c_i1:
            st.markdown("#### 📥 Importation de Liste")
            out_ex = io.BytesIO(); pd.DataFrame(columns=["Nom Complet"]).to_excel(out_ex, index=False)
            st.download_button("📂 TÉLÉCHARGER MODÈLE EXCEL", out_ex.getvalue(), "modele_section.xlsx")
            up_f = st.file_uploader("🚀 IMPORTER FICHIER ETUDIANTS", type=['xlsx'])
            if up_f and st.button("LANCER L'IMPORTATION MASSIVE"):
                df = pd.read_excel(up_f)
                for name in df.iloc[:, 0].dropna():
                    uid = name.lower().replace(" ", ".") + str(random.randint(10,99))
                    get_col('users').add({"name": name, "username": uid, "password": generate_pw(), "role": "student"})
                st.rerun()
        with c_i2:
            st.markdown("#### 📜 Fiches d'accès")
            if u_list: st.download_button("📥 GÉNÉRER DOCUMENT ÉMARGEMENT (PDF)", generate_pdf_credentials(u_list), "Acces_Section_ASR.pdf")
            st.dataframe(pd.DataFrame(u_list)[['name', 'username', 'password']], use_container_width=True)
            
    with t3:
        if r_list:
            df_res = pd.DataFrame([{"ID": r.id, "Nom": r.to_dict()['name'], "Note": r.to_dict()['score'], "Sorties": r.to_dict().get('cheats',0)} for r in r_docs])
            sel = st.dataframe(df_res.drop(columns=["ID"]), use_container_width=True, on_select="rerun", selection_mode="single-row")
            if sel and sel.selection.rows:
                doc_t = r_docs[sel.selection.rows[0]]; data = doc_t.to_dict()
                st.markdown(f'<div class="report-card"><h2>COPIE DE : {data["name"]}</h2><h1>{data["score"]} / 20</h1></div>', unsafe_allow_html=True)
                new_s = st.number_input("Ajustement manuel de la note :", 0.0, 20.0, float(data['score']), 0.25)
                if st.button("SAUVEGARDER L'AJUSTEMENT"):
                    get_col('results').document(doc_t.id).update({"score": new_s}); st.success("Note mise à jour !"); time.sleep(1); st.rerun()
                st.divider(); audit_results_detailed(data)
    show_footer()

def info_view():
    show_header(); st.markdown('<div class="white-card"><h1>Sujet Officiel de l\'Épreuve Professionnelle</h1>', unsafe_allow_html=True)
    for ex in EXERCICES:
        st.markdown(f'<div style="background:var(--midnight); padding:25px; border-radius:10px; margin-bottom:15px; border-left:8px solid #f57c00;"><h3 style="color:#f57c00; font-size:1.4rem;">Exercice {ex["id"]} : {ex["titre"]} [{ex["points"]} pts]</h3><p style="white-space: pre-wrap; color:white; font-size:1.6rem; font-weight:600;">{ex["enonce"]}</p></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True); show_footer()

def faq_view():
    show_header(); st.markdown('<div class="white-card"><h1>🔍 Processus d\'Évaluation & Sécurité</h1><p><b>1. Accès :</b> Identifiants générés par l\'administration de l\'Institut National Spécialisé Belazzoug Athmane.<br><b>2. Barème :</b> Chaque exercice est noté sur 5 points (1pt théorique, 4pts code source).<br><b>3. Surveillance :</b> Toute perte de focus (changement d\'onglet) réduit la note finale de 3 points par incident.</p></div>', unsafe_allow_html=True); show_footer()

def contact_view():
    show_header(); st.markdown('<div class="white-card"><h2>Support Pédagogique</h2><p>📧 haithemcomputing@gmail.com<br>📍 Département Administration Réseaux et Sécurité - Institut Belazzoug Athmane BBA 01</p></div>', unsafe_allow_html=True); show_footer()

def exam_view():
    if not st.session_state.exam_open: show_header(); st.error("🔒 Session verrouillée par l'enseignant."); show_footer(); return
    show_header(); step = st.session_state.step; ex = EXERCICES[step]; st.progress((step + 1) / 4); st.info(ex['enonce'])
    st.session_state.codes[ex['id']] = st.text_area("Console de Développement Python (Rédaction du Script) :", height=350, key=f"c_{ex['id']}")
    st.markdown("---"); st.markdown(f"#### **QUESTION THÉORIQUE :** {ex['questions'][0]['text']}")
    for q in ex['questions']:
        if q['type'] == 'choice': st.session_state.answers[q['id']] = st.radio(q['text'], q['options'], key=f"ans_{q['id']}", label_visibility="hidden")
        else: st.session_state.answers[q['id']] = st.number_input(q['text'], key=f"ans_{q['id']}", value=0)
    
    c_n1, c_n2 = st.columns(2)
    if step < 3 and c_n2.button("SUIVANT ➡️"):
        st.session_state.durations[ex['id']] = round(time.time() - st.session_state.ex_start_time, 1)
        st.session_state.step += 1; st.session_state.ex_start_time = time.time(); st.rerun()
    elif step == 3 and c_n2.button("🎯 FINALISER ET RENDRE LA COPIE"):
        st.session_state.durations[ex['id']] = round(time.time() - st.session_state.ex_start_time, 1)
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
    show_header(); st.markdown('<div style="max-width:500px; margin:auto;">', unsafe_allow_html=True); u = st.text_input("Identifiant"); p = st.text_input("Mot de passe", type="password")
    if st.button("ACCÉDER À LA SESSION"):
        if u == "admin" and p == "admin": st.session_state.user = {"name": "Administrateur", "username": "admin", "role": "teacher"}; st.session_state.page = "teacher"; st.rerun()
        docs = get_col('users').where('username', '==', u).where('password', '==', p).get()
        if docs: st.session_state.user = docs[0].to_dict(); st.session_state.page = "student_dash"; st.rerun()
        else: st.error("⚠️ Identifiants incorrects ou compte inexistant.")
    st.markdown('</div>', unsafe_allow_html=True); show_footer()

def student_dash():
    show_header(); u = st.session_state.user; st.markdown(f"<h1>Session de : {u['name']}</h1>", unsafe_allow_html=True)
    res_docs = get_col('results').where('username', '==', u['username']).get()
    if res_docs: 
        res = res_docs[0].to_dict()
        st.success(f"### NOTE FINALE OBTENUE : {res['score']} / 20")
        st.markdown("---")
        audit_results_detailed(res)
    elif st.session_state.exam_open:
        if st.button("🚀 DÉMARRER L'ÉPREUVE"): st.session_state.page = "exam"; st.session_state.ex_start_time = time.time(); st.rerun()
    else: st.warning("🔒 L'examen est actuellement verrouillé par l'administration."); show_footer()

def accueil_view():
    show_header(); st.markdown('<div class="white-card"><h2>Portail Académique de l\'Institut National Spécialisé</h2><p>Bienvenue sur le système d\'évaluation certifié de la Direction de la Formation Professionnelle de Bordj Bou Arréridj.</p></div>', unsafe_allow_html=True)
    if st.button("DÉVERROUILLER LE TERMINAL"): st.session_state.page = 'login'; st.rerun()
    show_footer()

# --- 9. ROUTAGE ---
with st.sidebar:
    st.markdown('<div class="hb-logo-container" style="margin-top:20px;"><div class="hb-logo" style="width:60px; height:60px; font-size:1.5rem;">HB</div></div>', unsafe_allow_html=True)
    if st.button("🏠 ACCUEIL"): st.session_state.page = 'accueil'; st.rerun()
    if st.button("ℹ️ INFO"): st.session_state.page = 'info'; st.rerun()
    if st.button("❓ FAQ"): st.session_state.page = 'faq'; st.rerun()
    if st.button("📞 CONTACT"): st.session_state.page = 'contact'; st.rerun()
    if st.session_state.user:
        st.divider(); 
        if st.button("🚪 DÉCONNEXION"): st.session_state.user = None; st.session_state.page = 'accueil'; st.rerun()

p = st.session_state.page
if p == 'teacher': teacher_dash()
elif p == 'exam': exam_view()
elif p == 'student_dash': student_dash()
elif p == 'login': login_view()
elif p == 'info': info_view()
elif p == 'faq': faq_view()
elif p == 'contact': contact_view()
else: accueil_view()
