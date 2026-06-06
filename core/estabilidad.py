"""
estabilidad.py
==============
Clasifica la eleccion de paso h en ZONAS DE ESTABILIDAD y traduce esa zona en
un efecto sobre la batalla. Es el mecanismo que conecta directamente la teoria
numerica con la jugabilidad: elegir un h grande con Euler tiene consecuencias.

El parametro clave es el producto  h * r  (para la logistica resuelta con Euler
explicito, el punto fijo pierde estabilidad cuando h*r supera 2, y aparece caos
cerca de 2.57; es el mismo fenomeno del mapa logistico):

    Verde    h*r < 1.0   -> estable y preciso
    Amarilla 1.0..2.0    -> precaucion, Euler ya se desvia
    Roja     2.0..2.5    -> Euler oscila (inestable)
    Caos     >= 2.5      -> Euler diverge / caotico

Efecto en combate: como RK4 es estable, casi no sufre. Euler, en cambio, en
zona Roja o Caos engana al jugador con una prediccion irreal, y eso se castiga
reduciendo su fuerza efectiva de ataque. Asi, confiar en Euler con h grande
puede costar una batalla que se habria ganado.
"""

ZONAS = ("verde", "amarilla", "roja", "caos")

DESCRIPCION = {
    "verde": "Estable y preciso",
    "amarilla": "Precaucion: Euler se desvia",
    "roja": "Inestable: Euler oscila",
    "caos": "Caotico: Euler diverge",
}

# Penalizacion a la fuerza del atacante segun metodo y zona
_FACTOR = {
    "rk4":   {"verde": 1.00, "amarilla": 1.00, "roja": 0.95, "caos": 0.90},
    "euler": {"verde": 1.00, "amarilla": 0.95, "roja": 0.80, "caos": 0.60},
}


def clasificar(h, r):
    """Devuelve la zona de estabilidad para un paso h y una tasa r."""
    hr = h * abs(r)
    if hr < 1.0:
        return "verde"
    if hr < 2.0:
        return "amarilla"
    if hr < 2.5:
        return "roja"
    return "caos"


def factor_combate(metodo, zona):
    """Multiplicador (<=1) sobre la fuerza de ataque por la zona de estabilidad."""
    return _FACTOR.get(metodo, _FACTOR["rk4"]).get(zona, 1.0)