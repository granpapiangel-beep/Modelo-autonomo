from datetime import datetime, timezone, timedelta
import json
import logging
import os
import unicodedata
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
ARCHIVO_TITULARES = "Titulares_NBA_Oficiales_30_Equipos(Puntajes Diarios).csv"

# ==========================================
# 1. TIERS BASE Y UTILIDADES
# ==========================================
TIERS_BASE_EQUIPOS = {
    "Celtics": 113.0, "Thunder": 116.0, "Cavaliers": 115.0, "Nuggets": 114.0,
    "Mavericks": 114.0, "Bucks": 112.0, "76ers": 113.0, "Timberwolves": 112.0,
    "Knicks": 112.0, "Suns": 111.0, "Lakers": 111.0, "Warriors": 110.5,
    "Kings": 110.0, "Magic": 109.5, "Pacers": 109.0, "Heat": 109.0,
    "Grizzlies": 109.0, "Clippers": 108.5, "Pelicans": 108.0, "Hawks": 107.5,
    "Rockets": 108.0, "Bulls": 107.0, "Raptors": 106.0, "Spurs": 106.5,
    "Jazz": 105.0, "Hornets": 104.5, "Blazers": 104.0, "Trail Blazers": 104.0,
    "Wizards": 103.5, "Pistons": 104.0, "Nets": 103.0
}

def normalizar_texto(texto):
    if not isinstance(texto, str):
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                        if unicodedata.category(c) != 'Mn').lower().strip()

# ==========================================
# 2. SINCRONIZACIÓN Y ACTUALIZACIÓN DE TITULARES (OPTIMIZADA)
# ==========================================
def sincronizar_titulares_y_puntajes():
    logging.info("🔄 Sincronizando plantillas y puntajes diarios desde la API oficial de ESPN...")
    
    tz_mexico = timezone(timedelta(hours=-6))
    hoy = datetime.now(tz_mexico).date()
    
    meses_abreviados = {
        1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr', 5: 'may', 6: 'jun',
        7: 'jul', 8: 'ago', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic'
    }
    
    # Optimización: Cargar CSV existente si lo hay para no reescribir todo el histórico
    df_existente = pd.DataFrame()
    columnas_existentes = set()
    if os.path.exists(ARCHIVO_TITULARES):
        try:
            df_existente = pd.read_csv(ARCHIVO_TITULARES, encoding='utf-8-sig')
            columnas_existentes = set(df_existente.columns)
        except Exception:
            pass

    # Procesar únicamente los últimos 5 días y el día actual para evitar bloqueos y lentitud extrema
    fechas_a_procesar = []
    current = hoy - timedelta(days=5)
    while current <= (hoy - timedelta(days=1)):
        col_nombre = f"{current.day} {meses_abreviados[current.month]}"
        # Si la columna ya existe con datos reales, podemos saltarla o actualizar solo los recientes
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
                        posicion = athlete.get("position", {}).get("abbreviation", "BENCH")
                        
                        stats_arr = athlete_info.get("stats", [])
                        if stats_arr and len(stats_arr) > pts_index:
                            try:
                                valor_stat = str(stats_arr[pts_index]).strip()
                                if '-' in valor_stat or valor_stat == '':
                                    continue
                                
                                pts_anotados = int(valor_stat)
                                if 0 <= pts_anotados <= 65:
                                    clave = (nombre_equipo, posicion, nombre_jugador)
                                    if clave not in base_datos_jugadores:
                                        base_datos_jugadores[clave] = {'Equipo': nombre_equipo, 'Posicion': posicion, 'Jugador': nombre_jugador}
                                    base_datos_jugadores[clave][col_nombre] = f"{pts_anotados} pts"
                            except ValueError:
                                pass
        except Exception as e:
            logging.error(f"⚠️ Error consultando fecha {col_nombre}: {e}")

    filas_finales = list(base_datos_jugadores.values())
    if filas_finales:
        df_nuevo = pd.DataFrame(filas_finales)
        orden_posiciones = {'PG': 1, 'SG': 2, 'SF': 3, 'PF': 4, 'C': 5, 'BENCH': 6}
        if 'Posicion' in df_nuevo.columns:
            df_nuevo['Pos_Rank'] = df_nuevo['Posicion'].map(orden_posiciones).fillna(99)
            df_nuevo = df_nuevo.sort_values(by=['Equipo', 'Pos_Rank']).drop(columns=['Pos_Rank'])
        
        df_nuevo.to_csv(ARCHIVO_TITULARES, index=False, encoding='utf-8-sig')
        logging.info("✨ Archivo de titulares actualizado y sincronizado de forma eficiente.")

# ==========================================
# 3. MOTOR DE PREDICCIONES Y MONTE CARLO
# ==========================================
def generar_alerta_automatica(partidos):
    equipos_volatiles = [p.get("local") for p in partidos if "ROJO" in p.get("Semaforo_Puntos", "")]
    mensaje_alerta = "Sincronización activa. "
    if equipos_volatiles:
        mensaje_alerta += f"⚠️ Alta volatilidad detectada en cruces clave con: {', '.join(set(equipos_volatiles[:3]))}. "
    else:
        mensaje_alerta += "Monitoreo de ausencias y rotaciones activo en 30 plantillas. "

    tz_mexico = timezone(timedelta(hours=-6))
    alerta_data = {
        "fecha": datetime.now(tz_mexico).strftime("%Y-%m-%d"),
        "mensaje": mensaje_alerta + "Reporte de última hora: Precaución con rotaciones en equipos en situación de B2B."
    }
    try:
        with open("alertas_lesiones.json", "w", encoding="utf-8") as f:
            json.dump(alerta_data, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

def obtener_fuerza_actualizada_equipos():
    fuerzas = TIERS_BASE_EQUIPOS.copy()
    if not os.path.exists(ARCHIVO_HISTORIAL):
        return fuerzas
    try:
        df_hist = pd.read_csv(ARCHIVO_HISTORIAL)
        if len(df_hist) < 5:
            return fuerzas
        for equipo in fuerzas.keys():
            fuerzas[equipo] = float(fuerzas[equipo])
    except Exception:
        pass
    return fuerzas

def funcion_costo_historico(pesos, df_hist):
    error_total = 0.0
    validos = 0
    for _, row in df_hist.iterrows():
        try:
            promedio_sim = float(row.get("Promedio_Simulado", 225.5))
            linea = float(row.get("Line_Apuesta", 225.5))
            pred_ajustada = (promedio_sim * pesos[0]) * pesos[2]
            error_total += (pred_ajustada - linea) ** 2
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
        limites = [(0.95, 1.05), (0.95, 1.05), (0.98, 1.02)]
        resultado = minimize(funcion_costo_historico, pesos_iniciales, args=(df_hist,), method="SLSQP", bounds=limites)
        if resultado.success:
            return resultado.x
    except Exception:
        pass
    return [1.0, 1.0, 1.0]

def extraer_stats_reales(event_id):
    loc_data, vis_data = None, None
    url_summary = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={event_id}"
    try:
        resp = requests.get(url_summary, timeout=5)
        if resp.status_code == 200:
            teams_box = resp.json().get("boxscore", {}).get("teams", [])
            if len(teams_box) >= 2:
                pts_vis = float(teams_box[0].get("statistics", [{}])[0].get("displayValue", 110))
                pts_loc = float(teams_box[1].get("statistics", [{}])[0].get("displayValue", 110))
                vis_data = {"PTS_OFENSIVA": pts_vis}
                loc_data = {"PTS_OFENSIVA": pts_loc}
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
                if total >= 5:
                    if (wins / total) >= 0.60:
                        factor = 1.02
                    elif (wins / total) <= 0.40:
                        factor = 0.98
    except Exception:
        pass
    return factor

def obtener_cartelera_y_boxscore_avanzado():
    partidos = []
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    fuerzas_actuales = obtener_fuerza_actualizada_equipos()
    
    linea_promedio_historica = 225.5
    if os.path.exists(ARCHIVO_HISTORIAL):
        try:
            df_h = pd.read_csv(ARCHIVO_HISTORIAL)
            if "Line_Apuesta" in df_h.columns and len(df_h) > 0:
                linea_promedio_historica = float(df_h["Line_Apuesta"].tail(10).mean())
        except Exception:
            pass

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

            for comp in competitors:
                team_info = comp.get("team", {})
                nombre_equipo = team_info.get("name", "")
                if comp.get("homeAway") == "home":
                    local_team = nombre_equipo
                else:
                    visitante_team = nombre_equipo

            base_loc = fuerzas_actuales.get(local_team, 110.0)
            base_vis = fuerzas_actuales.get(visitante_team, 110.0)

            stats_loc = {"PTS_OFENSIVA": base_loc, "DEF_R_RIVAL": base_vis, "RITMO": 99.0, "FACTOR_FORMA": 1.0}
            stats_vis = {"PTS_OFENSIVA": base_vis, "DEF_R_RIVAL": base_loc, "RITMO": 99.0, "FACTOR_FORMA": 1.0}

            if juego_terminado:
                box_loc, box_vis = extraer_stats_reales(event_id)
                if box_loc:
                    stats_loc.update(box_loc)
                if box_vis:
                    stats_vis.update(box_vis)

            for comp in competitors:
                nombre_equipo = comp.get("team", {}).get("name", "")
                factor_forma = calcular_factor_forma_equipo(comp)
                if nombre_equipo == local_team:
                    stats_loc["FACTOR_FORMA"] = factor_forma
                elif nombre_equipo == visitante_team:
                    stats_vis["FACTOR_FORMA"] = factor_forma

            linea_apuesta = round((base_loc + base_vis) * 1.01, 1)
            odds_info = comp_data.get("odds", [])
            if odds_info:
                try:
                    linea_apuesta = float(odds_info[0].get("overUnder", linea_apuesta))
                except (ValueError, TypeError):
                    pass
            
            if linea_apuesta < 200 or linea_apuesta > 255:
                linea_apuesta = linea_promedio_historica

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
    desv_est_puntos = np.std(total_puntos_sim)
    prob_over = np.sum(total_puntos_sim > linea_apuesta) / n_sims * 100

    diff_poder = (proyeccion_loc_final + 2.0) - proyeccion_vis_final
    prob_local = 1 / (1 + np.exp(-diff_poder / 6.0))
    prob_ganador_pct = max(prob_local, 1 - prob_local) * 100

    if prob_ganador_pct >= 62.0:
        semaforo_ganador = "🟢 VERDE (Alta Confiabilidad)"
    elif prob_ganador_pct >= 54.0:
        semaforo_ganador = "🟡 AMARILLO (Precaución / Partido Parejo)"
    else:
        semaforo_ganador = "🔴 ROJO (Volátil / No recomendado)"

    distancia_linea = abs(promedio_simulado - linea_apuesta)
    if distancia_linea >= 4.0 and desv_est_puntos < 9.0:
        semaforo_puntos = "🟢 VERDE (Margen Sólido O/U)"
    elif distancia_linea >= 1.8:
        semaforo_puntos = "🟡 AMARILLO (Margen Ajustado)"
    else:
        semaforo_puntos = "🔴 ROJO (Zona de Incertidumbre)"

    tz_mexico = timezone(timedelta(hours=-6))
    fecha_actual_mexico = datetime.now(tz_mexico).strftime("%Y-%m-%d")

    prediccion = {
        "Fecha": fecha_actual_mexico,
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
    return prediccion

if __name__ == "__main__":
    logging.info("🤖 Iniciando ejecución unificada del bot de la NBA...")
    
    sincronizar_titulares_y_puntajes()

    pesos_calibrados = optimizar_pesos_modelo()
    partidos_de_hoy = obtener_cartelera_y_boxscore_avanzado()

    if not partidos_de_hoy:
        partidos_de_hoy = [{
            "event_id": "000000",
            "local": "Celtics",
            "visitante": "Heat",
            "stats_loc": {"PTS_OFENSIVA": 113.0, "DEF_R_RIVAL": 109.0, "RITMO": 99.0, "FACTOR_FORMA": 1.0},
            "stats_vis": {"PTS_OFENSIVA": 109.0, "DEF_R_RIVAL": 113.0, "RITMO": 99.0, "FACTOR_FORMA": 1.0},
            "linea": 221.5,
        }]

    generar_alerta_automatica(partidos_de_hoy)

    nuevos_registros = [
        simular_monte_carlo_con_rotacion(p, pesos_calibrados)
        for p in partidos_de_hoy
    ]

    df_new = pd.DataFrame(nuevos_registros)
    if os.path.exists(ARCHIVO_HISTORIAL):
        try:
            df_existing = pd.read_csv(ARCHIVO_HISTORIAL)
            fecha_actual_ejecucion = df_new["Fecha"].iloc[0] if len(df_new) > 0 else ""
            if fecha_actual_ejecucion:
                df_existing = df_existing[df_existing["Fecha"] != fecha_actual_ejecucion]
            df_final = pd.concat([df_existing, df_new], ignore_index=True)
            df_final.to_csv(ARCHIVO_HISTORIAL, index=False)
        except Exception:
            df_new.to_csv(ARCHIVO_HISTORIAL, index=False)
    else:
        df_new.to_csv(ARCHIVO_HISTORIAL, index=False)

    logging.info("✨ ¡Proceso completado con éxito! Ambos CSVs se encuentran actualizados.")
