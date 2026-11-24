from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image


_HISTORIAL_FILE = Path(__file__).resolve().with_name("historial_evaluaciones_nba.csv")

_SINONIMOS_BOLETO: dict[str, tuple[str, ...]] = {
    "bulls": ("bulls", "chicago", "toros", "chi"),
    "nuggets": ("nuggets", "denver", "pepitas", "den"),
    "lakers": ("lakers", "los angeles lakers", "la lakers", "lal"),
    "clippers": ("clippers", "la clippers", "los angeles clippers", "lac"),
    "warriors": ("warriors", "golden state", "guerreros", "gsw"),
    "kings": ("kings", "sacramento", "reyes", "sac"),
    "suns": ("suns", "phoenix", "soles", "phx"),
    "mavericks": ("mavericks", "dallas", "mavs", "dal"),
    "spurs": ("spurs", "san antonio", "espuelas", "sas"),
    "rockets": ("rockets", "houston", "cohetes", "hou"),
    "thunder": ("thunder", "oklahoma", "okc", "trueno"),
    "timberwolves": ("timberwolves", "minnesota", "wolves", "lobos", "min"),
    "jazz": ("jazz", "utah", "uta"),
    "trail blazers": ("trail blazers", "blazers", "portland", "por"),
    "grizzlies": ("grizzlies", "memphis", "osos", "mem"),
    "pelicans": ("pelicans", "new orleans", "nueva orleans", "pelicanos", "nop"),
    "celtics": ("celtics", "boston", "bos"),
    "nets": ("nets", "brooklyn", "bkn"),
    "knicks": ("knicks", "new york", "nueva york", "nyk"),
    "76ers": ("76ers", "sixers", "philadelphia", "filadelfia", "phi"),
    "raptors": ("raptors", "toronto", "tor"),
    "bucks": ("bucks", "milwaukee", "ciervos", "mil"),
    "cavaliers": ("cavaliers", "cleveland", "cavs", "cle"),
    "pacers": ("pacers", "indiana", "ind"),
    "pistons": ("pistons", "detroit", "pistones", "det"),
    "heat": ("heat", "miami", "calor", "mia"),
    "magic": ("magic", "orlando", "magia", "orl"),
    "hawks": ("hawks", "atlanta", "halcones", "atl"),
    "hornets": ("hornets", "charlotte", "avispones", "cha"),
    "wizards": ("wizards", "washington", "magos", "was"),
}


def _norm(texto: Any) -> str:
    if texto is None:
        return ""
    s = unicodedata.normalize("NFKD", str(texto))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _numero(valor: Any, defecto: float = float("nan")) -> float:
    """Convierte valores del CSV sin dejar que NaN/None rompan el análisis."""
    try:
        if valor is None or pd.isna(valor):
            return defecto
        numero = float(str(valor).strip().replace(",", "."))
        return numero if np.isfinite(numero) else defecto
    except (TypeError, ValueError, OverflowError):
        return defecto


def _cargar_historial(historico: pd.DataFrame | None) -> pd.DataFrame:
    """Usa el historial entregado o el CSV habitual de la aplicación, si existe."""
    if isinstance(historico, pd.DataFrame):
        return historico
    try:
        return pd.read_csv(_HISTORIAL_FILE, encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError, pd.errors.ParserError, ValueError):
        return pd.DataFrame()


def _variantes_equipo(equipo: str) -> tuple[str, ...]:
    eq_norm = _norm(equipo)
    if not eq_norm:
        return ()
    for clave, variantes in _SINONIMOS_BOLETO.items():
        if clave in eq_norm or eq_norm in clave:
            return variantes
    return (eq_norm,)


def _equipo_en_texto(equipo: str, texto_norm: str, texto_raw: str = "") -> bool:
    if not texto_norm:
        return False
    # 1. Búsqueda normalizada (detecta palabras pegadas como "indianapacers")
    for variante in _variantes_equipo(equipo):
        if len(variante) >= 4 and variante in texto_norm:
            return True
    # 2. Búsqueda de siglas en mayúsculas en el texto crudo (ej. OKCvsIND, BKNvsMIN)
    if texto_raw:
        for variante in _variantes_equipo(equipo):
            if len(variante) == 3:
                sigla = variante.upper()
                if re.search(rf"(?<![A-Z]){sigla}(?![A-Z])", texto_raw):
                    return True
    return False


def _forma_reciente(
    equipo: str,
    fecha_partido: Any,
    historico: pd.DataFrame,
    max_partidos: int = 3,
) -> str:
    """Resume resultados anteriores disponibles; no inventa forma si faltan datos."""
    if historico.empty or not equipo:
        return ""

    requeridas = {"Fecha", "Local", "Visitante", "Puntaje_Local_Real", "Puntaje_Visita_Real"}
    if not requeridas.issubset(historico.columns):
        return ""

    fecha_actual = pd.to_datetime(fecha_partido, errors="coerce", utc=True)
    if pd.isna(fecha_actual):
        return ""

    equipo_norm = _norm(equipo)
    datos = historico.copy()
    datos["_fecha"] = pd.to_datetime(datos["Fecha"], errors="coerce", utc=True)
    datos = datos[datos["_fecha"].notna() & (datos["_fecha"] < fecha_actual)].copy()
    local_norm = datos["Local"].map(_norm)
    visita_norm = datos["Visitante"].map(_norm)
    datos = datos[(local_norm == equipo_norm) | (visita_norm == equipo_norm)].copy()
    if datos.empty:
        return ""

    datos["_pts_local"] = pd.to_numeric(datos["Puntaje_Local_Real"], errors="coerce")
    datos["_pts_visita"] = pd.to_numeric(datos["Puntaje_Visita_Real"], errors="coerce")
    datos = datos[datos["_pts_local"].notna() & datos["_pts_visita"].notna()].sort_values("_fecha", ascending=False)
    datos = datos.head(max_partidos)
    if datos.empty:
        return ""

    resumen: list[str] = []
    margenes: list[float] = []
    victorias = 0
    for _, juego in datos.iterrows():
        es_local = _norm(juego.get("Local")) == equipo_norm
        rival = str(juego.get("Visitante" if es_local else "Local", "rival"))
        a_favor = _numero(juego.get("_pts_local" if es_local else "_pts_visita"))
        en_contra = _numero(juego.get("_pts_visita" if es_local else "_pts_local"))
        if not np.isfinite(a_favor) or not np.isfinite(en_contra):
            continue
        margen = a_favor - en_contra
        victorias += int(margen > 0)
        margenes.append(margen)
        fecha = juego["_fecha"].strftime("%d/%m")
        resumen.append(f"{fecha} vs {rival}: {'ganó' if margen > 0 else 'perdió' if margen < 0 else 'empató'} por {abs(margen):.0f}")

    if not margenes:
        return ""
    media_margen = float(np.mean(margenes))
    etiqueta = "racha reciente positiva" if media_margen >= 5 else "resultados recientes parejos" if media_margen > -5 else "racha reciente negativa"
    return (
        f"Forma previa de {equipo}: {victorias}-{len(margenes) - victorias} en los últimos "
        f"{len(margenes)} juegos (margen medio {media_margen:+.1f}); {etiqueta}. "
        f"Últimos: {'; '.join(resumen[:2])}."
    )


def _contexto_partido(row: pd.Series, historico: pd.DataFrame) -> str:
    fecha = row.get("Fecha", row.get("Fecha_Clean", None))
    local = str(row.get("Local", ""))
    visitante = str(row.get("Visitante", ""))
    notas = [nota for nota in (
        _forma_reciente(local, fecha, historico),
        _forma_reciente(visitante, fecha, historico),
    ) if nota]
    return " ".join(notas)


def construir_parley_seguro(
    matchups: pd.DataFrame,
    max_picks: int = 3,
    historico: pd.DataFrame | None = None,
) -> list[dict[str, Any]]:
    """Prioriza selecciones con señal de modelo y añade contexto histórico verificable."""
    if max_picks <= 0 or matchups.empty:
        return []

    datos_historicos = _cargar_historial(historico)
    candidatos: list[dict[str, Any]] = []

    for _, row in matchups.iterrows():
        local = str(row.get("Local", "")).strip()
        visitante = str(row.get("Visitante", "")).strip()
        ganador = str(row.get("Pred_Ganador", "")).strip()
        prob = _numero(row.get("Prob_Ganador_Pct"), 0.0)
        linea = _numero(row.get("Line_Apuesta"))
        sim = _numero(row.get("Promedio_Simulado"))
        rec = re.sub(r"<[^>]+>", "", str(row.get("Recomendacion_Autonoma", "")))
        contexto = _contexto_partido(row, datos_historicos)
        sufijo_contexto = f" Contexto: {contexto}" if contexto else ""
        partido = f"{local} vs {visitante}"

        if np.isfinite(linea) and np.isfinite(sim) and 170 <= linea <= 270 and 170 <= sim <= 270:
            diferencia = sim - linea
            distancia = abs(diferencia)
            if distancia >= 6.5:
                tipo = "Altas (Over)" if diferencia > 0 else "Bajas (Under)"
                ajuste = min(3.0, max(1.0, round(distancia * 0.25, 1)))
                linea_objetivo = round(linea - ajuste if diferencia > 0 else linea + ajuste, 1)
                indice = min(75.0, 50.0 + distancia * 1.5)
                candidatos.append({
                    "partido": partido,
                    "seleccion": f"{tipo} — línea alternativa {linea_objetivo:.1f}",
                    "confianza": round(indice, 1),
                    "tipo": "Total alternativo",
                    "razon": (
                        f"Proyección {sim:.1f} frente a línea {linea:.1f} "
                        f"(diferencia de {distancia:.1f} pts). El ajuste reduce el margen requerido; "
                        f"normalmente implica menor cuota.{sufijo_contexto}"
                    ),
                })

        if 60 <= prob <= 100 and ganador in {local, visitante}:
            m_pick = re.search(
                r"Apuesta Recomendada[^:]*:\s*([^\n<]+)", rec,
                flags=re.IGNORECASE,
            )
            seleccion = re.sub(r"\s+", " ", m_pick.group(1)).strip(" .") if m_pick else ""
            if seleccion and any(_norm(equipo) in _norm(seleccion) for equipo in (local, visitante) if equipo):
                candidatos.append({
                    "partido": partido,
                    "seleccion": seleccion,
                    "confianza": round(min(prob, 75.0), 1),
                    "tipo": "Línea sugerida por el modelo",
                    "razon": (
                        f"El modelo favorece a {ganador} ({prob:.1f}%). Es un indicador, "
                        f"no una garantía; confirma hándicap, cuota y alineaciones.{sufijo_contexto}"
                    ),
                })
            elif prob >= 64:
                candidatos.append({
                    "partido": partido,
                    "seleccion": f"{ganador} Moneyline (ML)",
                    "confianza": round(min(prob, 75.0), 1),
                    "tipo": "Moneyline",
                    "razon": (
                        f"El modelo favorece a {ganador} ({prob:.1f}%). Compara la cuota con el "
                        f"riesgo; no se considera un pick seguro.{sufijo_contexto}"
                    ),
                })

    candidatos.sort(key=lambda item: item["confianza"], reverse=True)
    parley: list[dict[str, Any]] = []
    partidos_usados: set[str] = set()
    for item in candidatos:
        if item["partido"] in partidos_usados:
            continue
        parley.append(item)
        partidos_usados.add(item["partido"])
        if len(parley) >= max_picks:
            break
    return parley


@st.cache_resource(show_spinner=False)
def _cargar_lector_ocr():
    from rapidocr_onnxruntime import RapidOCR
    return RapidOCR()


def extraer_texto_captura(imagen_file) -> str:
    """Extrae el texto de una captura de boleto usando RapidOCR ligero en CPU."""
    img = Image.open(imagen_file).convert("RGB")
    if max(img.size) > 1100:
        img.thumbnail((1100, 1100), Image.Resampling.LANCZOS)
    img_np = np.array(img)
    engine = _cargar_lector_ocr()
    resultados, _ = engine(img_np)
    if not resultados:
        return ""
    lineas = [str(item[1]).strip() for item in resultados if len(item) >= 2 and str(item[1]).strip()]
    return "\n".join(lineas)


def auditar_parley_desde_texto(
    texto_ocr: str,
    matchups: pd.DataFrame,
    alertas_lesiones: list[dict[str, Any]],
    historico: pd.DataFrame | None = None,
) -> list[dict[str, str]]:
    """Cruza equipos, líneas reconocibles, forma reciente y alertas médicas."""
    texto_norm = _norm(texto_ocr)
    lineas_raw = [linea.strip() for linea in texto_ocr.splitlines() if linea.strip()]
    diagnosticos: list[dict[str, str]] = []
    datos_historicos = _cargar_historial(historico)

    equipos_lesionados: dict[str, list[str]] = {}
    for alerta in alertas_lesiones:
        if not isinstance(alerta, dict):
            continue
        equipo = _norm(alerta.get("equipo", ""))
        if equipo:
            equipos_lesionados.setdefault(equipo, []).append(
                f"{alerta.get('jugador', 'Jugador')} ({alerta.get('estatus', 'estatus desconocido')})"
            )

    for _, row in matchups.iterrows():
        local = str(row.get("Local", "")).strip()
        visitante = str(row.get("Visitante", "")).strip()
        loc_n, vis_n = _norm(local), _norm(visitante)
        if not (_equipo_en_texto(local, texto_norm, texto_ocr) or _equipo_en_texto(visitante, texto_norm, texto_ocr)):
            continue

        ganador = str(row.get("Pred_Ganador", "No disponible"))
        prob = _numero(row.get("Prob_Ganador_Pct"), float("nan"))
        linea = _numero(row.get("Line_Apuesta"))
        sim = _numero(row.get("Promedio_Simulado"))
        numeros_boleto: list[str] = []
        for linea_texto in lineas_raw:
            ln = _norm(linea_texto)
            asociado = _equipo_en_texto(local, ln, linea_texto) or _equipo_en_texto(visitante, ln, linea_texto)
            es_linea = any(k in ln.split() for k in (
                "handicap", "spread", "total", "over", "under", "altas", "bajas", "mas", "menos"
            )) or bool(re.search(r"(mas|menos|over|under)\s*\d", ln))
            if asociado or es_linea:
                numeros_boleto.extend(re.findall(r"[+-]?\d+(?:[.,]\d+)?", linea_texto))

        notas_lesiones: list[str] = []
        for equipo_norm in (loc_n, vis_n):
            if equipo_norm in equipos_lesionados:
                notas_lesiones.extend(equipos_lesionados[equipo_norm])

        estado = "CONSERVAR"
        consejo = (
            f"El modelo favorece a {ganador}"
            + (f" ({prob:.1f}%). " if np.isfinite(prob) else ". Datos de probabilidad no disponibles. ")
        )

        if np.isfinite(prob) and prob <= 60:
            estado = "AJUSTAR LÍNEA"
            consejo += (
                "Proyección de partido parejo: cualquiera puede ganar. No tomar el Moneyline como certeza; "
                "si consideras al no favorito, compara el hándicap positivo disponible y su cuota. "
                "El modelo no calcula aquí la probabilidad de cubrir ese hándicap. "
            )
        elif np.isfinite(prob) and prob < 64:
            estado = "AJUSTAR LÍNEA"
            consejo += "Ventaja moderada, no concluyente; revisa hándicap y cuota antes de decidir. "

        if numeros_boleto:
            consejo += f"Números detectados por OCR: {', '.join(numeros_boleto)}; verifica que sean la línea del juego y no la cuota u otro dato. "

        if np.isfinite(linea) and np.isfinite(sim) and 170 <= linea <= 270 and 170 <= sim <= 270:
            diferencia = sim - linea
            consejo += (
                f"Total de referencia {linea:.1f}, proyección {sim:.1f} "
                f"({abs(diferencia):.1f} pts hacia {'Over' if diferencia > 0 else 'Under' if diferencia < 0 else 'neutral'}). "
            )

        contexto = _contexto_partido(row, datos_historicos)
        if contexto:
            consejo += contexto + " El resultado previo es contexto, no garantía para este enfrentamiento. "

        if notas_lesiones:
            consejo += f"⚠️ Bajas reportadas: {'; '.join(notas_lesiones)}."

        diagnosticos.append({
            "partido": f"{local} vs {visitante}",
            "accion": estado,
            "detalle": consejo.strip(),
        })

    return diagnosticos
