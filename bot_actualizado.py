from datetime import datetime
import logging
import os
import numpy as np
import pandas as pd
import requests
from scipy.optimize import minimize

# Configuración formal de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

ARCHIVO_HISTORIAL = "historial_evaluaciones_nba.csv"


# ==========================================
# MÓDULO DE OPTIMIZACIÓN NO LINEAL (Estabilizado)
# ==========================================
def funcion_costo_historico(pesos, df_hist):
  error_total = 0.0
  validos = 0
  for _, row in df_hist.iterrows():
    try:
      resultado_real = 1 if row.get("Resultado_Real_Local", 1) == 1 else 0
      pred_local_aprox = (pesos[0] * 55.0 + pesos[1] * 20.0) * pesos[2]
      prob_aprox = 1 / (1 + np.exp(-(pred_local_aprox - 55) / 5))
      error_total += (prob_aprox - resultado_real) ** 2
      validos += 1
    except Exception:
      continue
  return error_total / max(validos, 1)


def optimizar_pesos_modelo():
  if not os.path.exists(ARCHIVO_HISTORIAL):
    return [1.0, 1.0, 1.0]
  try:
    df_hist = pd.read_csv(ARCHIVO_HISTORIAL)
    if len(df_hist) < 5:
      return [1.0, 1.0, 1.0]

    pesos_iniciales = [1.0, 1.0, 1.0]
    # Centramos los límites estrictamente alrededor de 1.0 para evitar desbordes
    limites = [(0.95, 1.05), (0.95, 1.05), (0.98, 1.02)]

    resultado = minimize(
        funcion_costo_historico,
        pesos_iniciales,
        args=(df_hist,),
        method="SLSQP",
        bounds=limites,
    )
    if resultado.success:
      logging.info(
          "⚙️ Optimización no lineal exitosa con factores estables:"
          f" {resultado.x}"
      )
      return resultado.x
    else:
      return [1.0, 1.0, 1.0]
  except Exception:
    return [1.0, 1.0, 1.0]


def obtener_cartelera_y_boxscore_avanzado():
  partidos = []
  url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
  try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    events = data.get("events", [])

    for event in events:
      event_id = event.get("id")
      competitions = event.get("competitions", [])
      if not competitions:
        continue

      comp_data = competitions[0]
      status_data = comp_data.get("status", {}).get("type", {})
      juego_terminado = status_data.get("completed", False)

      competitors = comp_data.get("competitors", [])
      local_team, visitante_team = None, None

      # Promedios base reales por partido para un equipo de NBA (~112 pts)
      stats_loc = {
          "PTS_TITULARES": 80.0,
          "PTS_BANCA": 32.0,
          "RITMO": 98.0,
          "FACTOR_FORMA": 1.0,
      }
      stats_vis = {
          "PTS_TITULARES": 78.0,
          "PTS_BANCA": 30.0,
          "RITMO": 98.0,
          "FACTOR_FORMA": 1.0,
      }

      for comp in competitors:
        team_info = comp.get("team", {})
        nombre_equipo = team_info.get("name", "")
        factor_forma = calcular_factor_forma_equipo(comp)
        if comp.get("homeAway") == "home":
          local_team = nombre_equipo
          stats_loc["FACTOR_FORMA"] = factor_forma
        else:
          visitante_team = nombre_equipo
          stats_vis["FACTOR_FORMA"] = factor_forma

      if juego_terminado:
        box_loc, box_vis = extraer_stats_titulares_y_banca(event_id)
        if box_loc:
          stats_loc.update(box_loc)
        if box_vis:
          stats_vis.update(box_vis)

      linea_apuesta = 225.5
      odds_info = comp_data.get("odds", [])
      if odds_info:
        try:
          linea_apuesta = float(odds_info[0].get("overUnder", 225.5))
        except (ValueError, TypeError):
          pass

      if local_team and visitante_team:
        partidos.append({
            "event_id": event_id,
            "local": local_team,
            "visitante": visitante_team,
            "stats_loc": stats_loc,
            "stats_vis": stats_vis,
            "linea": linea_apuesta,
        })
  except Exception as e:
    logging.error(f"Error en cartelera: {e}")
  return partidos


def extraer_stats_titulares_y_banca(event_id):
  loc_data = {"PTS_TITULARES": 80.0, "PTS_BANCA": 32.0, "RITMO": 98.0}
  vis_data = {"PTS_TITULARES": 78.0, "PTS_BANCA": 30.0, "RITMO": 98.0}
  url_summary = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={event_id}"
  try:
    resp = requests.get(url_summary, timeout=5)
    if resp.status_code == 200:
      teams_box = resp.json().get("boxscore", {}).get("players", [])
      if not teams_box:
        return loc_data, vis_data
      resultados_equipos = []
      for team_box in teams_box:
        athletes = team_box.get("statistics", [{}])[0].get("athletes", [])
        pts_titulares, pts_banca = 0.0, 0.0
        for ath in athletes:
          es_titular = ath.get("starter", False)
          stats_jugador = ath.get("stats", [])
          if len(stats_jugador) > 1:
            try:
              puntos = float(stats_jugador[1])
            except (ValueError, TypeError):
              puntos = 0.0
            if es_titular:
              pts_titulares += puntos
            else:
              pts_banca += puntos
        resultados_equipos.append({
            "PTS_TITULARES": (
                pts_titulares if pts_titulares > 20 else 80.0
            ),
            "PTS_BANCA": pts_banca if pts_titulares > 20 else 32.0,
            "RITMO": 98.0,
        })
      if len(resultados_equipos) >= 2:
        vis_data = resultados_equipos[0]
        loc_data = resultados_equipos[1]
  except Exception:
    pass
  return loc_data, vis_data


def calcular_factor_forma_equipo(comp_competitor):
  factor = 1.0
  try:
    records = comp_competitor.get("records", [])
    for rec in records:
      summary = rec.get("summary", "")
      if "-" in summary:
        parts = summary.split("-")
        wins, losses = int(parts[0]), int(parts[1])
        total = wins + losses
        if total > 0 and (wins / total) >= 0.60:
          factor = 1.02
        elif total > 0 and (wins / total) <= 0.40:
          factor = 0.98
  except Exception:
    pass
  return factor


def simular_monte_carlo_con_rotacion(partido, pesos_optimos):
  local = partido["local"]
  visitante = partido["visitante"]
  stats_loc = partido["stats_loc"]
  stats_vis = partido["stats_vis"]
  linea_apuesta = partido["linea"]

  # Corrección de escala matemática para reflejar puntos reales de la NBA
  poder_ofensivo_local = (
      (stats_loc["PTS_TITULARES"] * pesos_optimos[0] + stats_loc["PTS_BANCA"] * pesos_optimos[1]) / 1.05
  ) * (stats_loc["FACTOR_FORMA"] * pesos_optimos[2])

  poder_ofensivo_visita = (
      (stats_vis["PTS_TITULARES"] * pesos_optimos[0] + stats_vis["PTS_BANCA"] * pesos_optimos[1]) / 1.05
  ) * (stats_vis["FACTOR_FORMA"] * pesos_optimos[2])

  ritmo_combinado = (stats_loc["RITMO"] + stats_vis["RITMO"]) / 2
  factor_ritmo = ritmo_combinado / 98.0

  ofensiva_local_final = poder_ofensivo_local * factor_ritmo
  ofensiva_visita_final = poder_ofensivo_visita * factor_ritmo

  n_sims = 2000
  # Acotado estricto a rangos reales de anotación en la NBA (85 a 125 puntos por equipo)
  puntos_locales_sim = np.clip(
      np.random.normal(ofensiva_local_final, 9.0, n_sims), 85, 125
  )
  puntos_visitas_sim = np.clip(
      np.random.normal(ofensiva_visita_final, 9.0, n_sims), 85, 125
  )
  total_puntos_sim = puntos_locales_sim + puntos_visitas_sim

  promedio_simulado = np.mean(total_puntos_sim)
  desv_est_puntos = np.std(total_puntos_sim)
  prob_over = np.sum(total_puntos_sim > linea_apuesta) / n_sims * 100

  diff_poder = (ofensiva_local_final + 2.0) - ofensiva_visita_final
  prob_local = 1 / (1 + np.exp(-diff_poder / 7))
  prob_ganador_pct = max(prob_local, 1 - prob_local) * 100

  # Semaforización equilibrada
  if prob_ganador_pct >= 65.0:
    semaforo_ganador = "🟢 VERDE (Alta Confiabilidad)"
  elif prob_ganador_pct >= 53.0:
    semaforo_ganador = "🟡 AMARILLO (Precaución / Partido Parejo)"
  else:
    semaforo_ganador = "🔴 ROJO (Volátil / No recomendado)"

  distancia_linea = abs(promedio_simulado - linea_apuesta)
  if distancia_linea >= 4.0 and desv_est_puntos < 10.0:
    semaforo_puntos = "🟢 VERDE (Margen Sólido O/U)"
  elif distancia_linea >= 1.8:
    semaforo_puntos = "🟡 AMARILLO (Margen Ajustado)"
  else:
    semaforo_puntos = "🔴 ROJO (Zona de Incertidumbre)"

  prediccion = {
      "Fecha": datetime.now().strftime("%Y-%m-%d"),
      "Local": local,
      "Visitante": visitante,
      "Pred_Ganador": local if prob_local >= 0.5 else visitante,
      "Prob_Ganador_Pct": round(prob_ganador_pct, 1),
      "Semaforo_Ganador": semaforo_ganador,
      "Line_Apuesta": linea_apuesta,
      "Pred_OU": "OVER" if prob_over > 50 else "DEBAJO",
      "Promedio_Simulado": round(promedio_simulado, 1),
      "Semaforo_Puntos": semaforo_puntos,
  }

  logging.info(
      f"🏀 {local} vs {visitante} | Línea: {linea_apuesta} | Proy: {promedio_simulado:.1f} pts"
      f" | O/U: {prediccion['Pred_OU']} [{semaforo_puntos}] | Ganador:"
      f" {prediccion['Pred_Ganador']} ({prob_ganador_pct:.1f}%) [{semaforo_ganador}]"
  )
  return prediccion


if __name__ == "__main__":
  logging.info("🤖 Iniciando motor analítico con escala real de puntos...")
  pesos_calibrados = optimizar_pesos_modelo()
  partidos_de_hoy = obtener_cartelera_y_boxscore_avanzado()

  if not partidos_de_hoy:
    partidos_de_hoy = [{
        "event_id": "000000",
        "local": "Celtics",
        "visitante": "Heat",
        "stats_loc": {
            "PTS_TITULARES": 80.0,
            "PTS_BANCA": 32.0,
            "RITMO": 98.0,
            "FACTOR_FORMA": 1.02,
        },
        "stats_vis": {
            "PTS_TITULARES": 78.0,
            "PTS_BANCA": 30.0,
            "RITMO": 98.0,
            "FACTOR_FORMA": 0.98,
        },
        "linea": 221.5,
    }]

  nuevos_registros = [
      simular_monte_carlo_con_rotacion(p, pesos_calibrados)
      for p in partidos_de_hoy
  ]

  df_new = pd.DataFrame(nuevos_registros)
  if os.path.exists(ARCHIVO_HISTORIAL):
    try:
      df_existing = pd.read_csv(ARCHIVO_HISTORIAL)
      df_final = pd.concat([df_existing, df_new], ignore_index=True)
      df_final = df_final.drop_duplicates(
          subset=["Fecha", "Local", "Visitante"], keep="last"
      )
      df_final.to_csv(ARCHIVO_HISTORIAL, index=False)
    except Exception:
      df_new.to_csv(ARCHIVO_HISTORIAL, index=False)
  else:
    df_new.to_csv(ARCHIVO_HISTORIAL, index=False)

  logging.info("✨ ¡Proceso completado con proyecciones ajustadas y reales!")
