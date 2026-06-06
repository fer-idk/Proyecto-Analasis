"""
seed_demo.py
============
Prueba de extremo a extremo de la capa de persistencia. Genera una base de
datos con 3 partidas usando los metodos numericos REALES (paquete metodos),
registra cada paso de calculo y unas batallas, y luego consulta la BD.

No es "juego real" todavia: es la prueba de que el pipeline
metodos -> repositorio -> SQLite funciona. Cuando el juego este montado,
se regenerara con datos de partidas jugadas de verdad.

Ejecutar desde la raiz del proyecto:  python3 seed_demo.py
"""

import json
import os
import random

from metodos import euler, rk4
from metodos.modelos import logistica, logistica_exacta
from persistencia.repositorio import Repositorio

RUTA_JSON = "data/departamentos.json"
RUTA_DB = "partidas/risk_demo.db"

# Empezamos de cero para que la demo sea reproducible
if os.path.exists(RUTA_DB):
    os.remove(RUTA_DB)

with open(RUTA_JSON, encoding="utf-8") as f:
    mapa = json.load(f)
deptos = {d["id"]: d for d in mapa["departamentos"]}

repo = Repositorio(RUTA_DB)
random.seed(7)

# Departamentos y pasos h que probaremos. Incluimos h grandes a proposito
# para que Euler muestre su inestabilidad y la BD lo registre.
muestra = ["san_miguel", "la_paz", "santa_ana", "san_salvador"]
pasos_h = [0.1, 1.0, 2.5]
TURNOS_PREDICCION = mapa["config_global"]["turnos_prediccion"]

for n_partida in range(1, 4):
    pid = repo.crear_partida(notas=f"Partida de prueba #{n_partida}")

    for turno in range(1, 4):  # 3 turnos por partida
        # Evento de ejemplo: en el turno 2 de cada partida erupciona el
        # Chaparrastique y golpea las tropas de San Miguel.
        evento_sm = "erupcion_chaparrastique" if turno == 2 else None

        for dep_id in muestra:
            dep = deptos[dep_id]
            r_ef = dep["tropas"]["r_base"]
            k_ef = dep["tropas"]["K_base"]
            N0 = dep["tropas"]["poblacion_actual"]
            evento = evento_sm if dep_id == "san_miguel" else None

            for h in pasos_h:
                f_log = logistica(r_ef, k_ef)
                te, ye = euler.integrar(f_log, N0, 0, TURNOS_PREDICCION, h)
                tr, yr = rk4.integrar(f_log, N0, 0, TURNOS_PREDICCION, h)
                repo.registrar_trayectoria(pid, turno, dep_id, "tropas",
                                           "euler", h, r_ef, k_ef, te, ye,
                                           evento=evento)
                repo.registrar_trayectoria(pid, turno, dep_id, "tropas",
                                           "rk4", h, r_ef, k_ef, tr, yr,
                                           evento=evento)

        # Una batalla por turno: San Miguel ataca a Usulutan. El jugador
        # "confia" en la prediccion de Euler con h grande (la que sobreestima).
        h_batalla = 2.5
        dep = deptos["san_miguel"]
        f_log = logistica(dep["tropas"]["r_base"], dep["tropas"]["K_base"])
        _, ye = euler.integrar(f_log, dep["tropas"]["poblacion_actual"], 0,
                               TURNOS_PREDICCION, h_batalla)
        _, yr = rk4.integrar(f_log, dep["tropas"]["poblacion_actual"], 0,
                             TURNOS_PREDICCION, h_batalla)
        pred_e, pred_r = ye[-1], yr[-1]
        # Si Euler sobreestima mucho las tropas, el ataque "esperaba" ganar
        # pero el resultado real (cercano a RK4) lo contradice.
        resultado = "gano_defensor" if pred_e > pred_r * 1.15 else "gano_atacante"
        repo.registrar_batalla(
            pid, turno, "san_miguel", "usulutan", h_batalla,
            prediccion_euler=round(pred_e, 2), prediccion_rk4=round(pred_r, 2),
            metodo_confiado="euler", resultado=resultado,
            tropas_atacante=round(pred_r, 2),
            tropas_defensor=round(deptos["usulutan"]["tropas"]["poblacion_actual"], 2))

    repo.finalizar_partida(pid, ganador=f"jugador_{random.randint(1, 2)}")

# ---------- Verificacion ----------
n_calc = len(repo.obtener_calculos())
n_bat = len(repo.obtener_batallas())
print(f"Base de datos generada en: {RUTA_DB}")
print(f"Partidas: 3   Calculos (pasos): {n_calc}   Batallas: {n_bat}\n")

print("Divergencia Euler vs RK4 segun el paso h (San Miguel, tropas):")
print(f"{'h':>5} | {'pred_euler':>11} | {'pred_rk4':>9} | {'divergencia':>11}")
print("-" * 46)
vistos = set()
for fila in repo.divergencia_por_h():
    if fila["departamento"] != "san_miguel":
        continue
    clave = fila["h"]
    if clave in vistos:
        continue
    vistos.add(clave)
    print(f"{fila['h']:>5.1f} | {fila['pred_euler']:>11.3f} | "
          f"{fila['pred_rk4']:>9.3f} | {fila['divergencia']:>11.3f}")

repo.cerrar()