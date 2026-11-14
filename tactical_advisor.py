"""
Módulo: Tactical Advisor (Asesor Táctico y de Inteligencia Deportiva de Stephy)
Enfoque: Análisis de fatiga, contexto anímico, importancia del partido y gestión de descanso.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

class TacticalAdvisor:
    def __init__(self):
        # Umbrales y pesos para el análisis táctico
        self.factor_fatiga_b2b = 0.93  # Castigo de rendimiento en partidos consecutivos
        
    def evaluar_fatiga_y_calendario(self, equipo, es_b2b=False, gira_larga_visitante=False):
        """
        Evalúa el impacto físico del calendario reciente en las piernas de los jugadores.
        """
        notas = []
        coeficiente_rendimiento = 1.0
        
        if es_b2b:
            coeficiente_rendimiento *= self.fatiga_b2b if hasattr(self, 'fatiga_b2b') else 0.93
            notas.append(f"⚠️ Alerta de Fatiga (Back-to-Back): {equipo} jugó la noche anterior. Riesgo de piernas pesadas y menor intensidad defensiva.")
            
        if gira_larga_visitante:
            coeficiente_rendimiento *= 0.96
            notas.append(f"✈️ Desgaste por Viaje: {equipo} cierra una gira prolongada fuera de casa (efecto de inercia post-gira).")
            
        if not notas:
            notas.append(f"✅ Descanso óptimo: {equipo} llega con piernas frescas al encuentro.")
            
        return {
            "coeficiente_fisico": round(coeficiente_rendimiento, 3),
            "notas_fatiga": notas
        }

    def analizar_importancia_partido(self, equipo_local, equipo_visitante, modo_playoffs=False):
        """
        Evalúa el índice de urgencia y la motivación táctica del encuentro.
        """
        nivel_urgencia = "Estándar (Fase Regular)"
        estrategia_entrenador = "Rotación habitual de minutos."
        
        if modo_playoffs:
            nivel_urgencia = "Extremo (Postemporada / Lucha Directa)"
            estrategia_entrenador = "Rotaciones cortadas a 7-8 jugadores clave. Cero minutos de prueba para la banca."
        
        return {
            "urgencia": nivel_urgencia,
            "enfoque_entrenador": estrategia_entrenador,
            "consejo_tactico": f"Duelo táctico entre {equipo_local} y {equipo_visitante} con alta atención en ajustes defensivos de segunda mitad."
        }

    def predecir_gestion_descanso(self, equipo, estrellas_equipo, es_b2b=False):
        """
        Anticipa si el entrenador podría reservar a titulares o restringir minutos (*Load Management*).
        """
        alertas_descanso = []
        if es_b2b and estrellas_equipo:
            for estrella in estrellas_equipo:
                alertas_descanso.append({
                    "jugador": estrella,
                    "equipo": equipo,
                    "riesgo": "Alto",
                    "mensaje": f"⚠️ Precaución con {estrella}: Al ser B2B, alta probabilidad de descanso preventivo o minutos restringidos (máx. 22-25 min)."
                })
        else:
            for estrella in estrellas_equipo:
                alertas_descanso.append({
                    "jugador": estrella,
                    "equipo": equipo,
                    "riesgo": "Bajo",
                    "mensaje": f"🟢 {estrella} apunta a disputar su carga normal de minutos."
                })
                
        return alertas_descanso

    def generar_reporte_tactico_integral(self, local, visitante, b2b_local=False, b2b_visita=False, estrellas_locales=None, estrellas_visitas=None):
        """
        Genera el informe consejero completo para el usuario antes de analizar las estadísticas.
        """
        estrellas_locales = estrellas_locales or []
        estrellas_visitas = estrellas_visitas or []
        
        fatiga_loc = self.evaluar_fatiga_y_calendario(local, es_b2b=b2b_local)
        fatiga_vis = self.evaluar_fatiga_y_calendario(visitante, es_b2b=b2b_visita)
        
        contexto_partido = self.analizar_importancia_partido(local, visitante)
        
        descanso_loc = self.predecir_gestion_descanso(local, estrellas_locales, es_b2b=b2b_local)
        descanso_vis = self.predecir_gestion_descanso(visitante, estrellas_visitas, es_b2b=b2b_visita)
        
        return {
            "local": local,
            "visitante": visitante,
            "analisis_fisico_local": fatiga_loc,
            "analisis_fisico_visitante": fatiga_vis,
            "contexto_duelo": contexto_partido,
            "alertas_rotacion_local": descanso_loc,
            "alertas_rotacion_visitante": descanso_vis
        }
