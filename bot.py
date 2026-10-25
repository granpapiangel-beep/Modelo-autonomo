import pandas as pd
import numpy as np
import os
from datetime import datetime

ARCHIVO_HISTORIAL = 'historial_evaluaciones_nba.csv'

# Catálogo completo de los 30 equipos de la NBA
datos_nba_reales = {
    # --- CONFERENCIA ESTE ---
    'Celtics': {'PTS': 120.6, 'PTS_OPP': 109.2, 'RITMO': 98.5, 'ESTRELLA': 'Jayson Tatum', 'BONO_ESTRELLA': 4.5},
    'Knicks': {'PTS': 112.8, 'PTS_OPP': 110.1, 'RITMO': 96.0, 'ESTRELLA': 'Jalen Brunson', 'BONO_ESTRELLA': 4.0},
    'Bucks': {'PTS': 119.5, 'PTS_OPP': 116.4, 'RITMO': 101.0, 'ESTRELLA': 'Giannis Antetokounmpo', 'BONO_ESTRELLA': 5.0},
    '76ers': {'PTS': 114.6, 'PTS_OPP': 111.8, 'RITMO': 97.5, 'ESTRELLA': 'Joel Embiid', 'BONO_ESTRELLA': 5.5},
    'Cavaliers': {'PTS': 112.6, 'PTS_OPP': 110.3, 'RITMO': 96.5, 'ESTRELLA': 'Donovan Mitchell', 'BONO_ESTRELLA': 4.5},
    'Magic': {'PTS': 110.5, 'PTS_OPP': 108.4, 'RITMO': 97.0, 'ESTRELLA': 'Paolo Banchero', 'BONO_ESTRELLA': 4.0},
    'Pacers': {'PTS': 123.3, 'PTS_OPP': 120.2, 'RITMO': 103.0, 'ESTRELLA': 'Tyrese Haliburton', 'BONO_ESTRELLA': 4.5},
    'Heat': {'PTS': 110.1, 'PTS_OPP': 108.4, 'RITMO': 95.0, 'ESTRELLA': 'Jimmy Butler', 'BONO_ESTRELLA': 3.5},
    'Bulls': {'PTS': 112.3, 'PTS_OPP': 113.7, 'RITMO': 99.0, 'ESTRELLA': 'Zach LaVine', 'BONO_ESTRELLA': 3.0},
    'Hawks': {'PTS': 118.3, 'PTS_OPP': 120.0, 'RITMO': 102.5, 'ESTRELLA': 'Trae Young', 'BONO_ESTRELLA': 4.0},
    'Nets': {'PTS': 110.4, 'PTS_OPP': 113.5, 'RITMO': 97.0, 'ESTRELLA': 'Mikal Bridges', 'BONO_ESTRELLA': 3.0},
    'Raptors': {'PTS': 112.4, 'PTS_OPP': 118.8, 'RITMO': 99.0, 'ESTRELLA': 'Scottie Barnes', 'BONO_ESTRELLA': 3.5},
    'Hornets': {'PTS': 106.6, 'PTS_OPP': 116.8, 'RITMO': 98.0, 'ESTRELLA': 'LaMelo Ball', 'BONO_ESTRELLA': 3.5},
    'Wizards': {'PTS': 114.5, 'PTS_OPP': 123.0, 'RITMO': 102.0, 'ESTRELLA': 'Kyle Kuzma', 'BONO_ESTRELLA': 2.5},
    'Pistons': {'PTS': 110.0, 'PTS_OPP': 119.0, 'RITMO': 99.5, 'ESTRELLA': 'Cade Cunningham', 'BONO_ESTRELLA': 3.5},

    # --- CONFERENCIA OESTE ---
    'Thunder': {'PTS': 120.1, 'PTS_OPP': 112.7, 'RITMO': 101.0, 'ESTRELLA': 'Shai Gilgeous-Alexander', 'BONO_ESTRELLA': 5.5},
    'Nuggets': {'PTS': 114.9, 'PTS_OPP': 109.6, 'RITMO': 96.5, 'ESTRELLA': 'Nikola Jokic', 'BONO_ESTRELLA': 6.0},
    'Timberwolves': {'PTS': 113.0, 'PTS_OPP': 106.5, 'RITMO': 97.0, 'ESTRELLA': 'Anthony Edwards', 'BONO_ESTRELLA': 4.5},
    'Clippers': {'PTS': 115.6, 'PTS_OPP': 112.3, 'RITMO': 97.5, 'ESTRELLA': 'Kawhi Leonard', 'BONO_ESTRELLA': 4.5},
    'Mavericks': {'PTS': 117.9, 'PTS_OPP': 115.6, 'RITMO': 98.5, 'ESTRELLA': 'Luka Doncic', 'BONO_ESTRELLA': 6.0},
    'Suns': {'PTS': 116.2, 'PTS_OPP': 113.2, 'RITMO': 98.0, 'ESTRELLA': 'Kevin Durant', 'BONO_ESTRELLA': 5.0},
    'Pelicans': {'PTS': 115.1, 'PTS_OPP': 110.7, 'RITMO': 98.0, 'ESTRELLA': 'Zion Williamson', 'BONO_ESTRELLA': 4.0},
    'Lakers': {'PTS': 118.0, 'PTS_OPP': 117.4, 'RITMO': 101.5, 'ESTRELLA': 'LeBron James', 'BONO_ESTRELLA': 4.5},
    'Kings': {'PTS': 116.6, 'PTS_OPP': 114.8, 'RITMO': 100.5, 'ESTRELLA': 'DeAaron Fox', 'BONO_ESTRELLA': 4.0},
    'Warriors': {'PTS': 117.6, 'PTS_OPP': 115.5, 'RITMO': 100.0, 'ESTRELLA': 'Stephen Curry', 'BONO_ESTRELLA': 5.0},
    'Rockets': {'PTS': 114.3, 'PTS_OPP': 113.1, 'RITMO': 99.0, 'ESTRELLA': 'Alperen Sengun', 'BONO_ESTRELLA': 3.5},
    'Jazz': {'PTS': 115.7, 'PTS_OPP': 120.5, 'RITMO': 100.0, 'ESTRELLA': 'Lauri Markkanen', 'BONO_ESTRELLA': 3.5},
    'Grizzlies': {'PTS': 105.8, 'PTS_OPP': 112.8, 'RITMO': 99.0, 'ESTRELLA': 'Ja Morant', 'BONO_ESTRELLA': 4.5},
    'Blazers': {'PTS': 106.4, 'PTS_OPP': 115.4, 'RITMO': 98.0, 'ESTRELLA': 'Anfernee Simons', 'BONO_ESTRELLA': 3.0},
    'Spurs': {'PTS': 112.1, 'PTS_OPP': 118.6, 'RITMO': 101.0, 'ESTRELLA': 'Victor Wembanyama', 'BONO_ESTRELLA': 4.5}
}

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
    
    print(f"🏀 {local} vs {visitante} | Ganador Local: {prediccion['Pred_Ganador_Local']} | O/U: {prediccion['Pred_OU']} ({promedio_simulado:.1f} pts)")
    return prediccion

if __name__ == "__main__":
    print("🤖 Bot autónomo analizando la cartelera real del día...")
    
    # CARTELERA ACTUALIZADA DE HOY (Basada en tu imagen de la aplicación)
    partidos_de_hoy = [
        {"local": "Jazz", "visitante": "Lakers", "linea": 234.5},
        {"local": "Nets", "visitante": "Pacers", "linea": 230.0},
        {"local": "Knicks", "visitante": "Magic", "linea": 218.5},
        {"local": "Thunder", "visitante": "Clippers", "linea": 226.5},
        {"local": "Timberwolves", "visitante": "Raptors", "linea": 222.0},
        {"local": "76ers", "visitante": "Pistons", "linea": 221.5},
        {"local": "Kings", "visitante": "Grizzlies", "linea": 231.0}
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
        
    print("✨ ¡Cartelera de hoy analizada y guardada exitosamente!")
