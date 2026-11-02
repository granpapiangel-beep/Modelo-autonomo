import os
import pandas as pd
import streamlit as st

# Configuración formal de la página (Modo Wide / Ancho completo)
st.set_page_config(
    page_title="NBA AI Prediction Hub", page_icon="🏀", layout="wide"
)

# Estilo visual: Fondo blanco y tarjetas en AZUL CELESTE MUY CLARO (#EBF3FA)
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

  # Filtrar estrictamente la cartelera del día más reciente (hoy en el CSV)
  if "Fecha" in df.columns and len(df) > 0:
    ultima_fecha = df["Fecha"].dropna().iloc[-1]
    df_hoy = df[df["Fecha"] == ultima_fecha]
  else:
    df_hoy = pd.DataFrame()
    ultima_fecha = "N/A"

  # Métricas superiores estilizadas basadas en la cartelera actual
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
  # SECCIÓN DE FILTRADO Y BUSCADOR INTERACTIVO
  # ==========================================
  st.subheader("🔍 Buscador")

  col_opcion, col_busqueda = st.columns([1, 2])

  with col_opcion:
    ver_todos = st.checkbox("📅 Mostrar todos los encuentros de hoy", value=True)

  # Extraemos la lista de equipos que juegan hoy
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

  # Lógica de filtrado según lo que pida el usuario
  if ver_todos:
    df_a_mostrar = df_hoy
  else:
    if equipo_seleccionado != "-- Selecciona un equipo --":
      df_a_mostrar = df_hoy[
          (df_hoy["Local"] == equipo_seleccionado)
          | (df_hoy["Visitante"] == equipo_seleccionado)
      ]
    else:
      df_a_mostrar = df_hoy  # Si no selecciona nada específico, muestra los de hoy

  st.markdown(
      f"### 📊 Predicciones y Sugerencias Analíticas ({ultima_fecha})"
  )

  if len(df_a_mostrar) == 0:
    st.info(
        "No hay partidos registrados para los filtros seleccionados en la fecha"
        f" de hoy ({ultima_fecha})."
    )
  else:
    # Mostramos cada encuentro en tarjetas interactivas limpias con fondo azul celeste
    for _, row in df_a_mostrar.iterrows():
      local = row.get("Local", "Local")
      visita = row.get("Visitante", "Visitante")

      # Blindaje contra valores vacíos (nan)
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

      # Tarjeta visual con fondo azul celeste suave
      with st.container():
        st.markdown(f"""
                    <div class="card">
                        <h4>🏀 <b>{local}</b> vs <b>{visita}</b></h4>
                        <hr style="margin: 5px 0 10px 0; border-color: #B0D0E8;">
                        <p><b>🏆 Ganador Proyectado:</b> {ganador} (Confianza: <b>{prob}%</b>) &nbsp;|&nbsp; <b>Semáforo:</b> <code>{sem_ganador}</code></p>
                        <p><b>📈 Línea Over/Under ({linea}):</b> Sugerencia <b>{pred_ou}</b> (Puntos Proyectados: <b>{prom_sim}</b>) &nbsp;|&nbsp; <b>Foco Puntos:</b> <code>{sem_puntos}</code></p>
                        <p style="color: #004080; font-size: 0.9rem;">💡 <b>Consejo / Motivo del Modelo:</b> Análisis estocástico de Monte Carlo (2,000 iteraciones) cruzando eficiencia ofensiva, factor de forma e inercia defensiva del rival.</p>
                    </div>
                """, unsafe_allow_html=True)

else:
  st.warning(
      "⚠️ No se encontró el archivo 'historial_evaluaciones_nba.csv' en el"
      " repositorio."
  )
