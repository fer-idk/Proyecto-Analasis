"""
modelos.py
==========
Define las ecuaciones diferenciales del juego y, cuando existe, su solucion
analitica exacta (util para VALIDAR los metodos numericos).

Regla de diseno: aqui NO se resuelve nada numericamente. Solo se construyen
las funciones f(t, y) = dy/dt que luego reciben euler.py y rk4.py. De esta
forma los metodos numericos quedan completamente desacoplados del juego:
ellos solo ven una funcion y unos numeros.

La ecuacion central es la LOGISTICA:

        dN/dt = r * N * (1 - N / K)

donde:
    N : poblacion actual (tropas o cantidad de un recurso)
    r : tasa de crecimiento intrinseca
    K : capacidad maxima (carrying capacity) del territorio

Tanto el crecimiento de tropas como el "farmeo" de recursos usan ESTA MISMA
ecuacion con distintos parametros. Por eso un solo par de metodos
(euler/rk4) resuelve las dos mecanicas.
"""

import math


def logistica(r, K):
    """
    Construye la funcion f(t, N) de la ecuacion logistica con parametros
    (r, K) ya fijados.

    Devuelve una funcion lista para pasar a euler.paso / rk4.paso.

    Ejemplo:
        f = logistica(r=0.8, K=60.0)
        f(0.0, 22.0)  ->  0.8 * 22 * (1 - 22/60)
    """
    def f(t, N):
        return r * N * (1.0 - N / K)
    return f


def logistica_exacta(r, K, N0):
    """
    Solucion analitica exacta de la logistica para condicion inicial N(0)=N0:

                    K * N0
        N(t) = ----------------------------
               N0 + (K - N0) * exp(-r * t)

    Sirve como "verdad de referencia" para medir el error de Euler y RK4.
    El metodo numerico NO la usa nunca; solo la validacion y el informe.
    """
    def N(t):
        return (K * N0) / (N0 + (K - N0) * math.exp(-r * t))
    return N