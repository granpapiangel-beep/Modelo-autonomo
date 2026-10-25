import pandas as pd
import numpy as np
import os
from datetime import datetime
from nba_api.live.nba.endpoints import scoreboard

ARCHIVO_HISTORIAL = 'historial_evaluaciones_nba.csv'

# Base de datos de rendimiento, ritmo y estrellas de los 30 equipos
datos_nba_reales = {
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

def obtener_partidos_en_vivo_nba():
    """Extrae automáticamente la cartelera oficial del día usando la API de la NBA."""
    partidos = []
    try:
        board = scoreboard.ScoreBoard()
        games = board.get_games()
        for game in games:
            local = game['homeTeam']['teamName']
            visitante = game['awayTeam']['teamName']
            partidos.append({"local": local, "visitante": visitante, "linea": 225.5})
    except Exception as e:
        print(f"⚠️ Nota al conectar con el calendario oficial: {e}")
    return partidos

def generar_prediccion_partido(local, visitante, linea_apuesta=220.5):
    stats_loc = datos_nba_reales.get(local, {'PTS': 114, 'PTS_OPP': 112, 'RITMO': 98, 'BONO_ESTRELLA': 3})
    stats_vis = datos_nba_reales.get(visitante, {'PTS': 112, 'PTS_OPP': 114, 'RITMO': 98, 'BONO_ESTRELLA': 3})

    ritmo_combinado = (stats_loc['RITMO'] + stats_vis['RITMO']) / 2
    factor_ritmo = ritmo_combinado / 99.0

    ofensiva_local = (((stats_loc['PTS'] + stats_vis['PTS_OPP']) / 2) + stats_loc['BONO_ESTRELLA']) * factor_ritmo
    ofensiva_visita = (((stats_vis['PTS'] + stats_loc['PTS_OPP']) / 2) + stats_vis['BONO_ESTRELLA']) * factor_ritmo

    if stats_loc['PTS_OPP'] < 111 and stats_vis['PTS_OPP'] < 111:
        ofensiva_local -= 3.0
        ofensiva_visita -= 3.0

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
    
    print(f"🏀 [Automático] {local} vs {visitante} | Ganador Local: {prediccion['Pred_Ganador_Local']} | O/U: {prediccion['Pred_OU']} ({promedio_simulado:.1f} pts)")
    return prediccion

if __name__ == "__main__":
    print("🤖 Bot autónomo consultando la cartelera oficial de la NBA en tiempo real...")
    
    partidos_de_hoy = obtener_partidos_en_vivo_nba()
    
    # Respaldo de seguridad inteligente por si la consulta se realiza en un horario sin partidos programados
    if not partidos_de_hoy:
        print("📌 Sin partidos activos en este preciso instante. Cargando cartelera base de referencia...")
        partidos_de_hoy = [
            {"local": "Lakers", "visitante": "Warriors", "linea": 232.5},
            {"local": "Celtics", "visitante": "Knicks", "linea": 220.5},
            {"local": "Bucks", "visitante": "Nuggets", "linea": 226.0}
        ]
    
    nuevos_registros = []
    for p in partidos_de_hoy:
        pred = generar_prediccion_partido(
            local=p["local"], 
            visitante=p["visitante"], 
            linea_apuesta=p["linea"]
        )
        nuevos_registros.append(pred)
    
    df_new = pd.DataFrame(nuevos_registros)
    if os.path.exists(ARCHIVO_HISTORIAL):
        df_existing = pd.read_csv(ARCHIVO_HISTORIAL)
        df_final = pd.concat([df_existing, df_new], ignore_index=True)
        df_final.to_csv(ARCHIVO_HISTORIAL, index=False)
    else:
        df_new.to_csv(ARCHIVO_HISTORIAL, index=False)
        
    print("✨ ¡Proceso autónomo completado con éxito!")
