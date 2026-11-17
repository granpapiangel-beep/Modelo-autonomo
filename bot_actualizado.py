from datetime import datetime, timezone, timedelta
import json
import logging
import os
import time
import unicodedata
import numpy as np
import pandas as pd
import requests
from scipy.optimize import minimize

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

ARCHIVO_HISTORIAL = "historial_evaluaciones_nba.csv"
ARCHIVO_TITULARES = "Titulares_NBA_Oficiales_30_Equipos(Puntajes Diarios).csv"
ARCHIVO_LESIONES = "alertas_lesiones.json"
PLAYOFFS_MODE = False

TIERS_BASE_EQUIPOS = {
    "Celtics": 118.0, "Thunder": 114.5, "Cavaliers": 113.5, "Nuggets": 113.0, "Mavericks": 115.5,
    "Spurs": 117.0, "Bucks": 109.5, "76ers": 116.5, "Timberwolves": 114.0, "Knicks": 114.0,
    "Suns": 109.5, "Rockets": 113.0, "Lakers": 116.5, "Warriors": 112.0, "Kings": 112.0,
    "Magic": 111.0, "Pacers": 109.0, "Grizzlies": 110.5, "Pistons": 112.0, "Heat": 109.5,
    "Clippers": 109.0, "Pelicans": 108.5, "Hawks": 108.0, "Bulls": 107.5, "Raptors": 106.0,
    "Jazz": 105.0, "Hornets": 104.5, "Blazers": 104.0, "Trail Blazers": 104.0, "Wizards": 103.5,
    "Nets": 103.0,
}

ALIAS_EQUIPOS = {
    "boston celtics": "Celtics", "celtics": "Celtics",
    "okc thunder": "Thunder", "thunder": "Thunder",
    "cleveland cavaliers": "Cavaliers", "cavaliers": "Cavaliers",
    "denver nuggets": "Nuggets", "nuggets": "Nuggets",
    "dallas mavericks": "Mavericks", "mavericks": "Mavericks",
    "san antonio spurs": "Spurs", "spurs": "Spurs",
    "milwaukee bucks": "Bucks", "bucks": "Bucks",
    "philadelphia 76ers": "76ers", "76ers": "76ers",
    "minnesota timberwolves": "Timberwolves", "timberwolves": "Timberwolves",
    "new york knicks": "Knicks", "knicks": "Knicks",
    "phoenix suns": "Suns", "suns": "Suns",
    "houston rockets": "Rockets", "rockets": "Rockets",
    "los angeles lakers": "Lakers", "lakers": "Lakers",
    "golden state warriors": "Warriors", "warriors": "Warriors",
    "sacramento kings": "Kings", "kings": "Kings",
    "orlando magic": "Magic", "magic": "Magic",
    "indiana pacers": "Pacers", "pacers": "Pacers",
    "memphis grizzlies": "Grizzlies", "grizzlies": "Grizzlies",
    "detroit pistons": "Pistons", "pistons": "Pistons",
    "miami heat": "Heat", "heat": "Heat",
    "la clippers": "Clippers", "clippers": "Clippers",
    "new orleans pelicans": "Pelicans", "pelicans": "Pelicans",
    "atlanta hawks": "Hawks", "hawks": "Hawks",
    "chicago bulls": "Bulls", "bulls": "Bulls",
    "toronto raptors": "Raptors", "raptors": "Raptors",
    "utah jazz": "Jazz", "jazz": "Jazz",
    "charlotte hornets": "Hornets", "hornets": "Hornets",
    "portland trail blazers": "Trail Blazers", "trail blazers": "Trail Blazers",
    "blazers": "Blazers", "portland blazers": "Blazers",
    "washington wizards": "Wizards", "wizards": "Wizards",
    "brooklyn nets": "Nets", "nets": "Nets",
}


def normalizar_texto(texto):
    if not isinstance(texto, str):
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower().strip()


def resolver_nombre_equipo(nombre_equipo):
    if not nombre_equipo:
        return ""
    clave = normalizar_texto(nombre_equipo)
    if clave in ALIAS_EQUIPOS:
        return ALIAS_EQUIPOS[clave]
    for alias, nombre_canonico in ALIAS_EQUIPOS.items():
        if alias in clave or clave in alias:
            return nombre_canonico
    return nombre_equipo


def pedido_espn(url, timeout=10, max_retries=3, backoff=1.0):
    last_error = None
    for intento in range(max_retries):
        try:
            resp = requests.get(url, timeout=timeout)
            if resp.status_code == 200:
                return resp
            if resp.status_code in (429, 500, 502, 503, 504):
                last_error = RuntimeError(f"HTTP {resp.status_code} for {url}")
                if intento < max_retries - 1:
                    time.sleep(backoff * (2 ** intento))
                    continue
                return resp
            return resp
        except Exception as e:
            last_error = e
            if intento < max_retries - 1:
                time.sleep(backoff * (2 ** intento))
                continue
            logging.warning(f"Fallo en solicitud a ESPN ({url}): {e}")
            break
    if last_error:
        logging.warning(f"Último error de ESPN: {last_error}")
    return None


def traducir_motivo_lesion(motivo):
    if not isinstance(motivo, str):
        return "No especificado"
    m_lower = motivo.lower().strip()
    diccionario = {
        "soreness": "Molestia muscular",
        "strain": "Distensión muscular",
        "knee": "Lesión de rodilla",
        "ankle": "Lesión de tobillo",
        "bruise": "Contusión / Golpe",
        "illness": "Enfermedad / Indispuesto",
        "hamstring": "Molestia en isquiotibiales",
        "back": "Dolor de espalda",
        "shoulder": "Lesión de hombro",
        "rest": "Descanso programado",
        "concussion": "Protocolo de conmoción",
        "foot": "Lesión de pie",
        "wrist": "Lesión de muñeca",
        "hip": "Molestia en cadera",
        "inflammation": "Inflamación",
        "toe": "Lesión en el dedo del pie",
        "spasms": "Espasmos musculares",
        "sprain": "Esguince",
        "surgery": "Cirugía / Recuperación",
        "achilles": "Lesión en el talón de Aquiles",
        "elbow": "Lesión de codo",
        "hand": "Lesión de mano",
        "calf": "Molestia en pantorrilla",
        "not specified": "No especificado",
    }
    for eng, esp in diccionario.items():
        if eng in m_lower:
            return esp
    return motivo if motivo else "No especificado"


def sincronizar_titulares_y_puntajes():
    logging.info("🔄 Sincronizando plantillas y puntajes desde ESPN...")
    tz_mexico = timezone(timedelta(hours=-6))
    hoy = datetime.now(tz_mexico).date()
    meses_abreviados = {1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr', 5: 'may', 6: 'jun', 7: 'jul', 8: 'ago', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic'}

    df_existente = pd.DataFrame()
    if os.path.exists(ARCHIVO_TITULARES):
        try:
            df_existente = pd.read_csv(ARCHIVO_TITULARES, encoding='utf-8-sig')
        except Exception:
            pass

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
            resp = pedido_espn(url_scoreboard, timeout=10, max_retries=3)
            if resp is None or resp.status_code != 200:
                continue
            events = resp.json().get("events", [])
            if not events:
                continue

            for event in events:
                competitions = event.get("competitions", [])
                if not competitions:
                    continue
                if not competitions[0].get("status", {}).get("type", {}).get("completed", False):
                    continue

                event_id = event.get("id")
                url_summary = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={event_id}"
                sum_resp = pedido_espn(url_summary, timeout=5, max_retries=3)
                if sum_resp is None or sum_resp.status_code != 200:
                    continue

                boxscore = sum_resp.json().get("boxscore", {})
                for team_block in boxscore.get("players", []):
                    nombre_equipo = resolver_nombre_equipo(team_block.get("team", {}).get("displayName", "Equipo NBA"))
                    statistics_list = team_block.get("statistics", [])
                    if not statistics_list:
                        continue

                    labels = statistics_list[0].get("labels", [])
                    pts_index = 0
                    for idx, lbl in enumerate(labels):
                        if lbl.upper() in ["PTS", "POINTS"]:
                            pts_index = idx
                            break

                    for athlete_info in statistics_list[0].get("athletes", []):
                        athlete = athlete_info.get("athlete", {})
                        nombre_jugador = athlete.get("displayName", "")
                        posicion = athlete.get("position", {}).get("abbreviation", "BENCH")
                        stats_arr = athlete_info.get("stats", [])

                        if stats_arr and len(stats_arr) > pts_index:
                            try:
                                valor = str(stats_arr[pts_index]).strip()
                                if '-' in valor or valor == '':
                                    continue
                                pts = int(valor)
                                if 0 <= pts <= 75:
                                    clave = (nombre_equipo, posicion, nombre_jugador)
                                    if clave not in base_datos_jugadores:
                                        base_datos_jugadores[clave] = {'Equipo': nombre_equipo, 'Posicion': posicion, 'Jugador': nombre_jugador}
                                    base_datos_jugadores[clave][col_nombre] = f"{pts} pts"
                            except ValueError:
                                pass
        except Exception as e:
            logging.error(f"Error sincronizando titulares: {e}")

    filas_finales = list(base_datos_jugadores.values())
    if filas_finales:
        df_nuevo = pd.DataFrame(filas_finales)
        orden_posiciones = {'PG': 1, 'SG': 2, 'SF': 3, 'PF': 4, 'C': 5, 'BENCH': 6}
        if 'Posicion' in df_nuevo.columns:
            df_nuevo['Pos_Rank'] = df_nuevo['Posicion'].map(orden_posiciones).fillna(99)
            df_nuevo = df_nuevo.sort_values(by=['Equipo', 'Pos_Rank']).drop(columns=['Pos_Rank'])
        df_nuevo.to_csv(ARCHIVO_TITULARES, index=False, encoding='utf-8-sig')


def actualizar_resultados_historicos_desde_espn():
    if not os.path.exists(ARCHIVO_HISTORIAL):
        return
    try:
        df_hist = pd.read_csv(ARCHIVO_HISTORIAL)
        if df_hist.empty:
            return

        if "Puntaje_Local_Real" not in df_hist.columns:
            df_hist["Puntaje_Local_Real"] = np.nan
            df_hist["Puntaje_Visita_Real"] = np.nan
            df_hist["Evaluado"] = False

        for idx, row in df_hist.iterrows():
            if row.get("Evaluado", False) is True:
                continue
        
            fecha_str = str(row.get("Fecha", ""))
            local = row.get("Local", "")
            visitante = row.get("Visitante", "")
            if not fecha_str or not local:
                continue

            fecha_api = fecha_str.replace("-", "")
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={fecha_api}"
            resp = pedido_espn(url, timeout=5, max_retries=3)
            if resp is None or resp.status_code != 200:
                continue

            events = resp.json().get("events", [])
            for event in events:
                comps = event.get("competitions", [])
                if not comps:
                    continue
                status_type = comps[0].get("status", {}).get("type", {})
                if not status_type.get("completed", False):
                    continue

                competitors = comps[0].get("competitors", [])
                loc_name, vis_name, pts_l, pts_v = "", "", 0, 0
                for comp in competitors:
                    nombre = comp.get("team", {}).get("name", "")
                    score = int(comp.get("score", 0))
                    if comp.get("homeAway") == "home":
                        loc_name, pts_l = nombre, score
                    else:
                        vis_name, pts_v = nombre, score

                if normalizar_texto(local) in normalizar_texto(loc_name) and normalizar_texto(visitante) in normalizar_texto(vis_name):
                    df_hist.at[idx, "Puntaje_Local_Real"] = pts_l
                    df_hist.at[idx, "Puntaje_Visita_Real"] = pts_v
                    df_hist.at[idx, "Evaluado"] = True
                    break

        df_hist.to_csv(ARCHIVO_HISTORIAL, index=False)
    except Exception as e:
        logging.error(f"Error actualizando resultados históricos: {e}")


def detectar_lesiones_y_calcular_impacto(event_id, nombre_equipo):
    penizacion_total = 0.0
    alertas_equipo = []
    url_summary = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={event_id}"
    try:
        resp = pedido_espn(url_summary, timeout=8, max_retries=3)
        if resp is None or resp.status_code != 200:
            return penizacion_total, alertas_equipo

        data = resp.json()
        injuries = data.get("injuries", [])
        df_titulares = pd.read_csv(ARCHIVO_TITULARES, encoding='utf-8-sig') if os.path.exists(ARCHIVO_TITULARES) else pd.DataFrame()

        for team_inj in injuries:
            team_name = resolver_nombre_equipo(team_inj.get("team", {}).get("displayName", ""))
            if normalizar_texto(nombre_equipo) in normalizar_texto(team_name) or normalizar_texto(team_name) in normalizar_texto(nombre_equipo):
                for inj in team_inj.get("injuries", []):
                    status = inj.get("status", "").upper()
                    multiplicador = 0.25 if "OUT" in status else (0.05 if "QUESTIONABLE" in status or "DAY-TO-DAY" in status or "DOUBTFUL" in status else 0.0)
                    if multiplicador == 0.0:
                        continue

                    jugador = inj.get("athlete", {}).get("displayName", "")
                    details = inj.get("details", {})
                    motivo_raw = details.get("detail", details.get("type", "No especificado"))
                    motivo_texto = traducir_motivo_lesion(motivo_raw)
                    fecha_retorno = details.get("returnDate", "Por definir")

                    if not df_titulares.empty:
                        candidatos = df_titulares[
                            df_titulares['Jugador'].apply(
                                lambda x: isinstance(x, str) and (
                                    normalizar_texto(x) in normalizar_texto(jugador) or normalizar_texto(jugador) in normalizar_texto(x)
                                )
                            )
                        ]
                        if not candidatos.empty:
                            fila_jug = candidatos.iloc[0]
                            puntos_lista = []
                            for col in df_titulares.columns[3:]:
                                valor = fila_jug.get(col, "")
                                if "pts" in str(valor).lower():
                                    try:
                                        puntos_lista.append(float(str(valor).lower().replace("pts", "").strip()))
                                    except ValueError:
                                        continue
                            if puntos_lista:
                                prom = np.mean(puntos_lista)
                                factor_rol = 1.2 if "PG" in str(fila_jug.get("Posicion", "")).upper() or "SG" in str(fila_jug.get("Posicion", "")).upper() else 1.0
                                impacto_neto = prom * multiplicador * factor_rol
                                penizacion_total += impacto_neto
                                alertas_equipo.append({
                                    "jugador": jugador,
                                    "equipo": nombre_equipo,
                                    "estatus": status,
                                    "motivo": motivo_texto,
                                    "fecha_regreso": fecha_retorno,
                                    "impacto_simulador": f"-{round(impacto_neto, 1)} pts"
                                })
    except Exception as e:
        logging.error(f"Error consultando lesiones en ESPN para {nombre_equipo}: {e}")
    return penizacion_total, alertas_equipo


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
            prom_sim = float(row.get("Promedio_Simulado", 225.5))
            pred_total = prom_sim * pesos[0] * pesos[2]

            if pd.notna(row.get("Puntaje_Local_Real")) and pd.notna(row.get("Puntaje_Visita_Real")):
                total_objetivo = float(row.get("Puntaje_Local_Real", 0.0)) + float(row.get("Puntaje_Visita_Real", 0.0))
            else:
                total_objetivo = float(row.get("Line_Apuesta", 225.5))

            error_total += (pred_total - total_objetivo) ** 2
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
        resultado = minimize(funcion_costo_historico, [1.0, 1.0, 1.0], args=(df_hist,), method="SLSQP", bounds=[(0.95, 1.05), (0.95, 1.05), (0.98, 1.02)])
        if resultado.success:
            return resultado.x
    except Exception:
        pass
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
        except Exception:
            pass

    todas_las_alertas = []
    try:
        response = pedido_espn(url, timeout=10, max_retries=3)
        if response is None or response.status_code != 200:
            return partidos

        events = response.json().get("events", [])
        for event in events:
            event_id = event.get("id")
            competitions = event.get("competitions", [])
            if not competitions:
                continue
            comp_data = competitions[0]
            local_team, visitante_team = None, None
            for comp in comp_data.get("competitors", []):
                nombre_equipo = resolver_nombre_equipo(comp.get("team", {}).get("name", ""))
                if comp.get("homeAway") == "home":
                    local_team = nombre_equipo
                else:
                    visitante_team = nombre_equipo

            if not local_team or not visitante_team:
                continue

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
            spread_casa = 3.5
            momio_decimal = 1.88
            odds_info = comp_data.get("odds", [])
            if odds_info:
                try:
                    linea_apuesta = float(odds_info[0].get("overUnder", linea_apuesta))
                except Exception:
                    pass
                try:
                    spread_casa = float(odds_info[0].get("spread", spread_casa))
                except Exception:
                    pass
                try:
                    home_odds = odds_info[0].get("homeTeamOdds", {})
                    price_american = home_odds.get("price", -110)
                    if price_american > 0:
                        momio_decimal = round(1 + (price_american / 100), 2)
                    else:
                        momio_decimal = round(1 + (100 / abs(price_american)), 2)
                except Exception:
                    pass

            if linea_apuesta < 200 or linea_apuesta > 255:
                linea_apuesta = linea_promedio_historica

            partidos.append({
                "event_id": event_id,
                "local": local_team,
                "visitante": visitante_team,
                "stats_loc": stats_loc,
                "stats_vis": stats_vis,
                "linea": linea_apuesta,
                "spread_casa": spread_casa,
                "momio": momio_decimal,
            })

        tz_mexico = timezone(timedelta(hours=-6))
        ahora = datetime.now(tz_mexico)
        datos_json = {
            "fecha": ahora.strftime("%Y-%m-%d"),
            "ultima_actualizacion": ahora.strftime("%H:%M UTC-6"),
            "mensaje_general": "🏥 Reporte médico procesado.",
            "alertas_criticas": todas_las_alertas,
        }
        with open(ARCHIVO_LESIONES, "w", encoding="utf-8") as f:
            json.dump(datos_json, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Error procesando cartelera: {e}")
    return partidos


def generar_recomendacion_corta(local, visitante, pred_ganador, prob_ganador_pct, promedio_simulado, linea_apuesta, spread_casa, momio_real):
    es_local = pred_ganador == local
    prob_fav = prob_ganador_pct if es_local else (100.0 - prob_ganador_pct)
    favorito = local if es_local else visitante
    underdog = visitante if es_local else local

    lineas = []
    if prob_fav < 56.0:
        lineas.append("🛑 <b>Veredicto:</b> Partido muy parejo y volátil. <i>Preferible no meterle a este encuentro.</i>")
        return "<br>".join(lineas)

    if prob_fav >= 72.0:
        spread_real = -abs(spread_casa) if favorito == local else abs(spread_casa)
        lineas.append(f"• <b>Análisis:</b> Sólido favoritismo para <b>{favorito}</b> ({prob_fav}%).")
        lineas.append(f"🎯 <b>Apuesta Recomendada:</b> <b>{favorito} Hándicap ({spread_real:+.1f})</b> (Cuota mercado: <b>{momio_real}x</b>)")
    else:
        spread_protegido = abs(spread_casa) + 3.5
        lineas.append(f"• <b>Análisis:</b> Ventaja ajustada para <b>{favorito}</b> ({prob_fav}%).")
        lineas.append(f"🎯 <b>Apuesta Recomendada:</b> <b>{underdog} Hándicap (+{spread_protegido:.1f})</b> (Margen protegido)")

    diferencia_ou = abs(promedio_simulado - linea_apuesta)
    tipo_ou = "Altas (Over)" if promedio_simulado > linea_apuesta else "Bajas (Under)"
    if diferencia_ou >= 6.0:
        lineas.append(f"🎯 <b>Alternativa Totales:</b> <b>{tipo_ou} ({linea_apuesta})</b>")

    return "<br>".join(lineas)


def simular_monte_carlo_con_rotacion(partido, pesos_optimos):
    local = partido["local"]
    visitante = partido["visitante"]
    stats_loc = partido["stats_loc"]
    stats_vis = partido["stats_vis"]
    linea_apuesta = partido["linea"]
    spread_casa = partido["spread_casa"]
    momio = partido["momio"]

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
    np.random.seed(int(datetime.now().timestamp()) % 1000000)
    puntos_locales_sim = np.clip(np.random.normal(proyeccion_loc_final * multiplicador_ritmo, 9.0, n_sims), 80, 155)
    puntos_visitas_sim = np.clip(np.random.normal(proyeccion_vis_final * multiplicador_ritmo, 9.0, n_sims), 80, 155)
    total_puntos_sim = puntos_locales_sim + puntos_visitas_sim

    promedio_simulado = np.mean(total_puntos_sim)
    prob_over = np.sum(total_puntos_sim > linea_apuesta) / n_sims * 100

    diff_poder = (proyeccion_loc_final + 3.0) - proyeccion_vis_final
    prob_local = 1 / (1 + np.exp(-diff_poder / 6.5))
    prob_ganador_pct = max(prob_local, 1 - prob_local) * 100
    pred_ganador = local if prob_local >= 0.5 else visitante

    if prob_ganador_pct >= 65.0:
        semaforo_ganador = "🟢 VERDE (Alta Confiabilidad)"
    elif prob_ganador_pct >= 55.0:
        semaforo_ganador = "🟡 AMARILLO (Precaución - Juego Cerrado)"
    else:
        semaforo_ganador = "🔴 ROJO (Volátil - Evitar Moneyline)"

    distancia_linea = abs(promedio_simulado - linea_apuesta)
    if distancia_linea >= 7.5:
        semaforo_puntos = "🟢 GRAN VALOR (Divergencia Fuerte vs Vegas)"
    elif distancia_linea >= 4.0:
        semaforo_puntos = "🟡 VALOR MODERADO (Margen Aceptable)"
    else:
        semaforo_puntos = "⚪ NEUTRO (Línea Cerrada / Sin Ventaja)"

    recomendacion_texto = generar_recomendacion_corta(
        local,
        visitante,
        pred_ganador,
        round(prob_ganador_pct, 1),
        round(promedio_simulado, 1),
        linea_apuesta,
        spread_casa,
        momio,
    )

    fecha_actual_mexico = datetime.now(timezone(timedelta(hours=-6))).strftime("%Y-%m-%d")
    return {
        "Fecha": fecha_actual_mexico,
        "Local": local,
        "Visitante": visitante,
        "Pred_Ganador": pred_ganador,
        "Prob_Ganador_Pct": round(prob_ganador_pct, 1),
        "Semaforo_Ganador": semaforo_ganador,
        "Line_Apuesta": linea_apuesta,
        "Pred_OU": "OVER" if prob_over > 50 else "DEBAJO",
        "Promedio_Simulado": round(promedio_simulado, 1),
        "Semaforo_Puntos": semaforo_puntos,
        "Modo_Playoffs": PLAYOFFS_MODE,
        "Recomendacion_Autonoma": recomendacion_texto,
    }


if __name__ == "__main__":
    logging.info("🤖 Iniciando ejecución autónoma...")
    sincronizar_titulares_y_puntajes()
    actualizar_resultados_historicos_desde_espn()
    pesos_calibrados = optimizar_pesos_modelo()
    partidos_de_hoy = obtener_cartelera_y_boxscore_avanzado()

    if not partidos_de_hoy:
        logging.warning("No hubo partidos hoy o la API no respondió; no se registran predicciones artificiales.")
    else:
        nuevos_registros = [simular_monte_carlo_con_rotacion(p, pesos_calibrados) for p in partidos_de_hoy]
        df_new = pd.DataFrame(nuevos_registros)
        if os.path.exists(ARCHIVO_HISTORIAL):
            try:
                df_existing = pd.read_csv(ARCHIVO_HISTORIAL)
                if not df_existing.empty:
                    fecha_actual = df_new["Fecha"].iloc[0] if len(df_new) > 0 else ""
                    if fecha_actual:
                        df_merged = pd.concat([df_existing, df_new], ignore_index=True)
                        df_merged = df_merged.drop_duplicates(subset=["Fecha", "Local", "Visitante"], keep="last")
                        df_merged.to_csv(ARCHIVO_HISTORIAL, index=False)
                    else:
                        df_existing = pd.concat([df_existing, df_new], ignore_index=True)
                        df_existing.to_csv(ARCHIVO_HISTORIAL, index=False)
                else:
                    df_new.to_csv(ARCHIVO_HISTORIAL, index=False)
            except Exception:
                df_new.to_csv(ARCHIVO_HISTORIAL, index=False)
        else:
            df_new.to_csv(ARCHIVO_HISTORIAL, index=False)

    logging.info("✨ ¡Proceso completado con éxito!")
