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

def rellenar_histografico_sd():
    if not os.path.exists(ARCHIVO_TITULARES):
        logging.warning(f"⚠️ No se encontró el archivo {ARCHIVO_TITULARES}")
        return

    try:
        df_titulares = pd.read_csv(ARCHIVO_TITULARES, encoding='utf-8-sig')
    except Exception as e:
        logging.error(f"❌ Error al leer el CSV de titulares: {e}")
        return

    # Tomamos todas las columnas a partir de la cuarta (donde empiezan las fechas: '20 oct', etc.)
    columnas_fechas = df_titulares.columns[3:]
    
    # Mapeo de abreviaturas de meses en tu CSV a número de mes
    meses_map = {
        'oct': 10, 'nov': 11, 'dic': 12, 'ene': 1, 'feb': 2, 
        'mar': 3, 'abr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'ago': 8, 'sep': 9
    }

    logging.info("🔄 Iniciando barrido histórico adaptado a tus columnas...")

    for col_fecha in columnas_fechas:
        try:
            # Ejemplo de col_fecha: "20 oct" o "3 nov"
            partes = col_fecha.strip().split()
            if len(partes) != 2:
                continue
            dia = int(partes[0])
            mes_str = partes[1].lower()
            mes = meses_map.get(mes_str)

            if not mes:
                continue

            # Definimos el año correspondiente a la temporada actual (2025/2026)
            anio = 2025 if mes >= 10 else 2026
            fecha_str_api = f"{anio}{mes:02d}{dia:02d}"

            url_scoreboard = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={fecha_str_api}"
            resp = requests.get(url_scoreboard, timeout=10)
            if resp.status_code != 200:
                continue

            data = resp.json()
            for event in data.get("events", []):
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
                players_stats = boxscore.get("players", [])

                for team_block in players_stats:
                    for stat_group in team_block.get("statistics", []):
                        for athlete_info in stat_group.get("athletes", []):
                            athlete = athlete_info.get("athlete", {})
                            nombre_api = athlete.get("displayName", "")
                            stats_arr = athlete_info.get("stats", [])

                            if stats_arr and len(stats_arr) > 0:
                                try:
                                    pts_anotados = int(stats_arr[0])
                                    nombre_api_clean = normalizar_texto(nombre_api)
                                    
                                    mask = df_titulares['Jugador'].apply(lambda x: normalizar_texto(str(x)) == nombre_api_clean)
                                    
                                    # Si el jugador tiene "SD" en esa columna de fecha, rellenamos con sus puntos reales
                                    if mask.any():
                                        valor_actual = df_titulares.loc[mask, col_fecha].values[0]
                                        if str(valor_actual).strip() == "SD":
                                            df_titulares.loc[mask, col_fecha] = f"{pts_anotados} pts"
                                except ValueError:
                                    pass

            logging.info(f"✔️ Columna de fecha procesada: {col_fecha}")

        except Exception as e:
            logging.error(f"⚠️ Error procesando la columna {col_fecha}: {e}")

    df_titulares.to_csv(ARCHIVO_TITULARES, index=False, encoding='utf-8-sig')
    logging.info("✨ ¡Llenado histórico masivo completado con éxito!")

if __name__ == "__main__":
    rellenar_histografico_sd()
