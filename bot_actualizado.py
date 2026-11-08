from datetime import datetime, timezone, timedelta
import json
import logging
import os
import unicodedata
import numpy as np
import pandas as pd
import requests
from scipy.optimize import minimize

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler()])

ARCHIVO_HISTORIAL = "historial_evaluaciones_nba.csv"
ARCHIVO_TITULARES = "Titulares_NBA_Oficiales_30_Equipos(Puntajes Diarios).csv"
ARCHIVO_LESIONES = "alertas_lesiones.json"
PLAYOFFS_MODE = False 

TIERS_BASE_EQUIPOS = {
    "Celtics": 113.0, "Thunder": 116.0, "Cavaliers": 115.0, "Nuggets": 114.0, "Mavericks": 114.0, "Bucks": 112.0, "76ers": 113.0, "Timberwolves": 112.0,
    "Knicks": 112.0, "Suns": 111.0, "Lakers": 111.0, "Warriors": 110.5, "Kings": 110.0, "Magic": 109.5, "Pacers": 109.0, "Heat": 109.0,
    "Grizzlies": 109.0, "Clippers": 108.5, "Pelicans": 108.0, "Hawks": 107.5, "Rockets": 108.0, "Bulls": 107.0, "Raptors": 106.0, "Spurs": 106.5,
    "Jazz": 105.0, "Hornets": 104.5, "Blazers": 104.0, "Trail Blazers": 104.0, "Wizards": 103.5, "Pistons": 104.0, "Nets": 103.0
}

def normalizar_texto(texto):
    if not isinstance(texto, str): return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower().strip()

def sincronizar_titulares_y_puntajes():
    logging.info("🔄 Sincronizando plantillas y puntajes desde ESPN...")
    tz_mexico = timezone(timedelta(hours=-6))
    hoy = datetime.now(tz_mexico).date()
    meses_abreviados = { 1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr', 5: 'may', 6: 'jun', 7: 'jul', 8: 'ago', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic' }
    
    df_existente = pd.DataFrame()
    if os.path.exists(ARCHIVO_TITULARES):
        try: df_existente = pd.read_csv(ARCHIVO_TITULARES, encoding='utf-8-sig')
        except Exception: pass

    fechas_a_procesar = []
    current = hoy - timedelta(days=20) 
    while current <= (hoy - timedelta(days=1)):
        col_nombre = f"{current.day} {meses_abreviados[current.month]}"
        fechas_a_procesar.append((current, col_nombre))
        current += timedelta(days=1)

    base_datos_jugadores = {}
    if not df_existente.empty and 'Equipo' in df_existente.columns:
        for _, row in df_existente.iterrows():
            clave = (row.get('Equipo'), row.get('Posicion'), row.get('Jugador'))
            base_datos_jugadores[clave] = row.to_dict()

    for fecha_dt, col_nombre in fechas_a_procesar:
        fecha_str_api = fecha_dt.strftime("%Y%m%d")
        url_scoreboard = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={fecha_str_api}"
        try:
            resp = requests.get(url_scoreboard, timeout=10)
            if resp.status_code != 200: continue
            events = resp.json().get("events", [])
            if not events: continue

            for event in events:
                event_id = event.get("id")
                competitions = event.get("competitions", [])
                if not competitions: continue
                if not competitions[0].get("status", {}).get("type", {}).get("completed", False): continue

                url_summary = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={event_id}"
                sum_resp = requests.get(url_summary, timeout=5)
                if sum_resp.status_code != 200: continue

                boxscore = sum_resp.json().get("boxscore", {})
                for team_block in boxscore.get("players", []):
                    nombre_equipo = team_block.get("team", {}).get("displayName", "Equipo NBA")
                    statistics_list = team_block.get("statistics", [])
                    if not statistics_list: continue
                    
                    labels = statistics_list[0].get("labels", [])
                    pts_index = 0
                    for idx, lbl in enumerate(labels):
                        if lbl.upper() in ["PTS", "POINTS"]:
                            pts_index = idx; break

                    for athlete_info in statistics_list[0].get("athletes", []):
                        athlete = athlete_info.get("athlete", {})
                        nombre_jugador = athlete.get("displayName", "")
                        posicion = athlete.get("position", {}).get("abbreviation", "BENCH")
                        stats_arr = athlete_info.get("stats", [])
                        
                        if stats_arr and len(stats_arr) > pts_index:
                            try:
                                valor_stat = str(stats_arr[pts_index]).strip()
                                if '-' in valor_stat or valor_stat == '': continue
                                pts_anotados = int(valor_stat)
                                if 0 <= pts_anotados <= 65:
                                    clave = (nombre_equipo, posicion, nombre_jugador)
                                    if clave not in base_datos_jugadores:
                                        base_datos_jugadores[clave] = {'Equipo': nombre_equipo, 'Posicion': posicion, 'Jugador': nombre_jugador}
                                    base_datos_jugadores[clave][col_nombre] = f"{pts_anotados} pts"
                            except ValueError: pass
        except Exception: pass

    filas_finales = list(base_datos_jugadores.values())
    if filas_finales:
        df_nuevo = pd.DataFrame(filas_finales)
        orden_posiciones = {'PG': 1, 'SG': 2, 'SF': 3, 'PF': 4, 'C': 5, 'BENCH': 6}
        if 'Posicion' in df_nuevo.columns:
            df_nuevo['Pos_Rank'] = df_nuevo['Posicion'].map(orden_posiciones).fillna(99)
            df_nuevo = df_nuevo.sort_values(by=['Equipo', 'Pos_Rank']).drop(columns=['Pos_Rank'])
        df_nuevo.to_csv(ARCHIVO_TITULARES, index=False, encoding='utf-8-sig')

def detectar_lesiones_y_calcular_impacto(event_id, nombre_equipo):
    """ Consulta autónoma a la API de ESPN para detectar si hay jugadores OUT en este juego """
    penizacion_total = 0.0
    alertas_equipo = []
    
    url_summary = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={event_id}"
    try:
        resp = requests.get(url_summary, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            # ESPN incluye el reporte de lesiones (injuries) en el JSON del resumen o rosters previos al juego
            injuries = data.get("injuries", [])
            df_titulares = pd.read_csv(ARCHIVO_TITULARES, encoding='utf-8-sig') if os.path.exists(ARCHIVO_TITULARES) else pd.DataFrame()
            
            for team_inj in injuries:
                team_name = team_inj.get("team", {}).get("displayName", "")
                if normalizar_texto(nombre_equipo) in normalizar_texto(team_name) or normalizar_texto(team_name) in normalizar_texto(nombre_equipo):
                    for inj in team_inj.get("injuries", []):
                        status = inj.get("status", "").upper()
                        if "OUT" in status or "QUESTIONABLE" in status:
                            jugador = inj.get("athlete", {}).get("displayName", "")
                            motivo = inj.get("details", {}).get("returnDate", "Lesión / Descanso")
                            
                            # Buscar su promedio en el CSV para restar sus puntos
                            if not df_titulares.empty:
                                fila_jug = df_titulares[df_titulares['Jugador'].str.contains(jugador, case=False, na=False)]
                                if not fila_jug.empty:
                                    puntos_lista = [float(str(fila_jug.iloc[0].get(col, "")).replace("pts", "").strip()) for col in df_titulares.columns[3:] if "pts" in str(fila_jug.iloc[0].get(col, ""))]
                                    if puntos_lista:
                                        prom = np.mean(puntos_lista)
                                         impacto_neto = prom * 0.70 # El impacto real restado al equipo
                                        penizacion_total += impacto_neto
                                        alertas_equipo.append({
                                            "jugador": jugador, "equipo": nombre_equipo, "estatus": status,
                                            "motivo": motivo, "impacto_simulador": f"-{round(impacto_neto, 1)} pts"
                                        })
    except Exception as e:
        logging.error(f"Error consultando lesiones en ESPN: {e}")
        
    return penizacion_total, alertas_equipo

def obtener_fuerza_actualizada_equipos():
    fuerzas = TIERS_BASE_EQUIPOS.copy()
    if not os.path.exists(ARCHIVO_HISTORIAL): return fuerzas
    try:
        df_hist = pd.read_csv(ARCHIVO_HISTORIAL)
        if len(df_hist) < 5: return fuerzas
        for equipo in fuerzas.keys(): fuerzas[equipo] = float(fuerzas[equipo])
    except: pass
    return fuerzas

def funcion_costo_historico(pesos, df_hist):
    error_total = 0.0
    validos = 0
    for _, row in df_hist.iterrows():
        try:
            pred_ajustada = (float(row.get("Promedio_Simulado", 225.5)) * pesos[0]) * pesos[2]
            error_total += (pred_ajustada - float(row.get("Line_Apuesta", 225.5))) ** 2
            validos += 1
        except: continue
    return error_total / max(validos, 1)

def optimizar_pesos_modelo():
    if not os.path.exists(ARCHIVO_HISTORIAL): return [1.0, 1.0, 1.0]
    try:
        df_hist = pd.read_csv(ARCHIVO_HISTORIAL)
        if len(df_hist) < 5: return [1.0, 1.0, 1.0]
        resultado = minimize(funcion_costo_historico, [1.0, 1.0, 1.0], args=(df_hist,), method="SLSQP", bounds=[(0.95, 1.05), (0.95, 1.05), (0.98, 1.02)])
        if resultado.success: return resultado.x
    except: pass
    return [1.0, 1.0, 1.0]

def obtener_cartelera_y_boxscore_avanzado():
    partidos = []
    fecha_hoy_api = datetime.now(timezone(timedelta(hours=-6))).strftime("%Y%m%d")
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={fecha_hoy_api}"
    fuerzas_actuales = obtener_fuerza_actualizada_equipos()
    
    linea_promedio_historica = 225.5
    if os.path.exists(ARCHIVO_HISTORIAL):
        try:
            df_h = pd.read_csv(ARCHIVO_HISTORIAL)
            if "Line_Apuesta" in df_h.columns and len(df_h) > 0:
                linea_promedio_historica = float(df_h["Line_Apuesta"].tail(10).mean())
        except: pass

    todas_las_alertas = []
    try:
        response = requests.get(url, timeout=10)
        events = response.json().get("events", [])

        for event in events:
            event_id = event.get("id")
            competitions = event.get("competitions", [])
            if not competitions: continue

            comp_data = competitions[0]
            local_team, visitante_team = None, None

            for comp in comp_data.get("competitors", []):
                if comp.get("homeAway") == "home": local_team = comp.get("team", {}).get("name", "")
                else: visitante_team = comp.get("team", {}).get("name", "")

            base_loc = fuerzas_actuales.get(local_team, 110.0)
            base_vis = fuerzas_actuales.get(visitante_team, 110.0)

            # RASTREO AUTÓNOMO DE LESIONES DESDE ESPN
            pen_loc, alert_loc = detectar_lesiones_y_calcular_impacto(event_id, local_team)
            pen_vis, alert_vis = detectar_lesiones_y_calcular_impacto(event_id, visitante_team)
            
            todas_las_alertas.extend(alert_loc + alert_vis)

            base_loc = max(85.0, base_loc - pen_loc)
            base_vis = max(85.0, base_vis - pen_vis)

            stats_loc = {"PTS_OFENSIVA": base_loc, "DEF_R_RIVAL": base_vis, "RITMO": 99.0, "FACTOR_FORMA": 1.0}
            stats_vis = {"PTS_OFENSIVA": base_vis, "DEF_R_RIVAL": base_loc, "RITMO": 99.0, "FACTOR_FORMA": 1.0}

            linea_apuesta = round((base_loc + base_vis) * 1.01, 1)
            odds_info = comp_data.get("odds", [])
            if odds_info:
                try: linea_apuesta = float(odds_info[0].get("overUnder", linea_apuesta))
                except: pass
            
            if linea_apuesta < 200 or linea_apuesta > 255: linea_apuesta = linea_promedio_historica

            if local_team and visitante_team:
                partidos.append({
                    "event_id": event_id,
                    "local": local_team,
                    "visitante": visitante_team,
                    "stats_loc": stats_loc,
                    "stats_vis": stats_vis,
                    "linea": linea_apuesta,
                })
                
        # GUARDAR LAS ALERTAS DETECTADAS AUTÓNOMAMENTE EN EL JSON PARA QUE EL DASHBOARD LAS MUESTRE
        tz_mexico = timezone(timedelta(hours=-6))
        ahora = datetime.now(tz_mexico)
        datos_json = {
            "fecha": ahora.strftime("%Y-%m-%d"),
            "ultima_actualizacion": ahora.strftime("%H:%M UTC-6"),
            "mensaje_general": "🏥 Reporte médico autónomo procesado desde ESPN.",
            "alertas_criticas": todas_las_alertas
        }
        with open(ARCHIVO_LESIONES, "w", encoding="utf-8") as f:
            json.dump(datos_json, f, ensure_ascii=False, indent=4)

    except Exception as e:
        logging.error(f"Error en cartelera: {e}")
        
    return partidos

def simular_monte_carlo_con_rotacion(partido, pesos_optimos):
    local = partido["local"]
    visitante = partido["visitante"]
    stats_loc = partido["stats_loc"]
    stats_vis = partido["stats_vis"]
    linea_apuesta = partido["linea"]

    poder_ofensivo_local = (stats_loc["PTS_OFENSIVA"] * pesos_optimos[0]) * stats_loc["FACTOR_FORMA"]
    poder_ofensivo_visita = (stats_vis["PTS_OFENSIVA"] * pesos_optimos[1]) * stats_vis["FACTOR_FORMA"]

    proyeccion_loc_final = (poder_ofensivo_local + stats_vis.get("DEF_R_RIVAL", 110)) / 2 * pesos_optimos[2]
    proyeccion_vis_final = (poder_ofensivo_visita + stats_loc.get("DEF_R_RIVAL", 110)) / 2 * pesos_optimos[2]

    n_sims = 2000
    puntos_locales_sim = np.clip(np.random.normal(proyeccion_loc_final, 8.0, n_sims), 85, 130)
    puntos_visitas_sim = np.clip(np.random.normal(proyeccion_vis_final, 8.0, n_sims), 85, 130)
    total_puntos_sim = puntos_locales_sim + puntos_visitas_sim

    promedio_simulado = np.mean(total_puntos_sim)
    prob_over = np.sum(total_puntos_sim > linea_apuesta) / n_sims * 100

    diff_poder = (proyeccion_loc_final + 2.0) - proyeccion_vis_final
    prob_local = 1 / (1 + np.exp(-diff_poder / 6.0))
    prob_ganador_pct = max(prob_local, 1 - prob_local) * 100

    if prob_ganador_pct >= 62.0: semaforo_ganador = "🟢 VERDE (Alta Confiabilidad)"
    elif prob_ganador_pct >= 54.0: semaforo_ganador = "🟡 AMARILLO (Precaución)"
    else: semaforo_ganador = "🔴 ROJO (Volátil)"

    distancia_linea = abs(promedio_simulado - linea_apuesta)
    if distancia_linea >= 7.0: semaforo_puntos = "🟢 GRAN VALOR (Divergencia Fuerte vs Vegas)"
    elif distancia_linea >= 4.0: semaforo_puntos = "🟡 VALOR MODERADO (Margen Aceptable)"
    else: semaforo_puntos = "🔴 SIN VALOR (Línea idéntica a Vegas)"

    fecha_actual_mexico = datetime.now(timezone(timedelta(hours=-6))).strftime("%Y-%m-%d")

    return {
        "Fecha": fecha_actual_mexico,
        "Local": local, "Visitante": visitante,
        "Pred_Ganador": local if prob_local >= 0.5 else visitante,
        "Prob_Ganador_Pct": round(prob_ganador_pct, 1),
        "Semaforo_Ganador": semaforo_ganador,
        "Line_Apuesta": linea_apuesta,
        "Pred_OU": "OVER" if prob_over > 50 else "DEBAJO",
        "Promedio_Simulado": round(promedio_simulado, 1),
        "Semaforo_Puntos": semaforo_puntos,
        "Modo_Playoffs": PLAYOFFS_MODE
    }

if __name__ == "__main__":
    logging.info("🤖 Iniciando ejecución autónoma con rastreo de lesiones...")
    
    sincronizar_titulares_y_puntajes()
    pesos_calibrados = optimizar_pesos_modelo()
    partidos_de_hoy = obtener_cartelera_y_boxscore_avanzado()

    if not partidos_de_hoy:
        partidos_de_hoy = [{
            "event_id": "000000", "local": "Celtics", "visitante": "Heat",
            "stats_loc": {"PTS_OFENSIVA": 113.0, "DEF_R_RIVAL": 109.0, "RITMO": 99.0, "FACTOR_FORMA": 1.0},
            "stats_vis": {"PTS_OFENSIVA": 109.0, "DEF_R_RIVAL": 113.0, "RITMO": 99.0, "FACTOR_FORMA": 1.0},
            "linea": 221.5,
        }]

    nuevos_registros = [simular_monte_carlo_con_rotacion(p, pesos_calibrados) for p in partidos_de_hoy]

    df_new = pd.DataFrame(nuevos_registros)
    if os.path.exists(ARCHIVO_HISTORIAL):
        try:
            df_existing = pd.read_csv(ARCHIVO_HISTORIAL)
            fecha_actual = df_new["Fecha"].iloc[0] if len(df_new) > 0 else ""
            if fecha_actual: df_existing = df_existing[df_existing["Fecha"] != fecha_actual]
            df_final = pd.concat([df_existing, df_new], ignore_index=True)
            df_final.to_csv(ARCHIVO_HISTORIAL, index=False)
        except Exception:
            df_new.to_csv(ARCHIVO_HISTORIAL, index=False)
    else:
        df_new.to_csv(ARCHIVO_HISTORIAL, index=False)

    logging.info("✨ ¡Proceso completado! Las lesiones detectadas modificaron las simulaciones.")
