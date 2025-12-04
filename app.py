import streamlit as st
import requests
import google.generativeai as genai
from datetime import datetime, timedelta
import pytz
import json

# --- 1. CONFIGURAÇÕES E CHAVES ---
st.set_page_config(page_title="Laboratório Spark", page_icon="⚡", layout="wide")

# 🔑 SUAS CHAVES DE API
FOOTBALL_DATA_KEY = "80f8c20cdefe43a295389e79495db66b" # Sua chave de futebol (Já inclusa)
GEMINI_KEY = "AIzaSyDongRd1rUi5qOS0fS6Or452LzRtLn7OIg" # <--- ⚠️ COLE SUA CHAVE DO GOOGLE AQUI

# Configuração da IA
if "COLE_SUA" not in GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# --- 2. CSS "AURORA TECH" ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;500;700;800&family=Inter:wght@400;600&display=swap');

    /* FUNDO AURORA */
    [data-testid="stAppViewContainer"] {
        background-color: #030014;
        background-image: 
            radial-gradient(at 40% 10%, hsla(266, 68%, 20%, 1) 0px, transparent 50%),
            radial-gradient(at 80% 0%, hsla(249, 58%, 20%, 1) 0px, transparent 50%),
            radial-gradient(at 0% 50%, hsla(280, 50%, 10%, 1) 0px, transparent 50%);
        background-attachment: fixed;
        background-size: cover;
    }
    [data-testid="stHeader"] { background: transparent; }
    
    /* TIPOGRAFIA */
    h1, h2, h3 { font-family: 'Plus Jakarta Sans', sans-serif !important; color: white !important; }
    p, span, div { font-family: 'Inter', sans-serif; }

    /* CARDS */
    .match-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 12px;
        transition: transform 0.2s;
    }
    .match-card:hover {
        background: rgba(255, 255, 255, 0.05);
        border-color: rgba(120, 119, 198, 0.3);
        transform: translateY(-2px);
    }

    /* BADGES */
    .status-badge { font-size: 10px; font-weight: 800; text-transform: uppercase; padding: 4px 10px; border-radius: 20px; letter-spacing: 0.5px;}
    .badge-live { background: linear-gradient(90deg, #ff4b4b, #ff0055); color: white; box-shadow: 0 0 15px rgba(255, 0, 85, 0.3); animation: pulse 2s infinite; }
    .badge-end { background: rgba(255, 255, 255, 0.1); color: #888; }
    .badge-future { background: rgba(255, 255, 255, 0.05); color: #aaa; border: 1px solid rgba(255,255,255,0.1); }

    /* ESTATÍSTICAS DA IA */
    .ai-stats-box {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 10px;
        padding: 15px;
        margin-top: 15px;
        border: 1px dashed rgba(0, 255, 136, 0.3);
    }
    .stat-row { display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 0.9rem; color: #ddd; }
    .stat-highlight { color: #00ff88; font-weight: bold; }

    /* PLACAR */
    .score-display { font-family: 'Plus Jakarta Sans'; font-size: 26px; font-weight: 800; color: white; }
    .team-name { color: #e1e1e1; font-size: 13px; font-weight: 600; margin-top: 8px; }

    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNÇÕES (API + IA) ---

@st.cache_data(ttl=60) # Cache rápido para a lista de jogos
def get_matches_api():
    headers = {'X-Auth-Token': FOOTBALL_DATA_KEY}
    # Principais ligas
    competitions = "2021,2014,2019,2002,2001,2013" 
    today = datetime.now()
    date_from = today.strftime('%Y-%m-%d')
    date_to = (today + timedelta(days=5)).strftime('%Y-%m-%d')
    
    url = f"https://api.football-data.org/v4/matches?dateFrom={date_from}&dateTo={date_to}&competitions={competitions}"
    try:
        r = requests.get(url, headers=headers)
        return r.json() if r.status_code == 200 else None
    except: return None

# 🧠 A MÁGICA HÍBRIDA: Função que chama o Gemini
def ask_gemini_stats(home, away, date):
    if "COLE_SUA" in GEMINI_KEY:
        return None
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Atue como um analista de dados de futebol.
    Busque ou estime estatísticas realistas para o jogo: {home} vs {away} (Data: {date}).
    
    Retorne APENAS um JSON (sem markdown) com estes dados estimados ou reais:
    {{
        "possession_h": "valor%", "possession_a": "valor%",
        "shots_h": valor, "shots_a": valor,
        "corners_h": valor, "corners_a": valor,
        "summary": "Uma frase curta de 10 palavras resumindo o jogo."
    }}
    """
    try:
        response = model.generate_content(prompt)
        # Limpeza para garantir JSON puro
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except:
        return None

def to_br_time(utc):
    return datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc).astimezone(pytz.timezone("America/Sao_Paulo"))

# --- 4. INTERFACE ---
(st.markdown("<h1>Laboratório <span style='color:#00ff88'>Spark</span></h1>", unsafe_allow_html=True))

matches_data = get_matches_api()

if not matches_data or 'matches' not in matches_data:
    st.error("Erro ao carregar lista de jogos. Verifique a API Key do Football-Data.")
else:
    matches = matches_data['matches']
    if not matches: st.info("Sem jogos agendados.")
    
    # Agrupamento por Liga
    leagues = {}
    for m in matches:
        lname = m['competition']['name']
        if lname not in leagues: leagues[lname] = []
        leagues[lname].append(m)
    
    tabs = st.tabs(list(leagues.keys()))
    
    for i, (league_name, games) in enumerate(leagues.items()):
        with tabs[i]:
            st.markdown("<br>", unsafe_allow_html=True)
            cols = st.columns(3)
            
            for idx, game in enumerate(games):
                with cols[idx % 3]:
                    # Dados básicos da API (Rápido)
                    h = game['homeTeam']['shortName'] or game['homeTeam']['name']
                    a = game['awayTeam']['shortName'] or game['awayTeam']['name']
                    h_img = game['homeTeam']['crest']
                    a_img = game['awayTeam']['crest']
                    dt_obj = to_br_time(game['utcDate'])
                    status = game['status']
                    
                    # Score e Badge
                    if status in ['IN_PLAY', 'PAUSED', 'FINISHED']:
                        score_h = game['score']['fullTime']['home']
                        score_a = game['score']['fullTime']['away']
                        placar = f"{score_h} - {score_a}"
                        badge = "<span class='status-badge badge-live'>AO VIVO</span>" if status != 'FINISHED' else "<span class='status-badge badge-end'>FIM</span>"
                    else:
                        placar = "vs"
                        badge = f"<span class='status-badge badge-future'>{dt_obj.strftime('%H:%M')}</span>"

                    # CARD VISUAL
                    st.markdown(f"""
                    <div class="match-card">
                        <div style="display:flex; justify-content:space-between; margin-bottom:15px;">
                            <span style="color:#666; font-size:11px; font-weight:bold;">{dt_obj.strftime('%d/%m')}</span>
                            {badge}
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="text-align:center; width:30%;"><img src="{h_img}" style="height:40px;"><br><div class="team-name">{h}</div></div>
                            <div class="score-display">{placar}</div>
                            <div style="text-align:center; width:30%;"><img src="{a_img}" style="height:40px;"><br><div class="team-name">{a}</div></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 🤖 BOTÃO DE IA (EXPANDER)
                    # Usamos uma chave única para o expander não conflitar
                    with st.expander("🤖 Analisar Estatísticas (IA)", expanded=False):
                        if "COLE_SUA" in GEMINI_KEY:
                            st.warning("⚠️ Você precisa colocar sua GEMINI_KEY no código para usar a IA.")
                        else:
                            # Botão para ativar a IA sob demanda
                            if st.button(f"Gerar Dados: {h} x {a}", key=f"btn_{game['id']}"):
                                with st.spinner("A IA está analisando a partida..."):
                                    # Chama a IA aqui
                                    ai_stats = ask_gemini_stats(h, a, dt_obj.strftime('%Y-%m-%d'))
                                    
                                    if ai_stats:
                                        st.markdown(f"""
                                        <div class="ai-stats-box">
                                            <div style="color:#00ff88; font-size:11px; text-transform:uppercase; margin-bottom:10px;">📊 Análise Gemini AI</div>
                                            <div class="stat-row">
                                                <span>🔫 Finalizações</span>
                                                <span><b style="color:white">{ai_stats.get('shots_h','-')}</b> x <b style="color:white">{ai_stats.get('shots_a','-')}</b></span>
                                            </div>
                                            <div class="stat-row">
                                                <span>⛳ Escanteios</span>
                                                <span><b style="color:white">{ai_stats.get('corners_h','-')}</b> x <b style="color:white">{ai_stats.get('corners_a','-')}</b></span>
                                            </div>
                                            <div class="stat-row">
                                                <span>⚽ Posse de Bola</span>
                                                <span><b style="color:white">{ai_stats.get('possession_h','-')}</b> x <b style="color:white">{ai_stats.get('possession_a','-')}</b></span>
                                            </div>
                                            <hr style="border-color:rgba(255,255,255,0.1);">
                                            <div style="font-size:12px; color:#aaa; font-style:italic;">
                                                "{ai_stats.get('summary', 'Dados gerados por IA.')}"
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    else:
                                        st.error("A IA não conseguiu processar este jogo.")