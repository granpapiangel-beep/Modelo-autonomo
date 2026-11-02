# context_factors.py
# Módulo para evaluar fatiga, descanso (back-to-back) y motivación contextual


def calcular_factor_psicologico(
    equipo, rival, descansa_ayer_equipo, urgencia_tabla_equipo
):
  """Calcula un multiplicador de ajuste basado en el comportamiento humano,

  descanso y contexto competitivo (tanking / urgencia).
  """
  factor_ajuste = 1.0
  consejo_psicologico = ""

  # 1. Factor Fatiga / Back-to-Back (jugaron ayer)
  if descansa_ayer_equipo:
    factor_ajuste -= 0.04  # Reduce un 4% de rendimiento esperado por fatiga física
    consejo_psicologico = (
        "⚠️ Alerta de Fatiga: Equipo en situación de 'Back-to-Back' (jugaron"
        " ayer); posible rotación o bajón físico en el último cuarto."
    )

  # 2. Factor Motivación / Urgencia en la tabla
  if urgencia_tabla_equipo == "Eliminado_Sin_Incentivo":
    factor_ajuste -= (
        0.06  # Desmotivación importante (posible tanking o descanso de estrellas)
    )
    consejo_psicologico = (
        "🚨 Factor 'Libre Albedrío' / Tanking: El equipo ya no pelea playoffs;"
        " alto riesgo de descanso de jugadores estelares."
    )
  elif urgencia_tabla_equipo == "Urgido_Playoffs":
    factor_ajuste += (
        0.03  # Impulso anímico por urgencia de clasificar o asegurar posición
    )
    consejo_psicologico = (
        "🔥 Alta Motivación: Equipo necesitado de victoria; jugarán con intensidad"
        " máxima de postemporada."
    )

  if not consejo_psicologico:
    consejo_psicologico = (
        "⚖️ Contexto Estándar: Comportamiento competitivo normal sin alertas"
        " psicológicas de peso."
    )

  return factor_ajuste, consejo_psicologico
