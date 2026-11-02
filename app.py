import os
import pandas as pd
import streamlit as st

# Configuración formal de la página (Modo Wide / Ancho completo)
st.set_page_config(
    page_title="NBA AI Prediction Hub", page_icon="🏀", layout="wide"
)

# Estilo visual moderno y limpio
st.markdown("""
    <style>
        .main-title {
            font-size: 2.5rem;
            font-weight: 700;
            color: #FF4B4B;
            margin-bottom: 0px;
        }
        .sub-title {
            font-size: 1.1rem;
            color: #A0A0A0;
            margin-bottom: 20px;
        }
        .card {
            background-color: #1E1E1E;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #333333;
            margin-bottom: 15px;
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

  # Métricas superiores estilizadas
  col1, col2, col3, col4 = st.columns(4)
  with col1:
    st.metric("Total de Partidos", len(df))
  with col2:
    conf_prom = (
        df["Prob_Ganador_Pct"].dropna().mean()
        if "Prob_Ganador_Pct" in df.columns
        else 0
    )
    st.metric("Confianza Promedio", f"{conf_prom:.1f}%")
  with col3:
    ultima_fecha = (
        df["Fecha"].iloc[-1] if "Fecha" in df.columns else "Desconocida"
    )
    st.metric("Última Actualización", ultima_fecha)
  with col4:
    st.metric("Estado del Sistema", "🟢 Activo / Nube")

  st.divider()

  # ==========================================
  # BARRA INTERACTIVA: ¿Qué encuentro quieres ver?
  # ==========================================
  st.subheader("🔍 Buscador Interactivo de Partidos")

  # Obtenemos la lista única de equipos disponibles en el CSV
  equipos_locales = (
      df["Local"].dropna().unique().tolist()
      if "Local" in df.columns
      else []
  )
  equipos_visitas = (
      df["Visitante"].dropna().unique().tolist()
      if "Visitante" in df.columns
      else []
  )
  todos_los_equipos = sorted(list(set(equipos_locales + equipos_visitas)))

  equipo_seleccionado = st.selectbox(
      "¿Qué equipo o encuentro quieres consultar hoy?",
      ["-- Muestra todos los partidos --"] + todos_los_equipos,
  )

  # Filtrado dinámico
  df_filtrado = df.copy()
  if equipo_seleccionado != "-- Muestra todos los partidos --":
    df_filtrado = df[
        (df["Local"] == equipo_seleccionado)
        | (df["Visitante"] == equipo_seleccionado)
    ]

  st.markdown("### 📊 Detalle y Motivos de las Predicciones")

  # Mostramos cada partido en tarjetas interactivas con su respectivo "Motivo analítico"
  for _, row in df_filtrado.tail(10).iterrows():
    fecha = row.get("Fecha", "N/A")
    local = row.get("Local", "Local")
    visita = row.get("Visitante", "Visitante")
    ganador = row.get("Pred_Ganador", "N/A")
    prob = row.get("Prob_Ganador_Pct", 50.0)
    sem_ganador = row.get("Semaforo_Ganador", "N/A")
    linea = row.get("Line_Apuesta", 225.5)
    pred_ou = row.get("Pred_OU", "N/A")
    prom_sim = row.get("Promedio_Simulado", 225.5)
    sem_puntos = row.get("Semaforo_Puntos", "N/A")

    # Tarjeta visual por partido
    with st.container():
      st.markdown(f"""
                <div class="card">
                    <h4>📅 {fecha} | 🏀 <b>{local}</b> vs <b>{visita}</b></h4>
                    <hr style="margin: 5px 0 10px 0; border-color: #444;">
                    <p><b>🏆 Ganador Proyectado:</b> {ganador} (Confianza: <b>{prob}%</b>) - <i>{sem_ganador}</i></p>
                    <p><b>📈 Over/Under (Línea {linea}):</b> Predicción <b>{pred_ou}</b> (Simulado: {prom_sim} pts) - <i>{sem_puntos}</i></p>
                    <p style="color: #88CCEE; font-size: 0.9rem;">💡 <b>Motivo del Modelo:</b> Derivado del análisis matricial de Tiers, factor de forma reciente y cruce de eficiencia defensiva del rival mediante simulaciones estocásticas de Monte Carlo (2,000 iteraciones).</p>
                </div>
            """, unsafe_allow_html=True)

  st.divider()

  # Vista clásica de tabla completa para Métodos Numéricos / Minería de Datos
  with st.expander("📁 Ver base de datos completa en formato tabular"):
    st.dataframe(df, use_container_width=True)

else:
  st.warning(
      "⚠️ No se encontró el archivo 'historial_evaluaciones_nba.csv' en el"
      " repositorio."
  )
