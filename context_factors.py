def evaluar_factores_contextuales(equipo_local, equipo_visitante, modo_playoffs=False, 
                                  margen_juego_anterior_local=0, margen_juego_anterior_visita=0,
                                  b2b_local=False, b2b_visita=False):
    """
    Context Factory Avanzado: Evalúa fatiga (Back-to-Back), inercia de titulares, 
    teoría Zig-Zag para Playoffs y alertas de partidos trampa por rotación de banca.
    """
    csv_filename = ARCHIVO_TITULARES
    
    # Factores base predeterminados
    factor_local = 1.05    
    factor_visita = 0.98
    estabilidad = "Moderada (Base)"
    notas_contexto = []

    # 1. LÓGICA DE FATIGA Y BACK-TO-BACK (Partidos Trampa)
    # Si un equipo juega en días consecutivos, su banca suele tener más minutos y bajan su eficiencia defensiva/ofensiva
    if b2b_local:
        factor_local *= 0.93  # Castigo por fatiga acumulada al local
        notas_contexto.append("⚠️ Alerta B2B: Local en Back-to-Back (Riesgo de rotación/fatiga).")
    
    if b2b_visita:
        factor_visita *= 0.94 # Castigo por fatiga acumulada a la visita
        notas_contexto.append("⚠️ Alerta B2B: Visita en Back-to-Back (Riesgo de rotación/fatiga).")

    # 2. Lógica de Playoffs - Teoría Zig-Zag (Rebote tras derrota por paliza)
    if modo_playoffs:
        notas_contexto.append("Modo Playoffs activo (Rotaciones cortadas).")
        if margen_juego_anterior_local <= -15:
            factor_local *= 1.08  # Súper motivación / Ajuste táctico tras ser humillados
            notas_contexto.append("Zig-Zag aplicado: Gran rebote esperado para el Local tras paliza.")
        elif margen_juego_anterior_local >= 15:
            factor_local *= 0.95  # Exceso de confianza en el siguiente partido
            factor_visita *= 1.08
            notas_contexto.append("Zig-Zag aplicado: Rebote esperado para la Visita tras paliza.")

    # 3. Validación histórica con CSV de Titulares
    if os.path.exists(csv_filename):
        try:
            df = pd.read_csv(csv_filename, encoding='utf-8-sig')
            df['Equipo_Clean'] = df['Equipo'].apply(normalizar_texto)
            loc_clean = normalizar_texto(equipo_local)
            vis_clean = normalizar_texto(equipo_visitante)
            
            df_loc = df[df['Equipo_Clean'].str.contains(loc_clean, na=False)]
            df_vis = df[df['Equipo_Clean'].str.contains(vis_clean, na=False)]
            
            if not df_loc.empty and not df_vis.empty:
                estabilidad = "Alta (Validada con CSV)"
                factor_local *= 1.01 
                factor_visita *= 0.99
            else:
                estabilidad = "Estándar (Fase de calibración)"
        except Exception as e:
            estabilidad = "Error lectura CSV"
            notas_contexto.append(f"Excepción CSV: {str(e)}")

    nota_final = " | ".join(notas_contexto) if notas_contexto else "Factores contextuales estándar ponderados."

    return {
        "factor_local": round(factor_local, 3),
        "factor_visita": round(factor_visita, 3),
        "estabilidad_dupla": estabilidad,
        "impacto_lesiones": "Evaluación Oficial activa",
        "nota_analitica": nota_final,
        "alerta_trampa": True if (b2b_local or b2b_visita) else False
    }
