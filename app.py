# app.py
import os
import pandas as pd
import streamlit as st
from player_analysis import obtener_patron_titulares

st.set_page_config(
    page_title="NBA AI Prediction Hub", page_icon="🏀", layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; color: #222222; }
    .main-title { font-size: 2.5rem; font-weight: 700; color: #FF4B4B; margin-bottom: 0px; }
    .sub-title { font-size: 1.1rem; color: #555555; margin-bottom: 20px; }
    .card { background-color: #EBF3FA; padding: 20px; border-radius: 10px; border: 1px solid #D0E3F5; margin-bottom: 15px; color: #111111; }
    .notification-banner { background-color: #FFF3CD; border-left: 5px solid #FFC107; padding: 12px; border-radius: 4px; margin-bottom: 20px; font-size: 0.95rem; color: #856404; }
</style>
""", unsafe_allow_html=True)

def render_badge(texto):
    texto_str = str(texto).upper()
    bg_color, text_color = "#D6E8FC", "#003366"
    if "VERDE" in texto_str or "CUMPLIDOR" in texto_str:
        bg_color, text_color = "#D1E7DD", "#0F5132"
    elif "AMARILLO" in texto_str or "MODERADO" in texto_str:
        bg_color, text_color = "#FFF3CD", "#664D03"
    elif "ROJO" in texto_str or "VOLÁTIL" in texto_str:
        bg_color, text_color = "#F8D7DA", "#842029"
    return f'<span style="background-color: {bg_color}; color: {text_color}; padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 0.85rem;">{texto}</span>'

# Encabezado principal con Campanita de Alerta / Notificaciones del Bot
st.markdown('<p class="main-title">🏀 NBA AI Prediction Hub</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Panel analítico autónomo con simulación de Monte Carlo y patrones de cumplimiento.</p>', unsafe_allow_html=True)

# 🔔 Campanita de Notificaciones del Sistema y Estado de Lesiones
st.markdown("""
<div class="notification-banner">
    🔔 <b>Centro de Alertas & Reporte de Lesiones:</b> Sincronización nocturna completa. Monitoreo de ausencias y rotaciones activo en 30 plantillas. Los umbrales de volatilidad han sido recalculados.
</div>
""", unsafe_allow_html=True)

ARCHIVO_EVAL = "historial_evaluaciones_nba.csv"

if os.path.exists(ARCHIVO_EVAL):
    df = pd.read_csv(ARCHIVO_EVAL)
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
        st.metric("Confianza Promedio", f"{conf_prom:.1f}%")
    with col3:
        st.metric("Cartelera", ultima_fecha)
    with col4:
        st.metric("Estado del Bot", "🟢 Activo / 30 Equipos")
        
    st.divider()
    
    st.subheader("🔍 Buscador de Encuentros y Patrones de Jugadores")
    col_opcion, col_busqueda = st.columns([1, 2])
    with col_opcion:
        ver_todos = st.checkbox("📅 Mostrar todos los encuentros", value=True)
        
    equipos_hoy = sorted(list(set(df_hoy["Local"].dropna().tolist() + df_hoy["Visitante"].dropna().tolist())))
    with col_busqueda:
        equipo_seleccionado = st.selectbox("O filtra por un equipo específico:", ["-- Selecciona un equipo --"] + equipos_hoy, disabled=ver_todos)
        
    df_a_mostrar = df_hoy if ver_todos else (df_hoy[(df_hoy["Local"] == equipo_seleccionado) | (df_hoy["Visitante"] == equipo_seleccionado)] if equipo_seleccionado != "-- Selecciona un equipo --" else df_hoy)
            
    st.markdown(f"### 📊 Predicciones Analíticas ({ultima_fecha})")
    
    if len(df_a_mostrar) == 0:
        st.info("No hay partidos registrados para los filtros seleccionados.")
    else:
        for _, row in df_a_mostrar.iterrows():
            local, visita = row.get("Local", "Local"), row.get("Visitante", "Visitante")
            ganador = row.get("Pred_Ganador", row.get("Pred_Ganador_Local", "N/A"))
            prob = row.get("Prob_Ganador_Pct", 50.0)
            sem_ganador = row.get("Semaforo_Ganador", "Pendiente")
            linea = row.get("Line_Apuesta", 225.5)
            pred_ou = row.get("Pred_OU", "N/A")
            prom_sim = row.get("Promedio_Simulado", 225.5)
            sem_puntos = row.get("Semaforo_Puntos", "Margen Normal")
            
            badge_ganador_html = render_badge(sem_ganador)
            badge_puntos_html = render_badge(sem_puntos)
            
            # Llamado al motor de análisis de jugadores corregido
            titulares_local = obtener_patron_titulares(local)
            titulares_visita = obtener_patron_titulares(visita)
            
            html_loc = "".join([f"<li><b>{n}</b> (Línea Mínima: <b>{lp}</b>) ➔ {render_badge(f'{s} ({pat})')}</li>" for n, lp, pat, s in titulares_local])
            html_vis = "".join([f"<li><b>{n}</b> (Línea Mínima: <b>{lp}</b>) ➔ {render_badge(f'{s} ({pat})')}</li>" for n, lp, pat, s in titulares_visita])
            
            tarjeta_html = f"""<div class="card">
<h4>🏀 <b>{local}</b> vs <b>{visita}</b></h4>
<hr style="margin: 5px 0 10px 0; border-color: #B0D0E8;">
<p><b>🏆 Ganador Proyectado:</b> {ganador} (Confianza: <b>{prob}%</b>) &nbsp;|&nbsp; <b>Semáforo:</b> {badge_ganador_html}</p>
<p><b>📈 Línea Over/Under ({linea}):</b> Sugerencia <b>{pred_ou}</b> (Proyectados: <b>{prom_sim}</b>) &nbsp;|&nbsp; <b>Foco Puntos:</b> {badge_puntos_html}</p>
<p style="margin-top: 8px; margin-bottom: 2px;">👤 <b>Titulares y Consistencia ({local}):</b></p>
<ul style="margin-top: 0px; margin-bottom: 6px; font-size: 0.9rem; color: #111111;">{html_loc}</ul>
<p style="margin-top: 6px; margin-bottom: 2px;">👤 <b>Titulares y Consistencia ({visita}):</b></p>
<ul style="margin-top: 0px; font-size: 0.9rem; color: #111111;">{html_vis}</ul>
</div>"""
            st.markdown(tarjeta_html, unsafe_allow_html=True)
else:
    st.warning("⚠️ No se encontró el archivo 'historial_evaluaciones_nba.csv' en el repositorio.")
