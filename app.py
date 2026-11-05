from datetime import datetime
import json
import os
import numpy as np
import pandas as pd
import streamlit as st

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

def normalizar_texto(texto):
    if not isinstance(texto, str):
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                        if unicodedata.category(c) != 'Mn').lower().strip()

import unicodedata

# Función interna de análisis de jugadores integrada directamente para evitar errores de módulos externos
def obtener_patron_titulares(nombre_equipo):
    # Buscar archivos de titulares disponibles
    csv_filename = "Titulares_NBA_Oficiales_30_Equipos(Puntajes Diarios).csv"
    if not os.path.exists(csv_filename):
        if os.path.exists("Titulares_NBA_Oficiales_30_Equipos(Puntajes Diarios) (1).csv"):
            csv_filename = "Titulares_NBA_Oficiales_30_Equipos(Puntajes Diarios) (1).csv"
        else:
            return [("Jugador predeterminado", "15.5 pts", "Sin datos CSV", "AMARILLO")]
        
    try:
        df_titulares = pd.read_csv(csv_filename, encoding='utf-8-sig')
    except Exception:
        return [("Error leyendo CSV", "15.5 pts", "Error crítico", "ROJO")]
        
    # Acceso directo por posición de columna para evitar KeyErrors absolutos
    col_equipo = df_titulares.columns[0]
    col_posicion = df_titulares.columns[1] if len(df_titulares.columns) > 1 else 'Posicion'
    col_jugador = df_titulares.columns[2] if len(df_titulares.columns) > 2 else 'Jugador'
    
    eq_norm = ''.join(c for c in unicodedata.normalize('NFD', str(nombre_equipo)) if unicodedata.category(c) != 'Mn').lower().strip()
    
    df_titulares['Equipo_Clean'] = df_titulares[col_equipo].apply(lambda x: ''.join(c for c in unicodedata.normalize('NFD', str(x)) if unicodedata.category(c) != 'Mn').lower().strip())
    
    df_equipo = df_titulares[df_titulares['Equipo_Clean'].str.contains(eq_norm, na=False)]
    
    if df_equipo.empty and " " in eq_norm:
        ultima_palabra = eq_norm.split()[-1]
        df_equipo = df_titulares[df_titulares['Equipo_Clean'].str.contains(ultima_palabra, na=False)]
        
    if df_equipo.empty:
        return [(f"Plantilla ({nombre_equipo})", "15.5 pts", "Sin registros exactos en base", "AMARILLO")]
        
    columnas_fechas = df_titulares.columns[3:-1]
    
    resultado = []
    for _, row in df_equipo.iterrows():
        nombre_jugador = str(row.get(col_jugador, 'Jugador Desconocido')).replace("'", "").replace('"', "")
        puntos_lista = []
        for col in columnas_fechas:
            val = str(row.get(col, ""))
            if "pts" in val:
                try:
                    puntos_lista.append(float(val.replace("pts", "").strip()))
                except ValueError:
                    pass
                    
        if not puntos_lista:
            resultado.append((nombre_jugador, "15.5 pts", "Sin datos recientes", "AMARILLO"))
            continue
            
        promedio = np.mean(puntos_lista)
        desviacion = np.std(puntos_lista) if len(puntos_lista) > 1 else 1.0
        linea_prop = round(promedio - 2.0, 1)
        
        if promedio >= 22.0 and desviacion < 5.0:
            patron = "Élite Constante (Cumplidor)"
            semaforo = "VERDE"
        elif promedio >= 15.0 and desviacion < 7.0:
            patron = "Estable / Confiable"
            semaforo = "VERDE"
        elif desviacion >= 7.0 or (max(puntos_lista) - min(puntos_lista)) > 14:
            patron = "Alto Riesgo / Volátil e Irregular"
            semaforo = "ROJO"
        else:
            patron = "Bajo Perfil / Rango Estrecho"
            semaforo = "AMARILLO"
            
        resultado.append((nombre_jugador, f"{linea_prop} pts", patron, semaforo))
        
    return resultado

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
st.markdown('<p class="sub-title">Panel analítico autónomo y unificado.</p>', unsafe_allow_html=True)

# Centro de Alertas dinámico en vivo (Lee alertas_lesiones.json)
mensaje_notificacion = "Monitoreo activo en 30 plantillas. Reporte de última hora: Precaución con rotaciones en equipos en situación de B2B."
if os.path.exists("alertas_lesiones.json"):
    try:
        with open("alertas_lesiones.json", "r", encoding="utf-8") as f:
            data_alerta = json.load(f)
            mensaje_notificacion = data_alerta.get("mensaje", mensaje_notificacion)
    except Exception:
        pass

st.markdown(f"""
<div class="notification-banner">
    🔔 <b>Centro de Alertas & Reporte de Lesiones:</b> {mensaje_notificacion}
</div>
""", unsafe_allow_html=True)

ARCHIVO_EVAL = "historial_evaluaciones_nba.csv"

if os.path.exists(ARCHIVO_EVAL):
    try:
        df = pd.read_csv(ARCHIVO_EVAL, encoding='utf-8-sig')
    except Exception as e:
        st.error(f"Error al leer el archivo de evaluaciones: {e}")
        df = pd.DataFrame()
    
    if "Fecha" in df.columns and len(df) > 0:
        df["Fecha_Clean"] = df["Fecha"].astype(str).str.strip()
        fechas_disponibles = sorted(df["Fecha_Clean"].unique(), reverse=True)
        
        st.sidebar.markdown("### 🎛️ Panel de Control")
        fecha_seleccionada = st.sidebar.selectbox(
            "📅 Selecciona la fecha de la cartelera:", 
            fechas_disponibles,
            index=0
        )
        
        df_hoy = df[df["Fecha_Clean"] == fecha_seleccionada]
        ultima_fecha = fecha_seleccionada
    else:
        df_hoy = pd.DataFrame()
        ultima_fecha = "N/A"
        
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Partidos en Cartelera", len(df_hoy))
    with col2:
        conf_prom = df_hoy["Prob_Ganador_Pct"].dropna().mean() if "Prob_Ganador_Pct" in df_hoy.columns and not df_hoy.empty else 0
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
        
    equipos_hoy = sorted(list(set(df_hoy.get("Local", pd.Series()).dropna().tolist() + df_hoy.get("Visitante", pd.Series()).dropna().tolist())))
    
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
                
            sem_ganador = row.get("Semaforo_Ganador", "Evaluación estándar")
            if pd.isna(sem_ganador):
                sem_ganador = "Evaluación estándar"
                
            linea = row.get("Line_Apuesta", 225.5)
            if pd.isna(linea):
                linea = 225.5
                
            pred_ou = row.get("Pred_OU", "N/A")
            prom_sim = row.get("Promedio_Simulado", 225.5)
            if pd.isna(prom_sim):
                prom_sim = 225.5
                
            sem_puntos = row.get("Semaforo_Puntos", "Zona estándar")
            if pd.isna(sem_puntos):
                sem_puntos = "Zona estándar"
                
            badge_ganador_html = render_badge(sem_ganador)
            badge_puntos_html = render_badge(sem_puntos)
            
            titulares_local = obtener_patron_titulares(local)
            titulares_visita = obtener_patron_titulares(visita)
            
            html_titulares_local = ""
            for item in titulares_local:
                if len(item) >= 4:
                    nombre, linea_prop, patron, sem = item[0], item[1], item[2], item[3]
                else:
                    nombre, linea_prop, patron, sem = item[0], "15.5 pts", "Estable", "VERDE"
                badge_p = render_badge(f"{sem} ({patron})")
                html_titulares_local += f"<li><b>{nombre}</b> (Línea Mínima: <b>{linea_prop}</b>) ➔ {badge_p}</li>"
                
            html_titulares_visita = ""
            for item in titulares_visita:
                if len(item) >= 4:
                    nombre, linea_prop, patron, sem = item[0], item[1], item[2], item[3]
                else:
                    nombre, linea_prop, patron, sem = item[0], "15.5 pts", "Estable", "VERDE"
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
