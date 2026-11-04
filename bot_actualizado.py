from datetime import datetime, timedelta, timezone
import logging
import os
import pandas as pd
import requests
import unicodedata

# Configuración formal de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

ARCHIVO_TITULARES = "Titulares_NBA_Oficiales_30_Equipos(Puntajes Diarios).csv"


def normalizar_texto(texto):
  if not isinstance(texto, str):
    return ""
  return "".join(
      c
      for c in unicodedata.normalize("NFD", texto)
      if unicodedata.category(c) != "Mn"
  ).lower().strip()


def sincronizar_titulares_perfecto():
  logging.info(
      "🔄 Iniciando sincronización estricta por equipo y jugador desde la API"
      " oficial..."
  )

  tz_mexico = timezone(timedelta(hours=-6))
  hoy = datetime.now(tz_mexico).date()

  # Rango de fechas desde el 20 de octubre en adelante
  fecha_inicio = datetime(2025, 10, 20).date()
  fechas_a_procesar = []

  current = fecha_inicio
  meses_abreviados = {
      1: "ene",
      2: "feb",
      3: "mar",
      4: "abr",
      5: "may",
      6: "jun",
      7: "jul",
      8: "ago",
      9: "sep",
      10: "oct",
      11: "nov",
      12: "dic",
  }

  while current <= (hoy - timedelta(days=1)):
    col_nombre = f"{current.day} {meses_abreviados[current.month]}"
    fechas_a_procesar.append((current, col_nombre))
    current += timedelta(days=1)

  base_datos_jugadores = {}

  for fecha_dt, col_nombre in fechas_a_procesar:
    fecha_str_api = fecha_dt.strftime("%Y%m%d")
    url_scoreboard = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={fecha_str_api}"

    try:
      resp = requests.get(url_scoreboard, timeout=10)
      if resp.status_code != 200:
        continue
      data = resp.json()
      events = data.get("events", [])
      if not events:
        continue

      for event in events:
        event_id = event.get("id")
        competitions = event.get("competitions", [])
        if not competitions:
          continue

        status = (
            competitions[0].get("status", {}).get("type", {}).get("completed", False)
        )
        if not status:
          continue

        url_summary = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={event_id}"
        sum_resp = requests.get(url_summary, timeout=5)
        if sum_resp.status_code != 200:
          continue

        sum_data = sum_resp.json()
        boxscore = sum_data.get("boxscore", {})

        for team_block in boxscore.get("players", []):
          team_info = team_block.get("team", {})
          nombre_equipo = team_info.get("displayName", "Equipo NBA")

          statistics_list = team_block.get("statistics", [])
          if not statistics_list:
            continue

          labels = statistics_list[0].get("labels", [])
          pts_index = 0
          for idx, lbl in enumerate(labels):
            if lbl.upper() in ["PTS", "POINTS"]:
              pts_index = idx
              break

          athletes_list = statistics_list[0].get("athletes", [])
          for athlete_info in athletes_list:
            athlete = athlete_info.get("athlete", {})
            nombre_jugador = athlete.get("displayName", "")
            posicion = (
                athlete.get("position", {}).get("abbreviation", "BENCH")
            )

            stats_arr = athlete_info.get("stats", [])
            if stats_arr and len(stats_arr) > pts_index:
              try:
                valor_stat = str(stats_arr[pts_index]).strip()
                if "-" in valor_stat or valor_stat == "":
                  continue

                pts_anotados = int(valor_stat)
                if 0 <= pts_anotados <= 65:
                  # Clave compuesta estricta: Equipo + Posición + Jugador
                  clave = (nombre_equipo, posicion, nombre_jugador)
                  if clave not in base_datos_jugadores:
                    base_datos_jugadores[clave] = {}
                  base_datos_jugadores[clave][col_nombre] = f"{pts_anotados} pts"
              except ValueError:
                pass
    except Exception as e:
      logging.error(f"⚠️ Error consultando fecha {col_nombre}: {e}")

  filas_finales = []
  for (equipo, posicion, jugador), puntajes in base_datos_jugadores.items():
    fila = {"Equipo": equipo, "Posicion": posicion, "Jugador": jugador}
    for _, col_nombre in fechas_a_procesar:
      fila[col_nombre] = puntajes.get(col_nombre, "SD")
    filas_finales.append(fila)

  if filas_finales:
    df_nuevo = pd.DataFrame(filas_finales)
    orden_posiciones = {"PG": 1, "SG": 2, "SF": 3, "PF": 4, "C": 5, "BENCH": 6}
    df_nuevo["Pos_Rank"] = df_nuevo["Posicion"].map(orden_posiciones).fillna(99)
    df_nuevo = df_nuevo.sort_values(by=["Equipo", "Pos_Rank"]).drop(
        columns=["Pos_Rank"]
    )

    df_nuevo.to_csv(ARCHIVO_TITULARES, index=False, encoding="utf-8-sig")
    logging.info(
        "✨ ¡Archivo CSV reconstruido con validación estricta de equipos y"
        " puntajes!"
    )
  else:
    logging.warning(
        "⚠️ No se generaron registros. Verifique el rango o la red."
    )


if __name__ == "__main__":
  sincronizar_titulares_perfecto()
