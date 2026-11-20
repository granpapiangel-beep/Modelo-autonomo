"""
Módulo: Tactical Advisor (Asesor Táctico de Stephy)

Calcula heurísticas orientativas de fatiga, contexto y posible gestión de descanso.
Los resultados no deben interpretarse como certeza ni como asesoría deportiva o financiera.
"""

from __future__ import annotations

from typing import Iterable, Sequence


class TacticalAdvisor:
    """Asesor táctico basado en reglas configurables.

    Los parámetros representan heurísticas de interfaz. No sustituyen datos
    reales de calendario, minutos jugados, lesiones ni decisiones oficiales.
    """

    DEFAULT_CONFIG = {
        "b2b_factor": 0.93,
        "road_trip_factor": 0.96,
        "high_risk_minute_range": (22, 25),
    }

    def __init__(self, config: dict | None = None):
        config = config or {}
        self.factor_fatiga_b2b = float(config.get("b2b_factor", self.DEFAULT_CONFIG["b2b_factor"]))
        self.factor_gira_visitante = float(config.get("road_trip_factor", self.DEFAULT_CONFIG["road_trip_factor"]))
        if not 0.1 <= self.factor_fatiga_b2b <= 1.0:
            raise ValueError("b2b_factor debe estar entre 0.1 y 1.0")
        if not 0.1 <= self.factor_gira_visitante <= 1.0:
            raise ValueError("road_trip_factor debe estar entre 0.1 y 1.0")

        minute_range = config.get("high_risk_minute_range", self.DEFAULT_CONFIG["high_risk_minute_range"])
        if not isinstance(minute_range, (tuple, list)) or len(minute_range) != 2:
            raise ValueError("high_risk_minute_range debe contener [mínimo, máximo]")
        minimum, maximum = (int(value) for value in minute_range)
        if minimum < 0 or maximum < minimum:
            raise ValueError("El rango de minutos debe ser no negativo y estar ordenado")
        self.rango_minutos_alto_riesgo = (minimum, maximum)

    @staticmethod
    def _nombre(value: object, predeterminado: str = "Equipo") -> str:
        if value is None:
            return predeterminado
        text = str(value).strip()
        return text if text else predeterminado

    @staticmethod
    def _estrellas(estrellas: Iterable[str] | None) -> list[str]:
        if estrellas is None:
            return []
        if isinstance(estrellas, str):
            estrellas = [estrellas]

        resultado: list[str] = []
        vistos: set[str] = set()
        for estrella in estrellas:
            if estrella is None:
                continue
            nombre = str(estrella).strip()
            clave = nombre.casefold()
            if nombre and clave not in vistos:
                vistos.add(clave)
                resultado.append(nombre)
        return resultado

    def evaluar_fatiga_y_calendario(
        self,
        equipo: str,
        es_b2b: bool = False,
        gira_larga_visitante: bool = False,
    ) -> dict:
        """Evalúa heurísticas simples; no consulta el calendario real."""
        equipo = self._nombre(equipo)
        notas: list[str] = []
        coeficiente = 1.0

        if es_b2b:
            coeficiente *= self.factor_fatiga_b2b
            notas.append(f"⚠️ Fatiga probable por back-to-back: {equipo} jugó la noche anterior.")
        if gira_larga_visitante:
            coeficiente *= self.factor_gira_visitante
            notas.append(f"✈️ Posible desgaste por viaje: {equipo} cierra una gira prolongada fuera de casa.")
        if not notas:
            notas.append(f"✅ No se detectaron señales básicas de fatiga para {equipo}.")

        return {
            "coeficiente_fisico": round(coeficiente, 3),
            "notas_fatiga": notas,
            "es_heuristica": True,
        }

    def analizar_importancia_partido(
        self,
        equipo_local: str,
        equipo_visitante: str,
        modo_playoffs: bool = False,
        lucha_clasificacion: bool = False,
    ) -> dict:
        """Describe el contexto esperado usando solo los indicadores recibidos."""
        local = self._nombre(equipo_local)
        visitante = self._nombre(equipo_visitante)

        if modo_playoffs:
            nivel = "Alto (postemporada)"
            estrategia = "Es posible que se acorten las rotaciones; confirmar alineaciones oficiales."
        elif lucha_clasificacion:
            nivel = "Alto (lucha por clasificación)"
            estrategia = "Puede aumentar la importancia táctica del partido; confirmar contexto y alineaciones."
        else:
            nivel = "Estándar (fase regular)"
            estrategia = "No se infiere un cambio de rotación con los datos disponibles."

        return {
            "urgencia": nivel,
            "enfoque_entrenador": estrategia,
            "consejo_tactico": (
                f"Duelo entre {local} y {visitante}; verificar reportes y alineaciones "
                "antes del inicio."
            ),
            "es_heuristica": True,
        }

    def predecir_gestion_descanso(
        self,
        equipo: str,
        estrellas_equipo: Iterable[str] | None,
        es_b2b: bool = False,
        jugadores_baja: Iterable[str] | None = None,
    ) -> list[dict]:
        """Genera alertas orientativas; B2B por sí solo no confirma una baja."""
        equipo = self._nombre(equipo)
        estrellas = self._estrellas(estrellas_equipo)
        bajas = {name.casefold() for name in self._estrellas(jugadores_baja)}
        alertas: list[dict] = []

        for estrella in estrellas:
            confirmado = estrella.casefold() in bajas
            if confirmado:
                riesgo = "Baja indicada"
                mensaje = f"{estrella} aparece en la lista de bajas proporcionada; confirma el reporte oficial."
            elif es_b2b:
                riesgo = "Posible (no confirmado)"
                minimum, maximum = self.rango_minutos_alto_riesgo
                mensaje = (
                    f"El back-to-back puede motivar seguimiento de minutos para {estrella}; "
                    f"rango {minimum}–{maximum} min solo como referencia no confirmada."
                )
            else:
                riesgo = "Sin señal específica"
                mensaje = f"No se proporcionó una señal de descanso para {estrella}; verificar información oficial."

            alertas.append({
                "jugador": estrella,
                "equipo": equipo,
                "riesgo": riesgo,
                "mensaje": mensaje,
                "confirmado": confirmado,
            })
        return alertas

    def generar_reporte_tactico_integral(
        self,
        local: str,
        visitante: str,
        b2b_local: bool = False,
        b2b_visita: bool = False,
        estrellas_locales: Sequence[str] | None = None,
        estrellas_visitas: Sequence[str] | None = None,
        gira_larga_local: bool = False,
        gira_larga_visita: bool = False,
        modo_playoffs: bool = False,
        lucha_clasificacion: bool = False,
        jugadores_baja_local: Sequence[str] | None = None,
        jugadores_baja_visita: Sequence[str] | None = None,
    ) -> dict:
        """Genera el informe completo con contexto opcional."""
        local = self._nombre(local)
        visitante = self._nombre(visitante)
        bajas_locales = self._estrellas(jugadores_baja_local)
        bajas_visitas = self._estrellas(jugadores_baja_visita)

        return {
            "local": local,
            "visitante": visitante,
            "analisis_fisico_local": self.evaluar_fatiga_y_calendario(
                local, es_b2b=b2b_local, gira_larga_visitante=gira_larga_local
            ),
            "analisis_fisico_visitante": self.evaluar_fatiga_y_calendario(
                visitante, es_b2b=b2b_visita, gira_larga_visitante=gira_larga_visita
            ),
            "contexto_duelo": self.analizar_importancia_partido(
                local, visitante, modo_playoffs=modo_playoffs,
                lucha_clasificacion=lucha_clasificacion,
            ),
            "alertas_rotacion_local": self.predecir_gestion_descanso(
                local, estrellas_locales, es_b2b=b2b_local, jugadores_baja=bajas_locales
            ),
            "alertas_rotacion_visitante": self.predecir_gestion_descanso(
                visitante, estrellas_visitas, es_b2b=b2b_visita, jugadores_baja=bajas_visitas
            ),
            "jugadores_baja_local": bajas_locales,
            "jugadores_baja_visitante": bajas_visitas,
            "aviso": "Informe heurístico, no confirmación de lesiones, alineaciones ni minutos. Verificar fuentes oficiales.",
        }
