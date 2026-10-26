# bot_actualizado.py
import pandas as pd
import numpy as np
import os
import requests
from datetime import datetime

ARCHIVO_HISTORIAL = 'historial_evaluaciones_nba.csv'

def obtener_cartelera_y_boxscore_avanzado():
    """Consulta la cartelera del día, la línea de apuestas y calcula el factor de forma reciente."""
    partidos = []
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            for event in events:
                event_id = event.get('id')
                competitions = event.get('competitions', [])
                if competitions:
                    comp_data = competitions[0]
                    competitors = comp_data.get('competitors', [])
                    local_team = None
                    visitante_team = None
                    
                    stats_loc = {'PTS_TITULARES': 82.0, 'PTS_BANCA': 32.0, 'RITMO': 98.5, 'FACTOR_FORMA': 1.0}
                    stats_vis = {'PTS_TITULARES': 80.0, 'PTS_BANCA': 30.0, 'RITMO': 98.0, 'FACTOR_FORMA': 1.0}
                    
                    for comp in competitors:
                        team_info = comp.get('team', {})
                        nombre_equipo = team_info.get('name', '')
                        
                        # Analizar registros y racha reciente de la API de ESPN
                        factor_forma = calcular_factor_forma_equipo(comp)
                        
                        if comp.get('homeAway') == 'home':
                            local_team = nombre_equipo
                            stats_loc['FACTOR_FORMA'] = factor_forma
                        else:
                            visitante_team = nombre_equipo
                            stats_vis['FACTOR_FORMA'] = factor_forma
                    
                    # Extracción de la línea de puntos real (Over/Under)
                    linea_apuesta = 225.5
                    odds_info = comp_data.get('odds', [])
                    if odds_info:
                        linea_apuesta = float(odds_info[0].get('overUnder', 225.5))
                    
                    if local_team and visitante_team:
                        partidos.append({
                            "event_id": event_id,
                            "local": local_team, 
                            "visitante": visitante_team,
                            "stats_loc": stats_loc,
                            "stats_vis": stats_vis,
                            "linea": linea_apuesta
                        })
        print(f"🌐 Conexión avanzada exitosa: {len(partidos)} encuentros con análisis de forma reciente.")
    except Exception as e:
        print(f"⚠️ Aviso en la extracción de cartelera: {e}")
    return partidos

def calcular_factor_forma_equipo(comp_competitor):
    """Calcula un multiplicador basado en la racha de victorias/derrotas recientes de la API."""
    factor = 1.0  # Neutro por defecto
    try:
        records = comp_competitor.get('records', [])
        for rec in records:
            # Buscamos registros de tipo 'last ten' (últimos 10 partidos) o general
            summary = rec.get('summary', '') # Ej: "5-5" o registro general
            if '-' in summary:
                parts = summary.split('-')
                wins = int(parts[0])
                losses = int(parts[1])
                total = wins + losses
                if total > 0:
                    win_pct = wins / total
                    # Si el equipo gana más del 60%, se le da un bono de inercia positiva (>1.0)
                    # Si gana menos del 40% (bache/mala racha), se le aplica un castigo (<1.0)
                    if win_pct >= 0.60:
                        factor = 1.03
                    elif win_pct <= 0.40:
                        factor = 0.96
    except Exception:
        pass
    return factor

def simular_monte_carlo_con_rotacion(partido):
    """Simulación de Monte Carlo ajustada con el Factor de Forma Reciente."""
    local = partido["local"]
    visitante = partido["visitante"]
    stats_loc = partido["stats_loc"]
    stats_vis = partido["stats_vis"]
    linea_apuesta = partido["linea"]

    # Aporte ofensivo base modificado por la inercia/racha actual del equipo
    poder_ofensivo_local = (stats_loc['PTS_TITULARES'] + stats_loc['PTS_BANCA']) * stats_loc['FACTOR_FORMA']
    poder_ofensivo_visita = (stats_vis['PTS_TITULARES'] + stats_vis['PTS_BANCA']) * stats_vis['FACTOR_FORMA']

    ritmo_combinado = (stats_loc['RITMO'] + stats_vis['RITMO']) / 2
    factor_ritmo = ritmo_combinado / 99.0

    ofensiva_local_final = poder_ofensivo_local * factor_ritmo
    ofensiva_visita_final = poder_ofensivo_visita * factor_ritmo

    # Simulaciones de Monte Carlo (2000 iteraciones)
    n_sims = 2000
    puntos_locales_sim = np.clip(np.random.normal(ofensiva_local_final, 8.0, n_sims), 90, 145)
    puntos_visitas_sim = np.clip(np.random.normal(ofensiva_visita_final, 8.0, n_sims), 90, 145)
    total_puntos_sim = puntos_locales_sim + puntos_visitas_sim

    promedio_simulado = np.mean(total_puntos_sim)
    prob_over = np.sum(total_puntos_sim > linea_apuesta) / n_sims * 100
    
    # Diferencial de poder ponderando la forma reciente
    diff_poder = (ofensiva_local_final + 3.0) - ofensiva_visita_final
    prob_local = 1 / (1 + np.exp(-diff_poder / 10))

    prediccion = {
        'Fecha': datetime.today().strftime('%Y-%m-%d'),
        'Local': local,
        'Visitante': visitante,
        'Pred_Ganador_Local': bool(prob_local >= 0.5),
        'Line_Apuesta': linea_apuesta,
        'Pred_OU': "OVER" if prob_over > 50 else "UNDER",
        'Promedio_Simulado': round(promedio_simulado, 1)
    }
    
    ganador_str = local if prediccion['Pred_Ganador_Local'] else visitante
    print(f"🏀 {local} vs {visitante} | Línea: {linea_apuesta} | Proyectado: {promedio_simulado:.1f} pts | O/U: {prediccion['Pred_OU']} | Ganador: {ganador_str}")
    return prediccion

def ejecutar_feedback_loop():
    if not os.path.exists(ARCHIVO_HISTORIAL):
        return
    df = pd.read_csv(ARCHIVO_HISTORIAL)
    if 'Estado_Evaluacion' not in df.columns:
        df['Estado_Evaluacion'] = 'Pendiente'
        df.to_csv(ARCHIVO_HISTORIAL, index=False)

if __name__ == "__main__":
    print("🤖 Iniciando motor analítico con Factor de Forma Reciente y Momentum...")
    
    ejecutar_feedback_loop()
    
    partidos_de_hoy = obtener_cartelera_y_boxscore_avanzado()
    
    if not partidos_de_hoy:
        print("📌 Sin cartelera activa. Usando respaldo de prueba...")
        partidos_de_hoy = [{
            "event_id": "000000",
            "local": "Celtics", 
            "visitante": "Heat", 
            "stats_loc": {'PTS_TITULARES': 82.0, 'PTS_BANCA': 32.0, 'RITMO': 98.5, 'FACTOR_FORMA': 1.03},
            "stats_vis": {'PTS_TITULARES': 80.0, 'PTS_BANCA': 30.0, 'RITMO': 98.0, 'FACTOR_FORMA': 0.96},
            "linea": 221.5
        }]
    
    nuevos_registros = []
    for p in partidos_de_hoy:
        pred = simular_monte_carlo_con_rotacion(p)
        nuevos_registros.append(pred)
    
    df_new = pd.DataFrame(nuevos_registros)
    if os.path.exists(ARCHIVO_HISTORIAL):
        df_existing = pd.read_csv(ARCHIVO_HISTORIAL)
        df_final = pd.concat([df_existing, df_new], ignore_index=True)
        df_final.to_csv(ARCHIVO_HISTORIAL, index=False)
    else:
        df_new.to_csv(ARCHIVO_HISTORIAL, index=False)
        
    print("✨ ¡Proceso completado con inercia y momento competitivo integrados!")
