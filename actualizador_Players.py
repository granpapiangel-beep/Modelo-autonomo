import datetime
import os
import pandas as pd
import requests
import time


def actualizar_historial_partidos():
  # Nombre exacto del archivo CSV principal de tu repositorio
  archivo_csv = "Titulares_NBA_Oficiales_30_Equipos(Puntajes Diarios).csv"

  # Obtiene la fecha de ayer (o la fecha que corresponda al cierre de la jornada nocturna)
  hoy_dt = datetime.date.today() - datetime.timedelta(days=1)

  # Mapeo de meses en español para que coincida con el formato de tus columnas
  meses = {
      1: "enero",
      2: "febrero",
      3: "marzo",
      4: "abril",
      5: "mayo",
      6: "junio",
      7: "julio",
      8: "agosto",
      9: "septiembre",
      10: "octubre",
      11: "noviembre",
      12: "diciembre",
  }

  dia = hoy_dt.day
  mes_str = meses[hoy_dt.month]

  # Construye el nombre de la columna (ej. "2 de noviembre")
  columna_fecha = f"{dia} de {mes_str}"

  print(
      f"Iniciando actualización nocturna para la columna de fecha:"
      f" {columna_fecha}"
  )

  if not os.path.exists(archivo_csv):
    print(f"⚠️ Error: No se encontró el archivo {archivo_csv} en el repositorio.")
    return

  df = pd.read_csv(archivo_csv)

  # Si la columna del día actual todavía no existe en el CSV, la creamos inicializada en "SD" (Sin Datos)
  if columna_fecha not in df.columns:
    df[columna_fecha] = "SD"
    print(f"Se ha creado la nueva columna '{columna_fecha}' en el registro.")

  # -------------------------------------------------------------
  # ZONA DE ACTUALIZACIÓN DE PUNTOS REALES CON TU CLAVE DE RAPIDAPI:
  # -------------------------------------------------------------
  url = "https://nba-api-free-data.p.rapidapi.com/Team/SouthwestTeamList"  # Ejemplo de endpoint que muestra tu captura
  headers = {
      "X-RapidAPI-Key": "969c085cb7msh6926a29e619d670p18371cjsnc8c5c962373a",
      "X-RapidAPI-Host": "nba-api-free-data.p.rapidapi.com",
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
  }

  try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      print("¡Conexión exitosa con la API de la NBA!")
      # Aquí puedes procesar la respuesta JSON de la API para mapearla a tu DataFrame
      # data = response.json()
    else:
      print(f"⚠️ La API respondió con código de estado: {response.status_code}")

    time.sleep(2)  # Pausa preventiva anti-bloqueo

  except Exception as e:
    print(f"⚠️ Error al conectar con RapidAPI: {e}")

  # Guarda los cambios de vuelta en el archivo CSV oficial
  df.to_csv(archivo_csv, index=False)
  print(
      "¡Base de datos de puntajes diarios actualizada con éxito a las 3:00 AM!"
  )


if __name__ == "__main__":
  actualizar_historial_partidos()
