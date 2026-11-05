from datetime import datetime
import os
import numpy as np
import pandas as pd
import unicodedata

def normalizar_texto(texto):
    if not isinstance(texto, str):
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                        if unicodedata.category(c) != 'Mn').lower().strip()

def obtener_patron_titulares(nombre_equipo):
    csv_filename = "Titulares_NBA_Oficiales_30_Equipos(Puntajes Diarios).csv"
    
    if not os.path.exists(csv_filename):
        return [("Jugador predeterminado", "15.5 pts", "Sin datos CSV", "AMARILLO")]
        
    try:
        df_titulares = pd.read_csv(csv_filename, encoding='utf-8-sig')
    except Exception:
        return [("Error leyendo CSV", "15.5 pts", "Error crítico", "ROJO")]
        
    # --- ACCESO DIRECTO POR POSICIÓN (IGNORA NOMBRES DE COLUMNAS) ---
    # Columna 0 = Equipo, Columna 1 = Posición, Columna 2 = Jugador
    col_equipo = df_titulares.columns[0]
    col_posicion = df_titulares.columns[1] if len(df_titulares.columns) > 1 else 'Posicion'
    col_jugador = df_titulares.columns[2] if len(df_titulares.columns) > 2 else 'Jugador'
    
    eq_norm = normalizar_texto(nombre_equipo)
    df_titulares['Equipo_Clean'] = df_titulares[col_equipo].apply(normalizar_texto)
    
    # Búsqueda flexible de coincidencias
    df_equipo = df_titulares[df_titulares['Equipo_Clean'].str.contains(eq_norm, na=False)]
    
    if df_equipo.empty and " " in eq_norm:
        ultima_palabra = eq_norm.split()[-1]
        df_equipo = df_titulares[df_titulares['Equipo_Clean'].str.contains(ultima_palabra, na=False)]
        
    if df_equipo.empty:
        return [(f"Plantilla ({nombre_equipo})", "15.5 pts", "Sin registros exactos en base", "AMARILLO")]
        
    columnas_fechas = df_titulares.columns[3:-1] # Todas las fechas a partir de la columna 3
    
    resultado = []
    for _, row in df_equipo.iterrows():
        nombre_jugador = str(row.get(col_jugador, 'Jugador Desconocido')).replace("'", "").replace('"', "")
        puntos_lista = []
        for col in columnas_fechas:
            val = str(row.get(col, ""))
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
        
        if promedio >= 22.0 and desviacion < 5.0:
            patron = "Élite Constante (Cumplidor)"
            semaforo = "VERDE"
        elif promedio >= 15.0 and desviacion < 7.0:
            patron = "Estable / Confiable"
            semaforo = "VERDE"
        elif desviacion >= 7.0 or (max(puntos_lista) - min(puntos_lista)) > 14:
            patron = "Alto Riesgo / Volátil e Irregular"
            semaforo = "ROJO"
        else:
            patron = "Bajo Perfil / Rango Estrecho"
            semaforo = "AMARILLO"
            
        resultado.append((nombre_jugador, f"{linea_prop} pts", patron, semaforo))
        
    return resultado
