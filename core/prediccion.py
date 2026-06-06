"""
prediccion.py
=============
El PUENTE entre las tres capas. Toma un Territorio (con sus modificadores ya
aplicados), calcula la prediccion con Euler y RK4, y opcionalmente guarda cada
paso en la base de datos.

Es la funcion que el juego llama antes de cada batalla para mostrarle al
jugador las dos predicciones y dejarlo decidir. El territorio entrega sus
parametros EFECTIVOS (ya plegados los heroes y eventos), de modo que aqui solo
se ven numeros: la capa de metodos nunca sabe que detras hubo una Siguanaba.
"""

from metodos import euler, rk4
from metodos.modelos import logistica


def predecir(territorio, variable, h, turnos, repo=None,
             partida_id=None, turno=None):
    """
    Calcula la prediccion de Euler y RK4 para 'variable' ('tropas' o 'recurso')
    a 'turnos' de distancia, con paso h.

    Si se pasa 'repo' (y partida_id, turno), registra TODA la trayectoria de
    ambos metodos en la base de datos, etiquetada con el heroe y el evento
    activos en el territorio.

    Devuelve un dict:
        {
          'euler': prediccion final de Euler,
          'rk4':   prediccion final de RK4,
          'divergencia': |euler - rk4|,
          'r_efectiva', 'K_efectiva', 'N0'
        }
    """
    if variable == "tropas":
        r_ef, K_ef = territorio.parametros_tropas()
        N0 = territorio.tropas["poblacion_actual"]
    elif variable == "recurso":
        r_ef, K_ef = territorio.parametros_recurso()
        N0 = territorio.recurso["cantidad_actual"]
    else:
        raise ValueError("variable debe ser 'tropas' o 'recurso'")

    f = logistica(r_ef, K_ef)
    te, ye = euler.integrar(f, N0, 0, turnos, h)
    tr, yr = rk4.integrar(f, N0, 0, turnos, h)
    pred_e, pred_r = ye[-1], yr[-1]

    if repo is not None:
        evento = territorio.eventos_activos[0] if territorio.eventos_activos else None
        repo.registrar_trayectoria(partida_id, turno, territorio.id, variable,
                                   "euler", h, r_ef, K_ef, te, ye,
                                   heroe=territorio.heroe_presente, evento=evento)
        repo.registrar_trayectoria(partida_id, turno, territorio.id, variable,
                                   "rk4", h, r_ef, K_ef, tr, yr,
                                   heroe=territorio.heroe_presente, evento=evento)

    return {
        "euler": pred_e,
        "rk4": pred_r,
        "divergencia": abs(pred_e - pred_r),
        "r_efectiva": r_ef,
        "K_efectiva": K_ef,
        "N0": N0,
        # Trayectorias completas (mismos puntos de t para ambos metodos),
        # para que la interfaz pueda graficar Euler vs RK4.
        "ts": te,
        "euler_traj": ye,
        "rk4_traj": yr,
    }