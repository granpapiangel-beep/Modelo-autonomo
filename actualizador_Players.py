import os
import time
import pandas as pd
import requests


def actualizar_historial_partidos():
  # Nombre exacto del archivo CSV principal de tu repositorio
  archivo_csv = "Titulares_NBA_Oficiales_30_Equipos(Puntajes Diarios).csv"

  if not os.path.exists(archivo_csv):
    print(f"⚠️ Error: No se encontró el archivo {archivo_csv} en el repositorio.")
    return

  df = pd.read_csv(archivo_csv)

  # Configuración de acceso a RapidAPI
  url = "https://nba-api-free-data.p.rapidapi.com/endpoint_estadisticas"  # Reemplaza con el endpoint de estadísticas/jugadores que necesites
  headers = {
      "X-RapidAPI-Key": "969c085cb7msh6926a29e619d670p18371cjsnc8c5c962373a",
      "X-RapidAPI-Host": "nba-api-free-data.p.rapidapi.com",
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
  }

  print("Iniciando revisión y llenado de celdas con 'SD'...")

  # Identificar las columnas de fechas (asumiendo que las primeras 3 son Equipo, Posicion, Jugador)
  columnas_fechas = df.columns[3:]

  actualizaciones_realizadas = 0

  # Recorrer cada fila (jugador) del DataFrame
  for index, row in df.iterrows():
    jugador = row["Jugador"]
    equipo = row["Equipo"]

    # Revisar cada columna de fecha para este jugador
    for fecha_col in columnas_fechas:
      # Si la celda está vacía o dice "SD", procedemos a buscar el dato
      if str(row[fecha_col]).strip() == "SD":
        print(f"Buscando puntaje para {jugador} ({equipo}) en la fecha {fecha_col}...")

        try:
          # Parámetros de consulta para la API (puedes ajustarlos según lo que pida el endpoint)
          params = {"player": jugador, "date": fecha_col}

          response = requests.get(url, headers=headers, params=params)

          if response.status_code == 200:
            data = response.json()

            # --- ZONA DE EXTRACCIÓN ---
            # Aquí extraes el puntaje real de la respuesta JSON de la API.
            # Ejemplo ficticio: puntaje_real = data['response'][0]['points']
            puntaje_real = (
                "25 pts"  # Reemplaza esto con el valor extraído del JSON
            )

            # Asignar el valor real al DataFrame
            df.loc[index, fecha_col] = puntaje_real
            actualizaciones_realizadas += 1
          else:
            print(
                f"⚠️ Error en la API para {jugador}: Código"
                f" {response.status_code}"
            )

          # Pausa obligatoria de 2 segundos para cuidar las peticiones y evitar bloqueos en la nube
          time.sleep(2)

        except Exception as e:
          print(f"⚠️ Excepción al consultar la API para {jugador}: {e}")

  # Guardar los cambios masivos de vuelta en el archivo CSV oficial
  df.to_csv(archivo_csv, index=False)
  print(
      f"¡Proceso finalizado! Se actualizaron {actualizaciones_realizadas}"
      " registros con éxito en el CSV."
  )


if __name__ == "__main__":
  actualizar_historial_partidos()
