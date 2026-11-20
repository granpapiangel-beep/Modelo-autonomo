from __future__ import annotations

import html
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

from tactical_advisor import (
    auditar_parley_desde_texto,
    construir_parley_seguro,
    extraer_texto_captura,
)

EVALUATIONS_FILE = Path("historial_evaluaciones_nba.csv")
PLAYERS_FILE = Path("Titulares_NBA_Oficiales_30_Equipos(Puntajes Diarios).csv")
INJURIES_FILE = Path("alertas_lesiones.json")
LOGO_FILE = Path("Logo de stephy.png")

st.set_page_config(
    page_title="NBA AI Stephy | Analytics",
    page_icon=str(LOGO_FILE) if LOGO_FILE.is_file() else "🏀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .stApp { background-color: #0E1117; color: #E2E8F0; }
      section[data-testid="stSidebar"] { background-color: #111827; }
      [data-testid="stMetricValue"] { color: #F8FAFC; font-weight: 800; }
      [data-testid="stMetricLabel"] { color: #94A3B8; }
      .main-title { font-size: clamp(2rem, 5vw, 3rem); font-weight: 800;
        background: linear-gradient(45deg, #FF4B4B, #FF8C00);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
      .sub-title { color: #94A3B8; margin-top: -1rem; }
      .radar { width: 76px; height: 76px; margin: 18px auto; position: relative; }
      .radar:before, .radar:after { content: ""; position: absolute; inset: 0;
        border: 2px solid #FF4B4B; border-radius: 50%; animation: pulse 2s linear infinite; }
      .radar:after { border-color: #FF8C00; animation-delay: 1s; }
      @keyframes pulse { from { transform: scale(.2); opacity: 1; }
        to { transform: scale(1.45); opacity: 0; } }
      @media (prefers-reduced-motion: reduce) { .radar:before, .radar:after { animation: none; } }

      /* Tarjetas de Nota del Modelo */
      .note-card {
        background-color: #161B26;
        border: 1px solid #263042;
        border-radius: 10px;
        padding: 14px 16px;
        margin: 8px 0 16px 0;
        display: flex;
        flex-direction: column;
        gap: 10px;
      }
      .note-item {
        padding: 10px 14px;
        border-radius: 8px;
        font-size: 0.95rem;
        line-height: 1.45;
        border-left: 4px solid #64748B;
        background-color: #1E2534;
        color: #E2E8F0;
      }
      .note-item b { color: #FFFFFF; font-weight: 700; }
      .note-analysis { border-left-color: #38BDF8; background-color: rgba(56, 189, 248, 0.08); }
      .note-pick { border-left-color: #10B981; background-color: rgba(16, 185, 129, 0.12); }
      .note-pick b { color: #6EE7B7; }
      .note-total { border-left-color: #F59E0B; background-color: rgba(245, 158, 11, 0.12); }
      .note-total b { color: #FCD34D; }
      .note-avoid { border-left-color: #EF4444; background-color: rgba(239, 68, 68, 0.12); }
      .note-avoid b { color: #FCA5A5; }

      /* Badges de jugadores */
      .player-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 6px 10px;
        margin-bottom: 6px;
        border-radius: 6px;
        background-color: #161B26;
        border: 1px solid #232B3A;
        font-size: 0.9rem;
      }
      .badge-signal {
        font-size: 0.75rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 999px;
        text-transform: uppercase;
      }
      .sig-VERDE { background-color: rgba(16, 185, 129, 0.18); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.4); }
      .sig-AMARILLO { background-color: rgba(245, 158, 11, 0.18); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.4); }
      .sig-ROJO { background-color: rgba(239, 68, 68, 0.18); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.4); }

      /* Tarjetas del Asesor de Parleys */
      .parley-box {
        background-color: #131822;
        border: 1px solid #2A3548;
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 10px;
      }
      .parley-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
      }
      .tag-CONSERVAR { background: rgba(16, 185, 129, 0.2); color: #34D399; padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 0.78rem; }
      .tag-AJUSTAR { background: rgba(245, 158, 11, 0.2); color: #FBBF24; padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 0.78rem; }
      .tag-QUITAR { background: rgba(239, 68, 68, 0.2); color: #F87171; padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 0.78rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def safe_text(value: Any, default: str = "N/A") -> str:
    if value is None or pd.isna(value):
        return default
    text = str(value).strip()
    return text if text and text.lower() not in {"nan", "none", "null"} else default


def safe_float(value: Any, default: float = float("nan")) -> float:
    if value is None:
        return default
    try:
        text = str(value).strip().lower().replace(",", ".")
        text = re.sub(r"\s*(pts|pt|%)\s*$", "", text)
        number = float(text)
        return number if np.isfinite(number) else default
    except (TypeError, ValueError, OverflowError):
        return default


def normalize_name(value: Any) -> str:
    text = safe_text(value, "")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def sanitize_inline_html(raw_html: str) -> str:
    escaped = html.escape(raw_html)
    for tag in ("b", "i", "strong", "em"):
        escaped = re.sub(rf"&lt;{tag}&gt;", f"<{tag}>", escaped, flags=re.IGNORECASE)
        escaped = re.sub(rf"&lt;/{tag}&gt;", f"</{tag}>", escaped, flags=re.IGNORECASE)
    return escaped


def render_model_note(recommendation: str) -> None:
    parts = [p.strip() for p in re.split(r"<br\s*/?>", recommendation, flags=re.IGNORECASE) if p.strip()]
    if not parts:
        st.caption("Sin recomendación disponible.")
        return

    blocks_html: list[str] = ['<div class="note-card">']
    for part in parts:
        clean_part = re.sub(r"^•\s*", "", part)
        lower_part = normalize_name(re.sub(r"<[^>]+>", "", clean_part))

        if "veredicto" in lower_part or "no meterle" in lower_part or "volatil" in lower_part:
            css_class = "note-avoid"
        elif "apuesta recomendada" in lower_part:
            css_class = "note-pick"
        elif "alternativa totales" in lower_part:
            css_class = "note-total"
        elif "analisis" in lower_part:
            css_class = "note-analysis"
        else:
            css_class = ""

        safe_line = sanitize_inline_html(clean_part)
        blocks_html.append(f'<div class="note-item {css_class}">{safe_line}</div>')

    blocks_html.append("</div>")
    st.markdown("".join(blocks_html), unsafe_allow_html=True)


@st.cache_data(ttl=300, show_spinner=False)
def load_csv(path: str, modified_at: float) -> tuple[pd.DataFrame, str | None]:
    del modified_at
    try:
        return pd.read_csv(path, encoding="utf-8-sig"), None
    except FileNotFoundError:
        return pd.DataFrame(), f"No se encontró el archivo {Path(path).name}."
    except (OSError, UnicodeDecodeError, pd.errors.ParserError, ValueError) as exc:
        return pd.DataFrame(), f"No se pudo leer {Path(path).name}: {exc}"


def cached_csv(path: Path) -> tuple[pd.DataFrame, str | None]:
    try:
        modified_at = path.stat().st_mtime
    except OSError:
        modified_at = 0.0
    return load_csv(str(path), modified_at)


def load_injuries(path: Path) -> tuple[dict[str, Any], str | None]:
    if not path.is_file():
        return {"mensaje_general": "Sin bajas críticas registradas.", "alertas_criticas": []}, None
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            raise ValueError("El contenido debe ser un objeto JSON.")
        alerts = data.get("alertas_criticas", [])
        data["alertas_criticas"] = alerts if isinstance(alerts, list) else []
        return data, None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return {"mensaje_general": "No se pudieron cargar las alertas.", "alertas_criticas": []}, str(exc)


def find_column(df: pd.DataFrame, *terms: str) -> Any | None:
    for column in df.columns:
        normalized = normalize_name(column).replace(" ", "_")
        if any(term in normalized for term in terms):
            return column
    return None


@st.cache_data(ttl=300, show_spinner=False)
def player_patterns(path: str, modified_at: float, team: str) -> list[tuple[str, float, str, str]]:
    del modified_at
    try:
        players = pd.read_csv(path, encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError, pd.errors.ParserError, ValueError):
        return []
    if players.empty or len(players.columns) < 3:
        return []

    players.columns = [str(column).strip().strip("'\" ") for column in players.columns]
    team_column = find_column(players, "equipo", "team") or players.columns[0]
    player_column = find_column(players, "jugador", "player") or players.columns[2]
    search_team = normalize_name(team)
    if not search_team:
        return []

    # Agrupar por jugador para evitar duplicados cuando cambia de posición
    grouped_points: dict[str, tuple[str, list[float]]] = {}
    for _, row in players.iterrows():
        row_team = normalize_name(row.get(team_column))
        if not row_team or (search_team not in row_team and row_team not in search_team):
            continue

        raw_name = safe_text(row.get(player_column), "Desconocido")
        norm_player = normalize_name(raw_name)
        if not norm_player:
            continue

        for column in players.columns:
            cell = row.get(column)
            if "pts" not in normalize_name(column) and "pt" not in str(cell).lower():
                continue
            number = safe_float(cell)
            if np.isfinite(number) and 0 <= number <= 100:
                if norm_player not in grouped_points:
                    grouped_points[norm_player] = (raw_name, [])
                grouped_points[norm_player][1].append(number)

    results: list[tuple[str, float, str, str]] = []
    for display_name, points in grouped_points.values():
        if not points:
            continue
        average = float(np.mean(points))
        deviation = float(np.std(points)) if len(points) > 1 else 1.0
        if average >= 18 and deviation < 6:
            pattern, signal = "Estrella", "VERDE"
        elif average >= 12:
            pattern, signal = "Estable", "VERDE"
        elif deviation >= 7:
            pattern, signal = "Volátil", "ROJO"
        else:
            pattern, signal = "Rotación", "AMARILLO"
        results.append((display_name, round(average, 1), pattern, signal))

    results.sort(key=lambda item: item[1], reverse=True)
    return results[:6]


def date_sort_key(value: Any) -> pd.Timestamp:
    return pd.to_datetime(safe_text(value, ""), errors="coerce", utc=True)


def show_players(team: str, patterns: list[tuple[str, float, str, str]]) -> None:
    st.markdown(f"**{team} — jugadores destacados**")
    if not patterns:
        st.caption("Sin registros de jugadores para este equipo.")
        return
    rows_html: list[str] = []
    for name, average, pattern, signal in patterns:
        safe_name = html.escape(name)
        safe_pattern = html.escape(pattern)
        sig_class = signal if signal in {"VERDE", "AMARILLO", "ROJO"} else "AMARILLO"
        rows_html.append(
            f'<div class="player-row">'
            f'<span><strong>{safe_name}</strong> · <span style="color:#94A3B8;">{average:.1f} pts</span></span>'
            f'<span class="badge-signal sig-{sig_class}">{safe_pattern}</span>'
            f'</div>'
        )
    st.markdown("".join(rows_html), unsafe_allow_html=True)


# Header
st.markdown('<p class="main-title">🏀 NBA AI Stephy</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Panel de análisis estadístico y proyecciones NBA.</p>', unsafe_allow_html=True)
st.caption("Las proyecciones son estimaciones estadísticas; no garantizan resultados ni constituyen asesoría financiera.")

with st.sidebar:
    if LOGO_FILE.is_file():
        st.image(str(LOGO_FILE), use_container_width=True)
    st.markdown("### 📡 Monitor IA Stephy")
    st.markdown('<div class="radar" aria-hidden="true"></div>', unsafe_allow_html=True)
    st.info("Monitoreo de datos activo")
    st.caption("v 4.1 | Panel de análisis & Asesor")
    if st.button("↻ Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    injury_data, injury_error = load_injuries(INJURIES_FILE)
    st.markdown("---")
    st.markdown(f"**Última actualización médica:** {safe_text(injury_data.get('ultima_actualizacion'))}")
    if injury_error:
        st.warning(f"No se pudieron cargar las alertas médicas: {injury_error}")
    alerts = injury_data.get("alertas_criticas", [])
    if alerts:
        st.markdown("#### 🏥 Bajas confirmadas")
        for alert in alerts:
            if not isinstance(alert, dict):
                continue
            with st.container():
                st.warning(
                    f"**{safe_text(alert.get('jugador'), 'Jugador')}** ({safe_text(alert.get('equipo'), 'Equipo')})\n\n"
                    f"Motivo: {safe_text(alert.get('motivo'), 'Lesión')} · "
                    f"Regreso: {safe_text(alert.get('fecha_regreso'))} · "
                    f"Estado: {safe_text(alert.get('estatus'), 'N/A')}"
                )
    else:
        st.success(safe_text(injury_data.get("mensaje_general"), "Sin bajas críticas."))


df, load_error = cached_csv(EVALUATIONS_FILE)
if load_error:
    st.warning(load_error)

if df.empty:
    st.info("Esperando datos de evaluaciones. Cuando el bot genere el historial, aparecerán aquí los encuentros.")
    st.stop()

if "Fecha" not in df.columns:
    st.error("El historial no contiene la columna requerida 'Fecha'.")
    st.stop()
for column, default in {
    "Local": "Local", "Visitante": "Visitante", "Pred_Ganador": "N/A",
    "Prob_Ganador_Pct": np.nan, "Line_Apuesta": np.nan,
    "Promedio_Simulado": np.nan, "Semaforo_Puntos": "Estándar",
    "Semaforo_Ganador": "", "Recomendacion_Autonoma": "Sin recomendación disponible.",
}.items():
    if column not in df.columns:
        df[column] = default

df["Fecha_Clean"] = df["Fecha"].map(lambda value: safe_text(value, ""))
df = df[df["Fecha_Clean"] != ""].copy()
if df.empty:
    st.info("No hay filas con una fecha válida en el historial.")
    st.stop()

df["Prob_Ganador_Pct"] = pd.to_numeric(df["Prob_Ganador_Pct"], errors="coerce").clip(0, 100)
df["Line_Apuesta"] = pd.to_numeric(df["Line_Apuesta"], errors="coerce")
df["Promedio_Simulado"] = pd.to_numeric(df["Promedio_Simulado"], errors="coerce")
unique_dates = df["Fecha_Clean"].drop_duplicates().tolist()
unique_dates.sort(key=lambda value: (pd.isna(date_sort_key(value)), date_sort_key(value), value))

selected_date = st.selectbox("Jornada", unique_dates, index=len(unique_dates) - 1)
matchups = df[df["Fecha_Clean"] == selected_date].copy()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Encuentros", len(matchups))
mean_probability = matchups["Prob_Ganador_Pct"].mean()
c2.metric("Probabilidad media", f"{mean_probability:.1f}%" if pd.notna(mean_probability) else "N/D")
c3.metric("Jornada", selected_date)
c4.metric("Estado", "Datos cargados")

# ==============================================================================
# SECCIÓN ASESOR DE PARLEYS Y ESCÁNER DE CAPTURAS
# ==============================================================================
with st.expander("🎯 Asesor Táctico: Armar Parley Seguro o Revisar Captura de Apuesta", expanded=False):
    tab_builder, tab_scanner = st.tabs(["🎲 Parley Seguro Sugerido", "📸 Auditar mi Captura de Boleto"])

    with tab_builder:
        num_picks = st.slider("Cantidad de selecciones en el parley", min_value=2, max_value=4, value=3)
        parley_sugerido = construir_parley_seguro(matchups, max_picks=num_picks)
        if not parley_sugerido:
            st.info("No hay suficientes selecciones de alta confianza en esta jornada para armar un parley seguro.")
        else:
            for idx, leg in enumerate(parley_sugerido, start=1):
                st.markdown(
                    f"""
                    <div class="parley-box">
                      <div class="parley-header">
                        <span><strong>#{idx} · {html.escape(leg['partido'])}</strong></span>
                        <span class="tag-CONSERVAR">Confianza {leg['confianza']}%</span>
                      </div>
                      <div style="color:#6EE7B7; font-weight:700; font-size:1rem;">👉 {html.escape(leg['seleccion'])}</div>
                      <div style="color:#94A3B8; font-size:0.86rem; margin-top:4px;">{html.escape(leg['razon'])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with tab_scanner:
        st.caption("Sube la captura de pantalla de tu parley o apuesta (PNG/JPG) para cruzarla con las proyecciones y lesiones del día.")
        uploaded_ticket = st.file_uploader("Sube tu captura aquí", type=["png", "jpg", "jpeg"])
        if uploaded_ticket is not None:
            col_img, col_res = st.columns([1, 1.4])
            with col_img:
                st.image(uploaded_ticket, caption="Boleto cargado", use_container_width=True)
            with col_res:
                with st.spinner("Leyendo boleto y cruzando estadísticas..."):
                    try:
                        texto_detectado = extraer_texto_captura(uploaded_ticket)
                        diagnosticos = auditar_parley_desde_texto(texto_detectado, matchups, alerts)
                        if not diagnosticos:
                            st.warning("No se identificaron equipos de la jornada seleccionada en la imagen. Asegúrate de haber elegido la fecha correcta arriba.")
                        else:
                            for diag in diagnosticos:
                                accion = diag["accion"]
                                tag_cls = "tag-CONSERVAR" if accion == "CONSERVAR" else ("tag-AJUSTAR" if "AJUSTAR" in accion else "tag-QUITAR")
                                st.markdown(
                                    f"""
                                    <div class="parley-box">
                                      <div class="parley-header">
                                        <strong>{html.escape(diag['partido'])}</strong>
                                        <span class="{tag_cls}">{html.escape(accion)}</span>
                                      </div>
                                      <div style="color:#E2E8F0; font-size:0.9rem; margin-top:4px;">{sanitize_inline_html(diag['detalle'])}</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                        with st.expander("Ver texto crudo detectado en la imagen"):
                            st.text(texto_detectado)
                    except Exception as exc:
                        st.error(f"Error procesando la captura: {exc}")

st.divider()

try:
    players_mtime = PLAYERS_FILE.stat().st_mtime
except OSError:
    players_mtime = 0.0

for _, row in matchups.iterrows():
    home = safe_text(row.get("Local"), "Local")
    away = safe_text(row.get("Visitante"), "Visitante")
    winner = safe_text(row.get("Pred_Ganador"))
    probability = safe_float(row.get("Prob_Ganador_Pct"), float("nan"))
    line = safe_float(row.get("Line_Apuesta"), float("nan"))
    simulated = safe_float(row.get("Promedio_Simulado"), float("nan"))

    if not np.isfinite(line) or not 100 <= line <= 350:
        safe_line = None
        projected_total = None
        st.warning(f"{home} vs {away}: línea de apuesta ausente o fuera de rango; se omite Over/Under.")
    else:
        safe_line = line
        projected_total = simulated if np.isfinite(simulated) and 170 <= simulated <= 270 else safe_line

    status_points = safe_text(row.get("Semaforo_Puntos"), "Estándar")
    status_winner = safe_text(row.get("Semaforo_Ganador"), "Sin indicador")
    recommendation = safe_text(row.get("Recomendacion_Autonoma"), "Sin recomendación disponible.")

    with st.container():
        st.markdown(f"### 🏀 {home} vs {away}")
        left, right = st.columns(2)
        with left:
            st.markdown("**Moneyline — proyección**")
            confidence_text = f" · {probability:.1f}%" if np.isfinite(probability) else ""
            st.write(f"🏆 {winner}{confidence_text}")
            st.caption(f"Indicador: {status_winner}")
        with right:
            st.markdown("**Total de puntos**")
            if safe_line is None or projected_total is None:
                st.write("Proyección no disponible")
            else:
                pick = "OVER (Altas)" if projected_total > safe_line else "UNDER (Bajas)"
                st.write(f"{pick} · línea {safe_line:.1f} · proyección {projected_total:.1f}")
            st.caption(f"{status_points}")

        st.markdown("**Nota del modelo**")
        render_model_note(recommendation)

        home_players = player_patterns(str(PLAYERS_FILE), players_mtime, home)
        away_players = player_patterns(str(PLAYERS_FILE), players_mtime, away)
        player_left, player_right = st.columns(2)
        with player_left:
            show_players(home, home_players)
        with player_right:
            show_players(away, away_players)
        st.divider()
