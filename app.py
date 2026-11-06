from datetime import datetime
import json
import os
import numpy as np
import pandas as pd
import streamlit as st
import unicodedata

# 🏀 Configuración de la página
st.set_page_config(
    page_title="NBA AI Stephy | Analytics", 
    page_icon="🏀", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 CSS Moderno - Estilo Cancha / Premium Analytics y Sidebar Oscuro
st.markdown("""
<style>
    /* Fondo principal y textos */
    .stApp {
        background-color: #0E1117;
        color: #E2E8F0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* 🌑 FORZAR SIDEBAR OSCURO (Contraste) */
    section[data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1F2937 !important;
    }
    /* Letras del Sidebar */
    section[data-testid="stSidebar"] label p,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] h3 {
        color: #F8FAFC !important;
    }
    /* Estilo para los Selectores (Cajas desplegables) en el sidebar */
    div[data-baseweb="select"] > div {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        color: #F8FAFC !important;
    }
    div[data-baseweb="select"] span {
        color: #F8FAFC !important;
    }

    /* Animación del Radar IA para el hueco de la barra lateral */
    @keyframes radar-pulse {
        0% { transform: scale(0.1); opacity: 1; }
        100% { transform: scale(1.5); opacity: 0; }
    }
    .radar-container {
        position: relative; width: 100px; height: 100px; margin: 30px auto;
    }
    .radar-ring1 {
        position: absolute; width: 100%; height: 100%; border: 3px solid #FF4B4B; border-radius: 50%; opacity: 1; animation: radar-pulse 2s linear infinite;
    }
    .radar-ring2 {
        position: absolute; width: 100%; height: 100%; border: 3px solid #FF8C00; border-radius: 50%; opacity: 0; animation: radar-pulse 2s linear infinite; animation-delay: 1s;
    }
    .radar-core {
        position: absolute; top: 43px; left: 43px; width: 14px; height: 14px; background-color: #34D399; border-radius: 50%; box-shadow: 0 0 15px #34D399;
    }

    /* Títulos Principales */
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #FF4B4B, #FF8C00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
        letter-spacing: -1px;
    }
    .sub-title {
        font-size: 1.2rem;
        color: #94A3B8;
        margin-bottom: 25px;
        font-weight: 400;
    }
    
    /* Tarjetas de Partido con efecto Hover */
    .card {
        background-color: #1E293B;
        padding: 25px;
        border-radius: 16px;
        border: 1px solid #334155;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(255, 75, 75, 0.15);
        border-color: #FF4B4B;
    }
    
    /* Separadores y encabezados de tarjeta */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2px solid #334155;
        padding-bottom: 12px;
        margin-bottom: 15px;
    }
    .team-vs {
        font-size: 1.6rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    
    /* Banner de Alertas */
    .notification-banner { 
        background: linear-gradient(90deg, #2D3748 0%, #1A202C 100%);
        border-left: 5px solid #FFC107; 
        padding: 16px; 
        border-radius: 8px; 
        margin-bottom: 25px; 
        font-size: 1rem; 
        color: #E2E8F0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Etiquetas / Badges */
    .badge {
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.80rem;
        letter-spacing: 0.5px;
        display: inline-block;
    }
    
    /* Modificando las métricas nativas de Streamlit */
    [data-testid="stMetricValue"] {
        color: #F8FAFC !important;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
    }
    
    /* Listas de jugadores */
    .player-list {
        list-style-type: none;
        padding-left: 0;
        margin-top: 5px;
    }
    .player-item {
        background-color: #0F172A;
        margin-bottom: 8px;
        padding: 10px 14px;
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 3px solid #475569;
        font-size: 0.95rem;
    }
    .player-item:hover {
        border-left: 3px solid #FF8C00;
        background-color: #1E293B;
    }
    .player-name {
        font-weight: 600;
        color: #E2E8F0;
    }
    .player-stat {
        color: #94A3B8;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# 🛠️ Funciones Core
def normalizar_texto(texto):
    if not isinstance(texto, str): return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower().strip()

def render_badge(texto):
    texto_str = str(texto).upper()
    bg, text = "#334155", "#F8FAFC" # Default
    if "VERDE" in texto_str or "CUMPLIDOR" in texto_str: bg, text = "#065F46", "#34D399"
    elif "AMARILLO" in texto_str or "MODERADO" in texto_str: bg, text = "#78350F", "#FBBF24"
    elif "ROJO" in texto_str or "VOLÁTIL" in texto_str: bg, text = "#7F1D1D", "#F87171"
    return f'<span class="badge" style="background-color: {bg}; color: {text}; border: 1px solid {text}40;">{texto}</span>'

def obtener_patron_titulares(nombre_equipo):
    csv_filename = "Titulares_NBA_Oficiales_30_Equipos(Puntajes Diarios).csv"
    if not os.path.exists(csv_filename):
        if os.path.exists("Titulares_NBA_Oficiales_30_Equipos(Puntajes Diarios) (1).csv"):
            csv_filename = "Titulares_NBA_Oficiales_30_Equipos(Puntajes Diarios) (1).csv"
        else: return []
        
    try: df_titulares = pd.read_csv(csv_filename, encoding='utf-8-sig')
    except Exception: return []
        
    df_titulares.columns = [str(col).strip().replace("'", "").replace('"', "").replace('\ufeff', '') for col in df_titulares.columns]
    col_equipo = df_titulares.columns[0]
    col_jugador = df_titulares.columns[2] if len(df_titulares.columns) > 2 else 'Jugador'
    
    eq_norm = normalizar_texto(nombre_equipo)
    df_titulares['Equipo_Clean'] = df_titulares[col_equipo].apply(normalizar_texto)
    df_equipo = df_titulares[df_titulares['Equipo_Clean'].str.contains(eq_norm, na=False)]
    
    if df_equipo.empty and " " in eq_norm:
        df_equipo = df_titulares[df_titulares['Equipo_Clean'].str.contains(eq_norm.split()[-1], na=False)]
    if df_equipo.empty: return []
        
    columnas_fechas = df_titulares.columns[3:-1]
    
    titulares, banca = [], []
    for _, row in df_equipo.iterrows():
        nombre_jugador = str(row.get(col_jugador, 'Desconocido')).replace("'", "").replace('"', "")
        puntos_lista = [float(str(row.get(col, "")).replace("pts", "").strip()) for col in columnas_fechas if "pts" in str(row.get(col, ""))]
        
        if not puntos_lista: continue
            
        promedio = np.mean(puntos_lista)
        desviacion = np.std(puntos_lista) if len(puntos_lista) > 1 else 1.0
        linea_prop = round(promedio - 2.0, 1)
        
        if promedio >= 22.0 and desviacion < 5.0: patron, semaforo = "Estrella Constante", "VERDE"
        elif promedio >= 14.0 and desviacion < 7.0: patron, semaforo = "Estable / Confiable", "VERDE"
        elif desviacion >= 7.0 or (max(puntos_lista) - min(puntos_lista)) > 15: patron, semaforo = "Alto Riesgo (Volátil)", "ROJO"
        else: patron, semaforo = "Bajo Perfil", "AMARILLO"
            
        jugador_data = (nombre_jugador, linea_prop, patron, semaforo, promedio)
        
        # Separación inteligente
        if promedio >= 11.5: titulares.append(jugador_data)
        else: banca.append(jugador_data)
        
    titulares.sort(key=lambda x: x[4], reverse=True)
    banca.sort(key=lambda x: x[4], reverse=True)
    
    return titulares, banca

def generar_html_jugadores(lista_jugadores):
    if not lista_jugadores: return "<p style='color: #64748B; font-size: 0.9rem;'>No hay datos recientes disponibles.</p>"
    html = "<ul class='player-list'>"
    for j in lista_jugadores:
        badge = render_badge(f"{j[3]} ({j[2]})")
        html += f"""
        <li class='player-item'>
            <div><span class='player-name'>{j[0]}</span> <br> <span class='player-stat'>Línea base proyectada: <b style="color:#F8FAFC;">{j[1]} pts</b></span></div>
            <div>{badge}</div>
        </li>"""
    html += "</ul>"
    return html

# ==========================================
# 🚀 INTERFAZ VISUAL & SIDEBAR
# ==========================================
st.markdown('<p class="main-title">🏀 NBA AI Stephy</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Motor analítico de proyecciones y volatilidad en tiempo real.</p>', unsafe_allow_html=True)

ARCHIVO_EVAL = "historial_evaluaciones_nba.csv"
if os.path.exists(ARCHIVO_EVAL):
    try: df = pd.read_csv(ARCHIVO_EVAL, encoding='utf-8-sig')
    except: df = pd.DataFrame()
    
    if "Fecha" in df.columns and len(df) > 0:
        df["Fecha_Clean"] = df["Fecha"].astype(str).str.strip()
        fechas_disponibles = sorted(df["Fecha_Clean"].unique(), reverse=True)
        
        with st.sidebar:
            st.image("https://cdn-icons-png.flaticon.com/512/889/889442.png", width=60)
            st.markdown("### 🎛️ Centro de Comando")
            fecha_seleccionada = st.selectbox("📅 Selecciona la Jornada:", fechas_disponibles, index=0)
            ver_todos = st.checkbox("Mostrar toda la cartelera", value=True)
            df_hoy = df[df["Fecha_Clean"] == fecha_seleccionada]
            equipos_hoy = sorted(list(set(df_hoy.get("Local", pd.Series()).dropna().tolist() + df_hoy.get("Visitante", pd.Series()).dropna().tolist())))
            equipo_seleccionado = st.selectbox("🎯 Filtrar por Franquicia:", ["-- Selecciona --"] + equipos_hoy, disabled=ver_todos)
            
            st.markdown("---")
            st.markdown("### 📡 Monitor IA Stephy")
            
            # Animación del Radar CSS
            st.markdown("""
            <div class="radar-container">
                <div class="radar-ring1"></div>
                <div class="radar-ring2"></div>
                <div class="radar-core"></div>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("⚡ Escaneando fluctuaciones de líneas y ausencias en tiempo real...")
            st.caption("v 2.0 | Base de datos sincronizada")
            
        ultima_fecha = fecha_seleccionada
    else: df_hoy = pd.DataFrame(); ultima_fecha = "N/A"
    
    # Banner dinámico
    mensaje_noti = "Monitoreo activo en 30 plantillas. Reporte de última hora: Evaluando escenarios B2B."
    if os.path.exists("alertas_lesiones.json"):
        try:
            with open("alertas_lesiones.json", "r", encoding="utf-8") as f:
                mensaje_noti = json.load(f).get("mensaje", mensaje_noti)
        except: pass
    st.markdown(f'<div class="notification-banner">🚨 <b>Alerta del Sistema:</b> {mensaje_noti}</div>', unsafe_allow_html=True)
    
    # Métricas Dashboard
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Encuentros", len(df_hoy))
    conf_prom = df_hoy["Prob_Ganador_Pct"].dropna().mean() if "Prob_Ganador_Pct" in df_hoy.columns and not df_hoy.empty else 0
    c2.metric("Nivel de Certeza", f"{conf_prom:.1f}%")
    c3.metric("Jornada Activa", ultima_fecha)
    c4.metric("Status AI", "🟢 Óptimo")
    
    st.markdown("---")
    
    # Procesamiento de filtro
    df_a_mostrar = df_hoy if ver_todos or equipo_seleccionado == "-- Selecciona --" else df_hoy[(df_hoy["Local"] == equipo_seleccionado) | (df_hoy["Visitante"] == equipo_seleccionado)]
    
    if len(df_a_mostrar) == 0:
        st.info("No hay encuentros para los filtros seleccionados.")
    else:
        for _, row in df_a_mostrar.iterrows():
            local, visita = row.get("Local", "Local"), row.get("Visitante", "Visitante")
            ganador = row.get("Pred_Ganador", row.get("Pred_Ganador_Local", "N/A"))
            prob = row.get("Prob_Ganador_Pct", 50.0)
            sem_ganador = row.get("Semaforo_Ganador", "Estándar")
            linea, prom_sim = row.get("Line_Apuesta", 225.5), row.get("Promedio_Simulado", 225.5)
            pred_ou = row.get("Pred_OU", "N/A")
            sem_puntos = row.get("Semaforo_Puntos", "Estándar")
            
            tit_loc, ban_loc = obtener_patron_titulares(local)
            tit_vis, ban_vis = obtener_patron_titulares(visita)
            
            # HTML Tarjeta de Partido
            tarjeta = f"""
            <div class="card">
                <div class="card-header">
                    <div class="team-vs">🏀 {local} <span style="color:#64748B; font-weight:400; font-size:1.2rem;">vs</span> {visita}</div>
                    <div>{render_badge(sem_ganador)}</div>
                </div>
                <div style="display: flex; gap: 20px; margin-bottom: 20px;">
                    <div style="background:#0F172A; padding: 12px 20px; border-radius:8px; flex:1; border-left:4px solid #3B82F6;">
                        <span style="color:#94A3B8; font-size:0.9rem; display:block; margin-bottom:4px;">PROYECCIÓN DE VICTORIA</span>
                        <span style="color:#F8FAFC; font-size:1.2rem; font-weight:700;">🏆 {ganador} <span style="color:#34D399;">({prob}%)</span></span>
                    </div>
                    <div style="background:#0F172A; padding: 12px 20px; border-radius:8px; flex:1; border-left:4px solid #F59E0B;">
                        <span style="color:#94A3B8; font-size:0.9rem; display:block; margin-bottom:4px;">TOTAL PUNTOS (O/U: {linea})</span>
                        <span style="color:#F8FAFC; font-size:1.2rem; font-weight:700;">📈 {pred_ou} <span style="color:#94A3B8; font-size:1rem;">(Sim: {prom_sim})</span></span>
                    </div>
                </div>
            </div>
            """
            st.markdown(tarjeta, unsafe_allow_html=True)
            
            # Columnas nativas para jugadores debajo de la tarjeta
            col_loc, col_vis = st.columns(2)
            
            with col_loc:
                st.markdown(f"#### 🛡️ {local}")
                t1, t2 = st.tabs(["🌟 Titulares / Rotación Principal", "🪑 Banca / Minutos Bajos"])
                with t1: st.markdown(generar_html_jugadores(tit_loc), unsafe_allow_html=True)
                with t2: st.markdown(generar_html_jugadores(ban_loc), unsafe_allow_html=True)
                
            with col_vis:
                st.markdown(f"#### ⚔️ {visita}")
                t3, t4 = st.tabs(["🌟 Titulares / Rotación Principal", "🪑 Banca / Minutos Bajos"])
                with t3: st.markdown(generar_html_jugadores(tit_vis), unsafe_allow_html=True)
                with t4: st.markdown(generar_html_jugadores(ban_vis), unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
else:
    st.warning("⚠️ Esperando primer ciclo de datos del bot...")
