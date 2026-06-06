"""
test_metodos.py
===============
Pruebas automaticas de euler.py y rk4.py contra la solucion exacta de la
logistica. Ejecutar desde la raiz del proyecto con:  pytest -v

Dos clases de prueba:
1. Exactitud: con h pequeno, ambos metodos deben pegarse a la solucion real.
2. Orden de convergencia: al reducir h a la mitad, el error de Euler debe
   bajar ~2x (orden 1) y el de RK4 debe bajar ~16x (orden 4).
"""

import math
from metodos import euler, rk4
from metodos.modelos import logistica, logistica_exacta

# Parametros de prueba (similares a un territorio real del juego)
R = 0.8
K = 60.0
N0 = 10.0
T0 = 0.0
T_FINAL = 4.0   # zona de transicion: la solucion todavia tiene curvatura


def error_global(metodo, h):
    """Error absoluto maximo de un metodo sobre toda la trayectoria."""
    f = logistica(R, K)
    exacta = logistica_exacta(R, K, N0)
    ts, ys = metodo.integrar(f, N0, T0, T_FINAL, h)
    return max(abs(y - exacta(t)) for t, y in zip(ts, ys))


def test_euler_exacto_con_h_pequeno():
    # Con h chico Euler debe quedar razonablemente cerca de la solucion real
    assert error_global(euler, 0.01) < 0.5


def test_rk4_muy_exacto_con_h_pequeno():
    # RK4 debe ser practicamente indistinguible de la solucion exacta
    assert error_global(rk4, 0.01) < 1e-4


def test_rk4_mas_preciso_que_euler():
    # Con el mismo h, RK4 siempre debe tener menos error que Euler
    h = 0.2
    assert error_global(rk4, h) < error_global(euler, h)


def test_orden_de_convergencia_euler():
    # Al pasar de h a h/2 el error de Euler debe reducirse ~2x (orden 1)
    e_h = error_global(euler, 0.1)
    e_h2 = error_global(euler, 0.05)
    orden = math.log(e_h / e_h2, 2)
    assert 0.8 < orden < 1.3


def test_orden_de_convergencia_rk4():
    # Al pasar de h a h/2 el error de RK4 debe reducirse ~16x (orden 4)
    e_h = error_global(rk4, 0.2)
    e_h2 = error_global(rk4, 0.1)
    orden = math.log(e_h / e_h2, 2)
    assert 3.7 < orden < 4.3


def test_euler_inestable_con_h_grande():
    # Con h*r > 2 (aqui h=3.0, r=0.8 -> 2.4) Euler debe SOBREPASAR K
    # notablemente: senal de inestabilidad numerica.
    f = logistica(R, K)
    _, ys = euler.integrar(f, N0, T0, 30.0, 3.0)
    assert max(ys) > K * 1.1   # se dispara por encima de la capacidad


def test_rk4_estable_con_el_mismo_h_grande():
    # Con el mismo h=3.0, RK4 NO debe dispararse: se mantiene <= K aprox.
    f = logistica(R, K)
    _, ys = rk4.integrar(f, N0, T0, 30.0, 3.0)
    assert max(ys) < K * 1.05