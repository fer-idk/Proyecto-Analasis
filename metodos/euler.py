"""
euler.py
========
Metodo de Euler explicito, implementado DESDE CERO (sin scipy.integrate ni
ninguna libreria que resuelva la EDO por nosotros), tal como exige la guia.

Idea del metodo
---------------
Euler aproxima la solucion avanzando en linea recta usando la pendiente en
el punto actual:

        y_{n+1} = y_n + h * f(t_n, y_n)

Es decir: "parate donde estas, mira hacia donde apunta la derivada AHORA, y
camina un paso h en esa direccion". Es la formula mas simple posible.

Precision y estabilidad
------------------------
- Error local por paso: O(h^2). Error global: O(h)  -> es de PRIMER orden.
- Como solo usa la pendiente al inicio del intervalo, "no ve" la curvatura.
  En la logistica, cuando el paso h es grande, Euler SOBREPASA la capacidad K
  y empieza a oscilar; si h*r supera ~2, las oscilaciones crecen y el metodo
  se vuelve INESTABLE (diverge). Ese es justo el fenomeno que el juego deja
  ver al subir el slider de h.
"""


def paso(f, t, y, h):
    """
    Un unico paso de Euler.

    Parametros:
        f : funcion f(t, y) = dy/dt
        t : tiempo actual
        y : valor actual de la variable
        h : tamano del paso
    Devuelve:
        y en t + h (aproximado)
    """
    return y + h * f(t, y)


def integrar(f, y0, t0, t_final, h):
    """
    Integra la EDO desde t0 hasta t_final con paso h usando Euler.

    Devuelve dos listas paralelas (ts, ys) con toda la trayectoria, de modo
    que cada par (ts[i], ys[i]) puede guardarse en la base de datos como un
    registro de calculo.
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