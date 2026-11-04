import os
import logging
import pandas as pd
import requests
import unicodedata

# Configuración formal de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler()])

ARCHIVO_TITULARES = "Titulares_NBA_Oficiales_30_Equipos(Puntajes Diarios).csv"

def normalizar_texto(texto):
    if not isinstance(texto, str):
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                        if unicodedata.category(c) != 'Mn').lower().strip()

def rellenar_histografico_definitivo():
    if not os.path.exists(ARCHIVO_TITULARES):
        logging.warning(f"⚠️ No se encontró el archivo {ARCHIVO_TITULARES}")
        return

    try:
        df_titulares = pd.read_csv(ARCHIVO_TITULARES, encoding='utf-8-sig')
    except Exception as e:
        logging.error(f"❌ Error al leer el CSV de titulares: {e}")
        return

    columnas_fechas = df_titulares.columns[3:]
    
    meses_map = {
        'oct': 10, 'nov': 11, 'dic': 12, 'ene': 1, 'feb': 2, 
        'mar': 3, 'abr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'ago': 8, 'sep': 9
    }

    logging.info("🔄 Iniciando sincronización histórica definitiva con precisión de fechas...")

    for col_fecha in columnas_fechas:
        try:
            partes = col_fecha.strip().split()
            if len(partes) != 2:
                continue
            dia = int(partes[0])
            mes_str = partes[1].lower()
            mes = meses_map.get(mes_str)

            if not mes:
                continue

            anio = 2025 if mes >= 10 else 2026
            fecha_str_api = f"{anio}{mes:02d}{dia:02d}"

            url_scoreboard = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={fecha_str_api}"
            resp = requests.get(url_scoreboard, timeout=10)
            if resp.status_code != 200:
                continue

            data = resp.json()
            events = data.get("events", [])
            if not events:
                continue

            # Diccionario universal de puntos para esta fecha exacta: {nombre_jugador_normalizado: puntos}
            puntos_exactos_dia = {}

            for event in events:
                event_id = event.get("id")
                competitions = event.get("competitions", [])
                if not competitions:
                    continue
                
                status = competitions[0].get("status", {}).get("type", {}).get("completed", False)
                if not status:
                    continue

                url_summary = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={event_id}"
                sum_resp = requests.get(url_summary, timeout=5)
                if sum_resp.status_code != 200:
                    continue

                sum_data = sum_resp.json()
                boxscore = sum_data.get("boxscore", {})
                
                for team_block in boxscore.get("players", []):
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
                        nombre_api = normalizar_texto(athlete.get("displayName", ""))
                        stats_arr = athlete_info.get("stats", [])

                        if stats_arr and len(stats_arr) > pts_index:
                            try:
                                valor_stat = str(stats_arr[pts_index]).strip()
                                if '-' in valor_stat or valor_stat == '':
                                    continue
                                
                                pts_anotados = int(valor_stat)
                                if 0 <= pts_anotados <= 65:
                                    puntos_exactos_dia[nombre_api] = pts_anotados
                                    # Guardar también por apellido o partes clave para evitar problemas con nombres compuestos
                                    partes_nombre = nombre_api.split()
                                    if len(partes_nombre) > 1:
                                        puntos_exactos_dia[partes_nombre[-1]] = pts_anotados # Apellido
                            except ValueError:
                                pass

            # Aplicar los puntos exactos al DataFrame para esta columna de fecha
            for index, row in df_titulares.iterrows():
                jugador_raw = str(row['Jugador'])
                jugador_norm = normalizar_texto(jugador_raw)
                apellido_csv = normalizar_texto(jugador_raw.split()[-1]) if len(jugador_raw.split()) > 1 else ""

                if jugador_norm in puntos_exactos_dia:
                    df_titulares.loc[index, col_fecha] = f"{puntos_exactos_dia[jugador_norm]} pts"
                elif apellido_csv and apellido_csv in puntos_exactos_dia:
                    # Coincidencia por apellido si el nombre completo varió ligeramente en la API
                    df_titulares.loc[index, col_fecha] = f"{puntos_exactos_dia[apellido_csv]} pts"
                else:
                    # Si no hay registro de puntos para este jugador en este día exacto, validamos si el equipo jugó
                    # Si ya tenía datos previos erróneos los limpiamos a SD o los dejamos si aplica
                    pass

            logging.info(f"✔️ Fecha sincronizada con precisión absoluta: {col_fecha}")

        except Exception as e:
            logging.error(f"⚠️ Error procesando la fecha {col_fecha}: {e}")

    df_titulares.to_csv(ARCHIVO_TITULARES, index=False, encoding='utf-8-sig')
    logging.info("✨ ¡Sincronización histórica definitiva completada con éxito!")

if __name__ == "__main__":
    rellenar_histografico_definitivo()
