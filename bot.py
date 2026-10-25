import pandas as pd
import numpy as np
import os
import requests
from datetime import datetime

ARCHIVO_HISTORIAL = 'historial_evaluaciones_nba.csv'

# Catálogo completo de los 30 equipos de la NBA (Este y Oeste)
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

def obtener_partidos_hoy_api():
    """Consulta partidos de la jornada usando la API pública."""
    hoy = datetime.utcnow().strftime('%Y-%m-%d')
    url = f"https://api.balldontlie.io/v1/games?dates[]={hoy}"
    headers = {"Authorization": os.environ.get("BALLDONTLIE_API_KEY", "")}
    
    partidos = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json().get('data', [])
            for juego in data:
                local = juego['home_team']['name']
                visitante = juego['visitor_team']['name']
                partidos.append({"local": local, "visitante": visitante, "linea": 225.5})
    except Exception as e:
        print(f"⚠️ Aviso de API: {e}")
    return partidos

def generar_prediccion_partido(local, visitante, linea_apuesta=220.5):
    local_key = next((k for k in datos_nba_reales.keys() if k.lower() in local.lower()), 'Celtics')
    visita_key = next((k for k in datos_nba_reales.keys() if k.lower() in visitante.lower()), 'Knicks')

    stats_loc = datos_nba_reales[local_key]
    stats_vis = datos_nba_reales[visita_key]

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
        'Local': local_key,
        'Visitante': visita_key,
        'Pred_Ganador_Local': bool(prob_local >= 0.5),
        'Line_Apuesta': linea_apuesta,
        'Pred_OU': "OVER" if prob_over > 50 else "UNDER",
        'Promedio_Simulado': round(promedio_simulado, 1)
    }
    
    print(f"🏀 {local_key} vs {visita_key} | Ganador Local: {prediccion['Pred_Ganador_Local']} | O/U: {prediccion['Pred_OU']} ({promedio_simulado:.1f} pts)")
    return prediccion

if __name__ == "__main__":
    print("🤖 Bot autónomo analizando la jornada de la NBA...")
    
    partidos_hoy = obtener_partidos_hoy_api()
    
    # Respaldo dinámico con múltiples enfrentamientos del Este y Oeste si la API no responde o no hay juegos en vivo
    if not partidos_hoy:
        print("📌 Ejecutando cartelera representativa de ambas conferencias...")
        partidos_hoy = [
            {"local": "Celtics", "visitante": "Knicks", "linea": 220.5},
            {"local": "Bucks", "visitante": "Heat", "linea": 224.0},
            {"local": "Cavaliers", "visitante": "Pacers", "linea": 232.5},
            {"local": "Thunder", "visitante": "Nuggets", "linea": 231.0},
            {"local": "Lakers", "visitante": "Suns", "linea": 234.5},
            {"local": "Warriors", "visitante": "Mavericks", "linea": 238.0},
            {"local": "Timberwolves", "visitante": "Clippers", "linea": 218.5}
        ]
    
    nuevos_registros = []
    for p in partidos_hoy:
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
        
    print("✨ ¡Predicciones de la jornada completadas y guardadas en la nube!")
