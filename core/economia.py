"""
economia.py
===========
Extraccion ("farmeo") de recursos. La generacion de cada recurso sigue la
misma logistica que las tropas, asi que aqui aprovechamos una propiedad
matematica elegante de ese modelo:

    El RENDIMIENTO MAXIMO SOSTENIBLE de la logistica es  r*K/4,
    que ocurre cuando la poblacion esta en N = K/2.

Si el jugador extrae por debajo de ese rendimiento, el recurso se regenera y
se mantiene en equilibrio. Si extrae por encima de forma sostenida, la
poblacion del recurso cae por debajo de K/2 y entra en COLAPSO: cada vez se
regenera menos hasta agotarse. Es la tension "extraer lo justo vs exprimir".
"""


def rendimiento_maximo_sostenible(r, K):
    """Cosecha por turno que la logistica puede reponer indefinidamente."""
    return r * K / 4.0


def extraer(territorio, cantidad):
    """
    Extrae 'cantidad' del recurso del territorio (sin pasar de lo disponible).

    Devuelve un dict con:
        extraido    : cuanto se obtuvo realmente
        sostenible  : el rendimiento maximo sostenible r*K/4
        sobreexplota: True si esta extraccion supera lo sostenible
        en_colapso  : True si el recurso quedo por debajo de K/2 (zona de caida)
    """
    r, K = territorio.parametros_recurso()
    disponible = territorio.recurso["cantidad_actual"]
    extraido = min(cantidad, disponible)
    territorio.recurso["cantidad_actual"] = disponible - extraido

    sostenible = rendimiento_maximo_sostenible(r, K)
    restante = territorio.recurso["cantidad_actual"]
    return {
        "extraido": extraido,
        "sostenible": sostenible,
        "sobreexplota": extraido > sostenible,
        "en_colapso": restante < K / 2.0,
    }