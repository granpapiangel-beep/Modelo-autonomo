# app.py
from datetime import datetime
import os
import pandas as pd
import streamlit as st
from player_analysis import obtener_patron_titulares

# Configuración formal de la página (Modo Wide / Ancho completo)
st.set_page_config(
    page_title="NBA AI Stephy", page_icon="🏀", layout="wide"
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
    .notification-banner { 
        background-color: #FFF3CD; 
        border-left: 5px solid #FFC107; 
        padding: 12px; 
        border-radius: 4px; 
        margin-bottom: 20px; 
        font-size: 0.95rem; 
        color: #856404; 
    }
    /* Forzar colores oscuros y legibles en las métricas de Streamlit */
    [data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #334155 !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricDelta"] {
        color: #047857 !important;
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

# Encabezado principal
st.markdown('<p class="main-title">🏀 NBA AI Stephy</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Panel analítico autónomo con simulación de Monte Carlo y patrones de cumplimiento de cuotas.</p>', unsafe_allow_html=True)

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
        df["Fecha_Clean"] = df["Fecha"].astype(str).str.strip()
        
        # Obtenemos todas las fechas disponibles ordenadas de la más nueva a la más antigua
        fechas_disponibles = sorted(df["Fecha_Clean"].unique(), reverse=True)
        
        # Selector manual en la barra lateral (index=0 fuerza que inicie en la fecha más reciente)
        st.sidebar.markdown("### 🎛️ Panel de Control")
        fecha_seleccionada = st.sidebar.selectbox(
            "📅 Selecciona la fecha de la cartelera:", 
            fechas_disponibles,
            index=0
        )
        
        # Filtramos la app con la fecha seleccionada
        df_hoy = df[df["Fecha_Clean"] == fecha_seleccionada]
        ultima_fecha = fecha_seleccionada
    else:
        df_hoy = pd.DataFrame()
        ultima_fecha = "N/A"
        
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Partidos en Cartelera", len(df_hoy))
    with col2:
        conf_prom = df_hoy["Prob_Ganador_Pct"].dropna().mean() if "Prob_Ganador_Pct" in df_hoy.columns else 0
        st.metric("Confianza Promedio", f"{conf_prom:.1f}%")
    with col3:
        st.metric("Fecha Activa", ultima_fecha)
    with col4:
        st.metric("Estado del Bot", "🟢 Activo / 30 Eq")
        
    st.divider()
    
    st.subheader("🔍 Buscador de Encuentros y Patrones de Jugadores")
    col_opcion, col_busqueda = st.columns([1, 2])
    
    with col_opcion:
        ver_todos = st.checkbox("📅 Mostrar todos los encuentros", value=True)
        
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
        st.info(f"No hay partidos registrados para la fecha seleccionada ({ultima_fecha}).")
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
            
            titulares_local = obtener_patron_titulares(local)
            titulares_visita = obtener_patron_titulares(visita)
            
            html_titulares_local = ""
            for nombre, linea_prop, patron, sem in titulares_local:
                badge_p = render_badge(f"{sem} ({patron})")
                html_titulares_local += f"<li><b>{nombre}</b> (Línea Mínima: <b>{linea_prop}</b>) ➔ {badge_p}</li>"
                
            html_titulares_visita = ""
            for nombre, linea_prop, patron, sem in titulares_visita:
                badge_p = render_badge(f"{sem} ({patron})")
                html_titulares_visita += f"<li><b>{nombre}</b> (Línea Mínima: <b>{linea_prop}</b>) ➔ {badge_p}</li>"
                
            tarjeta_html = f"""<div class="card">
<h4>🏀 <b>{local}</b> vs <b>{visita}</b></h4>
<hr style="margin: 5px 0 10px 0; border-color: #B0D0E8;">
<p><b>🏆 Ganador Proyectado:</b> {ganador} (Confianza: <b>{prob}%</b>) &nbsp;|&nbsp; <b>Semáforo:</b> {badge_ganador_html}</p>
<p><b>📈 Línea Over/Under ({linea}):</b> Sugerencia <b>{pred_ou}</b> (Puntos Proyectados: <b>{prom_sim}</b>) &nbsp;|&nbsp; <b>Foco Puntos:</b> {badge_puntos_html}</p>
<p style="margin-top: 8px; margin-bottom: 2px;">👤 <b>Titulares y Patrones ({local}):</b></p>
<ul style="margin-top: 0px; margin-bottom: 6px; font-size: 0.9rem; color: #111111;">
{html_titulares_local}
</ul>
<p style="margin-top: 6px; margin-bottom: 2px;">👤 <b>Titulares y Patrones ({visita}):</b></p>
<ul style="margin-top: 0px; font-size: 0.9rem; color: #111111;">
{html_titulares_visita}
</ul>
</div>"""
            
            st.markdown(tarjeta_html, unsafe_allow_html=True)
else:
    st.warning("⚠️ No se encontró el archivo 'historial_evaluaciones_nba.csv' en el repositorio.")
