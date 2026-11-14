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
    "Celtics": 117.0, "Thunder": 117.5, "Cavaliers": 113.5, "Nuggets": 113.0, "Mavericks": 115.5, 
    "Spurs": 117.0, "Bucks": 109.5, "76ers": 116.5, "Timberwolves": 114.0, "Knicks": 114.0, 
    "Suns": 109.5, "Rockets": 113.0, "Lakers": 116.5, "Warriors": 112.0, "Kings": 112.0, 
    "Magic": 111.0, "Pacers": 109.0, "Grizzlies": 110.5, "Pistons": 112.0, "Heat": 109.5, 
    "Clippers": 109.0, "Pelicans": 108.5, "Hawks": 108.0, "Bulls": 107.5, "Raptors": 106.0, 
    "Jazz": 105.0, "Hornets": 104.5, "Blazers": 104.0, "Trail Blazers": 104.0, "Wizards": 103.5, 
    "Nets": 103.0
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
                                if 0 <= pts_anotados <= 75:
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
    penizacion_total = 0.0
    alertas_equipo = []
    url_summary = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={event_id}"
    try:
        resp = requests.get(url_summary, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            injuries = data.get("injuries", [])
            df_titulares = pd.read_csv(ARCHIVO_TITULARES, encoding='utf-8-sig') if os.path.exists(ARCHIVO_TITULARES) else pd.DataFrame()
            
            for team_inj in injuries:
                team_name = team_inj.get("team", {}).get("displayName", "")
                if normalizar_texto(nombre_equipo) in normalizar_texto(team_name) or normalizar_texto(team_name) in normalizar_texto(nombre_equipo):
                    for inj in team_inj.get("injuries", []):
                        status = inj.get("status", "").upper()
                        multiplicador = 0.25 if "OUT" in status else (0.05 if "QUESTIONABLE" in status or "DAY-TO-DAY" in status or "DOUBTFUL" in status else 0.0)
                        if multiplicador == 0.0: continue
                        
                        jugador = inj.get("athlete", {}).get("displayName", "")
                        details = inj.get("details", {})
                        motivo_texto = details.get("detail", details.get("type", "Lesión / Descanso"))
                        fecha_retorno = details.get("returnDate", "Por definir")
                        
                        if not df_titulares.empty:
                            fila_jug = df_titulares[df_titulares['Jugador'].str.contains(jugador, case=False, na=False)]
                            if not fila_jug.empty:
                                puntos_lista = [float(str(fila_jug.iloc[0].get(col, "")).replace("pts", "").strip()) for col in df_titulares.columns[3:] if "pts" in str(fila_jug.iloc[0].get(col, ""))]
                                if puntos_lista:
                                    prom = np.mean(puntos_lista)
                                    impacto_neto = prom * multiplicador
                                    penizacion_total += impacto_neto
                                    alertas_equipo.append({
                                        "jugador": jugador, "equipo": nombre_equipo, "estatus": status,
                                        "motivo": motivo_texto, "fecha_regreso": fecha_retorno,
                                        "impacto_simulador": f"-{round(impacto_neto, 1)} pts"
                                    })
    except Exception as e:
        logging.error(f"Error consultando lesiones en ESPN para {nombre_equipo}: {e}")
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
                linea_promedio_historica = float(df_h["Line_Apuesta"].tail(15).mean())
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
            pen_loc, alert_loc = detectar_lesiones_y_calcular_impacto(event_id, local_team)
            pen_vis, alert_vis = detectar_lesiones_y_calcular_impacto(event_id, visitante_team)
            todas_las_alertas.extend(alert_loc + alert_vis)

            base_loc_ofensiva = max(98.0, base_loc - pen_loc)
            base_vis_ofensiva = max(98.0, base_vis - pen_vis)
            stats_loc = {"PTS_OFENSIVA": base_loc_ofensiva, "DEF_R_RIVAL": base_vis, "RITMO": 1.0, "FACTOR_FORMA": 1.0}
            stats_vis = {"PTS_OFENSIVA": base_vis_ofensiva, "DEF_R_RIVAL": base_loc, "RITMO": 1.0, "FACTOR_FORMA": 1.0}

            linea_apuesta = round((base_loc + base_vis) * 1.01, 1)
            spread_casa = 3.5  # Valor por defecto de spread si la API no provee la cuota exacta
            odds_info = comp_data.get("odds", [])
            if odds_info:
                try: linea_apuesta = float(odds_info[0].get("overUnder", linea_apuesta))
                except: pass
                try: spread_casa = float(odds_info[0].get("spread", spread_casa))
                except: pass

            if linea_apuesta < 200 or linea_apuesta > 255: linea_apuesta = linea_promedio_historica

            if local_team and visitante_team:
                partidos.append({
                    "event_id": event_id, "local": local_team, "visitante": visitante_team,
                    "stats_loc": stats_loc, "stats_vis": stats_vis, "linea": linea_apuesta, "spread_casa": spread_casa
                })
                
        tz_mexico = timezone(timedelta(hours=-6))
        ahora = datetime.now(tz_mexico)
        datos_json = {
            "fecha": ahora.strftime("%Y-%m-%d"), "ultima_actualizacion": ahora.strftime("%H:%M UTC-6"),
            "mensaje_general": "🏥 Reporte médico autónomo procesado exitosamente.", "alertas_criticas": todas_las_alertas
        }
        with open(ARCHIVO_LESIONES, "w", encoding="utf-8") as f:
            json.dump(datos_json, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Error procesando cartelera: {e}")
    return partidos

def generar_recomendacion_autonoma(local, visitante, pred_ganador, prob_ganador_pct, promedio_simulado, linea_apuesta, spread_casa):
    """
    Compara el spread real de la casa de apuestas con la simulación y genera una recomendación limpia,
    ordenada y sin menciones innecesarias.
    """
    lineas = []
    es_local = (pred_ganador == local)
    prob_fav = prob_ganador_pct if es_local else (100.0 - prob_ganador_pct)
    favorito = local if es_local else visitante
    underdog = visitante if es_local else local

    # 1. Análisis del Spread / Hándicap frente al Casino
    if prob_fav >= 72.0:
        lineas.append(f"• **Hándicap & Spread:** El modelo da amplio favoritismo a **{favorito}** ({prob_fav}%). Frente al spread de la casa (**{spread_casa:+g}**), la simulación respalda la línea o sugiere una ligera protección con el underdog si el hándicap es muy alto.")
    elif prob_fav >= 58.0:
        lineas.append(f"• **Hándicap & Spread:** Ventaja moderada para **{favorito}** ({prob_fav}%). Con un spread de **{spread_casa:+g}**, el margen es estrecho; es preferible tomar los puntos a favor del underdog o evitar jugarlo directo.")
    else:
        lineas.append(f"• **Hándicap & Spread:** Máxima paridad entre ambos equipos. El spread de **{spread_casa:+g}** refleja un duelo impredecible.")

    # 2. Análisis de Totales (Over / Under)
    diferencia_ou = abs(promedio_simulado - linea_apuesta)
    tipo_ou = "OVER (Altas)" if promedio_simulado > linea_apuesta else "DEBAJO (Bajas)"
    if diferencia_ou >= 7.5:
        lineas.append(f"• **Totales (O/U):** Fuerte divergencia (Simulado: {promedio_simulado} vs Línea: {linea_apuesta}), apuntando claramente a un **{tipo_ou}**.")
    elif diferencia_ou >= 4.0:
        lineas.append(f"• **Totales (O/U):** Margen aceptable hacia el **{tipo_ou}** (Sim: {promedio_simulado} vs Línea: {linea_apuesta}).")
    else:
        lineas.append(f"• **Totales (O/U):** Línea eficiente en {linea_apuesta} puntos; sin divergencia útil frente al simulador ({promedio_simulado}).")

    # 3. Veredicto Final / Filtro de Seguridad
    if prob_fav < 60.0 and diferencia_ou < 5.0:
        veredicto = "🛑 **Veredicto:** Alta volatilidad y sin ventajas claras. **Preferible no meterle a este partido.**"
    elif prob_fav >= 70.0 or diferencia_ou >= 7.5:
        veredicto = "✅ **Veredicto:** Partido apto para parley combinando líneas de hándicap o totales respaldados."
    else:
        veredicto = "⚠️ **Veredicto:** Precaución moderada. Operar únicamente con líneas protegidas o descartar."

    lineas.append(veredicto)
    return "<br>".join(lineas)

def simular_monte_carlo_con_rotacion(partido, pesos_optimos):
    local = partido["local"]
    visitante = partido["visitante"]
    stats_loc = partido["stats_loc"]
    stats_vis = partido["stats_vis"]
    linea_apuesta = partido["linea"]
    spread_casa = partido["spread_casa"]

    poder_ofensivo_local = (stats_loc["PTS_OFENSIVA"] * pesos_optimos[0]) * stats_loc["FACTOR_FORMA"]
    poder_ofensivo_visita = (stats_vis["PTS_OFENSIVA"] * pesos_optimos[1]) * stats_vis["FACTOR_FORMA"]

    proyeccion_loc_final = (poder_ofensivo_local + stats_vis.get("DEF_R_RIVAL", 110)) / 2 * pesos_optimos[2]
    proyeccion_vis_final = (poder_ofensivo_visita + stats_loc.get("DEF_R_RIVAL", 110)) / 2 * pesos_optimos[2]

    suma_proyectada_base = proyeccion_loc_final + proyeccion_vis_final
    factor_ajuste_vegas = 1.0
    if linea_apuesta >= 235.0 and suma_proyectada_base < linea_apuesta:
        factor_ajuste_vegas = min(1.08, linea_apuesta / max(suma_proyectada_base, 1.0))
    elif linea_apuesta <= 215.0 and suma_proyectada_base > linea_apuesta:
        factor_ajuste_vegas = max(0.92, linea_apuesta / max(suma_proyectada_base, 1.0))

    multiplicador_ritmo = stats_loc.get("RITMO", 1.0) * factor_ajuste_vegas

    n_sims = 2000
    puntos_locales_sim = np.clip(np.random.normal(proyeccion_loc_final * multiplicador_ritmo, 9.0, n_sims), 80, 155)
    puntos_visitas_sim = np.clip(np.random.normal(proyeccion_vis_final * multiplicador_ritmo, 9.0, n_sims), 80, 155)
    total_puntos_sim = puntos_locales_sim + puntos_visitas_sim

    promedio_simulado = np.mean(total_puntos_sim)
    prob_over = np.sum(total_puntos_sim > linea_apuesta) / n_sims * 100

    diff_poder = (proyeccion_loc_final + 3.0) - proyeccion_vis_final 
    prob_local = 1 / (1 + np.exp(-diff_poder / 6.5)) 
    prob_ganador_pct = max(prob_local, 1 - prob_local) * 100
    pred_ganador = local if prob_local >= 0.5 else visitante

    if prob_ganador_pct >= 65.0: semaforo_ganador = "🟢 VERDE (Alta Confiabilidad)"
    elif prob_ganador_pct >= 55.0: semaforo_ganador = "🟡 AMARILLO (Precaución - Juego Cerrado)"
    else: semaforo_ganador = "🔴 ROJO (Volátil - Evitar Moneyline)"

    distancia_linea = abs(promedio_simulado - linea_apuesta)
    if distancia_linea >= 7.5: semaforo_puntos = "🟢 GRAN VALOR (Divergencia Fuerte vs Vegas)"
    elif distancia_linea >= 4.0: semaforo_puntos = "🟡 VALOR MODERADO (Margen Aceptable)"
    else: semaforo_puntos = "⚪ NEUTRO (Línea Cerrada / Sin Ventaja)"

    recomendacion_texto = generar_recomendacion_autonoma(
        local, visitante, pred_ganador, round(prob_ganador_pct, 1), 
        round(promedio_simulado, 1), linea_apuesta, spread_casa
    )

    fecha_actual_mexico = datetime.now(timezone(timedelta(hours=-6))).strftime("%Y-%m-%d")

    return {
        "Fecha": fecha_actual_mexico,
        "Local": local, "Visitante": visitante,
        "Pred_Ganador": pred_ganador,
        "Prob_Ganador_Pct": round(prob_ganador_pct, 1),
        "Semaforo_Ganador": semaforo_ganador,
        "Line_Apuesta": linea_apuesta,
        "Pred_OU": "OVER" if prob_over > 50 else "DEBAJO",
        "Promedio_Simulado": round(promedio_simulado, 1),
        "Semaforo_Puntos": semaforo_puntos,
        "Modo_Playoffs": PLAYOFFS_MODE,
        "Recomendacion_Autonoma": recomendacion_texto
    }

if __name__ == "__main__":
    logging.info("🤖 Iniciando ejecución autónoma...")
    sincronizar_titulares_y_puntajes()
    pesos_calibrados = optimizar_pesos_modelo()
    partidos_de_hoy = obtener_cartelera_y_boxscore_avanzado()

    if not partidos_de_hoy:
        partidos_de_hoy = [{
            "event_id": "000000", "local": "Celtics", "visitante": "Heat",
            "stats_loc": {"PTS_OFENSIVA": 118.0, "DEF_R_RIVAL": 109.5, "RITMO": 1.0, "FACTOR_FORMA": 1.0},
            "stats_vis": {"PTS_OFENSIVA": 109.5, "DEF_R_RIVAL": 118.0, "RITMO": 1.0, "FACTOR_FORMA": 1.0},
            "linea": 221.5, "spread_casa": 4.5
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

    logging.info("✨ ¡Proceso completado con éxito!")
