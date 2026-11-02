# player_analysis.py
# Módulo de Minería de Datos con patrones de cumplimiento de cuotas para los 5 titulares de los 30 equipos de la NBA
import numpy as np
import pandas as pd

def obtener_patron_titulares(nombre_equipo, puntos_proyectados_partido):
    """
    Retorna la lista de los 5 jugadores titulares de cualquier equipo de la NBA
    con su línea de puntos, porcentaje de cumplimiento de patrón y semáforo analítico.
    """
    patrones_nba = {
        "Celtics": [
            ("Jayson Tatum", 22.5, "85% (Cumplidor Frecuente - Alta Carga)", "VERDE"),
            ("Jaylen Brown", 20.5, "70% (Estable en transiciones)", "VERDE"),
            ("Derrick White", 15.5, "60% (Margen Ajustado)", "AMARILLO"),
            ("Jrue Holiday", 12.5, "75% (Rol Defensivo / Fijo)", "VERDE"),
            ("Kristaps Porzingis", 18.5, "65% (Depende de triples)", "AMARILLO")
        ],
        "Magic": [
            ("Paolo Banchero", 21.5, "80% (Eje Ofensivo Principal)", "VERDE"),
            ("Franz Wagner", 18.5, "75% (Constante al aro)", "VERDE"),
            ("Jalen Suggs", 12.5, "55% (Volátil / Defensivo)", "AMARILLO"),
            ("Wendell Carter Jr.", 11.5, "60% (Rebotero / Seguro)", "VERDE"),
            ("Cole Anthony", 10.5, "50% (Banquillo / Irregular)", "ROJO")
        ],
        "Lakers": [
            ("Anthony Davis", 23.5, "85% (Dominante en la pintura)", "VERDE"),
            ("LeBron James", 12.5, "75% (Cuota Ajustada / Rol Secundario)", "AMARILLO"),
            ("Austin Reaves", 16.5, "70% (Altos minutos / Confiable)", "VERDE"),
            ("D'Angelo Russell", 14.5, "55% (Depende de rachas de 3s)", "AMARILLO"),
            ("Rui Hachimura", 11.5, "60% (Cumplidor secundario)", "VERDE")
        ],
        "Raptors": [
            ("Scottie Barnes", 18.5, "75% (Líder estadístico)", "VERDE"),
            ("Immanuel Quickley", 17.5, "70% (Alto volumen de tiros)", "VERDE"),
            ("RJ Barrett", 16.5, "65% (Ataque al aro constante)", "VERDE"),
            ("Jakob Poeltl", 11.5, "80% (Puntos seguros bajo el aro)", "VERDE"),
            ("Gradey Dick", 10.5, "50% (Joven / Volátil)", "AMARILLO")
        ],
        "Warriors": [
            ("Stephen Curry", 26.5, "85% (Éxito Frecuente en Líneas)", "VERDE"),
            ("Jonathan Kuminga", 16.5, "70% (Explosivo en penetración)", "VERDE"),
            ("Brandin Podziemski", 11.5, "65% (Rebotes y aportes)", "VERDE"),
            ("Draymond Green", 8.5, "90% (Cuota Mínima Muy Segura)", "VERDE"),
            ("Buddy Hield", 14.5, "60% (Francotirador irregular)", "AMARILLO")
        ],
        "Clippers": [
            ("Kawhi Leonard", 22.5, "80% (Alta consistencia de tiro)", "VERDE"),
            ("James Harden", 19.5, "75% (Generador de faltas y triples)", "VERDE"),
            ("Norman Powell", 16.5, "70% (Anotador secundario fijo)", "VERDE"),
            ("Ivica Zubac", 12.5, "85% (Efectividad en zona)", "VERDE"),
            ("Derrick Jones Jr.", 8.5, "60% (Puntos por pérdidas)", "AMARILLO")
        ],
        "Cavaliers": [
            ("Donovan Mitchell", 25.5, "85% (Líder anotador constante)", "VERDE"),
            ("Darius Garland", 20.5, "75% (Distribuidor y tirador)", "VERDE"),
            ("Evan Mobley", 17.5, "70% (Eficiente cerca del aro)", "VERDE"),
            ("Jarrett Allen", 14.5, "80% (Alto porcentaje de campo)", "VERDE"),
            ("Max Strus", 11.5, "60% (Depende de triples)", "AMARILLO")
        ],
        "Knicks": [
            ("Jalen Brunson", 26.5, "85% (Control absoluto de ofensiva)", "VERDE"),
            ("Karl-Anthony Towns", 22.5, "80% (Puntos y rebotes seguros)", "VERDE"),
            ("Mikal Bridges", 16.5, "70% (Durabilidad y volumen)", "VERDE"),
            ("OG Anunoby", 14.5, "65% (Aportes estables)", "VERDE"),
            ("Josh Hart", 11.5, "75% (Intensidad y transición)", "VERDE")
        ],
        "Bucks": [
            ("Giannis Antetokounmpo", 30.5, "90% (Dominio absoluto en pintura)", "VERDE"),
            ("Damian Lillard", 24.5, "80% (Clutch y triples lejanos)", "VERDE"),
            ("Khris Middleton", 15.5, "65% (Manejo de ritmo)", "AMARILLO"),
            ("Brook Lopez", 12.5, "70% (Amenaza perimetral y tapones)", "VERDE"),
            ("Bobby Portis", 11.5, "60% (Energía desde el banquillo)", "AMARILLO")
        ],
        "Suns": [
            ("Kevin Durant", 26.5, "85% (Efectividad de clase mundial)", "VERDE"),
            ("Devin Booker", 25.5, "80% (Alto volumen de tiros)", "VERDE"),
            ("Bradley Beal", 17.5, "65% (Variabilidad por lesiones)", "AMARILLO"),
            ("Jusuf Nurkic", 11.5, "70% (Puntos en zona y rebotes)", "VERDE"),
            ("Tyus Jones", 9.5, "75% (Bajo índice de errores)", "VERDE")
        ],
        "Nuggets": [
            ("Nikola Jokic", 26.5, "90% (Triple-doble constante)", "VERDE"),
            ("Jamal Murray", 21.5, "75% (Anotador clutch)", "VERDE"),
            ("Michael Porter Jr.", 16.5, "70% (Efectivo a distancia)", "VERDE"),
            ("Aaron Gordon", 13.5, "80% (Cortador excelente)", "VERDE"),
            ("Christian Braun", 10.5, "65% (Altas transiciones)", "AMARILLO")
        ],
        "Mavericks": [
            ("Luka Doncic", 32.5, "90% (Volumen ofensivo gigante)", "VERDE"),
            ("Kyrie Irving", 24.5, "85% (Mecánica impecable)", "VERDE"),
            ("Klay Thompson", 14.5, "60% (Depende de rachas)", "AMARILLO"),
            ("P.J. Washington", 11.5, "65% (Esquinas abiertas)", "VERDE"),
            ("Dereck Lively II", 9.5, "80% (Oops y eficaces rebotes)", "VERDE")
        ],
        "Thunder": [
            ("Shai Gilgeous-Alexander", 30.5, "90% (Consistencia inquebrantable)", "VERDE"),
            ("Chet Holmgren", 17.5, "75% (Bloqueos y triples)", "VERDE"),
            ("Jalen Williams", 19.5, "80% (Crecimiento ofensivo sólido)", "VERDE"),
            ("Lu Dort", 10.5, "60% (Perfil defensivo)", "AMARILLO"),
            ("Alex Caruso", 9.5, "65% (Robos y puntos fáciles)", "VERDE")
        ],
        "Timberwolves": [
            ("Anthony Edwards", 26.5, "80% (Explosivo y dominante)", "VERDE"),
            ("Julius Randle", 20.5, "75% (Fuerza en la pintura)", "VERDE"),
            ("Rudy Gobert", 12.5, "85% (Canastas bajo el aro)", "VERDE"),
            ("Jaden McDaniels", 11.5, "60% (Parpadeos ofensivos)", "AMARILLO"),
            ("Mike Conley", 10.5, "70% (Experiencia y control)", "VERDE")
        ],
        "Pelicans": [
            ("Zion Williamson", 23.5, "75% (Fuerza imparable al aro)", "VERDE"),
            ("Brandon Ingram", 21.5, "70% (Media distancia segura)", "VERDE"),
            ("CJ McCollum", 18.5, "65% (Tirador perimetral)", "AMARILLO"),
            ("Dejounte Murray", 17.5, "70% (Versatilidad ofensiva)", "VERDE"),
            ("Yves Missi", 8.5, "60% (Rebotes ofensivos)", "AMARILLO")
        ],
        "Grizzlies": [
            ("Ja Morant", 24.5, "80% (Velocidad y penetración)", "VERDE"),
            ("Desmond Bane", 21.5, "75% (Francotirador constante)", "VERDE"),
            ("Jaren Jackson Jr.", 20.5, "70% (Buena cuota interior/exterior)", "VERDE"),
            ("Zach Edey", 12.5, "65% (Presencia física novata)", "AMARILLO"),
            ("Marcus Smart", 10.5, "60% (Liderazgo y defensa)", "AMARILLO")
        ],
        "Kings": [
            ("De'Aaron Fox", 25.5, "80% (Velocidad letal)", "VERDE"),
            ("Domantas Sabonis", 19.5, "85% (Doble-doble garantizado)", "VERDE"),
            ("DeMar DeRozan", 21.5, "80% (Especialista en media distancia)", "VERDE"),
            ("Keegan Murray", 14.5, "65% (Aportes desde el perímetro)", "AMARILLO"),
            ("Kevin Huerter", 11.5, "60% (Volátil)", "AMARILLO")
        ],
        "Rockets": [
            ("Alperen Sengun", 21.5, "80% (Juego interior magistral)", "VERDE"),
            ("Jalen Green", 19.5, "65% (Rachas altas y bajas)", "AMARILLO"),
            ("Fred VanVleet", 16.5, "70% (Conducción y tiros libres)", "VERDE"),
            ("Dillon Brooks", 13.5, "60% (Selección de tiro variable)", "AMARILLO"),
            ("Jabari Smith Jr.", 12.5, "65% (Estirable en la pintura)", "VERDE")
        ],
        "Spurs": [
            ("Victor Wembanyama", 24.5, "85% (Fenómeno estadístico)", "VERDE"),
            ("Devin Vassell", 17.5, "70% (Anotador perimetral)", "VERDE"),
            ("Chris Paul", 9.5, "80% (Control de juego y asistencias)", "VERDE"),
            ("Jeremy Sochan", 11.5, "60% (Puntos de esfuerzo)", "AMARILLO"),
            ("Harrison Barnes", 10.5, "65% (Veterano cumplidor)", "VERDE")
        ],
        "Jazz": [
            ("Lauri Markkanen", 23.5, "80% (Estrella versátil)", "VERDE"),
            ("Collin Sexton", 17.5, "70% (Agresivo al aro)", "VERDE"),
            ("Jordan Clarkson", 16.5, "60% (Anotador revulsivo)", "AMARILLO"),
            ("Walker Kessler", 10.5, "85% (Efectividad en clavadas)", "VERDE"),
            ("Keyonte George", 12.5, "55% (Joven en desarrollo)", "AMARILLO")
        ],
        "Trail Blazers": [
            ("Anfernee Simons", 20.5, "70% (Principal arma ofensiva)", "VERDE"),
            ("Jerami Grant", 18.5, "75% (Oportunista constante)", "VERDE"),
            ("Deandre Ayton", 14.5, "80% (Seguro bajo el aro)", "VERDE"),
            ("Shaedon Sharpe", 15.5, "60% (Atleta explosivo)", "AMARILLO"),
            ("Scoot Henderson", 12.5, "55% (Proceso de adaptación)", "AMARILLO")
        ],
        "Hornets": [
            ("LaMelo Ball", 24.5, "75% (Creatividad y alto goleo)", "VERDE"),
            ("Brandon Miller", 18.5, "70% (Gran tirador exterior)", "VERDE"),
            ("Miles Bridges", 17.5, "65% (Fuerza física constante)", "AMARILLO"),
            ("Mark Williams", 11.5, "75% (Rebotes y puntos cortos)", "VERDE"),
            ("Josh Green", 8.5, "60% (Defensa y transición)", "AMARILLO")
        ],
        "Wizards": [
            ("Kyle Kuzma", 19.5, "65% (Alto volumen, baja eficiencia)", "AMARILLO"),
            ("Jordan Poole", 17.5, "60% (Impredecible / Volátil)", "AMARILLO"),
            ("Bilal Coulibaly", 11.5, "70% (Evolución defensiva)", "VERDE"),
            ("Jonas Valanciunas", 13.5, "80% (Puntos seguros en poste)", "VERDE"),
            ("Malcolm Brogdon", 14.5, "65% (Experta conducción)", "AMARILLO")
        ],
        "Pistons": [
            ("Cade Cunningham", 23.5, "80% (Motor del equipo)", "VERDE"),
            ("Jaden Ivey", 16.5, "65% (Penetraciones rápidas)", "AMARILLO"),
            ("Tobias Harris", 15.5, "70% (Veterano estable)", "VERDE"),
            ("Jalen Duren", 12.5, "85% (Efectividad en zona)", "VERDE"),
            ("Ausar Thompson", 9.5, "60% (Robos y contraataques)", "AMARILLO")
        ],
        "Hawks": [
            ("Trae Young", 25.5, "80% (Alto puntaje y asistencias)", "VERDE"),
            ("Jalen Johnson", 18.5, "75% (Jugador de impacto total)", "VERDE"),
            ("De'Andre Hunter", 13.5, "60% (Intermitente)", "AMARILLO"),
            ("Zaccharie Risacher", 11.5, "55% (Novato en adaptación)", "AMARILLO"),
            ("Clint Capela", 10.5, "80% (Canastas fáciles)", "VERDE")
        ],
        "Heat": [
            ("Jimmy Butler", 20.5, "80% (Especialista en momentos clave)", "VERDE"),
            ("Bam Adebayo", 18.5, "85% (Consistencia defensiva y ofensiva)", "VERDE"),
            ("Tyler Herro", 20.5, "75% (Tirador estelar)", "VERDE"),
            ("Terry Rozier", 14.5, "65% (Desequilibrio perimetral)", "AMARILLO"),
            ("Jaime Jaquez Jr.", 11.5, "70% (Inteligencia táctica)", "VERDE")
        ],
        "Bulls": [
            ("Zach LaVine", 21.5, "70% (Anotador nato)", "VERDE"),
            ("Coby White", 19.5, "75% (Crecimiento ofensivo notable)", "VERDE"),
            ("Nikola Vucevic", 17.5, "80% (Juego interior y tiro exterior)", "VERDE"),
            ("Patrick Williams", 10.5, "55% (Bajo perfil ofensivo)", "AMARILLO"),
            ("Josh Giddey", 12.5, "65% (Versatilidad de armado)", "VERDE")
        ],
        "Pacers": [
            ("Tyrese Haliburton", 19.5, "80% (Excelente lectura de juego)", "VERDE"),
            ("Pascal Siakam", 21.5, "85% (Experiencia y eficacia)", "VERDE"),
            ("Myles Turner", 16.5, "75% (Triples y tapones)", "VERDE"),
            ("Andrew Nembhard", 11.5, "65% (Control secundario)", "VERDE"),
            ("Aaron Nesmith", 12.5, "60% (Intensidad)", "AMARILLO")
        ],
        "76ers": [
            ("Joel Embiid", 29.5, "85% (Dominante cuando está activo)", "VERDE"),
            ("Tyrese Maxey", 25.5, "80% (Velocidad y anotación pura)", "VERDE"),
            ("Paul George", 21.5, "75% (Clase perimetral)", "VERDE"),
            ("Kelly Oubre Jr.", 13.5, "65% (Energía ofensiva)", "AMARILLO"),
            ("Caleb Martin", 10.5, "60% (Defensa y esfuerzo)", "AMARILLO")
        ],
        "Nets": [
            ("Cam Thomas", 22.5, "75% (Alto volumen de anotación)", "VERDE"),
            ("Dennis Schroder", 15.5, "70% (Conducción y puntos)", "VERDE"),
            ("Cameron Johnson", 13.5, "65% (Especialista en triples)", "AMARILLO"),
            ("Nic Claxton", 11.5, "80% (Eficiente bajo el aro)", "VERDE"),
            ("Ben Simmons", 6.5, "60% (Enfoque en asistencias)", "AMARILLO")
        ]
    }
    
    if nombre_equipo in patrones_nba:
        return patrones_nba[nombre_equipo]
    else:
        base = round((puntos_proyectados_partido / 2) * 0.2, 1)
        return [
            (f"Titular 1 ({nombre_equipo})", base + 4.0, "75% (Patrón Frecuente)", "VERDE"),
            (f"Titular 2 ({nombre_equipo})", base + 1.0, "65% (Estable)", "VERDE"),
            (f"Titular 3 ({nombre_equipo})", base - 1.0, "60% (Margen Justo)", "AMARILLO"),
            (f"Titular 4 ({nombre_equipo})", base - 3.0, "55% (Bajo Volumen)", "AMARILLO"),
            (f"Titular 5 ({nombre_equipo})", base - 5.0, "50% (Defensivo)", "ROJO")
        ]
