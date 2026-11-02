import os
import pandas as pd
import streamlit as st

# Importamos la función autónoma desde nuestro módulo player_analysis.py
from player_analysis import obtener_jugador_autonomo

# Configuración formal de la página (Modo Wide / Ancho completo)
st.set_page_config(
    page_title="NBA AI Prediction Hub", page_icon="🏀", layout="wide"
)

# Estilo visual: Fondo blanco, tarjetas azul celeste y métricas optimizadas
st.markdown("""
<style>
    .stApp {
        background-color: #FFFFFF;
        color: #222222;
    }
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #FF4B4B;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #555555;
        margin-bottom: 20px;
    }
    .card {
        background-color: #EBF3FA;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #D0E3F5;
        margin-bottom: 15px;
        color: #111111;
    }
    [data-testid="stMetricValue"] {
        color: #111111 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #444444 !important;
    }
</style>
""", unsafe_allow_html=True)

def render_badge(texto):
    texto_str = str(texto).upper()
    bg_color = "#D6E8FC"
    text_color = "#003366"
    
    if "VERDE" in texto_str or "CUMPLIDOR" in texto_str:
        bg_color = "#D1E7DD"
        text_color = "#0F5132"
    elif "AMARILLO" in texto_str or "MODERADO" in texto_str:
        bg_color = "#FFF3CD"
        text_color = "#664D03"
    elif "ROJO" in texto_str or "VOLÁTIL" in texto_str:
        bg_color = "#F8D7DA"
        text_color = "#842029"
        
    return f'<span style="background-color: {bg_color}; color: {text_color}; padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 0.85rem;">{texto}</span>'

def generar_consejo_apuesta(prob_ganador, sem_ganador, sem_puntos, pred_ou):
    sem_g_str = str(sem_ganador).upper()
    sem_p_str = str(sem_puntos).upper()
    
    if "VERDE" in sem_g_str and "VERDE" in sem_p_str:
        return "🔥 <b>Alta Confiabilidad (Stake Alto):</b> Escenario ideal. Apuesta al ganador con confianza y entra directo al <b>{}</b> en puntos.".format(pred_ou)
    elif "ROJO" in sem_g_str or "ROJO" in sem_p_str:
        return "🚨 <b>Mucho Riesgo / Volátil (Stake Bajo):</b> Partido impredecible. <b>Evita meter dinero fuerte aquí</b>."
    elif "AMARILLO" in sem_g_str and prob_ganador < 58.0:
        return "⚖️ <b>Partido Muy Parejo (Stake Mínimo):</b> Cuotas cerradas; mejor busca hándicaps o evita el partido."
    else:
        return "⚠️ <b>Precaución Moderada (Stake Medio):</b> Margen ajustado sobre el <b>{}</b>.".format(pred_ou)

# Encabezado principal
st.markdown('<p class="main-title">🏀 NBA AI Prediction Hub</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Panel analítico autónomo con simulación de Monte Carlo y optimización no lineal.</p>', unsafe_allow_html=True)

ARCHIVO_CSV = "historial_evaluaciones_nba.csv"

if os.path.exists(ARCHIVO_CSV):
    df = pd.read_csv(ARCHIVO_CSV)
    
    if "Fecha" in df.columns and len(df) > 0:
        ultima_fecha = df["Fecha"].dropna().iloc[-1]
        df_hoy = df[df["Fecha"] == ultima_fecha]
    else:
        df_hoy = pd.DataFrame()
        ultima_fecha = "N/A"
        
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Partidos de Hoy", len(df_hoy))
    with col2:
        conf_prom = df_hoy["Prob_Ganador_Pct"].dropna().mean() if "Prob_Ganador_Pct" in df_hoy.columns else 0
        st.metric("Confianza Promedio Hoy", f"{conf_prom:.1f}%")
    with col3:
        st.metric("Cartelera del Día", ultima_fecha)
    with col4:
        st.metric("Estado del Sistema", "🟢 Activo / Nube")
        
    st.divider()
    
    st.subheader("🔍 Buscador")
    col_opcion, col_busqueda = st.columns([1, 2])
    
    with col_opcion:
        ver_todos = st.checkbox("📅 Mostrar todos los encuentros de hoy", value=True)
        
    equipos_hoy = sorted(list(set(df_hoy["Local"].dropna().tolist() + df_hoy["Visitante"].dropna().tolist())))
    
    with col_busqueda:
        equipo_seleccionado = st.selectbox("O selecciona un equipo específico:", ["-- Selecciona un equipo --"] + equipos_hoy, disabled=ver_todos)
        
    if ver_todos:
        df_a_mostrar = df_hoy
    else:
        if equipo_seleccionado != "-- Selecciona un equipo --":
            df_a_mostrar = df_hoy[(df_hoy["Local"] == equipo_seleccionado) | (df_hoy["Visitante"] == equipo_seleccionado)]
        else:
            df_a_mostrar = df_hoy
            
    st.markdown(f"### 📊 Predicciones y Sugerencias Analíticas ({ultima_fecha})")
    
    if len(df_a_mostrar) == 0:
        st.info(f"No hay partidos registrados para los filtros seleccionados en la fecha de hoy ({ultima_fecha}).")
    else:
        for _, row in df_a_mostrar.iterrows():
            local = row.get("Local", "Local")
            visita = row.get("Visitante", "Visitante")
            
            ganador = row.get("Pred_Ganador", "N/A")
            if pd.isna(ganador):
                ganador = row.get("Pred_Ganador_Local", "N/A")
                
            prob = row.get("Prob_Ganador_Pct", 50.0)
            if pd.isna(prob):
                prob = 50.0
                
            sem_ganador = row.get("Semaforo_Ganador", "Pendiente")
            if pd.isna(sem_ganador):
                sem_ganador = "Evaluación estándar"
                
            linea = row.get("Line_Apuesta", 225.5)
            pred_ou = row.get("Pred_OU", "N/A")
            prom_sim = row.get("Promedio_Simulado", 225.5)
            
            sem_puntos = row.get("Semaforo_Puntos", "Margen Normal")
            if pd.isna(sem_puntos):
                sem_puntos = "Zona estándar"
                
            badge_ganador_html = render_badge(sem_ganador)
            badge_puntos_html = render_badge(sem_puntos)
            consejo_apuesta = generar_consejo_apuesta(prob, sem_ganador, sem_puntos, pred_ou)
            
            # Consultamos los datos dinámicos mediante el módulo autónomo
            nombre_j1, linea_j1, perfil_j1 = obtener_jugador_autonomo(local, prom_sim)
            nombre_j2, linea_j2, perfil_j2 = obtener_jugador_autonomo(visita, prom_sim)
            
            badge_loc = render_badge(perfil_j1)
            badge_vis = render_badge(perfil_j2)
            
            tarjeta_html = f"""<div class="card">
<h4>🏀 <b>{local}</b> vs <b>{visita}</b></h4>
<hr style="margin: 5px 0 10px 0; border-color: #B0D0E8;">
<p><b>🏆 Ganador Proyectado:</b> {ganador} (Confianza: <b>{prob}%</b>) &nbsp;|&nbsp; <b>Semáforo:</b> {badge_ganador_html}</p>
<p><b>📈 Línea Over/Under ({linea}):</b> Sugerencia <b>{pred_ou}</b> (Puntos Proyectados: <b>{prom_sim}</b>) &nbsp;|&nbsp; <b>Foco Puntos:</b> {badge_puntos_html}</p>
<p style="margin-top: 8px; margin-bottom: 4px;">👤 <b>Análisis de Consistencia Autónoma (Props de Jugadores):</b></p>
<ul style="margin-top: 0px; font-size: 0.9rem; color: #111111;">
<li><b>{nombre_j1}</b> (Línea Mínima: <b>{linea_j1} pts</b>) ➔ {badge_loc}</li>
<li><b>{nombre_j2}</b> (Línea Mínima: <b>{linea_j2} pts</b>) ➔ {badge_vis}</li>
</ul>
<p style="color: #003366; font-size: 0.95rem; margin-top: 10px;">💡 <b>Consejo de Apuesta:</b> {consejo_apuesta}</p>
</div>"""
            
            st.markdown(tarjeta_html, unsafe_allow_html=True)
else:
    st.warning("⚠️ No se encontró el archivo 'historial_evaluaciones_nba.csv' en el repositorio.")
