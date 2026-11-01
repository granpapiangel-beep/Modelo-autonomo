import os
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="NBA Prediction Bot", page_icon="🏀", layout="wide"
)

st.title("🏀 Panel de Control - NBA Prediction Bot")
st.markdown(
    "Interfaz analítica en tiempo real conectada a GitHub Actions y el motor"
    " de Monte Carlo."
)

# Verificar si existe el historial CSV
if os.path.exists("historial_evaluaciones_nba.csv"):
  df = pd.read_csv("historial_evaluaciones_nba.csv")

  # Métricas rápidas arriba
  col1, col2, col3 = st.columns(3)
  with col1:
    st.metric("Total de Partidos Analizados", len(df))
  with col2:
    if "Prob_Ganador_Pct" in df.columns:
      st.metric(
          "Confianza Promedio", f"{df['Prob_Ganador_Pct'].dropna().mean():.1f}%"
      )
  with col3:
    st.metric("Última Actualización", df["Fecha"].iloc[-1])

  st.divider()

  # Filtro o vista de la tabla
  st.subheader("📊 Historial Reciente de Predicciones")
  st.dataframe(df.tail(15), use_container_width=True)

else:
  st.warning("⚠️ No se encontró el archivo historial_evaluaciones_nba.csv.")
