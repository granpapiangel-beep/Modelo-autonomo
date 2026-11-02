# actualizador_autonomo.py
# Script autónomo para reescribir y actualizar el archivo JSON con los 30 equipos de la NBA
import datetime
import json

# Lista oficial de los 30 equipos de la NBA y sus estrellas principales por posición
nba_equipos_30 = {
    "Celtics": [
        ("Jayson Tatum", 27.5, "85% (Alta Carga Ofensiva)", "VERDE"),
        ("Jaylen Brown", 22.0, "80% (Estable en Transición)", "VERDE"),
        ("Derrick White", 15.5, "75% (Confiable en Triples)", "VERDE"),
        ("Jrue Holiday", 13.0, "72% (Rol Defensivo / Fijo)", "VERDE"),
        ("Kristaps Porzingis", 18.0, "68% (Depende de Triples)", "AMARILLO"),
    ],
    "Magic": [
        ("Paolo Banchero", 24.5, "82% (Eje Principal)", "VERDE"),
        ("Franz Wagner", 18.5, "75% (Ataque al Aro Seguro)", "VERDE"),
        ("Jalen Suggs", 13.5, "65% (Defensa y Transición)", "AMARILLO"),
        ("Wendell Carter Jr.", 11.5, "60% (Pintura y Rebotes)", "AMARILLO"),
        ("Cole Anthony", 10.0, "55% (Banquillo / Irregular)", "ROJO"),
    ],
    "Lakers": [
        ("Anthony Davis", 24.5, "85% (Dominio Interior)", "VERDE"),
        ("Austin Reaves", 18.0, "75% (Altos Minutos)", "VERDE"),
        ("LeBron James", 16.5, "70% (Controlador y Asistente)", "VERDE"),
        ("D'Angelo Russell", 14.5, "60% (Depende de Rachas)", "AMARILLO"),
        ("Rui Hachimura", 11.5, "65% (Cumplidor Secundario)", "VERDE"),
    ],
    "Raptors": [
        ("Scottie Barnes", 20.5, "78% (Líder Estadístico)", "VERDE"),
        ("Immanuel Quickley", 18.5, "75% (Alto Volumen)", "VERDE"),
        ("RJ Barrett", 17.0, "70% (Penetración Constante)", "VERDE"),
        ("Jakob Poeltl", 12.0, "80% (Puntos Fáciles)", "VERDE"),
        ("Gradey Dick", 11.0, "55% (Joven Volátil)", "AMARILLO"),
    ],
    "Warriors": [
        ("Stephen Curry", 26.5, "85% (Éxito Frecuente)", "VERDE"),
        ("Jonathan Kuminga", 17.5, "72% (Explosivo)", "VERDE"),
        ("Buddy Hield", 15.0, "65% (Tirador Exterior)", "AMARILLO"),
        ("Brandin Podziemski", 12.0, "68% (Aportes Múltiples)", "VERDE"),
        ("Draymond Green", 8.5, "88% (Cuota Muy Segura)", "VERDE"),
    ],
    "Clippers": [
        ("Kawhi Leonard", 23.0, "80% (Alta Confiabilidad)", "VERDE"),
        ("James Harden", 20.5, "76% (Faltas y Tiros Libres)", "VERDE"),
        ("Norman Powell", 17.0, "72% (Anotador Fijo)", "VERDE"),
        ("Ivica Zubac", 13.0, "82% (Efectividad en Zona)", "VERDE"),
        ("Derrick Jones Jr.", 9.0, "60% (Contraataques)", "AMARILLO"),
    ],
    "Cavaliers": [
        ("Donovan Mitchell", 25.5, "85% (Líder constante)", "VERDE"),
        ("Darius Garland", 20.5, "75% (Distribuidor)", "VERDE"),
        ("Evan Mobley", 17.5, "70% (Eficiente en pintura)", "VERDE"),
        ("Jarrett Allen", 14.5, "80% (Alto porcentaje)", "VERDE"),
        ("Max Strus", 11.5, "60% (Triples)", "AMARILLO"),
    ],
    "Knicks": [
        ("Jalen Brunson", 26.5, "85% (Control de ofensiva)", "VERDE"),
        ("Karl-Anthony Towns", 22.5, "80% (Puntos y rebotes)", "VERDE"),
        ("Mikal Bridges", 16.5, "70% (Volumen)", "VERDE"),
        ("OG Anunoby", 14.5, "65% (Estable)", "VERDE"),
        ("Josh Hart", 11.5, "75% (Transición)", "VERDE"),
    ],
    "Bucks": [
        ("Giannis Antetokounmpo", 30.5, "90% (Dominio absoluto)", "VERDE"),
        ("Damian Lillard", 24.5, "80% (Clutch)", "VERDE"),
        ("Khris Middleton", 15.5, "65% (Ritmo)", "AMARILLO"),
        ("Brook Lopez", 12.5, "70% (Perímetro)", "VERDE"),
        ("Bobby Portis", 11.5, "60% (Banquillo)", "AMARILLO"),
    ],
    "Suns": [
        ("Kevin Durant", 26.5, "85% (Clase mundial)", "VERDE"),
        ("Devin Booker", 25.5, "80% (Alto volumen)", "VERDE"),
        ("Bradley Beal", 17.5, "65% (Lesiones)", "AMARILLO"),
        ("Jusuf Nurkic", 11.5, "70% (Zonas)", "VERDE"),
        ("Tyus Jones", 9.5, "75% (Control)", "VERDE"),
    ],
    "Nuggets": [
        ("Nikola Jokic", 26.5, "90% (Triple-doble)", "VERDE"),
        ("Jamal Murray", 21.5, "75% (Clutch)", "VERDE"),
        ("Michael Porter Jr.", 16.5, "70% (Distancia)", "VERDE"),
        ("Aaron Gordon", 13.5, "80% (Cortador)", "VERDE"),
        ("Christian Braun", 10.5, "65% (Transiciones)", "AMARILLO"),
    ],
    "Mavericks": [
        ("Luka Doncic", 32.5, "90% (Volumen gigante)", "VERDE"),
        ("Kyrie Irving", 24.5, "85% (Mecánica)", "VERDE"),
        ("Klay Thompson", 14.5, "60% (Rachas)", "AMARILLO"),
        ("P.J. Washington", 11.5, "65% (Esquinas)", "VERDE"),
        ("Dereck Lively II", 9.5, "80% (Rebotes)", "VERDE"),
    ],
    "Thunder": [
        ("Shai Gilgeous-Alexander", 30.5, "90% (Consistencia)", "VERDE"),
        ("Chet Holmgren", 17.5, "75% (Bloqueos)", "VERDE"),
        ("Jalen Williams", 19.5, "80% (Crecimiento)", "VERDE"),
        ("Lu Dort", 10.5, "60% (Defensa)", "AMARILLO"),
        ("Alex Caruso", 9.5, "65% (Robos)", "VERDE"),
    ],
    "Timberwolves": [
        ("Anthony Edwards", 26.5, "80% (Dominante)", "VERDE"),
        ("Julius Randle", 20.5, "75% (Pintura)", "VERDE"),
        ("Rudy Gobert", 12.5, "85% (Bajo el aro)", "VERDE"),
        ("Jaden McDaniels", 11.5, "60% (Parpadeos)", "AMARILLO"),
        ("Mike Conley", 10.5, "70% (Control)", "VERDE"),
    ],
    "Pelicans": [
        ("Zion Williamson", 23.5, "75% (Imparable)", "VERDE"),
        ("Brandon Ingram", 21.5, "70% (Media distancia)", "VERDE"),
        ("CJ McCollum", 18.5, "65% (Tirador)", "AMARILLO"),
        ("Dejounte Murray", 17.5, "70% (Versatilidad)", "VERDE"),
        ("Yves Missi", 8.5, "60% (Rebotes)", "AMARILLO"),
    ],
    "Grizzlies": [
        ("Ja Morant", 24.5, "80% (Velocidad)", "VERDE"),
        ("Desmond Bane", 21.5, "75% (Constante)", "VERDE"),
        ("Jaren Jackson Jr.", 20.5, "70% (Interior/Exterior)", "VERDE"),
        ("Zach Edey", 12.5, "65% (Físico novato)", "AMARILLO"),
        ("Marcus Smart", 10.5, "60% (Liderazgo)", "AMARILLO"),
    ],
    "Kings": [
        ("De'Aaron Fox", 25.5, "80% (Velocidad)", "VERDE"),
        ("Domantas Sabonis", 19.5, "85% (Doble-doble)", "VERDE"),
        ("DeMar DeRozan", 21.5, "80% (Media distancia)", "VERDE"),
        ("Keegan Murray", 14.5, "65% (Perímetro)", "AMARILLO"),
        ("Kevin Huerter", 11.5, "60% (Volátil)", "AMARILLO"),
    ],
    "Rockets": [
        ("Alperen Sengun", 21.5, "80% (Interior)", "VERDE"),
        ("Jalen Green", 19.5, "65% (Rachas)", "AMARILLO"),
        ("Fred VanVleet", 16.5, "70% (Conducción)", "VERDE"),
        ("Dillon Brooks", 13.5, "60% (Selección tiro)", "AMARILLO"),
        ("Jabari Smith Jr.", 12.5, "65% (Pintura)", "VERDE"),
    ],
    "Spurs": [
        ("Victor Wembanyama", 24.5, "85% (Fenómeno)", "VERDE"),
        ("Devin Vassell", 17.5, "70% (Perímetro)", "VERDE"),
        ("Chris Paul", 9.5, "80% (Asistencias)", "VERDE"),
        ("Jeremy Sochan", 11.5, "60% (Esfuerzo)", "AMARILLO"),
        ("Harrison Barnes", 10.5, "65% (Veterano)", "VERDE"),
    ],
    "Jazz": [
        ("Lauri Markkanen", 23.5, "80% (Versátil)", "VERDE"),
        ("Collin Sexton", 17.5, "70% (Agresivo)", "VERDE"),
        ("Jordan Clarkson", 16.5, "60% (Revulsivo)", "AMARILLO"),
        ("Walker Kessler", 10.5, "85% (Clavadas)", "VERDE"),
        ("Keyonte George", 12.5, "55% (Desarrollo)", "AMARILLO"),
    ],
    "Trail Blazers": [
        ("Anfernee Simons", 20.5, "70% (Arma ofensiva)", "VERDE"),
        ("Jerami Grant", 18.5, "75% (Oportunista)", "VERDE"),
        ("Deandre Ayton", 14.5, "80% (Bajo el aro)", "VERDE"),
        ("Shaedon Sharpe", 15.5, "60% (Explosivo)", "AMARILLO"),
        ("Scoot Henderson", 12.5, "55% (Adaptación)", "AMARILLO"),
    ],
    "Hornets": [
        ("LaMelo Ball", 24.5, "75% (Creatividad)", "VERDE"),
        ("Brandon Miller", 18.5, "70% (Exterior)", "VERDE"),
        ("Miles Bridges", 17.5, "65% (Fuerza)", "AMARILLO"),
        ("Mark Williams", 11.5, "75% (Rebotes)", "VERDE"),
        ("Josh Green", 8.5, "60% (Defensa)", "AMARILLO"),
    ],
    "Wizards": [
        ("Kyle Kuzma", 19.5, "65% (Alto volumen)", "AMARILLO"),
        ("Jordan Poole", 17.5, "60% (Volátil)", "AMARILLO"),
        ("Bilal Coulibaly", 11.5, "70% (Defensivo)", "VERDE"),
        ("Jonas Valanciunas", 13.5, "80% (Poste)", "VERDE"),
        ("Malcolm Brogdon", 14.5, "65% (Conducción)", "AMARILLO"),
    ],
    "Pistons": [
        ("Cade Cunningham", 23.5, "80% (Motor)", "VERDE"),
        ("Jaden Ivey", 16.5, "65% (Penetraciones)", "AMARILLO"),
        ("Tobias Harris", 15.5, "70% (Estable)", "VERDE"),
        ("Jalen Duren", 12.5, "85% (Zona)", "VERDE"),
        ("Ausar Thompson", 9.5, "60% (Robos)", "AMARILLO"),
    ],
    "Hawks": [
        ("Trae Young", 25.5, "80% (Asistencias)", "VERDE"),
        ("Jalen Johnson", 18.5, "75% (Impacto total)", "VERDE"),
        ("De'Andre Hunter", 13.5, "60% (Intermitente)", "AMARILLO"),
        ("Zaccharie Risacher", 11.5, "55% (Novato)", "AMARILLO"),
        ("Clint Capela", 10.5, "80% (Fáciles)", "VERDE"),
    ],
    "Heat": [
        ("Jimmy Butler", 20.5, "80% (Clave)", "VERDE"),
        ("Bam Adebayo", 18.5, "85% (Consistencia)", "VERDE"),
        ("Tyler Herro", 20.5, "75% (Tirador)", "VERDE"),
        ("Terry Rozier", 14.5, "65% (Perímetro)", "AMARILLO"),
        ("Jaime Jaquez Jr.", 11.5, "70% (Táctico)", "VERDE"),
    ],
    "Bulls": [
        ("Zach LaVine", 21.5, "70% (Anotador)", "VERDE"),
        ("Coby White", 19.5, "75% (Crecimiento)", "VERDE"),
        ("Nikola Vucevic", 17.5, "80% (Interior/Exterior)", "VERDE"),
        ("Patrick Williams", 10.5, "55% (Bajo perfil)", "AMARILLO"),
        ("Josh Giddey", 12.5, "65% (Armado)", "VERDE"),
    ],
    "Pacers": [
        ("Tyrese Haliburton", 19.5, "80% (Lectura)", "VERDE"),
        ("Pascal Siakam", 21.5, "85% (Eficacia)", "VERDE"),
        ("Myles Turner", 16.5, "75% (Tapones)", "VERDE"),
        ("Andrew Nembhard", 11.5, "65% (Control)", "VERDE"),
        ("Aaron Nesmith", 12.5, "60% (Intensidad)", "AMARILLO"),
    ],
    "76ers": [
        ("Joel Embiid", 29.5, "85% (Dominante)", "VERDE"),
        ("Tyrese Maxey", 25.5, "80% (Velocidad)", "VERDE"),
        ("Paul George", 21.5, "75% (Perímetro)", "VERDE"),
        ("Kelly Oubre Jr.", 13.5, "65% (Energía)", "AMARILLO"),
        ("Caleb Martin", 10.5, "60% (Esfuerzo)", "AMARILLO"),
    ],
    "Nets": [
        ("Cam Thomas", 22.5, "75% (Volumen)", "VERDE"),
        ("Dennis Schroder", 15.5, "70% (Conducción)", "VERDE"),
        ("Cameron Johnson", 13.5, "65% (Triples)", "AMARILLO"),
        ("Nic Claxton", 11.5, "80% (Aro)", "VERDE"),
        ("Ben Simmons", 6.5, "60% (Asistencias)", "AMARILLO"),
    ],
}


def generar_json_actualizado():
  estructura_final = {
      "ultima_actualizacion": str(datetime.date.today()),
      "equipos": {},
  }

  for equipo, jugadores in nba_equipos_30.items():
    lista_jugadores = []
    for nombre, linea, patron, semaforo in jugadores:
      lista_jugadores.append({
          "nombre": nombre,
          "linea": linea,
          "patron": patron,
          "semaforo": semaforo,
      })
    estructura_final["equipos"][equipo] = lista_jugadores

  # Reescribe el archivo JSON local de forma completamente autónoma
  with open(
      "rosters_y_patrones_nba.json", "w", encoding="utf-8"
  ) as archivo_salida:
    json.dump(estructura_final, archivo_salida, ensure_ascii=False, indent=4)
  print("¡Archivo rosters_y_patrones_nba.json reescrito y actualizado con éxito!")


if __name__ == "__main__":
  generar_json_actualizado()
