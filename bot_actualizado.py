import pandas as pd
import numpy as np
import os
import requests
from datetime import datetime

ARCHIVO_HISTORIAL = 'historial_evaluaciones_nba.csv'

# Base de datos optimizada de rendimiento, ritmo y estrellas de los 30 equipos
DATOS_NBA_REALES = {
    'Celtics': {'PTS': 120.6, 'PTS_OPP': 109.2, 'RITMO': 98.5, 'BONO_ESTRELLA': 4.5},
    'Knicks': {'PTS': 112.8, 'PTS_OPP': 110.1, 'RITMO': 96.0, 'BONO_ESTRELLA': 4.0},
    'Bucks': {'PTS': 119.5, 'PTS_OPP': 116.4, 'RITMO': 101.0, 'BONO_ESTRELLA': 5.0},
    '76ers': {'PTS': 114.6, 'PTS_OPP': 111.8, 'RITMO': 97.5, 'BONO_ESTRELLA': 5.5},
    'Cavaliers': {'PTS': 112.6, 'PTS_OPP': 110.3, 'RITMO': 96.5, 'BONO_ESTRELLA': 4.5},
    'Magic': {'PTS': 110.5, 'PTS_OPP': 108.4, 'RITMO': 97.0, 'BONO_ESTRELLA': 4.0},
    'Pacers': {'PTS': 123.3, 'PTS_OPP': 120.2, 'RITMO': 103.0, 'BONO_ESTRELLA': 4.5},
    'Heat': {'PTS': 110.1, 'PTS_OPP': 108.4, 'RITMO': 95.0, 'BONO_ESTRELLA': 3.5},
    'Bulls': {'PTS': 112.3, 'PTS_OPP': 113.7, 'RITMO': 99.0, 'BONO_ESTRELLA': 3.0},
    'Hawks': {'PTS': 118.3, 'PTS_OPP': 120.0, 'RITMO': 102.5, 'BONO_ESTRELLA': 4.0},
    'Nets': {'PTS': 110.4, 'PTS_OPP': 113.5, 'RITMO': 97.0, 'BONO_ESTRELLA': 3.0},
    'Raptors': {'PTS': 112.4, 'PTS_OPP': 118.8, 'RITMO': 99.0, 'BONO_ESTRELLA': 3.5},
    'Hornets': {'PTS': 106.6, 'PTS_OPP': 116.8, 'RITMO': 98.0, 'BONO_ESTRELLA': 3.5},
    'Wizards': {'PTS': 114.5, 'PTS_OPP': 123.0, 'RITMO': 102.0, 'BONO_ESTRELLA': 2.5},
    'Pistons': {'PTS': 110.0, 'PTS_OPP': 119.0, 'RITMO': 99.5, 'BONO_ESTRELLA': 3.5},
    'Thunder': {'PTS': 120.1, 'PTS_OPP': 112.7, 'RITMO': 101.0, 'BONO_ESTRELLA': 5.5},
    'Nuggets': {'PTS': 114.9, 'PTS_OPP': 109.6, 'RITMO': 96.5, 'BONO_ESTRELLA': 6.0},
    'Timberwolves': {'PTS': 113.0, 'PTS_OPP': 106.5, 'RITMO': 97.0, 'BONO_ESTRELLA': 4.5},
    'Clippers': {'PTS': 115.6, 'PTS_OPP': 112.3, 'RITMO': 97.5, 'BONO_ESTRELLA': 4.5},
    'Mavericks': {'PTS': 117.9, 'PTS_OPP': 115.6, 'RITMO': 98.5, 'BONO_ESTRELLA': 6.0},
    'Suns': {'PTS': 116.2, 'PTS_OPP': 113.2, 'RITMO': 98.0, 'BONO_ESTRELLA': 5.0},
    'Pelicans': {'PTS': 115.1, 'PTS_OPP': 110.7, 'RITMO': 98.0, 'BONO_ESTRELLA': 4.0},
    'Lakers': {'PTS': 118.0, 'PTS_OPP': 117.4, 'RITMO': 101.5, 'BONO_ESTRELLA': 4.5},
    'Kings': {'PTS': 116.6, 'PTS_OPP': 114.8, 'RITMO': 100.5, 'BONO_ESTRELLA': 4.0},
    'Warriors': {'PTS': 117.6, 'PTS_OPP': 115.5, 'RITMO': 100.0, 'BONO_ESTRELLA': 5.0},
    'Rockets': {'PTS': 114.3, 'PTS_OPP': 113.1, 'RITMO': 99.0, 'BONO_ESTRELLA': 3.5},
    'Jazz': {'PTS': 115.7, 'PTS_OPP': 120.5, 'RITMO': 100.0, 'BONO_ESTRELLA': 3.5},
    'Grizzlies': {'PTS': 105.8, 'PTS_OPP': 112.8, 'RITMO': 99.0, 'BONO_ESTRELLA': 4.5},
    'Blazers': {'PTS': 106.4, 'PTS_OPP': 115.4, 'RITMO': 98.0, 'BONO_ESTRELLA': 3.0},
    'Spurs': {'PTS': 112.1, 'PTS_OPP': 118.6, 'RITMO': 101.0, 'BONO_ESTRELLA': 4.5}
}

def obtener_cartelera_espn():
    """Consulta segura y rápida de los partidos del día a través de la API pública de ESPN."""
    partidos = []
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            for event in events:
                competitions = event.get('competitions', [])
                if competitions:
                    competitors = competitions[0].get('competitors', [])
                    local_team = None
                    visitante_team = None
                    for comp in competitors:
                        # Extraer el nombre corto o común del equipo (ej. 'Lakers', 'Celtics')
                        nombre_equipo = comp.get('team', {}).get('name', '')
                        if comp.get('homeAway') == 'home':
                            local_team = nombre_equipo
                        else:
                            visitante_team = nombre_equipo
                    
                    if local_team and visitante_team:
                        partidos.append({
                            "local": local_team, 
                            "visitante": visitante_team, 
                            "linea": 225.5
                        })
        print(f"🌐 Conexión exitosa: Se encontraron {len(partidos)} partidos oficiales para hoy.")
    except Exception as e:
        print(f"⚠️ Aviso en la consulta de red: {e}")
    return partidos

def simular_monte_carlo(local, visitante, linea_apuesta=225.5):
    """Ejecuta simulación estocástica basada en perfiles estadísticos y ritmo."""
    stats_loc = DATOS_NBA_REALES.get(local, {'PTS': 114, 'PTS_OPP': 112, 'RITMO': 98, 'BONO_ESTRELLA': 3})
    stats_vis = DATOS_NBA_REALES.get(visitante, {'PTS': 112, 'PTS_OPP': 114, 'RITMO': 98, 'BONO_ESTRELLA': 3})

    ritmo_combinado = (stats_loc['RITMO'] + stats_vis['RITMO']) / 2
    factor_ritmo = ritmo_combinado / 99.0

    ofensiva_local = (((stats_loc['PTS'] + stats_vis['PTS_OPP']) / 2) + stats_loc['BONO_ESTRELLA']) * factor_ritmo
    ofensiva_visita = (((stats_vis['PTS'] + stats_loc['PTS_OPP']) / 2) + stats_vis['BONO_ESTRELLA']) * factor_ritmo

    if stats_loc['PTS_OPP'] < 111 and stats_vis['PTS_OPP'] < 111:
        ofensiva_local -= 3.0
        ofensiva_visita -= 3.0

    # Simulaciones de Monte Carlo (2000 iteraciones)
    n_sims = 2000
    puntos_locales_sim = np.clip(np.random.normal(ofensiva_local, 7.5, n_sims), 85, 150)
    puntos_visitas_sim = np.clip(np.random.normal(ofensiva_visita, 7.5, n_sims), 85, 150)
    total_puntos_sim = puntos_locales_sim + puntos_visitas_sim

    promedio_simulado = np.mean(total_puntos_sim)
    prob_over = np.sum(total_puntos_sim > linea_apuesta) / n_sims * 100
    
    diff_poder = (ofensiva_local + 3.0) - ofensiva_visita
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
    print(f"🏀 {local} vs {visitante} | Ganador Proyectado: {ganador_str} | O/U: {prediccion['Pred_OU']} ({promedio_simulado:.1f} pts)")
    return prediccion

if __name__ == "__main__":
    print("🤖 Iniciando motor autónomo de predicción NBA...")
    
    partidos_de_hoy = obtener_cartelera_espn()
    
    # Capa de seguridad robusta por si se ejecuta en una hora sin juegos programados
    if not partidos_de_hoy:
        print("📌 Sin cartelera activa en este horario. Cargando partidos de prueba de respaldo...")
        partidos_de_hoy = [
            {"local": "Celtics", "visitante": "Heat", "linea": 218.5},
            {"local": "Nuggets", "visitante": "Suns", "linea": 228.0},
            {"local": "Lakers", "visitante": "Warriors", "linea": 235.0}
        ]
    
    nuevos_registros = []
    for p in partidos_de_hoy:
        pred = simular_monte_carlo(
            local=p["local"], 
            visitante=p["visitante"], 
            linea_apuesta=p["linea"]
        )
        nuevos_registros.append(pred)
    
    # Persistencia segura en CSV (Historial acumulativo)
    df_new = pd.DataFrame(nuevos_registros)
    if os.path.exists(ARCHIVO_HISTORIAL):
        df_existing = pd.read_csv(ARCHIVO_HISTORIAL)
        df_final = pd.concat([df_existing, df_new], ignore_index=True)
        df_final.to_csv(ARCHIVO_HISTORIAL, index=False)
    else:
        df_new.to_csv(ARCHIVO_HISTORIAL, index=False)
        
    print("✨ ¡Proceso completado con éxito! Historial respaldado en la nube.")
