from datetime import datetime
import json
import os
import numpy as np
import pandas as pd
import streamlit as st
import unicodedata

st.set_page_config(page_title="NBA AI Stephy | Analytics", page_icon="🏀", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #E2E8F0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    section[data-testid="stSidebar"] { background-color: #111827 !important; border-right: 1px solid #1F2937 !important; }
    section[data-testid="stSidebar"] * { color: #F8FAFC !important; }
    div[data-baseweb="select"] > div { background-color: #1E293B !important; border: 1px solid #334155 !important; }
    
    @keyframes radar-pulse { 0% { transform: scale(0.1); opacity: 1; } 100% { transform: scale(1.5); opacity: 0; } }
    .radar-container { position: relative; width: 100px; height: 100px; margin: 30px auto; }
    .radar-ring1 { position: absolute; width: 100%; height: 100%; border: 3px solid #FF4B4B; border-radius: 50%; opacity: 1; animation: radar-pulse 2s linear infinite; }
    .radar-ring2 { position: absolute; width: 100%; height: 100%; border: 3px solid #FF8C00; border-radius: 50%; opacity: 0; animation: radar-pulse 2s linear infinite; animation-delay: 1s; }
    .radar-core { position: absolute; top: 43px; left: 43px; width: 14px; height: 14px; background-color: #34D399; border-radius: 50%; box-shadow: 0 0 15px #34D399; }

    .main-title { font-size: 3rem; font-weight: 800; background: -webkit-linear-gradient(45deg, #FF4B4B, #FF8C00); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 5px; letter-spacing: -1px; }
    .sub-title { font-size: 1.2rem; color: #94A3B8; margin-bottom: 25px; font-weight: 400; }
    
    .card { background-color: #1E293B; padding: 25px; border-radius: 16px; border: 1px solid #334155; margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2); transition: transform 0.2s ease, box-shadow 0.2s ease; }
    .card:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(255, 75, 75, 0.15); border-color: #FF4B4B; }
    .card-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #334155; padding-bottom: 12px; margin-bottom: 15px; }
    .team-vs { font-size: 1.6rem; font-weight: 700; color: #F8FAFC; }
    
    .badge { padding: 4px 10px; border-radius: 20px; font-weight: 700; font-size: 0.80rem; letter-spacing: 0.5px; display: inline-block; }
    [data-testid="stMetricValue"] { color: #F8FAFC !important; font-size: 2.2rem !important; font-weight: 800 !important; }
    [data-testid="stMetricLabel"] { color: #94A3B8 !important; font-size: 1rem !important; font-weight: 600 !important; }
    
    .player-list { list-style-type: none; padding-left: 0; margin-top: 5px; }
    .player-item { background-color: #0F172A; margin-bottom: 8px; padding: 10px 14px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; border-left: 3px solid #475569; font-size: 0.95rem; }
    
    /* Panel de Enfermería */
    .injury-panel { background: #1F0D0D; border: 1px solid #7F1D1D; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    .injury-item { background: #2F1515; padding: 10px; border-radius: 6px; margin-top: 8px; border-left: 4px solid #EF4444; }
</style>
""", unsafe_allow_html=True)

def normalizar_texto(texto):
    if not isinstance(texto, str): return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower().strip()

def render_badge(texto):
    texto_str = str(texto).upper()
    bg, text = "#334155", "#F8FAFC"
    if "VERDE" in texto_str or "CUMPLIDOR" in texto_str or "GRAN VALOR" in texto_str: bg, text = "#065F46", "#34D399"
    elif "AMARILLO" in texto_str or "MODERADO" in texto_str: bg, text = "#78350F", "#FBBF24"
    elif "ROJO" in texto_str or "VOLÁTIL" in texto_str or "SIN VALOR" in texto_str: bg, text = "#7F1D1D", "#F87171"
    elif "PLAYOFFS" in texto_str: bg, text = "#4C1D95", "#C4B5FD"
    return f'<span class="badge" style="background-color: {bg}; color: {text}; border: 1px solid {text}40;">{texto}</span>'

def obtener_patron_titulares(nombre_equipo):
    csv_filename = "Titulares_NBA_Oficiales_30_Equipos(Puntajes Diarios).csv"
    if not os.path.exists(csv_filename): return [], []
    try: df_titulares = pd.read_csv(csv_filename, encoding='utf-8-sig')
    except: return [], []
        
    df_titulares.columns = [str(col).strip().replace("'", "").replace('"', "") for col in df_titulares.columns]
    eq_norm = normalizar_texto(nombre_equipo)
    df_titulares['Equipo_Clean'] = df_titulares[df_titulares.columns[0]].apply(normalizar_texto)
    df_equipo = df_titulares[df_titulares['Equipo_Clean'].str.contains(eq_norm, na=False)]
    
    if df_equipo.empty and " " in eq_norm:
        df_equipo = df_titulares[df_titulares['Equipo_Clean'].str.contains(eq_norm.split()[-1], na=False)]
    if df_equipo.empty: return [], []
        
    titulares, banca = [], []
    for _, row in df_equipo.iterrows():
        nombre_jugador = str(row.get('Jugador', 'Desconocido'))
        puntos_lista = [float(str(row.get(col, "")).replace("pts", "").strip()) for col in df_titulares.columns[3:-1] if "pts" in str(row.get(col, ""))]
        if not puntos_lista: continue
            
        promedio = np.mean(puntos_lista)
        desviacion = np.std(puntos_lista) if len(puntos_lista) > 1 else 1.0
        
        if promedio >= 22.0 and desviacion < 5.0: patron, semaforo = "Estrella Constante", "VERDE"
        elif promedio >= 14.0 and desviacion < 7.0: patron, semaforo = "Estable", "VERDE"
        elif desviacion >= 7.0: patron, semaforo = "Volátil", "ROJO"
        else: patron, semaforo = "Bajo Perfil", "AMARILLO"
            
        jugador_data = (nombre_jugador, round(promedio - 2.0, 1), patron, semaforo, promedio)
        if promedio >= 11.5: titulares.append(jugador_data)
        else: banca.append(jugador_data)
        
    titulares.sort(key=lambda x: x[4], reverse=True)
    banca.sort(key=lambda x: x[4], reverse=True)
    return titulares, banca

st.markdown('<p class="main-title">🏀 NBA AI Stephy</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Motor analítico de proyecciones, divergencia de líneas y reportes de lesiones.</p>', unsafe_allow_html=True)

# LECTURA DEL NUEVO JSON DE LESIONES
alertas_data = {"mensaje_general": "Esperando datos...", "alertas_criticas": [], "ultima_actualizacion": "N/A"}
if os.path.exists("alertas_lesiones.json"):
    try:
        with open("alertas_lesiones.json", "r", encoding="utf-8") as f:
            alertas_data = json.load(f)
    except: pass

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/889/889442.png", width=60)
    st.markdown("### 📡 Monitor IA Stephy")
    st.markdown("""<div class="radar-container"><div class="radar-ring1"></div><div class="radar-ring2"></div><div class="radar-core"></div></div>""", unsafe_allow_html=True)
    st.info("⚡ Escaneando ineficiencias de Las Vegas y Reportes de Lesiones.")
    st.caption("v 3.5 | Injury Tracker Integrado")
    
    # Renderizado del Panel de Lesiones en la barra lateral
    st.markdown("---")
    st.markdown(f"**Última act. médica:** `{alertas_data.get('ultima_actualizacion', 'N/A')}`")
    
    if alertas_data.get("alertas_criticas"):
        st.markdown('<div class="injury-panel">🏥 <b>Bajas Confirmadas (Impacto Alto)</b>', unsafe_allow_html=True)
        for alerta in alertas_data["alertas_criticas"]:
            st.markdown(f"""
            <div class="injury-item">
                <span style="color:#F8FAFC; font-weight:bold;">{alerta['jugador']}</span> ({alerta['equipo']})<br>
                <span style="color:#94A3B8; font-size:0.85rem;">Motivo: {alerta['motivo']}</span><br>
                <span style="color:#F87171; font-weight:bold; font-size:0.9rem;">Impacto: {alerta['impacto_simulador']}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.success(alertas_data.get("mensaje_general", "Sin bajas reportadas."))

ARCHIVO_EVAL = "historial_evaluaciones_nba.csv"
if os.path.exists(ARCHIVO_EVAL):
    try: df = pd.read_csv(ARCHIVO_EVAL, encoding='utf-8-sig')
    except: df = pd.DataFrame()
    
    if "Fecha" in df.columns and len(df) > 0:
        df["Fecha_Clean"] = df["Fecha"].astype(str).str.strip()
        fecha_seleccionada = df["Fecha_Clean"].max()
        df_hoy = df[df["Fecha_Clean"] == fecha_seleccionada]
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Encuentros", len(df_hoy))
        conf_prom = df_hoy["Prob_Ganador_Pct"].dropna().mean() if not df_hoy.empty else 0
        c2.metric("Certeza Moneyline", f"{conf_prom:.1f}%")
        c3.metric("Jornada Activa", fecha_seleccionada)
        c4.metric("Status AI", "🟢 Óptimo")
        st.markdown("---")
        
        for _, row in df_hoy.iterrows():
            local, visita = row.get("Local", "Local"), row.get("Visitante", "Visitante")
            ganador, prob = row.get("Pred_Ganador", "N/A"), row.get("Prob_Ganador_Pct", 50.0)
            linea, prom_sim = row.get("Line_Apuesta", 225.5), row.get("Promedio_Simulado", 225.5)
            pred_ou, sem_puntos = row.get("Pred_OU", "N/A"), row.get("Semaforo_Puntos", "Estándar")
            
            borde_ou = "#F59E0B"
            if "GRAN VALOR" in sem_puntos: borde_ou = "#34D399"
            elif "SIN VALOR" in sem_puntos: borde_ou = "#EF4444"
            
            tit_loc, ban_loc = obtener_patron_titulares(local)
            tit_vis, ban_vis = obtener_patron_titulares(visita)
            
            tarjeta = f"""
            <div class="card">
                <div class="card-header"><div class="team-vs">🏀 {local} <span style="color:#64748B;">vs</span> {visita}</div><div>{render_badge(row.get("Semaforo_Ganador", ""))}</div></div>
                <div style="display: flex; gap: 20px; margin-bottom: 20px;">
                    <div style="background:#0F172A; padding: 12px 20px; border-radius:8px; flex:1; border-left:4px solid #3B82F6;">
                        <span style="color:#94A3B8; font-size:0.9rem; display:block;">MONEYLINE (PROYECCIÓN)</span>
                        <span style="color:#F8FAFC; font-size:1.2rem; font-weight:700;">🏆 {ganador} <span style="color:#34D399;">({prob}%)</span></span>
                    </div>
                    <div style="background:#0F172A; padding: 12px 20px; border-radius:8px; flex:1; border-left:4px solid {borde_ou};">
                        <span style="color:#94A3B8; font-size:0.9rem; display:block;">ANÁLISIS OVER/UNDER (Vegas: {linea})</span>
                        <span style="color:#F8FAFC; font-size:1.2rem; font-weight:700;">📉 {pred_ou} <span style="color:#94A3B8; font-size:1rem;">(Bot Sim: {prom_sim})</span></span>
                        <br><span style="font-size:0.85rem; color:#CBD5E1;">{sem_puntos}</span>
                    </div>
                </div>
            </div>
            """
            st.markdown(tarjeta, unsafe_allow_html=True)
            
            c_loc, c_vis = st.columns(2)
            with c_loc:
                st.markdown(f"#### 🛡️ {local}")
                st.markdown("<ul class='player-list'>" + "".join([f"<li class='player-item'><div><span class='player-name'>{j[0]}</span><br><span class='player-stat'>Proyección: <b style='color:#F8FAFC;'>{j[1]} pts</b></span></div><div>{render_badge(j[3])}</div></li>" for j in tit_loc[:5]]) + "</ul>", unsafe_allow_html=True)
            with c_vis:
                st.markdown(f"#### ⚔️ {visita}")
                st.markdown("<ul class='player-list'>" + "".join([f"<li class='player-item'><div><span class='player-name'>{j[0]}</span><br><span class='player-stat'>Proyección: <b style='color:#F8FAFC;'>{j[1]} pts</b></span></div><div>{render_badge(j[3])}</div></li>" for j in tit_vis[:5]]) + "</ul>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
else:
    st.warning("⚠️ Esperando primer ciclo de datos del bot...")
