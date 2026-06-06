"""
demo_core.py
============
Prueba en vivo de la capa core: muestra como heroes y eventos modifican los
parametros EFECTIVOS de un territorio y como eso cambia la prediccion de
Euler y RK4. Ejecutar desde la raiz:  python3 demo_core.py
"""

import os

from core.cargador import cargar_mapa
from core import comandantes, eventos
from core.prediccion import predecir
from persistencia.repositorio import Repositorio

RUTA_JSON = "data/departamentos.json"
RUTA_DB = "partidas/risk_core_demo.db"
if os.path.exists(RUTA_DB):
    os.remove(RUTA_DB)

territorios, config = cargar_mapa(RUTA_JSON)
h = config["h_default"]
turnos_pred = config["turnos_prediccion"]
print(f"Mapa cargado: {len(territorios)} departamentos. "
      f"h={h}, turnos_prediccion={turnos_pred}\n")

repo = Repositorio(RUTA_DB)
pid = repo.crear_partida(notas="Demo de la capa core")

# --- 1. SIGUANABA: vuelve r negativa (desgaste) en un territorio enemigo ---
usulutan = territorios["usulutan"]
r0, K0 = usulutan.parametros_tropas()
comandantes.siguanaba_terror(usulutan)            # Terror sobre Usulutan
r1, K1 = usulutan.parametros_tropas()
print(f"[Siguanaba] Usulutan  r: {r0:+.2f} -> {r1:+.2f}  (K={K1:.0f})")
pre = predecir(usulutan, "tropas", h, turnos_pred, repo, pid, turno=1)
print(f"            Prediccion {turnos_pred} turnos: "
      f"Euler={pre['euler']:.1f}  RK4={pre['rk4']:.1f}  "
      f"(N0={pre['N0']:.0f}) -> las tropas DECAEN\n")

# --- 2. VENDEDOR DE MINUTAS: sube K mientras este presente ---
ss = territorios["san_salvador"]
r0, K0 = ss.parametros_tropas()
comandantes.vendedor_minutas_fresco(ss)           # Fresco sobre San Salvador
r1, K1 = ss.parametros_tropas()
print(f"[Vendedor]  San Salvador  K: {K0:.0f} -> {K1:.0f}  (r={r1:+.2f})")
pre = predecir(ss, "tropas", h, turnos_pred, repo, pid, turno=1)
print(f"            Prediccion: Euler={pre['euler']:.1f}  RK4={pre['rk4']:.1f}\n")

# --- 3. ERUPCION: golpe discreto -30% en San Miguel ---
sm = territorios["san_miguel"]
antes = sm.tropas["poblacion_actual"]
perdidas = eventos.erupcion_chaparrastique(sm)
print(f"[Erupcion]  San Miguel  tropas: {antes:.0f} -> "
      f"{sm.tropas['poblacion_actual']:.0f}  (perdio {perdidas:.0f}, "
      f"produccion anulada={sm.produccion_anulada})\n")

# --- 4. MARCHA UES: bloqueo discreto + bono de defensa ---
eventos.marcha_ues(ss)
print(f"[Marcha]    San Salvador  bloqueado={ss.bloqueado}  "
      f"bono_defensa={ss.bono_defensa}\n")

# --- 5. CIPITIO: teletransporte entre NO vecinos ---
lu = territorios["la_union"]
print(f"[Cipitio]   La Union vecino de Santa Ana? "
      f"{lu.es_vecino_de('santa_ana')}")
movidas = comandantes.cipitio_teletransporte(lu, territorios["santa_ana"], 5)
print(f"            Teletransporto {movidas:.0f} tropas La Union -> Santa Ana "
      f"(ignorando fronteras)\n")

# --- 6. PASO DEL TIEMPO: el huracan dura 2 turnos, el Vendedor persiste ---
eventos.huracan(territorios["la_paz"])             # huracan en La Paz (turnos=2)
lp = territorios["la_paz"]
print("[Tiempo]    Evolucion de r efectiva en La Paz (huracan, 2 turnos):")
for t in range(0, 4):
    r_ef, _ = lp.parametros_tropas()
    print(f"            turno {t}: r_ef = {r_ef:+.2f}")
    lp.fin_de_turno()

# El Vendedor en San Salvador NO expira con el tiempo (es permanente)
ss.fin_de_turno(); ss.fin_de_turno()
_, K_ss = ss.parametros_tropas()
print(f"\n[Tiempo]    San Salvador tras 2 turnos, K_ef sigue = {K_ss:.0f} "
      f"(el Vendedor persiste)\n")

# --- Verificacion BD ---
print(f"Calculos guardados en BD: {len(repo.obtener_calculos())}")
repo.finalizar_partida(pid, ganador="jugador_1")
repo.cerrar()
print(f"Base de datos: {RUTA_DB}")