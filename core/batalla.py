"""
batalla.py
==========
Resolucion de batallas. El metodo numerico ya hizo su trabajo ANTES de llegar
aqui: prediccion.predecir() le mostro al jugador cuantas tropas tendra segun
Euler y segun RK4. Con esa informacion el jugador decide cuantas tropas
comprometer. Esta funcion resuelve el choque y registra el resultado junto con
las dos predicciones, para poder analizar despues si confiar en una prediccion
imprecisa (Euler con h grande) llevo a una mala decision.

Resolucion: se comparan las FUERZAS efectivas. El defensor suma su bono de
defensa (por ejemplo, el de la Marcha en la UES). Hay un factor de azar
opcional que imita los dados del Risk clasico; con factor_azar=0 el resultado
es determinista y facil de explicar.
"""

import random


def resolver(estado, origen, defensor, tropas_comprometidas,
             prediccion=None, metodo_confiado="rk4", factor_azar=0.0,
             factor_atacante=1.0,
             repo=None, partida_id=None, turno=None):
    """
    origen, defensor : Territorio
    tropas_comprometidas : cuantas tropas envia el atacante desde 'origen'
    prediccion : dict {'euler':..., 'rk4':...} que se mostro al jugador (se guarda)
    factor_atacante : multiplicador de la fuerza de ataque (p. ej. la
        penalizacion por zona de estabilidad cuando se confio en Euler con h grande)
    """
    # No se puede comprometer mas tropas de las disponibles; siempre queda al
    # menos 1 defendiendo el territorio de origen.
    disponible = origen.tropas["poblacion_actual"]
    comprometidas = min(float(tropas_comprometidas), max(0.0, disponible - 1.0))

    pob_def = defensor.tropas["poblacion_actual"]
    fuerza_atacante = comprometidas * factor_atacante
    fuerza_defensor = pob_def + defensor.bono_defensa

    if factor_azar > 0:
        fuerza_atacante *= random.uniform(1 - factor_azar, 1 + factor_azar)
        fuerza_defensor *= random.uniform(1 - factor_azar, 1 + factor_azar)

    # Las tropas comprometidas salen del territorio de origen
    origen.tropas["poblacion_actual"] -= comprometidas

    gana_atacante = fuerza_atacante > fuerza_defensor
    if gana_atacante:
        sobrevivientes = max(1.0, fuerza_atacante - 0.7 * fuerza_defensor)
        defensor.tropas["dueno"] = origen.tropas["dueno"]
        defensor.tropas["poblacion_actual"] = sobrevivientes
        resultado = "gano_atacante"
        tropas_atk_final = sobrevivientes
        tropas_def_final = 0.0
    else:
        # El defensor resiste pero sufre bajas proporcionales al ataque
        defensor.tropas["poblacion_actual"] = max(1.0, pob_def - 0.6 * fuerza_atacante)
        resultado = "gano_defensor"
        tropas_atk_final = origen.tropas["poblacion_actual"]
        tropas_def_final = defensor.tropas["poblacion_actual"]

    if repo is not None:
        repo.registrar_batalla(
            partida_id, turno, origen.id, defensor.id, estado.h_activo,
            prediccion_euler=round(prediccion["euler"], 2) if prediccion else None,
            prediccion_rk4=round(prediccion["rk4"], 2) if prediccion else None,
            metodo_confiado=metodo_confiado, resultado=resultado,
            tropas_atacante=round(tropas_atk_final, 2),
            tropas_defensor=round(tropas_def_final, 2))

    return {
        "resultado": resultado,
        "fuerza_atacante": fuerza_atacante,
        "fuerza_defensor": fuerza_defensor,
        "gano_atacante": gana_atacante,
    }