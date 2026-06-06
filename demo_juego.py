"""
demo_juego.py
=============
Simula una mini-partida usando TODO el core junto. Ejecutar desde la raiz:
    python3 demo_juego.py
"""

import os

from core.cargador import cargar_mapa
from core.game_state import EstadoJuego
from core.jugador import Jugador
from core.turnos import MotorTurnos
from core import comandantes, eventos, economia, batalla
from core.prediccion import predecir
from persistencia.repositorio import Repositorio

RUTA_JSON = "data/departamentos.json"
RUTA_DB = "partidas/risk_juego_demo.db"
if os.path.exists(RUTA_DB):
    os.remove(RUTA_DB)

territorios, config = cargar_mapa(RUTA_JSON)

# --- Jugadores y reparto del oriente ---
j1 = Jugador("j1", "Cuscatlecos", comandante="vendedor_minutas")
j2 = Jugador("j2", "Pipiles", comandante="siguanaba")
jugadores = {"j1": j1, "j2": j2}
for tid in ("san_miguel", "morazan", "la_union"):
    territorios[tid].tropas["dueno"] = "j1"
for tid in ("usulutan", "la_paz", "san_vicente"):
    territorios[tid].tropas["dueno"] = "j2"

estado = EstadoJuego(territorios, jugadores, config)
repo = Repositorio(RUTA_DB)
pid = repo.crear_partida(notas="Demo de partida completa")
motor = MotorTurnos(estado, repo, pid)

sm = territorios["san_miguel"]
us = territorios["usulutan"]

print("=== TURNO 1 (metodo=RK4, h=0.1: crecimiento estable) ===")
estado.metodo_activo, estado.h_activo = "rk4", 0.1
comandantes.vendedor_minutas_fresco(sm)          # j1 sube K de San Miguel
print(f"San Miguel tropas antes refuerzo: {sm.tropas['poblacion_actual']:.1f}")
motor.fase_refuerzo()
print(f"San Miguel tropas tras refuerzo:  {sm.tropas['poblacion_actual']:.1f}")

# j2 usa la Siguanaba sobre San Miguel (territorio enemigo): r negativa
comandantes.siguanaba_terror(sm)
r_ef, _ = sm.parametros_tropas()
print(f"Tras Terror de la Siguanaba, r efectiva de San Miguel: {r_ef:+.2f}")

# Evento: huracan golpea La Paz (de j2)
eventos.huracan(territorios["la_paz"])
print("Huracan activo en La Paz (r negativa 2 turnos).")

# Batalla: j1 ataca Usulutan desde San Miguel. Primero se muestran predicciones.
pred = predecir(us, "tropas", estado.h_activo, config["turnos_prediccion"],
                repo, pid, estado.turno)
print(f"\nPrediccion defensa de Usulutan ({config['turnos_prediccion']} turnos): "
      f"Euler={pred['euler']:.1f}  RK4={pred['rk4']:.1f}")
res = batalla.resolver(estado, sm, us, tropas_comprometidas=40,
                       prediccion=pred, metodo_confiado="rk4",
                       repo=repo, partida_id=pid, turno=estado.turno)
print(f"Batalla San Miguel -> Usulutan: {res['resultado']} "
      f"(fuerza {res['fuerza_atacante']:.0f} vs {res['fuerza_defensor']:.0f})")
print(f"Usulutan ahora es de: {us.tropas['dueno']}")

# Economia: j1 extrae pupusas de San Miguel
ext = economia.extraer(sm, cantidad=10)
j1.ingresar("pupusas", ext["extraido"])
print(f"\nj1 extrajo {ext['extraido']:.1f} pupusas "
      f"(sostenible={ext['sostenible']:.1f}, sobreexplota={ext['sobreexplota']})")

motor.fin_de_turno()

# --- Comparacion: el costo de elegir mal el metodo (parametros limpios) ---
print("\n=== El costo de elegir mal el metodo (un turno) ===")
from metodos import euler as me, rk4 as mr
from metodos.modelos import logistica
# Parametros representativos tipo pupusas de La Paz: r=1.0, K=150
N0_cmp, r_cmp, K_cmp = 20.0, 1.0, 150.0
f = logistica(r_cmp, K_cmp)
print(f"N inicial={N0_cmp:.0f}, r={r_cmp:+.2f}, K={K_cmp:.0f}  (umbral Euler: h>2)")
for h in (0.1, 2.5):
    print(f"  h={h}: Euler -> {me.paso(f,0,N0_cmp,h):7.1f}   "
          f"RK4 -> {mr.paso(f,0,N0_cmp,h):7.1f}")

# --- Mostrar colapso por sobreexplotacion en varios turnos ---
print("\n=== Sobreexplotacion de un recurso (colapso logistico) ===")
lu = territorios["la_union"]
print(f"La Union, recurso={lu.recurso['tipo']}, "
      f"sostenible/turno={economia.rendimiento_maximo_sostenible(*lu.parametros_recurso()):.1f}")
estado.metodo_activo, estado.h_activo = "rk4", 0.3
for turno in range(1, 6):
    motor.fase_refuerzo()                       # el recurso se regenera
    ext = economia.extraer(lu, cantidad=30)     # pero extraemos de mas
    print(f"  turno {turno}: extraido={ext['extraido']:5.1f}  "
          f"queda={lu.recurso['cantidad_actual']:6.1f}  "
          f"colapso={ext['en_colapso']}")
    motor.fin_de_turno()

print(f"\nCalculos en BD: {len(repo.obtener_calculos())}   "
      f"Batallas: {len(repo.obtener_batallas())}")
repo.finalizar_partida(pid, ganador="j1")
repo.cerrar()
print(f"Base de datos: {RUTA_DB}")