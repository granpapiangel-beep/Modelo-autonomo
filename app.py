import os
import pandas as pd
import streamlit as st

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
        /* Forzar visibilidad de textos en métricas */
        [data-testid="stMetricValue"] {
            color: #111111 !important;
        }
        [data-testid="stMetricLabel"] {
            color: #444444 !important;
        }
    </style>
""", unsafe_allow_html=True)


# Función para asignar colores suaves a los semáforos
def render_badge(texto):
  texto_str = str(texto).upper()
  bg_color = "#D6E8FC"
  text_color = "#003366"

  if "VERDE" in texto_str:
    bg_color = "#D1E7DD"
    text_color = "#0F5132"
  elif "AMARILLO" in texto_str:
    bg_color = "#FFF3CD"  # Amarillo claro suave
    text_color = "#664D03"
  elif "ROJO" in texto_str:
    bg_color = "#F8D7DA"
    text_color = "#842029"

  return f'<span style="background-color: {bg_color}; color: {text_color}; padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 0.85rem;">{texto}</span>'


# Función para generar un consejo de apuesta claro y directo (usando HTML en lugar de Markdown)
def generar_consejo_apuesta(prob_ganador, sem_ganador, sem_puntos, pred_ou):
  sem_g_str = str(sem_ganador).upper()
  sem_p_str = str(sem_puntos).upper()

  if "VERDE" in sem_g_str and "VERDE" in sem_p_str:
    return (
        "🔥 <b>Alta Confiabilidad (Stake Alto):</b> Escenario ideal. Apuesta al"
        f" ganador con confianza y entra directo al <b>{pred_ou}</b> en puntos."
        " Margen sólido."
    )
  elif "ROJO" in sem_g_str or "ROJO" in sem_p_str:
    return (
        "🚨 <b>Mucho Riesgo / Volátil (Stake Bajo o Nulo):</b> Partido"
        " impredecible o con alta incertidumbre estadística. <b>Evita meter"
        " dinero fuerte aquí</b> o busca líneas alternativas."
    )
  elif "AMARILLO" in sem_g_str and prob_ganador < 58.0:
    return (
        "⚖️ <b>Partido Muy Parejo (Stake Mínimo):</b> No hay un favorito claro"
        " en la duela. Las cuotas están cerradas; mejor busca un hándicap"
        " favorable o abstente."
    )
  else:
    return (
        "⚠️ <b>Precaución Moderada (Stake Medio):</b> Hay ligera tendencia, pero"
        " el margen es ajustado. Si apuestas, hazlo con cautela sobre el "
        f"<b>{pred_ou}</b>."
    )


# Encabezado principal
st.markdown(
    '<p class="main-title">🏀 NBA AI Prediction Hub</p>', unsafe_allow_html=True
)
st.markdown(
    '<p class="sub-title">Panel analítico autónomo con simulación de Monte'
    " Carlo y optimización no lineal.</p>",
    unsafe_allow_html=True,
)

# Carga de datos
ARCHIVO_CSV = "historial_evaluaciones_nba.csv"

if os.path.exists(ARCHIVO_CSV):
  df = pd.read_csv(ARCHIVO_CSV)

  # Filtrar estrictamente la cartelera del día más reciente
  if "Fecha" in df.columns and len(df) > 0:
    ultima_fecha = df["Fecha"].dropna().iloc[-1]
    df_hoy = df[df["Fecha"] == ultima_fecha]
  else:
    df_hoy = pd.DataFrame()
    ultima_fecha = "N/A"

  # Métricas superiores estilizadas
  col1, col2, col3, col4 = st.columns(4)
  with col1:
    st.metric("Partidos de Hoy", len(df_hoy))
  with col2:
    conf_prom = (
        df_hoy["Prob_Ganador_Pct"].dropna().mean()
        if "Prob_Ganador_Pct" in df_hoy.columns
        else 0
    )
    st.metric("Confianza Promedio Hoy", f"{conf_prom:.1f}%")
  with col3:
    st.metric("Cartelera del Día", ultima_fecha)
  with col4:
    st.metric("Estado del Sistema", "🟢 Activo / Nube")

  st.divider()

  # ==========================================
  # SECCIÓN DE FILTRADO Y BUSCADOR
  # ==========================================
  st.subheader("🔍 Buscador")

  col_opcion, col_busqueda = st.columns([1, 2])

  with col_opcion:
    ver_todos = st.checkbox("📅 Mostrar todos los encuentros de hoy", value=True)

  equipos_hoy = sorted(
      list(
          set(
              df_hoy["Local"].dropna().tolist()
              + df_hoy["Visitante"].dropna().tolist()
          )
      )
  )

  with col_busqueda:
    equipo_seleccionado = st.selectbox(
        "O selecciona un equipo específico:",
        ["-- Selecciona un equipo --"] + equipos_hoy,
        disabled=ver_todos,
    )

  if ver_todos:
    df_a_mostrar = df_hoy
  else:
    if equipo_seleccionado != "-- Selecciona un equipo --":
      df_a_mostrar = df_hoy[
          (df_hoy["Local"] == equipo_seleccionado)
          | (df_hoy["Visitante"] == equipo_seleccionado)
      ]
    else:
      df_a_mostrar = df_hoy

  st.markdown(
      f"### 📊 Predicciones y Sugerencias Analíticas ({ultima_fecha})"
  )

  if len(df_a_mostrar) == 0:
    st.info(
        "No hay partidos registrados para los filtros seleccionados en la fecha"
        f" de hoy ({ultima_fecha})."
    )
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

      consejo_apuesta = generar_consejo_apuesta(
          prob, sem_ganador, sem_puntos, pred_ou
      )

      # Tarjeta visual limpia con consejo de apuestas en HTML puro
      with st.container():
        st.markdown(f"""
                    <div class="card">
                        <h4>🏀 <b>{local}</b> vs <b>{visita}</b></h4>
                        <hr style="margin: 5px 0 10px 0; border-color: #B0D0E8;">
                        <p><b>🏆 Ganador Proyectado:</b> {ganador} (Confianza: <b>{prob}%</b>) &nbsp;|&nbsp; <b>Semáforo:</b> {badge_ganador_html}</p>
                        <p><b>📈 Línea Over/Under ({linea}):</b> Sugerencia <b>{pred_ou}</b> (Puntos Proyectados: <b>{prom_sim}</b>) &nbsp;|&nbsp; <b>Foco Puntos:</b> {badge_puntos_html}</p>
                        <p style="color: #003366; font-size: 0.95rem; margin-top: 10px;">💡 <b>Consejo de Apuesta:</b> {consejo_apuesta}</p>
                    </div>
                """, unsafe_allow_html=True)

else:
  st.warning(
      "⚠️ No se encontró el archivo 'historial_evaluaciones_nba.csv' en el"
      " repositorio."
  )
