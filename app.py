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
# Configuration initiale pour un affichage large et professionnel
st.set_page_config(
    page_title="ASR Pro - Excellence Pédagogique",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SÉCURITÉ & PROTECTION (JS ANTI-TRICHE AVANCÉ) ---
# Ce bloc injecte du JavaScript pour surveiller le comportement des stagiaires
st.markdown("""
    <style>
    /* Masquage du bouton technique de triche pour éviter toute manipulation manuelle */
    div[data-testid="stButton"]:has(button:contains("INTEGRITY_TRIGGER")) {
        display: none !important;
        visibility: hidden !important;
        height: 0; width: 0; position: absolute;
    }
    </style>
""", unsafe_allow_html=True)

st.components.v1.html("""
    <script>
    // Désactivation totale du menu contextuel, de la copie et du collage pour protéger le sujet
    document.addEventListener('contextmenu', event => event.preventDefault());
    document.addEventListener('copy', e => e.preventDefault());
    document.addEventListener('paste', e => e.preventDefault());
    
    // Fonction pour envoyer un signal de triche au serveur Streamlit
    function sendCheatSignal() {
        const buttons = window.parent.document.querySelectorAll('button');
        for (const btn of buttons) {
            if (btn.innerText.includes('INTEGRITY_TRIGGER')) {
                btn.click();
                break;
            }
        }
    }

    // Surveillance de la perte de focus : changement d'onglet ou réduction de fenêtre
    window.addEventListener('blur', function() {
        sendCheatSignal();
    });
    
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            sendCheatSignal();
        }
    });

    // Blocage des touches de développement (F12, Ctrl+Maj+I, etc.)
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
# Définition de la charte graphique : Midnight Blue, Orange Pro et Navy
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

    /* Style global de l'application */
    html, body, [data-testid="stAppViewContainer"], .main {
        background-color: var(--midnight) !important;
        color: var(--white) !important;
        font-family: 'Inter', sans-serif;
    }

    /* Suppression de la barre latérale Streamlit pour une immersion totale */
    [data-testid="stSidebar"] { display: none; }
    
    /* Boutons Premium avec effets de transition */
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
        letter-spacing: 1.5px;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3) !important;
    }

    .stButton > button:hover {
        background-color: var(--orange-light) !important;
        transform: scale(1.02);
        box-shadow: 0 15px 30px rgba(245, 124, 0, 0.4) !important;
    }

    /* Cartes Blanches pour le contenu principal */
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

    /* Style des indicateurs (Metrics) du tableau de bord */
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

    /* Navigation Haute Personnalisée */
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
    
    /* Personnalisation de l'éditeur de code */
    .stTextArea textarea {
        background-color: #1e293b !important;
        color: #38bdf8 !important;
        font-family: 'Fira Code', monospace !important;
        font-size: 1.1rem !important;
        border: 2px solid var(--navy) !important;
    }

    /* Style des DataFrames (Tableaux) */
    .stDataFrame {
        background: white;
        border-radius: 12px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. INITIALISATION FIREBASE ---
# Connexion sécurisée à la base de données Firestore
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
        st.error(f"Erreur d'initialisation Firebase : {e}")

db = firestore.client()
PROJET_ID = "examen-asr-prod-main-final"

# --- 5. INITIALISATION SESSION STATE ---
# Gestion des variables persistantes durant la session utilisateur
def init_session():
    keys = {
        'user': None,           # Données de l'utilisateur connecté
        'page': '🏠 Accueil',    # Page actuelle
        'step': 0,              # Étape de l'examen
        'answers': {},          # Réponses QCM
        'codes': {},            # Scripts Python
        'durations': {},        # Temps passé par exercice
        'ex_start_time': None,  # Timestamp de début
        'cheats': 0,            # Compteur de triche
        'exam_open': True,      # État de la session (Ouvert/Fermé)
        'manual_inscrits': 25   # Nombre d'inscrits ajustable par le formateur
    }
    for k, v in keys.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# Capture du signal de triche envoyé par le script JS
if st.button("INTEGRITY_TRIGGER", key="cheat_trigger"):
    st.session_state.cheats += 1

# --- 6. CLASSES ET HELPERS (PDF & GESTION TEMPS) ---
def get_algeria_time(timestamp):
    """Convertit un timestamp UTC en format lisible Heure Algérie (UTC+1)"""
    try:
        if not timestamp: return "--:--"
        ts = float(timestamp)
        utc_dt = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)
        alg_dt = utc_dt + datetime.timedelta(hours=1)
        return alg_dt.strftime("%H:%M:%S")
    except:
        return "--:--"

def generate_pw(l=8):
    """Génère un mot de passe aléatoire pour les nouveaux inscrits"""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(l))

class DeliberationPDF(FPDF):
    """Classe personnalisée pour générer le PV de délibération avec les couleurs nationales"""
    def header(self):
        # BANDEAU DRAPEAU ALGERIEN (Style Officiel : Vert / Blanc / Rouge)
        self.set_fill_color(0, 102, 51) # Vert Algérie
        self.rect(0, 0, 105, 12, 'F')
        self.set_fill_color(255, 255, 255) # Blanc
        self.rect(105, 0, 105, 12, 'F')
        self.set_fill_color(204, 0, 0) # Rouge Croissant/Étoile
        self.ellipse(101, 3, 8, 8, 'F')
        
        self.ln(20)
        self.set_font('Arial', 'B', 10)
        self.cell(0, 5, "REPUBLIQUE ALGERIENNE DEMOCRATIQUE ET POPULAIRE", 0, 1, 'C')
        self.cell(0, 5, "MINISTERE DE LA FORMATION ET DE L'ENSEIGNEMENT PROFESSIONNELS", 0, 1, 'C')
        self.set_font('Arial', 'B', 9)
        self.cell(0, 5, "INSFP BELAZZOUG ATHMANE BBA 01", 0, 1, 'C')
        self.ln(15)
        
        # TITRE DU PV EN BLEU HB
        self.set_text_color(0, 71, 171) # Bleu HB
        self.set_font('Arial', 'B', 26)
        self.cell(0, 15, "PROCES VERBAL DE DELIBERATION", 0, 1, 'C')
        self.set_text_color(0, 0, 0)
        
        now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f"Session de délibération clôturée le : {now.strftime('%d/%m/%Y à %H:%M')}", 0, 1, 'C')
        self.ln(10)

    def footer(self):
        # Pied de page avec pagination
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()} | Document Généré par Terminal ASR Pro - Certification Officielle', 0, 0, 'C')

def generate_pv_pdf(stats, results_df):
    """Génère le flux binaire du PDF pour le téléchargement"""
    pdf = DeliberationPDF()
    pdf.add_page()
    
    # 1. Résumé Statistique de la Session
    pdf.set_font("Arial", "B", 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 12, " 1. SYNTHESE QUANTITATIVE DE LA SESSION D'EXAMEN", 1, 1, 'L', 1)
    pdf.set_font("Arial", "", 12)
    pdf.cell(95, 12, f" Effectif Total (Inscrits) : {stats['inscrits']}", 1)
    pdf.cell(95, 12, f" Présents (Copies Uniques) : {stats['present']}", 1, 1)
    pdf.cell(95, 12, f" Moyenne Générale de Section : {stats['moyenne']}/20", 1)
    pdf.cell(95, 12, f" Note Maximale Obtenue : {stats['max']}/20", 1, 1)
    pdf.ln(10)

    # 2. Tableau détaillé des résultats nominatifs
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 12, " 2. LISTE NOMINATIVE ET RESULTATS DES STAGIAIRES", 1, 1, 'L', 1)
    
    # Header du Tableau (Orange dark pro)
    pdf.set_fill_color(245, 124, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(85, 12, " Nom & Prénom du Stagiaire", 1, 0, 'L', 1)
    pdf.cell(25, 12, "Note /20", 1, 0, 'C', 1)
    pdf.cell(40, 12, "Heure Remise", 1, 0, 'C', 1)
    pdf.cell(40, 12, "Décision", 1, 1, 'C', 1)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 11)
    
    # Tri automatique des stagiaires par note décroissante pour le PV
    df_sorted = results_df.sort_values(by='Note', ascending=False)
    
    for _, row in df_sorted.iterrows():
        pdf.cell(85, 12, f" {str(row['Nom']).upper()}", 1)
        
        note = float(row['Note'])
        # Affichage en rouge si échec (< 10)
        if note < 10: pdf.set_text_color(204, 0, 0)
        pdf.cell(25, 12, str(row['Note']), 1, 0, 'C')
        pdf.set_text_color(0, 0, 0)
        
        pdf.cell(40, 12, str(row['Heure']), 1, 0, 'C')
        decision = "ADMIS" if note >= 10 else "AJOURNÉ"
        pdf.cell(40, 12, decision, 1, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

def get_col(name): 
    """Raccourci pour accéder aux collections Firestore"""
    return db.collection('artifacts').document(PROJET_ID).collection('public').document('data').collection(name)

# --- 7. DONNÉES PÉDAGOGIQUES (EXERCICES COMPLETS) ---
# Définition des 4 exercices de l'examen ASR Pro
EXERCICES = [
    {
        "id": 1, "titre": "Algorithmique - Contrôle d'Accès", "points": 5, 
        "enonce": "Écrivez un programme qui demande l'année de naissance de l'utilisateur.\n1. Calculer l'âge (référence 2026).\n2. Si l'utilisateur a 18 ans ou plus : afficher 'Accès autorisé', sinon afficher 'Accès refusé'.",
        "questions": [
            {"id":"q1_1","text":"Âge calculé pour une naissance en 2010 ?", "type":"number", "correct":16},
            {"id":"q1_2","text":"Message affiché pour un stagiaire de 16 ans ?", "type":"choice", "options":["Accès autorisé", "Accès refusé"], "correct":"Accès refusé"}
        ]
    },
    {
        "id": 2, "titre": "Physique - États de la Matière", "points": 5,
        "enonce": "Déterminez l'état de l'eau selon la température T (°C) fournie par l'utilisateur :\n- T <= 0 : Glace\n- 0 < T < 100 : Liquide\n- T >= 100 : Vapeur",
        "questions": [
            {"id":"q2_1","text":"Quel est l'état physique exact à 100°C pile ?", "type":"choice", "options":["Glace", "Liquide", "Vapeur"], "correct":"Vapeur"}
        ]
    },
    {
        "id": 3, "titre": "Gestion - Assurance Automobile", "points": 5,
        "enonce": "Calculez le tarif final de l'assurance (Base : 500€).\n- Si l'utilisateur a < 25 ans ET < 2 ans de permis : +200€.\n- Si l'utilisateur a > 25 ans OU > 5 ans de permis : -50€.",
        "questions": [
            {"id":"q3_1","text":"Conducteur de 22 ans avec 1 an de permis. Quel est le prix final ?", "type":"number", "correct":700}
        ]
    },
    {
        "id": 4, "titre": "Ingénierie Financière - Crédit", "points": 5,
        "enonce": "Déterminez l'éligibilité au crédit bancaire :\n- Si épargne <= 0 : Refus immédiat.\n- Si taux endettement > 33% : Refus.\n- Dans tous les autres cas : Dossier pré-approuvé.",
        "questions": [
            {"id":"q4_1","text":"Revenu mensuel 2000€, Dépenses fixes 2000€. Décision ?", "type":"choice", "options":["Refusé", "Accordé"], "correct":"Refusé"}
        ]
    }
]

# --- 8. VUES (COMPOSANTS DE L'INTERFACE) ---

def show_header():
    """Affiche l'en-tête officiel de l'Institut avec le logo HB"""
    st.markdown(f"""
        <div style="text-align:center; margin-bottom:50px;">
            <div style="display:flex; justify-content:center; margin-bottom:25px;">
                <div style="width:115px; height:115px; background:white; border:7px solid #f57c00; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#0047AB; font-weight:900; font-size:3.5rem; box-shadow:0 0 35px rgba(245,124,0,0.7);">HB</div>
            </div>
            <h4 style="opacity:0.8; letter-spacing:4px; text-transform:uppercase; font-size:1.1rem;">République Algérienne Démocratique et Populaire</h4>
            <h1 style="color:#f57c00; font-size:3.5rem; margin:15px 0; font-weight:900;">INSFP BELAZZOUG ATHMANE BBA 01</h1>
            <p style="font-weight:700; color:white; letter-spacing:6px; font-size:1.8rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">PLATEFORME D'EXAMEN ASR PRO</p>
        </div>
    """, unsafe_allow_html=True)

def audit_results_detailed(data):
    """Permet au formateur d'inspecter les réponses et le code d'une copie"""
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
                st.markdown("**Implémentation Algorithmique Python**")
                code_content = data.get('codes', {}).get(str(ex['id']), "# Aucun code saisi")
                st.code(code_content, "python")
                # Analyse de la vitesse de saisie pour détection IA/Copier-Coller
                cpm = data.get('cpm_data', {}).get(str(ex['id']), 0)
                if cpm > 300: st.error(f"🚩 Alerte Plagiat / IA probable ({int(cpm)} CPM détectés)")
                else: st.info(f"🟢 Saisie normale ({int(cpm)} CPM)")

def teacher_dash():
    """Interface d'administration complète pour le formateur"""
    show_header()
    st.title("🎛️ Terminal Formateur - Gestion & Délibération")
    
    # 1. Extraction des Stagiaires inscrits
    u_docs = get_col('users').where('role', '==', 'student').get()
    u_list = [{"id": u.id, **u.to_dict()} for u in u_docs]
    
    # 2. Extraction des Résultats bruts
    r_docs = get_col('results').get()
    r_raw = [{"id": r.id, **r.to_dict()} for r in r_docs]
    
    # --- LOGIQUE DE DÉDOUBLONNAGE STRICT ---
    # On ne conserve que la tentative la plus récente pour chaque stagiaire unique
    processed_results = {}
    for r in r_raw:
        uname = r.get('username', 'unknown')
        ts = float(r.get('timestamp', 0))
        if uname not in processed_results or ts > processed_results[uname]['timestamp']:
            processed_results[uname] = {**r, 'timestamp': ts}
    
    # Liste finale des copies uniques retenues pour la délibération
    r_list = list(processed_results.values())
    r_list.sort(key=lambda x: x['timestamp']) # Ordre chronologique pour l'audit

    # Organisation du Dashboard en 4 onglets
    t1, t2, t3, t4 = st.tabs(["📊 ANALYSE STATISTIQUE", "👥 GESTION SECTION", "📑 AUDIT DES COPIES", "📦 EXPORT JSON"])
    
    with t1:
        st.markdown("### 🔒 Contrôle de la Session")
        col_ctrl1, col_ctrl2 = st.columns([2, 1])
        with col_ctrl1:
            st.info(f"État de la plateforme : **{'OUVERTE' if st.session_state.exam_open else 'FERMÉE'}**")
        with col_ctrl2:
            if st.button("CHANGER ÉTAT SESSION"):
                st.session_state.exam_open = not st.session_state.exam_open
                st.rerun()

        st.divider()
        # --- AJUSTEMENT MANUEL DE L'EFFECTIF (FONCTIONNALITÉ CRITIQUE) ---
        st.markdown("#### Configuration du PV de Délibération")
        st.session_state.manual_inscrits = st.number_input(
            "Régler le nombre d'inscrits théorique pour le PV :", 
            1, 100, st.session_state.manual_inscrits, 
            help="Ce chiffre sera utilisé pour calculer le taux de présence et les absents sur le PV PDF."
        )
        
        # Affichage des KPIs dynamiques
        col_kpi = st.columns(4)
        col_kpi[0].metric("Inscrits (PV)", st.session_state.manual_inscrits)
        col_kpi[1].metric("Présents (Indiv.)", len(r_list))
        absents_count = max(0, st.session_state.manual_inscrits - len(r_list))
        col_kpi[2].metric("Absents", absents_count)
        moyenne_section = pd.DataFrame(r_list)['score'].mean() if r_list else 0.00
        col_kpi[3].metric("Moyenne Section", f"{moyenne_section:.2f}")
        
        if r_list:
            st.divider()
            df_pv = pd.DataFrame([{
                "ID": r['id'], "Nom": r['name'], "Note": r['score'], 
                "Heure": get_algeria_time(r['timestamp']), "Alertes": r.get('cheats', 0)
            } for r in r_list])
            
            stats_pdf_data = {
                "inscrits": st.session_state.manual_inscrits, 
                "present": len(r_list),
                "moyenne": f"{moyenne_section:.2f}", 
                "max": df_pv['Note'].max(), 
                "min": df_pv['Note'].min()
            }
            
            # Bouton de génération du PV Algérien
            st.download_button(
                "📄 GÉNÉRER LE PV DE DÉLIBÉRATION OFFICIEL (PDF)", 
                generate_pv_pdf(stats_pdf_data, df_pv), 
                f"PV_Deliberation_ASR_Pro_{datetime.date.today()}.pdf",
                mime="application/pdf"
            )

    with t2:
        st.subheader("Effectif des Stagiaires et Accès")
        if u_list:
            st.dataframe(pd.DataFrame(u_list)[['name', 'username', 'password']], use_container_width=True)
            if st.button("Actualiser la liste des stagiaires"): 
                st.rerun()
            
            # Fonctionnalité d'importation Excel pour préparer la session
            st.divider()
            up_file = st.file_uploader("Importer des nouveaux stagiaires (Fichier .xlsx)", type=['xlsx'])
            if up_file and st.button("LANCER IMPORTATION EXCEL"):
                try:
                    df_imp = pd.read_excel(up_file)
                    for n in df_imp.iloc[:, 0].dropna():
                        u_name = str(n).lower().replace(" ", ".") + str(random.randint(10,99))
                        get_col('users').add({"name": n, "username": u_name, "password": generate_pw(), "role": "student"})
                    st.success("Importation réussie ! Veuillez actualiser.")
                except Exception as e:
                    st.error(f"Erreur d'import : {e}")
        else:
            st.warning("Aucun stagiaire n'est actuellement inscrit dans la section.")

    with t3:
        if r_list:
            st.markdown("### Liste des copies transmises (Sans répétitions)")
            df_audit_view = pd.DataFrame(r_list)[['name', 'score', 'timestamp']]
            df_audit_view['Heure Remise'] = df_audit_view['timestamp'].apply(get_algeria_time)
            
            # Sélecteur de copie pour inspection
            selection_list = [f"{r['name']} ({r['score']}/20)" for r in r_list]
            sel_stagiaire = st.selectbox("Sélectionner un stagiaire pour audit complet :", selection_list)
            
            target_name = sel_stagiaire.split(" (")[0]
            selected_copy = next(r for r in r_list if r['name'] == target_name)
            
            st.markdown(f"""
                <div class="white-card">
                    <h2>STAGIAIRE : {selected_copy["name"]}</h2>
                    <h1>Note Finale : {selected_copy["score"]} / 20</h1>
                    <p>Alertes Sécurité enregistrées : <b>{selected_copy.get("cheats", 0)}</b></p>
                </div>
            """, unsafe_allow_html=True)
            
            # Possibilité d'ajuster la note manuellement par le formateur
            st.markdown("#### Ajustement Manuel de la Note")
            new_val = st.number_input("Modifier la note finale :", 0.0, 20.0, float(selected_copy['score']), 0.25)
            if st.button("VALIDER LE CHANGEMENT DE NOTE"):
                get_col('results').document(selected_copy['id']).update({"score": new_val})
                st.success("Note mise à jour avec succès !")
                st.rerun()
                
            st.divider()
            # Affichage de l'audit pédagogique (QCM + Code)
            audit_results_detailed(selected_copy)
        else:
            st.info("En attente de transmission de copies par les stagiaires...")
            
    with t4:
        st.markdown("### 📦 Sauvegarde & Migration")
        if st.button("GÉNÉRER EXTRACTION JSON COMPLÈTE"):
            json_export = json.dumps(r_raw, indent=4, default=str)
            st.download_button("TÉLÉCHARGER BACKUP JSON", json_export, "full_backup_results.json", "application/json")

def exam_view():
    """Interface d'examen pour les stagiaires"""
    if not st.session_state.exam_open:
        show_header()
        st.error("🔒 SESSION CLÔTURÉE. Veuillez contacter votre formateur.")
        return
    
    show_header()
    step_idx = st.session_state.step
    current_ex = EXERCICES[step_idx]
    
    st.markdown(f"### Exercice {current_ex['id']} / {len(EXERCICES)}")
    st.progress((step_idx + 1) / len(EXERCICES))
    
    # Énoncé de l'exercice
    st.markdown(f"""
        <div class="white-card">
            <h3>{current_ex["titre"]}</h3>
            <p style="white-space:pre-wrap; font-size:1.3rem; line-height:1.6;">{current_ex["enonce"]}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Zone de saisie du script Python (Console)
    st.session_state.codes[current_ex['id']] = st.text_area(
        "Éditeur de Code Python (Logiciel : 4 points) :", 
        height=450, 
        key=f"code_editor_{current_ex['id']}", 
        placeholder="# Écrivez votre algorithme ici pour répondre à l'énoncé..."
    )
    
    st.divider()
    # Questions de Validation Théorique
    st.markdown("#### Questions Théoriques (Théorie : 1 point)")
    for q_item in current_ex['questions']:
        if q_item['type'] == 'choice':
            st.session_state.answers[q_item['id']] = st.radio(
                q_item['text'], 
                q_item['options'], 
                key=f"ans_widget_{q_item['id']}"
            )
        else:
            st.session_state.answers[q_item['id']] = st.number_input(
                q_item['text'], 
                key=f"ans_widget_{q_item['id']}", 
                value=0
            )

    # Système de navigation entre les exercices
    st.markdown("---")
    nav_col1, nav_col2 = st.columns([1, 1])
    
    if step_idx > 0:
        if nav_col1.button("⬅️ EXERCICE PRÉCÉDENT"): 
            st.session_state.step -= 1
            st.rerun()
    
    # Bouton de validation finale ou passage à la suite
    is_last = (step_idx == len(EXERCICES) - 1)
    btn_label = "🎯 TRANSMETTRE LA COPIE FINALE" if is_last else "EXERCICE SUIVANT ➡️"
    
    if nav_col2.button(btn_label):
        # Enregistrement du temps passé sur l'étape actuelle
        if st.session_state.ex_start_time:
            st.session_state.durations[current_ex['id']] = time.time() - st.session_state.ex_start_time
            
        if not is_last:
            st.session_state.step += 1
            st.session_state.ex_start_time = time.time()
            st.rerun()
        else:
            # CALCUL AUTOMATIQUE DE LA NOTE FINALE
            final_points = 0.0
            breakdown_stats = {}
            cpm_stats = {}
            
            for e_obj in EXERCICES:
                pts_current = 0.0
                # Calcul QCM (Pondération 1/5)
                q_correct_count = 0
                for q_ref in e_obj['questions']:
                    if str(st.session_state.answers.get(q_ref['id'])) == str(q_ref['correct']):
                        q_correct_count += 1
                pts_current += (q_correct_count / len(e_obj['questions'])) * 1.0
                
                # Calcul Algorithme (Pondération 4/5 - Détection simple de volume de code)
                code_str = st.session_state.codes.get(e_obj['id'], "").strip()
                if len(code_str) > 35: pts_current += 4.0
                elif len(code_str) > 15: pts_current += 2.0
                
                # Analyse de la cadence de frappe (CPM)
                duration_val = st.session_state.durations.get(e_obj['id'], 60)
                calculated_cpm = (len(code_str) / (duration_val/60)) if duration_val > 0 else 0
                cpm_stats[str(e_obj['id'])] = calculated_cpm
                
                breakdown_stats[str(e_obj['id'])] = round(pts_current, 2)
                final_points += pts_current
            
            # Application de la sanction automatique pour non-respect de l'intégrité
            # Chaque perte de focus coûte 2 points sur la note finale
            deduction = st.session_state.cheats * 2.0
            total_score = max(0.0, final_points - deduction)
            
            # Transmission sécurisée à Firestore
            get_col('results').add({
                "username": st.session_state.user['username'],
                "name": st.session_state.user['name'],
                "score": round(total_score, 2),
                "answers": st.session_state.answers,
                "codes": {str(k): v for k, v in st.session_state.codes.items()},
                "timestamp": time.time(),
                "cheats": st.session_state.cheats,
                "breakdown": breakdown_stats,
                "cpm_data": cpm_stats
            })
            
            # Redirection vers l'espace candidat
            st.session_state.page = "👤 Espace Candidat"
            st.rerun()

def login_view():
    """Vue d'authentification centralisée"""
    show_header()
    st.markdown('<div style="max-width:500px; margin:auto; padding-top:40px;">', unsafe_allow_html=True)
    st.markdown('<h2 style="text-align:center; margin-bottom:30px; font-weight:900; color:white;">Terminal d\'Identification</h2>', unsafe_allow_html=True)
    
    user_input = st.text_input("Identifiant Stagiaire / Admin", placeholder="votre.nom.xx")
    pass_input = st.text_input("Mot de passe", type="password", placeholder="********")
    
    if st.button("OUVRIR UNE SESSION"):
        # Accès spécial Formateur
        if user_input == "admin" and pass_input == "admin":
            st.session_state.user = {"name": "Haithem Berkane", "role": "teacher", "username": "admin"}
            st.session_state.page = "📊 Tableau de Bord"
            st.rerun()
        
        # Recherche dans la base stagiaires
        try:
            res_query = get_col('users').where('username', '==', user_input).where('password', '==', pass_input).get()
            if res_query:
                st.session_state.user = res_query[0].to_dict()
                st.session_state.page = "👤 Espace Candidat"
                st.rerun()
            else:
                st.error("Identifiants incorrects ou stagiaire non répertorié.")
        except Exception as e:
            st.error(f"Erreur de connexion : {e}")
            
    st.markdown('</div>', unsafe_allow_html=True)

def student_dash():
    """Dashboard personnel du stagiaire"""
    show_header()
    u_data = st.session_state.user
    st.markdown(f"<h1>Bienvenue, {u_data['name']}</h1>", unsafe_allow_html=True)
    
    # Vérification d'une copie déjà transmise (pour éviter les doublons visuels)
    existing_copie = get_col('results').where('username', '==', u_data['username']).get()
    
    if existing_copie:
        latest_data = existing_copie[0].to_dict()
        st.success(f"### ÉVALUATION TERMINÉE ! Votre note : {latest_data['score']} / 20")
        st.divider()
        # Affichage du retour pédagogique immédiat
        audit_results_detailed(latest_data)
    elif st.session_state.exam_open:
        st.markdown("""
            <div class="white-card">
                <h2>Protocole d'Évaluation</h2>
                <ul>
                    <li><b>Confidentialité :</b> Le partage de sujet est strictement interdit.</li>
                    <li><b>Intégrité :</b> Tout changement de fenêtre sera détecté et entraînera une pénalité automatique de 2 points.</li>
                    <li><b>Sauvegarde :</b> Vos réponses sont enregistrées uniquement lors de la transmission finale.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 DÉMARRER L'ÉPREUVE (SESSION CHRONOMÉTRÉE)"):
            st.session_state.page = "exam"
            st.session_state.ex_start_time = time.time()
            st.rerun()
    else:
        st.warning("🔒 L'EXAMEN EST ACTUELLEMENT CLÔTURÉ. Veuillez patienter jusqu'à l'ouverture de la session.")

def accueil_view():
    """Page d'accueil de la plateforme"""
    show_header()
    st.markdown("""
        <div class="white-card" style="text-align:center; padding:80px !important;">
            <h1 style="font-size:4rem; margin-bottom:30px;">Portail Académique ASR</h1>
            <p style="font-size:1.6rem; color:#444 !important; max-width:800px; margin:auto;">
                Terminal d'évaluation numérique certifié de l'INSFP Belazzoug Athmane. 
                Connectez-vous pour accéder à vos épreuves certificatives.
            </p>
        </div>
    """, unsafe_allow_html=True)

# --- 9. ROUTAGE GÉNÉRAL ET NAVIGATION ---
# Définition dynamique des pages accessibles selon le rôle
current_nav_pages = ["🏠 Accueil", "🔐 Connexion"]
if st.session_state.user:
    current_nav_pages = ["🏠 Accueil"]
    if st.session_state.user['role'] == 'teacher':
        current_nav_pages.append("📊 Tableau de Bord")
    else:
        current_nav_pages.append("👤 Espace Candidat")
    current_nav_pages.append("🚪 Déconnexion")

# Rendu de la Barre de Navigation Style HB
st.markdown('<div class="nav-container">', unsafe_allow_html=True)
nav_cols = st.columns(len(current_nav_pages))
selected_nav = st.session_state.page

for i_nav, p_title in enumerate(current_nav_pages):
    if nav_cols[i_nav].button(p_title, key=f"nav_comp_{p_title}"):
        if p_title == "🚪 Déconnexion":
            st.session_state.user = None
            st.session_state.page = "🏠 Accueil"
        else:
            st.session_state.page = p_title
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# Dispatcher de rendu de page
active_view = st.session_state.page
if active_view == '📊 Tableau de Bord' and st.session_state.user['role'] == 'teacher':
    teacher_dash()
elif active_view == 'exam':
    exam_view()
elif active_view == '👤 Espace Candidat' and st.session_state.user:
    student_dash()
elif active_view == '🔐 Connexion':
    login_view()
else:
    accueil_view()

# --- 10. FOOTER ---
st.markdown(f"""
    <div style="text-align:center; margin-top:120px; padding:60px; border-top:1px solid #333; opacity:0.3; font-size:1rem;">
        Architecture Système ASR Pro v2.7 | Développé par Haithem Berkane | INSFP BBA 01 | © 2026
    </div>
""", unsafe_allow_html=True)
