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

# --- 2. SÉCURITÉ & PROTECTION (JS ANTI-TRICHE AVANCÉ) ---
# Blocage des interactions et détection de changement d'onglet
st.markdown("""
    <style>
    /* Masquage du bouton technique de triche */
    div[data-testid="stButton"]:has(button:contains("INTEGRITY_TRIGGER")) {
        display: none !important;
        visibility: hidden !important;
        height: 0; width: 0; position: absolute;
    }
    </style>
""", unsafe_allow_html=True)

st.components.v1.html("""
    <script>
    // Désactivation du menu contextuel, de la copie et du collage
    document.addEventListener('contextmenu', event => event.preventDefault());
    document.addEventListener('copy', e => e.preventDefault());
    document.addEventListener('paste', e => e.preventDefault());
    
    function sendCheatSignal() {
        const buttons = window.parent.document.querySelectorAll('button');
        for (const btn of buttons) {
            if (btn.innerText.includes('INTEGRITY_TRIGGER')) {
                btn.click();
                break;
            }
        }
    }

    // Détection de la perte de focus (Changement d'onglet ou fenêtre)
    window.addEventListener('blur', function() {
        sendCheatSignal();
    });
    
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            sendCheatSignal();
        }
    });

    // Protection contre l'inspection (F12 / Ctrl+Maj+I)
    document.onkeydown = function(e) {
        if(e.keyCode == 123) return false;
        if(e.ctrlKey && e.shiftKey && e.keyCode == 'I'.charCodeAt(0)) return false;
        if(e.ctrlKey && e.shiftKey && e.keyCode == 'C'.charCodeAt(0)) return false;
        if(e.ctrlKey && e.shiftKey && e.keyCode == 'J'.charCodeAt(0)) return false;
        if(e.ctrlKey && e.keyCode == 'U'.charCodeAt(0)) return false;
    }
    </script>
""", height=0)

# --- 3. DESIGN SYSTEM "ÉLITE" (SYSTÈME CSS COMPLET) ---
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
        --success: #10b981;
        --danger: #ef4444;
    }

    html, body, [data-testid="stAppViewContainer"], .main {
        background-color: var(--midnight) !important;
        color: var(--white) !important;
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stSidebar"] { display: none; }
    
    /* Boutons Premium */
    .stButton > button, [data-testid="stFormSubmitButton"] > button, .stDownloadButton > button {
        background-color: var(--orange-dark) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        height: 55px !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        width: 100% !important;
        font-size: 1.1rem !important;
        letter-spacing: 1px;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    }

    .stButton > button:hover {
        background-color: var(--orange-light) !important;
        transform: scale(1.02);
        box-shadow: 0 15px 30px rgba(245, 124, 0, 0.4) !important;
    }

    /* Cartes Blanches */
    .white-card {
        background-color: var(--white) !important;
        padding: 45px !important;
        border-radius: 24px !important;
        border-left: 15px solid var(--orange-light) !important;
        color: var(--midnight) !important;
        box-shadow: 0 25px 50px rgba(0,0,0,0.5) !important;
        margin-bottom: 30px;
    }
    .white-card * { color: var(--midnight) !important; }
    .white-card h1, .white-card h2, .white-card h3 { color: var(--orange-dark) !important; font-weight: 900; }

    /* Metrics Dashboard */
    [data-testid="stMetric"] {
        background-color: var(--white) !important;
        padding: 35px 20px !important;
        border-radius: 20px !important;
        border-bottom: 10px solid var(--orange-light) !important;
        box-shadow: 0 15px 35px rgba(0,0,0,0.4) !important;
        text-align: center !important;
    }
    [data-testid="stMetricValue"] div {
        color: var(--orange-dark) !important;
        font-size: 4.5rem !important;
        font-weight: 900 !important;
        line-height: 1;
    }
    [data-testid="stMetricLabel"] p {
        color: var(--midnight) !important;
        font-size: 1.4rem !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        margin-bottom: 15px;
    }

    /* Navigation Haute */
    .nav-container {
        background-color: var(--navy);
        padding: 15px;
        border-bottom: 6px solid var(--orange-light);
        margin-bottom: 40px;
        display: flex;
        justify-content: center;
        gap: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    
    /* Code Editor Custom */
    .stTextArea textarea {
        background-color: #1e293b !important;
        color: #38bdf8 !important;
        font-family: 'Fira Code', monospace !important;
        font-size: 1.1rem !important;
        border: 2px solid var(--navy) !important;
    }

    /* Tableaux Streamlit */
    .stDataFrame {
        background: white;
        border-radius: 12px;
        padding: 10px;
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
    except: pass

db = firestore.client()
PROJET_ID = "examen-asr-prod-main-final"

# --- 5. INITIALISATION SESSION STATE ---
def init_session():
    keys = {
        'user': None, 'page': '🏠 Accueil', 'step': 0, 'answers': {}, 
        'codes': {}, 'durations': {}, 'ex_start_time': None, 
        'cheats': 0, 'exam_open': True, 'manual_inscrits': 25
    }
    for k, v in keys.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# Signal de triche activé par le script JS
if st.button("INTEGRITY_TRIGGER", key="cheat_trigger"):
    st.session_state.cheats += 1

# --- 6. CLASSES ET HELPERS (PDF & GESTION TEMPS) ---
def get_algeria_time(timestamp):
    try:
        if not timestamp: return "--:--"
        ts = float(timestamp)
        utc_dt = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)
        alg_dt = utc_dt + datetime.timedelta(hours=1)
        return alg_dt.strftime("%H:%M:%S")
    except: return "--:--"

def generate_pw(l=8):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(l))

class DeliberationPDF(FPDF):
    def header(self):
        # BANDEAU DRAPEAU ALGERIEN (Style Officiel)
        self.set_fill_color(0, 102, 51) # Vert
        self.rect(0, 0, 105, 12, 'F')
        self.set_fill_color(255, 255, 255) # Blanc
        self.rect(105, 0, 105, 12, 'F')
        self.set_fill_color(204, 0, 0) # Rouge
        self.ellipse(101, 3, 8, 8, 'F')
        
        self.ln(20)
        self.set_font('Arial', 'B', 10)
        self.cell(0, 5, "REPUBLIQUE ALGERIENNE DEMOCRATIQUE ET POPULAIRE", 0, 1, 'C')
        self.cell(0, 5, "MINISTERE DE LA FORMATION ET DE L'ENSEIGNEMENT PROFESSIONNELS", 0, 1, 'C')
        self.set_font('Arial', 'B', 9)
        self.cell(0, 5, "INSFP BELAZZOUG ATHMANE BBA 01", 0, 1, 'C')
        self.ln(15)
        
        # TITRE BLEU HB
        self.set_text_color(0, 71, 171) # Bleu HB
        self.set_font('Arial', 'B', 26)
        self.cell(0, 15, "PROCES VERBAL DE DELIBERATION", 0, 1, 'C')
        self.set_text_color(0, 0, 0)
        
        now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f"Session de délibération du : {now.strftime('%d/%m/%Y à %H:%M')}", 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()} | Terminal ASR Pro - Certification Officielle', 0, 0, 'C')

def generate_pv_pdf(stats, results_df):
    pdf = DeliberationPDF()
    pdf.add_page()
    
    # 1. Résumé Statistique
    pdf.set_font("Arial", "B", 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 12, " 1. SYNTHESE QUANTITATIVE DE LA SESSION", 1, 1, 'L', 1)
    pdf.set_font("Arial", "", 12)
    pdf.cell(95, 12, f" Effectif Total (Inscrits) : {stats['inscrits']}", 1)
    pdf.cell(95, 12, f" Présents (Copies Uniques) : {stats['present']}", 1, 1)
    pdf.cell(95, 12, f" Moyenne Générale : {stats['moyenne']}/20", 1)
    pdf.cell(95, 12, f" Note Maximale : {stats['max']}/20", 1, 1)
    pdf.ln(10)

    # 2. Tableau des résultats
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 12, " 2. LISTE NOMINATIVE ET RESULTATS DES STAGIAIRES", 1, 1, 'L', 1)
    
    # Header Tableau Orange dark
    pdf.set_fill_color(245, 124, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(85, 12, " Nom & Prénom", 1, 0, 'L', 1)
    pdf.cell(25, 12, "Note", 1, 0, 'C', 1)
    pdf.cell(40, 12, "Heure", 1, 0, 'C', 1)
    pdf.cell(40, 12, "Décision", 1, 1, 'C', 1)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 11)
    
    # Tri par note pour le PV
    df_sorted = results_df.sort_values(by='Note', ascending=False)
    
    for _, row in df_sorted.iterrows():
        pdf.cell(85, 12, f" {str(row['Nom']).upper()}", 1)
        
        note = float(row['Note'])
        if note < 10: pdf.set_text_color(204, 0, 0)
        pdf.cell(25, 12, str(row['Note']), 1, 0, 'C')
        pdf.set_text_color(0, 0, 0)
        
        pdf.cell(40, 12, str(row['Heure']), 1, 0, 'C')
        decision = "ADMIS" if note >= 10 else "AJOURNÉ"
        pdf.cell(40, 12, decision, 1, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

def get_col(name): 
    return db.collection('artifacts').document(PROJET_ID).collection('public').document('data').collection(name)

# --- 7. DONNÉES PÉDAGOGIQUES (EXERCICES COMPLETS) ---
EXERCICES = [
    {
        "id": 1, "titre": "Algorithmique - Contrôle d'Accès", "points": 5, 
        "enonce": "Écrivez un programme qui demande l'année de naissance de l'utilisateur.\n1. Calculer l'âge (référence 2026).\n2. Si l'utilisateur a 18 ans ou plus : afficher 'Accès autorisé', sinon afficher 'Accès refusé'.",
        "questions": [
            {"id":"q1_1","text":"Âge pour une naissance en 2010 ?", "type":"number", "correct":16},
            {"id":"q1_2","text":"Message pour un utilisateur de 16 ans ?", "type":"choice", "options":["Accès autorisé", "Accès refusé"], "correct":"Accès refusé"}
        ]
    },
    {
        "id": 2, "titre": "Physique - États de la Matière", "points": 5,
        "enonce": "Déterminez l'état de l'eau selon la température T (°C) :\n- T <= 0 : Glace\n- 0 < T < 100 : Liquide\n- T >= 100 : Vapeur",
        "questions": [
            {"id":"q2_1","text":"Quel est l'état à 100°C pile ?", "type":"choice", "options":["Glace", "Liquide", "Vapeur"], "correct":"Vapeur"}
        ]
    },
    {
        "id": 3, "titre": "Gestion - Assurance Automobile", "points": 5,
        "enonce": "Calculez le tarif de base 500€.\n- Si < 25 ans ET < 2 ans de permis : +200€.\n- Si > 25 ans OU > 5 ans de permis : -50€.",
        "questions": [
            {"id":"q3_1","text":"Conducteur de 22 ans, 1 an de permis. Prix final ?", "type":"number", "correct":700}
        ]
    },
    {
        "id": 4, "titre": "Ingénierie Financière - Crédit", "points": 5,
        "enonce": "Éligibilité au crédit :\n- Épargne <= 0 : Refus immédiat.\n- Taux endettement > 33% : Refus.\n- Sinon : Pré-approuvé.",
        "questions": [
            {"id":"q4_1","text":"Revenu 2000, Dépenses 2000. Décision ?", "type":"choice", "options":["Refusé", "Accordé"], "correct":"Refusé"}
        ]
    }
]

# --- 8. VUES ---

def show_header():
    st.markdown(f"""
        <div style="text-align:center; margin-bottom:50px;">
            <div style="display:flex; justify-content:center; margin-bottom:25px;">
                <div style="width:110px; height:110px; background:white; border:7px solid #f57c00; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#0047AB; font-weight:900; font-size:3.5rem; box-shadow:0 0 35px rgba(245,124,0,0.7);">HB</div>
            </div>
            <h4 style="opacity:0.8; letter-spacing:4px; text-transform:uppercase; font-size:1.1rem;">République Algérienne Démocratique et Populaire</h4>
            <h1 style="color:#f57c00; font-size:3.2rem; margin:15px 0; font-weight:900;">INSFP BELAZZOUG ATHMANE BBA 01</h1>
            <p style="font-weight:700; color:white; letter-spacing:6px; font-size:1.8rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">PLATEFORME D'EXAMEN ASR PRO</p>
        </div>
    """, unsafe_allow_html=True)

def audit_results_detailed(data):
    st.markdown("### 🔍 Analyse Pédagogique de la Copie")
    for ex in EXERCICES:
        with st.expander(f"Exercice {ex['id']} : {ex['titre']} ({ex['points']} pts)"):
            c1, c2 = st.columns([1, 1.5])
            with c1:
                st.markdown("**Validation Théorique (QCM)**")
                for q in ex['questions']:
                    u_ans = data.get('answers', {}).get(q['id'], "Non répondu")
                    is_ok = str(u_ans) == str(q['correct'])
                    icon = "✅" if is_ok else "❌"
                    color = "#10b981" if is_ok else "#ef4444"
                    st.markdown(f"""
                        <div style="padding:15px; border-left:6px solid {color}; background:rgba(255,255,255,0.05); border-radius:8px; margin-bottom:12px;">
                            <small style="color:#aaa;">{q['text']}</small><br>
                            <span style="font-size:1.2rem;">{icon} <b>{u_ans}</b></span><br>
                            <small style="color:#aaa;">Correction attendue : {q['correct']}</small>
                        </div>
                    """, unsafe_allow_html=True)
            with c2:
                st.markdown("**Implémentation Python**")
                code_content = data.get('codes', {}).get(str(ex['id']), "# Aucun code saisi")
                st.code(code_content, "python")
                cpm = data.get('cpm_data', {}).get(str(ex['id']), 0)
                if cpm > 300: st.error(f"🚩 Alerte Plagiat / IA probable ({int(cpm)} CPM)")

def teacher_dash():
    show_header()
    st.title("🎛️ Terminal Formateur - Gestion de la Délibération")
    
    # Récupération des Stagiaires
    u_docs = get_col('users').where('role', '==', 'student').get()
    u_list = [{"id": u.id, **u.to_dict()} for u in u_docs]
    
    # Récupération des Résultats
    r_docs = get_col('results').get()
    r_raw = [{"id": r.id, **r.to_dict()} for r in r_docs]
    
    # --- LOGIQUE DE DÉDOUBLONNAGE (Conservation de la dernière tentative) ---
    processed_results = {}
    for r in r_raw:
        uname = r.get('username', 'unknown')
        ts = float(r.get('timestamp', 0))
        if uname not in processed_results or ts > processed_results[uname]['timestamp']:
            processed_results[uname] = {**r, 'timestamp': ts}
    
    r_list = list(processed_results.values())
    r_list.sort(key=lambda x: x['timestamp']) # Tri Chronologique pour l'audit

    t1, t2, t3, t4 = st.tabs(["📊 ANALYSE STATISTIQUE", "👥 GESTION SECTION", "📑 AUDIT DES COPIES", "📦 EXPORT JSON"])
    
    with t1:
        st.markdown("### 🔒 Contrôle Administratif")
        # AJUSTEMENT MANUEL DE L'EFFECTIF (Pour correspondre à vos 25 inscrits réels)
        st.session_state.manual_inscrits = st.number_input("Nombre d'inscrits à délibérer (Effectif théorique) :", 1, 100, st.session_state.manual_inscrits)
        
        c = st.columns(4)
        c[0].metric("Inscrits", st.session_state.manual_inscrits)
        c[1].metric("Présents", len(r_list))
        absents = max(0, st.session_state.manual_inscrits - len(r_list))
        c[2].metric("Absents", absents)
        c[3].metric("Moyenne", f"{pd.DataFrame(r_list)['score'].mean():.2f}" if r_list else "0.00")
        
        if r_list:
            st.divider()
            df_pv = pd.DataFrame([{
                "ID": r['id'], "Nom": r['name'], "Note": r['score'], 
                "Heure": get_algeria_time(r['timestamp']), "Alertes": r.get('cheats', 0)
            } for r in r_list])
            
            stats_pdf = {
                "inscrits": st.session_state.manual_inscrits, 
                "present": len(r_list),
                "moyenne": f"{df_pv['Note'].mean():.2f}", 
                "max": df_pv['Note'].max(), 
                "min": df_pv['Note'].min()
            }
            
            st.download_button("📄 GÉNÉRER LE PV DE DÉLIBÉRATION (PDF OFFICIEL)", generate_pv_pdf(stats_pdf, df_pv), "PV_Deliberation_ASR_Pro.pdf")

    with t2:
        st.subheader("Effectif des Stagiaires Inscrits")
        if u_list:
            st.dataframe(pd.DataFrame(u_list)[['name', 'username', 'password']], use_container_width=True)
            if st.button("Actualiser la liste"): st.rerun()
            
            # Optionnel : Ajout d'étudiants via Excel
            st.divider()
            up_f = st.file_uploader("Importer des stagiaires (Excel)", type=['xlsx'])
            if up_f and st.button("Lancer Import"):
                df_imp = pd.read_excel(up_f)
                for name in df_imp.iloc[:, 0].dropna():
                    uid = str(name).lower().replace(" ", ".") + str(random.randint(10,99))
                    get_col('users').add({"name": name, "username": uid, "password": generate_pw(), "role": "student"})
                st.success("Import terminé !")
        else:
            st.warning("Aucun stagiaire n'est actuellement inscrit.")

    with t3:
        if r_list:
            st.markdown("### Liste des copies (Copies uniques retenues)")
            df_audit = pd.DataFrame(r_list)[['name', 'score', 'timestamp']]
            df_audit['Heure'] = df_audit['timestamp'].apply(get_algeria_time)
            
            sel_name = st.selectbox("Sélectionner un stagiaire pour audit :", [f"{r['name']} ({r['score']}/20)" for r in r_list])
            target_name = sel_name.split(" (")[0]
            data = next(r for r in r_list if r['name'] == target_name)
            
            st.markdown(f'<div class="white-card"><h2>STAGIAIRE : {data["name"]}</h2><h1>Note Finale : {data["score"]} / 20</h1><p>Alerte Sécurité : {data.get("cheats", 0)} fois</p></div>', unsafe_allow_html=True)
            
            # Modification manuelle de note possible
            new_note = st.number_input("Ajuster la note :", 0.0, 20.0, float(data['score']), 0.25)
            if st.button("Valider la nouvelle note"):
                get_col('results').document(data['id']).update({"score": new_note})
                st.success("Note mise à jour !")
                st.rerun()
                
            st.divider()
            audit_results_detailed(data)
        else:
            st.info("Aucune copie n'a été transmise pour le moment.")
            
    with t4:
        if st.button("Extraire toutes les données (JSON)"):
            st.json(r_raw)

def exam_view():
    if not st.session_state.exam_open:
        show_header(); st.error("🔒 Session verrouillée par le formateur."); return
    
    show_header()
    step = st.session_state.step; ex = EXERCICES[step]
    
    st.markdown(f"### Exercice {ex['id']} / {len(EXERCICES)}")
    st.progress((step + 1) / len(EXERCICES))
    
    st.markdown(f"""
        <div class="white-card">
            <h3>{ex["titre"]}</h3>
            <p style="white-space:pre-wrap; font-size:1.3rem;">{ex["enonce"]}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Zone d'écriture de code
    st.session_state.codes[ex['id']] = st.text_area(
        "Console Python (Barème : 4 pts) :", 
        height=400, 
        key=f"code_area_{ex['id']}", 
        placeholder="# Écrivez votre algorithme ici..."
    )
    
    st.divider()
    # Questions Théoriques
    for q in ex['questions']:
        if q['type'] == 'choice':
            st.session_state.answers[q['id']] = st.radio(q['text'], q['options'], key=f"ans_q_{q['id']}")
        else:
            st.session_state.answers[q['id']] = st.number_input(q['text'], key=f"ans_q_{q['id']}", value=0)

    # Navigation entre les étapes
    st.markdown("---")
    col_nav1, col_nav2 = st.columns([1, 1])
    if step > 0:
        if col_nav1.button("⬅️ EXERCICE PRÉCÉDENT"): 
            st.session_state.step -= 1; st.rerun()
    
    label_btn = "🎯 TRANSMETTRE LA COPIE FINALE" if step == len(EXERCICES)-1 else "EXERCICE SUIVANT ➡️"
    if col_nav2.button(label_btn):
        # Enregistrement durée
        if st.session_state.ex_start_time:
            st.session_state.durations[ex['id']] = time.time() - st.session_state.ex_start_time
            
        if step < len(EXERCICES)-1:
            st.session_state.step += 1
            st.session_state.ex_start_time = time.time()
            st.rerun()
        else:
            # CALCUL DU SCORE AUTOMATIQUE
            total_points = 0
            breakdown_dict = {}
            cpm_dict = {}
            
            for e in EXERCICES:
                pts_exo = 0
                # Calcul QCM (1 pt par exo)
                correct_q = 0
                for q in e['questions']:
                    if str(st.session_state.answers.get(q['id'])) == str(q['correct']):
                        correct_q += 1
                pts_exo += (correct_q / len(e['questions'])) * 1.0
                
                # Calcul Code (4 pts par exo)
                code_txt = st.session_state.codes.get(e['id'], "").strip()
                if len(code_txt) > 30: pts_exo += 4.0
                elif len(code_txt) > 10: pts_exo += 2.0
                
                # CPM (Caractères par minute) pour détection triche/IA
                dur = st.session_state.durations.get(e['id'], 60)
                cpm = (len(code_txt) / (dur/60)) if dur > 0 else 0
                cpm_dict[str(e['id'])] = cpm
                
                breakdown_dict[str(e['id'])] = round(pts_exo, 2)
                total_points += pts_exo
            
            # Application malus triche focus
            score_final = max(0, total_points - (st.session_state.cheats * 2.0))
            
            # Enregistrement Firebase
            get_col('results').add({
                "username": st.session_state.user['username'],
                "name": st.session_state.user['name'],
                "score": round(score_final, 1),
                "answers": st.session_state.answers,
                "codes": {str(k): v for k, v in st.session_state.codes.items()},
                "timestamp": time.time(),
                "cheats": st.session_state.cheats,
                "breakdown": breakdown_dict,
                "cpm_data": cpm_dict
            })
            st.session_state.page = "👤 Espace Candidat"; st.rerun()

def login_view():
    show_header()
    st.markdown('<div style="max-width:500px; margin:auto; padding-top:40px;">', unsafe_allow_html=True)
    st.markdown('<h2 style="text-align:center; margin-bottom:30px; font-weight:900; color:white;">Authentification Sécurisée</h2>', unsafe_allow_html=True)
    
    user_id = st.text_input("Identifiant Stagiaire / Admin")
    password = st.text_input("Mot de passe", type="password")
    
    if st.button("ACCÉDER AU TERMINAL D'EXAMEN"):
        if user_id == "admin" and password == "admin":
            st.session_state.user = {"name": "Haithem Berkane", "role": "teacher", "username": "admin"}
            st.session_state.page = "📊 Tableau de Bord"; st.rerun()
        
        try:
            res_user = get_col('users').where('username', '==', user_id).where('password', '==', password).get()
            if res_user:
                st.session_state.user = res_user[0].to_dict()
                st.session_state.page = "👤 Espace Candidat"; st.rerun()
            else:
                st.error("Identifiants de connexion incorrects.")
        except:
            st.error("Erreur critique de connexion à la base de données.")
            
    st.markdown('</div>', unsafe_allow_html=True)

def student_dash():
    show_header()
    u = st.session_state.user
    st.markdown(f"<h1>Bienvenue dans votre session, {u['name']}</h1>", unsafe_allow_html=True)
    
    # Vérification si une copie a déjà été rendue
    res_copie = get_col('results').where('username', '==', u['username']).get()
    if res_copie:
        data_copie = res_copie[0].to_dict()
        st.success(f"### ÉPREUVE TERMINÉE ! Note finale : {data_copie['score']} / 20")
        st.divider()
        audit_results_detailed(data_copie)
    elif st.session_state.exam_open:
        st.markdown("""
            <div class="white-card">
                <h2>Consignes de l'Épreuve</h2>
                <ul>
                    <li><b>Temps :</b> Vous disposez de 2 heures pour l'ensemble des exercices.</li>
                    <li><b>Sécurité :</b> Toute sortie de la fenêtre ou changement d'onglet entraînera une alerte et un malus.</li>
                    <li><b>Évaluation :</b> 1 pt pour la théorie (QCM) et 4 pts pour l'algorithme (Python) par exercice.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 DÉMARRER L'ÉPREUVE MAINTENANT"):
            st.session_state.page = "exam"
            st.session_state.ex_start_time = time.time()
            st.rerun()
    else:
        st.warning("🔒 L'accès à l'examen est actuellement clôturé par l'administration.")

def accueil_view():
    show_header()
    st.markdown("""
        <div class="white-card" style="text-align:center;">
            <h1 style="font-size:3rem;">Portail Académique ASR</h1>
            <p style="font-size:1.4rem;">Système d'évaluation numérique certifié de l'INSFP Belazzoug Athmane.</p>
            <p style="font-size:1.2rem; opacity:0.7;">Veuillez vous authentifier pour accéder à vos épreuves ou consulter vos résultats de délibération.</p>
        </div>
    """, unsafe_allow_html=True)

# --- 9. ROUTAGE GÉNÉRAL ET NAVIGATION ---
pages_available = ["🏠 Accueil", "🔐 Connexion"]
if st.session_state.user:
    pages_available = ["🏠 Accueil"]
    if st.session_state.user['role'] == 'teacher':
        pages_available.append("📊 Tableau de Bord")
    else:
        pages_available.append("👤 Espace Candidat")
    pages_available.append("🚪 Déconnexion")

# Barre de Navigation Style HB
st.markdown('<div class="nav-container">', unsafe_allow_html=True)
cols_nav = st.columns(len(pages_available))
current_page = st.session_state.page

for i, p_name in enumerate(pages_available):
    if cols_nav[i].button(p_name, key=f"nav_btn_{p_name}"):
        if p_name == "🚪 Déconnexion":
            st.session_state.user = None
            st.session_state.page = "🏠 Accueil"
        else:
            st.session_state.page = p_name
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# Dispatcher de rendu
if current_page == '📊 Tableau de Bord' and st.session_state.user['role'] == 'teacher':
    teacher_dash()
elif current_page == 'exam':
    exam_view()
elif current_page == '👤 Espace Candidat' and st.session_state.user:
    student_dash()
elif current_page == '🔐 Connexion':
    login_view()
else:
    accueil_view()

# --- 10. FOOTER ---
st.markdown(f"""
    <div style="text-align:center; margin-top:100px; padding:40px; border-top:1px solid #333; opacity:0.4; font-size:0.9rem;">
        Certification ASR Pro v2.5 | Architecture par Haithem Berkane | INSFP BBA 01 | © 2026
    </div>
""", unsafe_allow_html=True)
