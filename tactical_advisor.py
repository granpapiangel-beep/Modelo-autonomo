from __future__ import annotations

import re
import unicodedata
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image


def _norm(texto: Any) -> str:
    if texto is None:
        return ""
    s = unicodedata.normalize("NFKD", str(texto))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def construir_parley_seguro(matchups: pd.DataFrame, max_picks: int = 3) -> list[dict[str, Any]]:
    """
    Construye un parley conservador priorizando:
    1) Totales (Over/Under) con divergencia >= 7.5 pts y margen ajustado.
    2) Moneyline seguro o Hándicap con colchón comprobado.
    """
    candidatos: list[dict[str, Any]] = []

    for _, row in matchups.iterrows():
        local = str(row.get("Local", ""))
        visitante = str(row.get("Visitante", ""))
        ganador = str(row.get("Pred_Ganador", ""))
        prob = float(row.get("Prob_Ganador_Pct", 0) or 0)
        linea = float(row.get("Line_Apuesta", 0) or 0)
        sim = float(row.get("Promedio_Simulado", 0) or 0)
        rec = re.sub(r"<[^>]+>", "", str(row.get("Recomendacion_Autonoma", "")))

        # 1. Prioridad máxima: Totales con divergencia fuerte
        diff_ou = abs(sim - linea)
        if linea > 0 and sim > 0 and diff_ou >= 7.5:
            tipo_ou = "Altas (Over)" if sim > linea else "Bajas (Under)"
            linea_segura = round(linea - 3.5, 1) if sim > linea else round(linea + 3.5, 1)
            score_ou = min(92.0, 68.0 + diff_ou * 1.6)
            candidatos.append({
                "partido": f"{local} vs {visitante}",
                "seleccion": f"{tipo_ou} {linea_segura}",
                "confianza": round(score_ou, 1),
                "tipo": "Totales (Alta Efectividad)",
                "razon": f"Proyección ({sim:.1f} pts) diverge {diff_ou:.1f} pts de la línea ({linea:.1f}).",
            })

        # 2. Picks de lado (Moneyline / Hándicap Protegido / Hándicap Seguro con Edge)
        if prob >= 62.0 and ganador in (local, visitante):
            m_pick = re.search(r"Apuesta Recomendada[^:]*:\s*([^\(\n]+(?:\([A-Za-z0-9+.\-]+\))?)", rec)
            if m_pick:
                seleccion = m_pick.group(1).strip()
                es_handicap_negativo = bool(re.search(r"\(-\d+", seleccion))
                score_lado = prob - (6.0 if es_handicap_negativo else 0.0)
                if score_lado >= 60.0:
                    candidatos.append({
                        "partido": f"{local} vs {visitante}",
                        "seleccion": seleccion,
                        "confianza": round(score_lado, 1),
                        "tipo": "Línea / Moneyline",
                        "razon": f"Respaldo estadístico de {prob:.1f}% con línea ajustada al margen proyectado.",
                    })

    candidatos.sort(key=lambda x: x["confianza"], reverse=True)
    parley: list[dict[str, Any]] = []
    partidos_usados: set[str] = set()
    for item in candidatos:
        if item["partido"] not in partidos_usados:
            parley.append(item)
            partidos_usados.add(item["partido"])
        if len(parley) >= max_picks:
            break
    return parley


@st.cache_resource(show_spinner=False)
def _cargar_lector_ocr():
    import easyocr
    return easyocr.Reader(["es", "en"], gpu=False)


def extraer_texto_captura(imagen_file) -> str:
    """Extrae el texto de una captura de boleto usando EasyOCR."""
    img = Image.open(imagen_file).convert("RGB")
    img_np = np.array(img)
    reader = _cargar_lector_ocr()
    resultados = reader.readtext(img_np, detail=0)
    return "\n".join(resultados)


def auditar_parley_desde_texto(
    texto_ocr: str,
    matchups: pd.DataFrame,
    alertas_lesiones: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Cruza los equipos y líneas detectados en la captura contra las proyecciones del modelo."""
    texto_norm = _norm(texto_ocr)
    lineas_raw = [l.strip() for l in texto_ocr.splitlines() if l.strip()]
    diagnosticos: list[dict[str, str]] = []

    equipos_lesionados: dict[str, list[str]] = {}
    for a in alertas_lesiones:
        if not isinstance(a, dict):
            continue
        eq = _norm(a.get("equipo", ""))
        if eq:
            equipos_lesionados.setdefault(eq, []).append(f"{a.get('jugador')} ({a.get('estatus')})")

    for _, row in matchups.iterrows():
        local = str(row.get("Local", ""))
        visitante = str(row.get("Visitante", ""))
        loc_n, vis_n = _norm(local), _norm(visitante)

        if (loc_n and loc_n in texto_norm) or (vis_n and vis_n in texto_norm):
            ganador = str(row.get("Pred_Ganador", ""))
            prob = float(row.get("Prob_Ganador_Pct", 0) or 0)
            linea = float(row.get("Line_Apuesta", 0) or 0)
            sim = float(row.get("Promedio_Simulado", 0) or 0)

            numeros_boleto: list[str] = []
            for l in lineas_raw:
                ln = _norm(l)
                if loc_n in ln or vis_n in ln or any(
                    k in ln for k in ("handicap", "spread", "total", "mas", "menos", "over", "under", "altas", "bajas")
                ):
                    nums = re.findall(r"[+-]?\d+\.\d+|[+-]\d+", l)
                    numeros_boleto.extend(nums)

            bajas_txt: list[str] = []
            for eq_key in (loc_n, vis_n):
                if eq_key in equipos_lesionados:
                    bajas_txt.append(", ".join(equipos_lesionados[eq_key]))

            estado = "CONSERVAR"
            consejo = f"El modelo respalda a <b>{ganador}</b> ({prob:.1f}%). "

            if prob < 56.0:
                estado = "QUITAR"
                consejo = f"Partido demasiado volátil ({prob:.1f}%). Conviene sacarlo del parley."
            elif numeros_boleto:
                consejo += f"Líneas detectadas: <b>{', '.join(numeros_boleto)}</b>. "
                if any(12.0 <= abs(float(n)) < 50.0 for n in numeros_boleto):
                    estado = "AJUSTAR LÍNEA"
                    consejo += "Hándicap muy largo; conviene bajar 4-5 puntos para asegurar el cobro."
                elif linea > 0 and sim > 0:
                    tendencia = "Altas (Over)" if sim > linea else "Bajas (Under)"
                    consejo += f"En totales el modelo proyecta <b>{sim:.1f}</b> (tendencia a <b>{tendencia}</b> vs {linea:.1f})."

            if bajas_txt:
                consejo += f" ⚠️ Bajas reportadas: {'; '.join(bajas_txt)}."

            diagnosticos.append({
                "partido": f"{local} vs {visitante}",
                "accion": estado,
                "detalle": consejo,
            })

    return diagnosticos
