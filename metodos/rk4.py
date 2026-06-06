"""
rk4.py
======
Metodo de Runge-Kutta de 4to orden (RK4), implementado DESDE CERO, tal como
exige la guia.

Idea del metodo
---------------
En lugar de usar una sola pendiente como Euler, RK4 evalua la derivada en
CUATRO puntos dentro del intervalo y los combina con un promedio ponderado.
Asi "anticipa" la curvatura de la solucion:

        k1 = f(t,         y)
        k2 = f(t + h/2,   y + (h/2)*k1)
        k3 = f(t + h/2,   y + (h/2)*k2)
        k4 = f(t + h,     y + h*k3)

        y_{n+1} = y_n + (h/6) * (k1 + 2*k2 + 2*k3 + k4)

Interpretacion: k1 es la pendiente al inicio, k2 y k3 son dos estimaciones
en el medio del paso, y k4 al final. El promedio (con doble peso al centro)
da una direccion mucho mas fiel que la recta unica de Euler.

Precision y estabilidad
-----------------------
- Error local por paso: O(h^5). Error global: O(h^4) -> es de CUARTO orden.
- Su region de estabilidad es mucho mayor que la de Euler, por lo que sigue
  pegado a la solucion exacta de la logistica con pasos h en los que Euler
  ya oscila o diverge. Ese contraste es el nucleo del analisis de la defensa.
- Cuesta 4 evaluaciones de f por paso (Euler solo 1): mas preciso pero mas
  caro. Es el clasico compromiso costo/precision.
"""


def paso(f, t, y, h):
    """
    Un unico paso de RK4.

    Parametros:
        f : funcion f(t, y) = dy/dt
        t : tiempo actual
        y : valor actual de la variable
        h : tamano del paso
    Devuelve:
        y en t + h (aproximado con cuarto orden de precision)
    """
    k1 = f(t, y)
    k2 = f(t + h / 2.0, y + (h / 2.0) * k1)
    k3 = f(t + h / 2.0, y + (h / 2.0) * k2)
    k4 = f(t + h, y + h * k3)
    return y + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def integrar(f, y0, t0, t_final, h):
    """
    Integra la EDO desde t0 hasta t_final con paso h usando RK4.

    Devuelve (ts, ys), dos listas paralelas con toda la trayectoria para
    poder registrar cada paso en la base de datos.
    """
    n_pasos = int(round((t_final - t0) / h))
    ts = [t0]
    ys = [y0]
    t, y = t0, y0
    for _ in range(n_pasos):
        y = paso(f, t, y, h)
        t = t + h
        ts.append(t)
        ys.append(y)
    return ts, ys