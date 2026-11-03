# player_analysis.py
import os
import pandas as pd
import unicodedata
import numpy as np

def normalizar_texto(texto):
    """Limpia acentos y convierte a minúsculas para una coincidencia exacta."""
    if not isinstance(texto, str):
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                   if unicodedata.category(c) != 'Mn').lower().strip()

def obtener_patron_titulares(nombre_equipo):
    """
    Analiza rigurosamente el CSV de titulares, calcula promedios móviles,
    desviación estándar y emite un semáforo analítico estricto.
    """
    csv_filename = "Titulares_NBA_Oficiales_30_Equipos(Puntajes Diarios).csv"
    if not os.path.exists(csv_filename):
        return [("Jugador predeterminado", "15.5 pts", "Sin datos CSV", "AMARILLO")]
        
    try:
        df_titulares = pd.read_csv(csv_filename)
    except Exception:
        return [("Error leyendo CSV", "15.5 pts", "Error crítico", "ROJO")]
        
    df_titulares['Equipo_Clean'] = df_titulares['Equipo'].apply(normalizar_texto)
    equipo_busq = normalizar_texto(nombre_equipo)
    
    df_equipo = df_titulares[df_titulares['Equipo_Clean'] == equipo_busq]
    
    if df_equipo.empty:
        df_equipo = df_titulares[df_titulares['Equipo_Clean'].str.contains(equipo_busq, na=False)]
        
    if df_equipo.empty:
        return [(nombre_equipo, "15.5 pts", "Sin registros", "AMARILLO")]
        
    # Identificar columnas de fechas dinámicamente
    columnas_fechas = [col for col in df_titulares.columns if col not in ['Equipo', 'Posicion', 'Jugador', 'Equipo_Clean']]
    
    resultado = []
    for _, row in df_equipo.iterrows():
        nombre_jugador = row['Jugador']
        puntos_lista = []
        for col in columnas_fechas:
            val = str(row[col])
            if "pts" in val:
                try:
                    puntos_lista.append(float(val.replace("pts", "").strip()))
                except ValueError:
                    pass
                    
        if not puntos_lista:
            resultado.append((nombre_jugador, "15.5 pts", "Sin datos recientes", "AMARILLO"))
            continue
            
        promedio = np.mean(puntos_lista)
        desviacion = np.std(puntos_lista) if len(puntos_lista) > 1 else 1.0
        linea_prop = round(promedio - 2.0, 1)
        
        # Criterios analíticos rigurosos de cumplimiento
        if promedio >= 22.0 and desviacion < 5.0:
            patron = "Élite Consistente"
            semaforo = "VERDE"
        elif promedio >= 15.0 and desviacion < 7.0:
            patron = "Estable / Confiable"
            semaforo = "VERDE"
        elif desviacion >= 7.0 or (max(puntos_lista) - min(puntos_lista)) > 14:
            patron = "Alto Riesgo / Volátil"
            semaforo = "ROJO"
        else:
            patron = "Bajo Perfil / Rango Estrecho"
            semaforo = "AMARILLO"
            
        resultado.append((nombre_jugador, f"{linea_prop} pts", patron, semaforo))
        
    return resultado
