from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st


# Paths are relative to the app's working directory, as in the original app.
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
    </style>
    """,
    unsafe_allow_html=True,
)


def safe_text(value: Any, default: str = "N/A") -> str:
    """Return readable text for CSV/JSON values without exposing null markers."""
    if value is None or pd.isna(value):
        return default
    text = str(value).strip()
    return text if text and text.lower() not in {"nan", "none", "null"} else default


def safe_float(value: Any, default: float = float("nan")) -> float:
    """Convert common numeric strings safely, rejecting infinities and NaN."""
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


@st.cache_data(ttl=300, show_spinner=False)
def load_csv(path: str, modified_at: float) -> tuple[pd.DataFrame, str | None]:
    """Read a CSV safely; modified_at makes file updates invalidate the cache."""
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
    """Find a column by normalized name, including common variants."""
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

    results: list[tuple[str, float, str, str]] = []
    for _, row in players.iterrows():
        row_team = normalize_name(row.get(team_column))
        if not row_team or (search_team not in row_team and row_team not in search_team):
            continue

        points: list[float] = []
        for column in players.columns:
            # Keep compatibility with the source file's daily cells such as "24 pts";
            # also accept numeric columns explicitly named as points.
            cell = row.get(column)
            if "pts" not in normalize_name(column) and "pt" not in str(cell).lower():
                continue
            number = safe_float(cell)
            if np.isfinite(number) and 0 <= number <= 100:
                points.append(number)
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
        results.append((safe_text(row.get(player_column), "Desconocido"), round(average, 1), pattern, signal))

    results.sort(key=lambda item: item[1], reverse=True)
    return results[:6]


def date_sort_key(value: Any) -> pd.Timestamp:
    return pd.to_datetime(safe_text(value, ""), errors="coerce", utc=True)


def show_players(team: str, patterns: list[tuple[str, float, str, str]]) -> None:
    st.markdown(f"**{team} — jugadores destacados**")
    if not patterns:
        st.caption("Sin registros de jugadores para este equipo.")
        return
    for name, average, pattern, _signal in patterns:
        st.write(f"**{name}** · {average:.1f} pts de promedio · {pattern}")


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
    st.caption("v 4.0 | Panel de análisis")
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

# Normalize columns needed by the dashboard and tolerate incomplete historical rows.
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

    # Ignore implausible totals and avoid inventing a pick when the line is missing.
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
        st.write(recommendation)

        home_players = player_patterns(str(PLAYERS_FILE), players_mtime, home)
        away_players = player_patterns(str(PLAYERS_FILE), players_mtime, away)
        player_left, player_right = st.columns(2)
        with player_left:
            show_players(home, home_players)
        with player_right:
            show_players(away, away_players)
        st.divider()
