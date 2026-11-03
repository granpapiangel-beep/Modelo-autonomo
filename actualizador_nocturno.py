import datetime
import os
import pandas as pd

def actualizar_historial_partidos():
    # Nombre exacto del archivo CSV principal de tu repositorio
    archivo_csv = "Titulares_NBA_Oficiales_30_Equipos(Puntajes Diarios).csv"
    
    # Obtiene la fecha de ayer (o la fecha que corresponda al cierre de la jornada nocturna)
    hoy_dt = datetime.date.today() - datetime.timedelta(days=1)
    
    # Mapeo de meses en español para que coincida con el formato de tus columnas
    meses = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 
        5: "mayo", 6: "junio", 7: "julio", 8: "agosto", 
        9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
    }
    
    dia = hoy_dt.day
    mes_str = meses[hoy_dt.month]
    
    # Construye el nombre de la columna (ej. "2 de noviembre" o puedes ajustarlo a "2 nov")
    columna_fecha = f"{dia} de {mes_str}"
    
    print(f"Iniciando actualización nocturna para la columna de fecha: {columna_fecha}")
    
    if not os.path.exists(archivo_csv):
        print(f"⚠️ Error: No se encontró el archivo {archivo_csv} en el repositorio.")
        return
        
    df = pd.read_csv(archivo_csv)
    
    # Si la columna del día actual todavía no existe en el CSV, la creamos inicializada en "SD" (Sin Datos)
    if columna_fecha not in df.columns:
        df[columna_fecha] = "SD"
        print(f"Se ha creado la nueva columna '{columna_fecha}' en el registro.")
    
    # -------------------------------------------------------------
    # ZONA DE ACTUALIZACIÓN DE PUNTOS REALES:
    # Aquí es donde tu script nocturno puede consultar una API deportiva 
    # o actualizar los puntos de los jugadores que jugaron anoche.
    # Ejemplo:
    # df.loc[df['Jugador'] == 'Tyrese Maxey', columna_fecha] = '31 pts'
    # -------------------------------------------------------------

    # Guarda los cambios de vuelta en el archivo CSV oficial
    df.to_csv(archivo_csv, index=False)
    print("¡Base de datos de puntajes diarios actualizada con éxito a las 3:00 AM!")

if __name__ == "__main__":
    actualizar_historial_partidos()
