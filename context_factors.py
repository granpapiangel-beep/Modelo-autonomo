"""Factores contextuales para ajustar una proyección NBA.

Los ajustes de este módulo son heurísticos, no probabilidades ni evidencia
estadística por sí solos. El CSV se usa únicamente para comprobar cobertura de
equipos; su mera presencia no altera la proyección.
"""

from pathlib import Path
import unicodedata

import pandas as pd


ARCHIVO_TITULARES = Path(__file__).resolve().with_name(
    "Titulares_NBA_Oficiales_30_Equipos(Puntajes Diarios).csv"
)

# Ajustes deliberadamente moderados: deben calibrarse con resultados históricos
# antes de interpretarse como ventaja predictiva.
FACTOR_LOCAL_BASE = 1.03
FACTOR_VISITANTE_BASE = 1.00
PENALIZACION_B2B = 0.98
BONIFICACION_REBOTE_PLAYOFFS = 1.01
FACTOR_MINIMO = 0.90
FACTOR_MAXIMO = 1.10


_ALIAS_EQUIPOS = {
    "atlanta hawks": "hawks", "hawks": "hawks",
    "boston celtics": "celtics", "celtics": "celtics",
    "brooklyn nets": "nets", "nets": "nets",
    "charlotte hornets": "hornets", "hornets": "hornets",
    "chicago bulls": "bulls", "bulls": "bulls",
    "cleveland cavaliers": "cavaliers", "cavaliers": "cavaliers",
    "dallas mavericks": "mavericks", "mavericks": "mavericks",
    "denver nuggets": "nuggets", "nuggets": "nuggets",
    "detroit pistons": "pistons", "pistons": "pistons",
    "golden state warriors": "warriors", "warriors": "warriors",
    "houston rockets": "rockets", "rockets": "rockets",
    "indiana pacers": "pacers", "pacers": "pacers",
    "la clippers": "clippers", "los angeles clippers": "clippers", "clippers": "clippers",
    "los angeles lakers": "lakers", "lakers": "lakers",
    "memphis grizzlies": "grizzlies", "grizzlies": "grizzlies",
    "miami heat": "heat", "heat": "heat",
    "milwaukee bucks": "bucks", "bucks": "bucks",
    "minnesota timberwolves": "timberwolves", "timberwolves": "timberwolves",
    "new orleans pelicans": "pelicans", "pelicans": "pelicans",
    "new york knicks": "knicks", "knicks": "knicks",
    "oklahoma city thunder": "thunder", "okc thunder": "thunder", "thunder": "thunder",
    "orlando magic": "magic", "magic": "magic",
    "philadelphia 76ers": "76ers", "76ers": "76ers",
    "phoenix suns": "suns", "suns": "suns",
    "portland trail blazers": "trail blazers", "trail blazers": "trail blazers",
    "sacramento kings": "kings", "kings": "kings",
    "san antonio spurs": "spurs", "spurs": "spurs",
    "toronto raptors": "raptors", "raptors": "raptors",
    "utah jazz": "jazz", "jazz": "jazz",
    "washington wizards": "wizards", "wizards": "wizards",
}


def _normalizar_equipo(nombre):
    """Normaliza acentos, mayúsculas y alias sin usar coincidencias parciales."""
    if not isinstance(nombre, str):
        return ""
    texto = unicodedata.normalize("NFKD", nombre)
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    texto = " ".join(texto.casefold().strip().split())
    return _ALIAS_EQUIPOS.get(texto, texto)


def _margen_valido(margen):
    """Devuelve un margen finito como float, o None cuando falta/no es válido."""
    try:
        valor = float(margen)
    except (TypeError, ValueError):
        return None
    return valor if pd.notna(valor) else None


def _equipos_en_csv(csv_filename, equipo_local, equipo_visitante):
    """Comprueba los equipos del CSV; falla de forma segura si no está disponible."""
    try:
        df = pd.read_csv(csv_filename, encoding="utf-8-sig")
        columnas = {str(columna).strip().casefold(): columna for columna in df.columns}
        columna_equipo = columnas.get("equipo")
        if columna_equipo is None:
            return None
        equipos = {_normalizar_equipo(nombre) for nombre in df[columna_equipo].dropna()}
        return (
            _normalizar_equipo(equipo_local) in equipos,
            _normalizar_equipo(equipo_visitante) in equipos,
        )
    except (OSError, ValueError, pd.errors.ParserError, UnicodeError):
        return None


def evaluar_factores_contextuales(
    equipo_local,
    equipo_visitante,
    modo_playoffs=False,
    margen_juego_anterior_local=0,
    margen_juego_anterior_visita=0,
    b2b_local=False,
    b2b_visita=False,
    csv_filename=ARCHIVO_TITULARES,
):
    """Calcula ajustes contextuales conservadores para ambos equipos.

    ``margen_juego_anterior_*`` representa puntos a favor menos puntos en contra
    del equipo correspondiente en su partido anterior. Los factores de fatiga y
    rebote son heurísticos y no deben confundirse con una evaluación de lesiones.
    Se mantiene la forma de los campos de retorno para compatibilidad con clientes.
    """
    factor_local = FACTOR_LOCAL_BASE
    factor_visita = FACTOR_VISITANTE_BASE
    notas = []
    factores_aplicados = {"local": [], "visitante": []}

    if b2b_local:
        factor_local *= PENALIZACION_B2B
        notas.append("B2B: ajuste moderado por posible fatiga del local.")
        factores_aplicados["local"].append("B2B")
    if b2b_visita:
        factor_visita *= PENALIZACION_B2B
        notas.append("B2B: ajuste moderado por posible fatiga del visitante.")
        factores_aplicados["visitante"].append("B2B")

    if modo_playoffs:
        notas.append("Playoffs: modo de contexto activado.")
        margen_local = _margen_valido(margen_juego_anterior_local)
        margen_visita = _margen_valido(margen_juego_anterior_visita)
        if margen_local is not None and margen_local <= -15:
            factor_local *= BONIFICACION_REBOTE_PLAYOFFS
            factores_aplicados["local"].append("rebote tras derrota amplia")
            notas.append("Ajuste pequeño de rebote para el local tras derrota amplia.")
        if margen_visita is not None and margen_visita <= -15:
            factor_visita *= BONIFICACION_REBOTE_PLAYOFFS
            factores_aplicados["visitante"].append("rebote tras derrota amplia")
            notas.append("Ajuste pequeño de rebote para el visitante tras derrota amplia.")

    presencia_csv = _equipos_en_csv(csv_filename, equipo_local, equipo_visitante)
    if presencia_csv == (True, True):
        estabilidad = "Cobertura completa (CSV)"
    elif presencia_csv is None:
        estabilidad = "Sin validar (CSV no disponible o inválido)"
    elif any(presencia_csv):
        estabilidad = "Cobertura parcial (CSV)"
    else:
        estabilidad = "Sin cobertura de equipos (CSV)"

    # Limita efectos acumulados para evitar que varios indicadores heurísticos
    # produzcan multiplicadores extremos.
    factor_local = min(FACTOR_MAXIMO, max(FACTOR_MINIMO, factor_local))
    factor_visita = min(FACTOR_MAXIMO, max(FACTOR_MINIMO, factor_visita))

    if not notas:
        notas.append("Sin ajustes contextuales adicionales; se aplica ventaja local base.")

    return {
        "factor_local": round(factor_local, 3),
        "factor_visita": round(factor_visita, 3),
        "estabilidad_dupla": estabilidad,
        "impacto_lesiones": "No evaluado por esta función",
        "nota_analitica": " | ".join(notas),
        "alerta_trampa": bool(b2b_local or b2b_visita),
        "factores_aplicados": factores_aplicados,
        "fuente_datos": "CSV usado solo para validar cobertura; ajustes contextuales heurísticos",
    }
