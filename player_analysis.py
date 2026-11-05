import os
import pandas as pd
import unicodedata
import numpy as np

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
        df_titulares = pd.read_csv(csv_filename, encoding='latin1')
    except Exception:
        return [("Error leyendo CSV", "15.5 pts", "Error crítico", "ROJO")]
        
    # --- BLINDAJE TOTAL DE COLUMNAS ---
    df_titulares.columns = [str(col).strip() for col in df_titulares.columns]
    
    col_equipo = None
    for col in df_titulares.columns:
        if col.lower() == 'equipo':
            col_equipo = col
            break
            
    if not col_equipo:
        col_equipo = df_titulares.columns[0] # Usar la primera columna por defecto si no encuentra el nombre
    # ------------------------------------
        
    mapeo_equipos = {
        "boston celtics": "boston celtics", "celtics": "boston celtics",
        "brooklyn nets": "brooklyn nets", "nets": "brooklyn nets",
        "new york knicks": "new york knicks", "knicks": "new york knicks",
        "philadelphia 76ers": "philadelphia 76ers", "76ers": "philadelphia 76ers", "sixers": "philadelphia 76ers",
        "toronto raptors": "toronto raptors", "raptors": "toronto raptors",
        "chicago bulls": "chicago bulls", "bulls": "chicago bulls",
        "cleveland cavaliers": "cleveland cavaliers", "cavaliers": "cleveland cavaliers", "cavs": "cleveland cavaliers",
        "detroit pistons": "detroit pistons", "pistons": "detroit pistons",
        "indiana pacers": "indiana pacers", "pacers": "indiana pacers",
        "milwaukee bucks": "milwaukee bucks", "bucks": "milwaukee bucks",
        "atlanta hawks": "atlanta hawks", "hawks": "atlanta hawks",
        "charlotte hornets": "charlotte hornets", "hornets": "charlotte hornets",
        "miami heat": "miami heat", "heat": "miami heat",
        "orlando magic": "orlando magic", "magic": "orlando magic",
        "washington wizards": "washington wizards", "wizards": "washington wizards",
        "denver nuggets": "denver nuggets", "nuggets": "denver nuggets",
        "minnesota timberwolves": "minnesota timberwolves", "timberwolves": "minnesota timberwolves", "wolves": "minnesota timberwolves",
        "oklahoma city thunder": "oklahoma city thunder", "thunder": "oklahoma city thunder",
        "portland trail blazers": "portland trail blazers", "trail blazers": "portland trail blazers", "blazers": "portland trail blazers",
        "utah jazz": "utah jazz", "jazz": "utah jazz",
        "golden state warriors": "golden state warriors", "warriors": "golden state warriors",
        "los angeles clippers": "los angeles clippers", "la clippers": "los angeles clippers", "clippers": "los angeles clippers",
        "los angeles lakers": "los angeles lakers", "la lakers": "los angeles lakers", "lakers": "los angeles lakers",
        "phoenix suns": "phoenix suns", "suns": "phoenix suns",
        "sacramento kings": "sacramento kings", "kings": "sacramento kings",
        "dallas mavericks": "dallas mavericks", "mavericks": "dallas mavericks", "mavs": "dallas mavericks",
        "houston rockets": "houston rockets", "rockets": "houston rockets",
        "memphis grizzlies": "memphis grizzlies", "grizzlies": "memphis grizzlies",
        "new orleans pelicans": "new orleans pelicans", "pelicans": "new orleans pelicans",
        "san antonio spurs": "san antonio spurs", "spurs": "san antonio spurs"
    }
    
    eq_norm = normalizar_texto(nombre_equipo)
    eq_busqueda = mapeo_equipos.get(eq_norm, eq_norm)
    
    df_titulares['Equipo_Clean'] = df_titulares[col_equipo].apply(normalizar_texto)
    df_equipo = df_titulares[df_titulares['Equipo_Clean'] == eq_busqueda]
    
    if df_equipo.empty:
        df_equipo = df_titulares[df_titulares['Equipo_Clean'].str.contains(eq_busqueda, na=False)]
        
    if df_equipo.empty:
        return [(nombre_equipo, "15.5 pts", "Sin registros en base", "AMARILLO")]
        
    columnas_fechas = [col for col in df_titulares.columns if col not in [col_equipo, 'Posicion', 'Jugador', 'Equipo_Clean']]
    
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
