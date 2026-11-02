# player_analysis.py
# Analiza la consistencia individual de anotación usando desviación estándar
import numpy as np
import pandas as pd


def evaluar_consistencia_jugador(df_historico_jugador):
  """Toma un DataFrame con el historial de puntos por juego de un jugador.

  Calcula su promedio y su desviación estándar para clasificarlo.
  """
  if df_historico_jugador.empty or "PTS" not in df_historico_jugador.columns:
    return None

  promedio_puntos = df_historico_jugador["PTS"].mean()
  desviacion_std = df_historico_jugador["PTS"].std()

  # Coeficiente de Variación (CV) = Desviación / Promedio
  # Menor CV significa que el jugador es sumamente "cumplidor y constante"
  if promedio_puntos > 0:
    coef_variacion = desviacion_std / promedio_puntos
  else:
    coef_variacion = 1.0

  # Clasificación analítica para la clase
  if coef_variacion < 0.20 and promedio_puntos >= 12.0:
    perfil = "🎯 Jugador Altamente Cumplidor (Baja varianza, cuota fija asegurada)"
  elif coef_variacion > 0.40:
    perfil = "🎢 Jugador Volátil / Montaña Rusa (Lo mismo anota 30 que 5 puntos)"
  else:
    perfil = "⚖️ Jugador de Rendimiento Moderado / Estándar"

  return {
      "Promedio": round(promedio_puntos, 1),
      "Desviacion_Std": round(desviacion_std, 1),
      "Perfil": perfil,
  }
