import pandas as pd
import numpy as np
import os
import requests
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN Y RUTAS DE ARCHIVOS
# ==========================================
ARCHIVO_HISTORIAL = 'historial_evaluaciones_nba.csv'

# Catálogo completo de equipos y estrellas con sus factores de impacto
datos_nba_reales = {
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

# ==========================================
# 2. MÓDULO DE PREDICCIÓN (Ejecución 10:00 AM)
# ==========================================
def generar_prediccion_partido(local, visitante, linea_apuesta=220.5, estrella_local=True, estrella_visita=True):
    stats_loc = datos_nba_reales.get(local, {'PTS': 114, 'PTS_OPP': 112, 'RITMO': 98, 'BONO_ESTRELLA': 3})
    stats_vis = datos_nba_reales.get(visitante, {'PTS': 112, 'PTS_OPP': 114, 'RITMO': 98, 'BONO_ESTRELLA': 3})

    bono_loc = stats_loc['BONO_ESTRELLA'] if estrella_local else 0.0
    bono_vis = stats_vis['BONO_ESTRELLA'] if estrella_visita else 0.0

    ritmo_combinado = (stats_loc['RITMO'] + stats_vis['RITMO']) / 2
    factor_ritmo = ritmo_combinado / 99.0

    ofensiva_local = (((stats_loc['PTS'] + stats_vis['PTS_OPP']) / 2) + bono_loc) * factor_ritmo
    ofensiva_visita = (((stats_vis['PTS'] + stats_loc['PTS_OPP']) / 2) + bono_vis) * factor_ritmo

    if stats_loc['PTS_OPP'] < 111 and stats_vis['PTS_OPP'] < 111:
        ofensiva_local -= 3.0
        ofensiva_visita -= 3.0

    # Simulación Monte Carlo
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
        'Promedio_Simulado': promedio_simulado
    }
    
    print(f"🔮 Predicción generada para {local} vs {visitante}: Ganador Local={prediccion['Pred_Ganador_Local']} | O/U={prediccion['Pred_OU']}")
    return prediccion

# ==========================================
# 3. MÓDULO DE VERIFICACIÓN Y APRENDIZAJE (Ejecución 3:00 AM)
# ==========================================
def evaluar_resultados_ayer(partidos_ayer_reales):
    """
    partidos_ayer_reales es una lista de diccionarios con los resultados oficiales 
    obtenidos desde una API externa de deportes (ej. Balldontlie API).
    """
    if not os.path.exists(ARCHIVO_HISTORIAL):
        print("⚠️ No hay historial previo para evaluar.")
        return

    df_hist = pd.read_csv(ARCHIVO_HISTORIAL)
    
    for real in partidos_ayer_reales:
        local = real['Local']
        visitante = real['Visitante']
        pts_l = real['Pts_Real_Local']
        pts_v = real['Pts_Real_Visitante']
        total_real = pts_l + pts_v

        # Buscar si el sistema tenía registrada una predicción para este juego
        match = df_hist[(df_hist['Local'] == local) & (df_hist['Visitante'] == visitante) & (df_hist['Total_Real'].isna())]
        
        if not match.empty:
            idx = match.index[0]
            ganador_real_es_local = pts_l > pts_v
            acerto_ganador = ganador_real_es_local == df_hist.loc[idx, 'Pred_Ganador_Local']
            
            linea = df_hist.loc[idx, 'Line_Apuesta']
            ou_real = "OVER" if total_real > linea else "UNDER"
            acerto_ou = ou_real == df_hist.loc[idx, 'Pred_OU']

            # Actualizar base de datos con la realidad (Auto-aprendizaje)
            df_hist.loc[idx, 'Total_Real'] = total_real
            df_hist.loc[idx, 'Acerto_Ganador'] = "ACIERTO" if acerto_ganador else "FALLO"
            df_hist.loc[idx, 'Acerto_Lineas'] = "ACIERTO" if acerto_ou else "FALLO"
            
            print(f"📊 Evaluado {local} vs {visitante}: Ganador [{'ACIERTO' if acerto_ganador else 'FALLO'}] | O/U [{'ACIERTO' if acerto_ou else 'FALLO'}]")

    df_hist.to_csv(ARCHIVO_HISTORIAL, index=False)
    print("💾 Historial actualizado y guardado de forma autónoma.")

# ==========================================
# 4. PUNTO DE ENTRADA PRINCIPAL DEL SCRIPT
# ==========================================
if __name__ == "__main__":
    print("🤖 Bot de la NBA ejecutándose en la nube...")
    
    # Aquí puedes programar llamadas automáticas a una API de deportes 
    # para jalar los partidos del día o los resultados de la jornada pasada.
    
    # Ejemplo de prueba manual del flujo:
    pred = generar_prediccion_partido("Celtics", "Knicks", 225.5)
    
    # Guardar simulación pendiente de calificar
    df_new = pd.DataFrame([pred])
    if os.path.exists(ARCHIVO_HISTORIAL):
        df_existing = pd.read_csv(ARCHIVO_HISTORIAL)
        pd.concat([df_existing, df_new], ignore_index=True).to_csv(ARCHIVO_HISTORIAL, index=False)
    else:
        df_new.to_csv(ARCHIVO_HISTORIAL, index=False)
